from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import pandas as pd

from src.database.db_reader import read_sql, read_table
from src.reporter.banners import (
    banner_comparison_groups,
    banner_order,
    expand_banner,
    normalize_banner_mode,
    normalize_banners,
)
from src.reporter.calculations import (
    attach_report_weights,
    bottom2box,
    frequency_summary,
    nps_group,
    nps_summary,
    rm_summary,
    scale_summary,
    top2box,
)
from src.reporter.charts import build_chart
from src.reporter.filters import (
    apply_multiple_filters,
    summarize_filters,
)
from src.reporter.multi_metrics import (
    build_multi_metric_table,
    validate_calculations_for_question,
)
from src.reporter.significance import (
    column_legend,
    combine_significance_tables,
    insufficient_bases,
    mean_significance,
    percentage_significance,
)
from src.utils.question_order import order_question_catalog


@dataclass
class ReportResult:
    question_id: str
    title: str
    section: str
    question_type: str
    calculation: str
    calculations: list[str]
    base: int
    banner: str | None
    banners: list[str]
    filters: dict[str, list[object]]
    filter_summary: str
    filter_variable: str | None
    filter_display: str | None
    ponderador: str | None
    display_mode: str
    response_order: str
    confidence: float | None
    significance_display: str
    table: pd.DataFrame
    summary: pd.DataFrame
    summaries: dict[str, pd.DataFrame]
    significance: pd.DataFrame = field(default_factory=pd.DataFrame)
    significance_legend: pd.DataFrame = field(default_factory=pd.DataFrame)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    figure: Any = None
    question_order: float | None = None
    min_base: int | None = None
    recommended_banners: list[str] = field(default_factory=list)
    recommended_filters: list[str] = field(default_factory=list)
    recommendation_details: dict[str, dict[str, str]] = field(
        default_factory=dict
    )
    base_before_filters: int | None = None
    banner_mode: str = "nested"


def available_questions(
    db_path: Path,
    datamap_paths=None,
) -> pd.DataFrame:
    try:
        questions = read_table(db_path, "preguntas")
    except Exception:
        return pd.DataFrame(
            columns=["pregunta_id", "texto_pregunta", "tipo_calculo"]
        )
    if questions.empty:
        return questions
    questions = questions.drop_duplicates("pregunta_id").copy()
    if "usar_en_dashboard" in questions.columns:
        active = pd.to_numeric(
            questions["usar_en_dashboard"], errors="coerce"
        ).fillna(0)
        questions = questions[active.astype(bool)]
    enriched = _enrich_question_catalog(
        db_path, questions.reset_index(drop=True)
    )
    variables = _safe_read_table(db_path, "variables")
    if (
        not variables.empty
        and {"pregunta_id", "clasificacion_analitica"}.issubset(
            variables.columns
        )
    ):
        classifications = (
            variables.groupby("pregunta_id", sort=False)[
                "clasificacion_analitica"
            ]
            .agg(
                lambda values: " | ".join(
                    dict.fromkeys(
                        values.dropna().astype(str).tolist()
                    )
                )
            )
            .rename("clasificacion_analitica")
        )
        enriched = enriched.merge(
            classifications,
            left_on="pregunta_id",
            right_index=True,
            how="left",
        )
    return order_question_catalog(enriched, datamap_paths)


def _enrich_question_catalog(
    db_path: Path,
    questions: pd.DataFrame,
) -> pd.DataFrame:
    response_ids = _question_ids_from_table(db_path, "respuestas_long")
    rm_ids = _question_ids_from_table(
        db_path, "multirrespuesta_long"
    )
    scale_ids = _question_ids_from_table(db_path, "escalas_long")
    open_ids = _question_ids_from_table(db_path, "abiertas")
    multi_ids = _multi_response_question_ids(db_path)

    result = questions.copy()
    result["seccion_reporter"] = result.apply(
        lambda row: _derive_section(
            row.get("seccion"), row.get("pregunta_id")
        ),
        axis=1,
    )
    result["tipo_pregunta_reporter"] = result.apply(
        lambda row: _infer_question_type(
            row,
            str(row.get("pregunta_id", "")),
            response_ids,
            rm_ids,
            scale_ids,
            open_ids,
            multi_ids,
        ),
        axis=1,
    )
    analytical = result[
        result["tipo_pregunta_reporter"] != "Requiere validación"
    ]
    return (
        analytical.reset_index(drop=True)
        if not analytical.empty
        else result.reset_index(drop=True)
    )


def _safe_read_table(db_path: Path, table: str) -> pd.DataFrame:
    try:
        return read_table(db_path, table)
    except Exception:
        return pd.DataFrame()


def _question_ids_from_table(db_path: Path, table: str) -> set[str]:
    try:
        frame = read_sql(
            db_path,
            f'SELECT DISTINCT pregunta_id FROM "{table}" '
            "WHERE pregunta_id IS NOT NULL",
        )
    except Exception:
        return set()
    return _question_ids(frame)


def _multi_response_question_ids(db_path: Path) -> set[str]:
    try:
        frame = read_sql(
            db_path,
            """
            SELECT DISTINCT pregunta_id
            FROM (
                SELECT pregunta_id, id_respondente, COUNT(*) AS n
                FROM respuestas_long
                GROUP BY pregunta_id, id_respondente
                HAVING n > 1
            )
            """,
        )
    except Exception:
        return set()
    return _question_ids(frame)


def _question_ids(df: pd.DataFrame) -> set[str]:
    if df.empty or "pregunta_id" not in df.columns:
        return set()
    return set(df["pregunta_id"].dropna().astype(str))


def _infer_question_type(
    row: pd.Series,
    question_id: str,
    response_ids: set[str],
    rm_ids: set[str],
    scale_ids: set[str],
    open_ids: set[str],
    multi_ids: set[str],
) -> str:
    metadata = " ".join(
        str(row.get(column) or "")
        for column in (
            "tipo_pregunta",
            "tipo_calculo",
            "tipo_estructura_grid",
        )
    ).lower()
    normalized_metadata = _normalize_metadata(metadata)
    if "grid_rm_loop" in normalized_metadata:
        return "GRID_RM_LOOP"
    if "rm_dicotomica_label" in normalized_metadata:
        return "RM_DICOTOMICA_LABEL"
    if "nps" in metadata:
        return "NPS"
    if question_id in scale_ids or (
        "grid_rm_loop" not in normalized_metadata
        and any(
            token in metadata
            for token in (
                "escala",
                "grid",
                "media",
                "top2box",
                "bottombox",
            )
        )
    ):
        return "Escala"
    if (
        question_id in rm_ids
        or question_id in multi_ids
        or metadata.startswith("rm")
        or any(
            token in metadata
            for token in ("multirrespuesta", "multiple", " rm")
        )
    ):
        return "RM"
    if question_id in response_ids:
        return "RU"
    if question_id in open_ids or "abierta" in metadata:
        return "Abierta"
    return "Requiere validación"


def _normalize_metadata(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _is_rm_question_type(value: object) -> bool:
    normalized = _normalize_metadata(value)
    return normalized in {
        "rm",
        "rm_dicotomica_label",
        "grid_rm_loop",
    }


def _is_scale_question_type(value: object) -> bool:
    normalized = _normalize_metadata(value)
    return normalized in {"escala", "nps"}


def _derive_section(section: object, question_id: object) -> str:
    raw_section = str(section or "").strip()
    if raw_section and raw_section.lower() not in {"nan", "none"}:
        return (
            raw_section
            if raw_section.lower().startswith("sección")
            else f"Sección {raw_section}"
        )
    match = re.match(r"([A-Za-z]+)", str(question_id or "").strip())
    if match:
        return f"Sección {match.group(1).upper()}"
    return "General"


def generate_report(
    db_path: Path,
    question_id: str,
    calculation: str = "Frecuencia",
    banner: str | list[str] | tuple[str, ...] | None = None,
    filter_variable: str | None = None,
    filter_value: object | None = None,
    filter_display: str | None = None,
    ponderador: str | None = None,
    display_mode: str = "n y %",
    include_significance: bool = False,
    confidence: float = 0.95,
    min_base: int = 30,
    *,
    calculations: list[str] | None = None,
    banner_mode: str = "nested",
    filters: dict[str, list[object]] | None = None,
    filter_labels: dict[str, dict[str, str] | list[str]] | None = None,
    significance_display: str | None = None,
    response_order: str = "Orden de Value Labels",
    question_order: float | None = None,
    recommended_banners: list[str] | None = None,
    recommended_filters: list[str] | None = None,
    recommendation_details: dict[
        str, dict[str, str]
    ] | None = None,
) -> ReportResult:
    questions = read_table(db_path, "preguntas")
    respondentes = read_table(db_path, "respondentes")
    opciones = read_table(db_path, "opciones")
    banners = normalize_banners(banner, respondentes)
    banner_mode = normalize_banner_mode(banner_mode)
    banner_display = " + ".join(banners) if banners else None
    question = questions[
        questions["pregunta_id"].astype(str) == str(question_id)
    ]
    question_row = question.iloc[0] if not question.empty else pd.Series()
    title = str(question_row.get("texto_pregunta") or question_id)
    requested = calculations or _legacy_calculations(
        calculation, display_mode, bool(ponderador)
    )
    legacy_filter = filters is None and bool(filter_variable)
    filters = _normalize_filters(
        filters, filter_variable, filter_value
    )
    filter_summary = summarize_filters(filters, filter_labels)
    if legacy_filter and filter_variable and filter_display:
        filter_summary = f"{filter_variable}: {filter_display}"

    selected_respondents = apply_multiple_filters(respondentes, filters)
    response_raw = _read_question_table(
        db_path, "respuestas_long", question_id
    )
    rm_raw = _read_question_table(
        db_path, "multirrespuesta_long", question_id
    )
    native_scale = _read_question_table(
        db_path, "escalas_long", question_id
    )
    open_raw = _read_question_table(
        db_path, "abiertas", question_id
    )
    multi_ids = set()
    if {
        "pregunta_id",
        "id_respondente",
    }.issubset(response_raw.columns):
        max_responses = response_raw.groupby(
            "id_respondente"
        ).size().max()
        if pd.notna(max_responses) and max_responses > 1:
            multi_ids.add(str(question_id))
    question_type_display = _infer_question_type(
        question_row,
        str(question_id),
        _question_ids(response_raw),
        _question_ids(rm_raw),
        _question_ids(native_scale),
        _question_ids(open_raw),
        multi_ids,
    )
    section_display = _derive_section(
        question_row.get("seccion"), question_id
    )
    metadata_text = " ".join(
        str(question_row.get(column) or "")
        for column in (
            "tipo_pregunta",
            "tipo_calculo",
            "tipo_estructura_grid",
        )
    )
    rm_like_question = _is_rm_question_type(question_type_display)
    scale_like_question = _is_scale_question_type(question_type_display)
    metadata_is_scale = scale_like_question or (
        not rm_like_question
        and any(
            token in metadata_text.lower()
            for token in (
                "escala",
                "grid",
                "media",
                "top2box",
                "bottombox",
                "nps",
            )
        )
    )
    scale_raw = native_scale
    if scale_raw.empty and metadata_is_scale:
        scale_raw = _scale_fallback(response_raw)

    question_type = metadata_text
    if rm_like_question:
        question_type += " __rm__"
    if scale_like_question:
        question_type += " __scale__"
    if question_type_display == "NPS" or (
        not scale_raw.empty
        and "nps_grupo" in scale_raw.columns
        and scale_raw["nps_grupo"].isin(
            ["Promotor", "Pasivo", "Detractor"]
        ).any()
    ):
        question_type += " __nps__"

    valid_calculations, warnings = validate_calculations_for_question(
        question_type, requested
    )
    if not ponderador:
        weighted = {
            "n ponderado",
            "% ponderado",
        }.intersection(valid_calculations)
        if weighted:
            valid_calculations = [
                item for item in valid_calculations if item not in weighted
            ]
            warnings.append(
                "Las métricas ponderadas requieren seleccionar un ponderador."
            )
    if not valid_calculations:
        warnings.append(
            "No hay cálculos aplicables para esta selección."
        )

    valid_ids = set(
        selected_respondents["id_respondente"].astype(str)
    )
    response_data = _prepare_data(
        response_raw,
        valid_ids,
        selected_respondents,
        opciones,
        banners,
        ponderador,
        response_column="respuesta_label",
        banner_mode=banner_mode,
    )
    rm_data = _prepare_data(
        rm_raw,
        valid_ids,
        selected_respondents,
        opciones,
        banners,
        ponderador,
        response_column="respuesta_label",
        banner_mode=banner_mode,
    )
    scale_data = _prepare_data(
        scale_raw,
        valid_ids,
        selected_respondents,
        opciones,
        banners,
        ponderador,
        banner_mode=banner_mode,
    )
    if response_data.empty and not rm_data.empty:
        response_data = rm_data.copy()
    if (
        rm_like_question
        and rm_data.empty
        and not response_data.empty
    ):
        rm_data = response_data.drop_duplicates(
            ["id_respondente", "banner", "respuesta"]
        ).copy()
    if response_data.empty and not scale_data.empty:
        response_data = scale_data.copy()
        response_data["respuesta"] = response_data.get(
            "respuesta_label",
            response_data["valor"].astype(str),
        )

    base_sources = [response_raw, rm_raw, scale_raw]
    source_ids = set()
    for source in base_sources:
        if not source.empty and "id_respondente" in source:
            source_ids.update(source["id_respondente"].astype(str))
    base = len(valid_ids.intersection(source_ids))
    base_before_filters = len(
        set(respondentes["id_respondente"].astype(str)).intersection(
            source_ids
        )
    )

    summaries = {
        "frequency": (
            frequency_summary(response_data)
            if not response_data.empty
            and {"respuesta", "banner", "_peso"}.issubset(
                response_data.columns
            )
            else pd.DataFrame()
        ),
        "rm": (
            rm_summary(rm_data) if not rm_data.empty else pd.DataFrame()
        ),
        "scale": (
            scale_summary(scale_data)
            if not scale_data.empty
            else pd.DataFrame()
        ),
        "nps": (
            nps_summary(scale_data)
            if not scale_data.empty
            and "nps_grupo" in scale_data.columns
            else pd.DataFrame()
        ),
    }
    summaries = _order_response_summaries(
        summaries,
        opciones,
        str(question_id),
        response_order,
    )

    significance_display = _normalize_significance_display(
        significance_display, include_significance
    )
    significance = pd.DataFrame()
    legend = pd.DataFrame()
    summary_for_legend = _primary_summary(
        summaries, valid_calculations
    )
    comparison_groups = (
        banner_comparison_groups(
            summary_for_legend["banner"],
            banners,
            banner_mode,
        )
        if not summary_for_legend.empty
        and "banner" in summary_for_legend.columns
        else None
    )
    if (
        significance_display != "none"
        and banners
        and valid_calculations
    ):
        significance = _multi_significance(
            summaries,
            scale_data,
            valid_calculations,
            confidence,
            min_base,
            comparison_groups,
        )
        if not summary_for_legend.empty:
            categories = [
                item
                for item in banner_order(summary_for_legend["banner"])
                if item != "Total"
            ]
            legend = column_legend(categories)

    table = build_multi_metric_table(
        question_id,
        banner=banners,
        filters=filters,
        weight=ponderador,
        calculations=valid_calculations,
        summaries=summaries,
        significance=significance,
        significance_mode=significance_display,
    )
    primary_summary = _primary_summary(summaries, valid_calculations)
    chart_calculation = _chart_calculation(valid_calculations)
    figure = build_chart(
        chart_calculation,
        primary_summary,
        title,
        bool(banners),
        selected_calculations=valid_calculations,
    )
    notes = _method_notes(
        valid_calculations,
        banner_display,
        filter_summary,
        ponderador,
        significance_display,
        confidence,
        min_base,
        primary_summary,
        banner_mode,
    )
    return ReportResult(
        question_id=str(question_id),
        title=title,
        section=section_display,
        question_type=question_type_display,
        calculation=chart_calculation,
        calculations=valid_calculations,
        base=base,
        banner=banner_display,
        banners=banners,
        filters=filters,
        filter_summary=filter_summary,
        filter_variable=next(iter(filters), None),
        filter_display=filter_summary,
        ponderador=ponderador,
        display_mode=display_mode,
        response_order=response_order,
        confidence=(
            confidence if significance_display != "none" else None
        ),
        significance_display=significance_display,
        table=table,
        summary=primary_summary,
        summaries=summaries,
        significance=significance,
        significance_legend=legend,
        notes=notes,
        warnings=warnings,
        figure=figure,
        question_order=question_order,
        min_base=(
            min_base if significance_display != "none" else None
        ),
        recommended_banners=recommended_banners or [],
        recommended_filters=recommended_filters or [],
        recommendation_details=recommendation_details or {},
        base_before_filters=base_before_filters,
        banner_mode=banner_mode,
    )


def _prepare_data(
    data: pd.DataFrame,
    valid_ids: set[str],
    respondentes: pd.DataFrame,
    opciones: pd.DataFrame,
    banner: str | list[str] | tuple[str, ...] | None,
    ponderador: str | None,
    response_column: str | None = None,
    banner_mode: str = "nested",
) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    result = data[
        data["id_respondente"].astype(str).isin(valid_ids)
    ].copy()
    if response_column and response_column in result.columns:
        result = result.rename(columns={response_column: "respuesta"})
    result = attach_report_weights(result, respondentes, ponderador)
    return expand_banner(
        result,
        respondentes,
        opciones,
        banner,
        mode=banner_mode,
    )


def _read_question_table(
    db_path: Path, table: str, question_id: str
) -> pd.DataFrame:
    try:
        data = read_sql(
            db_path,
            f'SELECT * FROM "{table}" WHERE pregunta_id = ?',
            (str(question_id),),
        )
    except Exception:
        return pd.DataFrame()
    return data.copy()


def _scale_fallback(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    result = data.copy()
    result["valor"] = pd.to_numeric(
        result.get("valor_numerico"), errors="coerce"
    )
    result = result[result["valor"].notna()].copy()
    if result.empty:
        return result
    scale_min = float(result["valor"].min())
    scale_max = float(result["valor"].max())
    if scale_max <= 5 and scale_min >= 0:
        result = result[result["valor"] != 0].copy()
        scale_min, scale_max = 1.0, 5.0
    elif scale_max <= 10 and scale_min >= 0:
        scale_min, scale_max = 0.0, 10.0
    result["top2box"] = result["valor"].apply(
        lambda value: top2box(value, scale_min, scale_max)
    )
    result["bottombox"] = result["valor"].apply(
        lambda value: bottom2box(value, scale_min, scale_max)
    )
    result["nps_grupo"] = result["valor"].apply(nps_group)
    return result


def _multi_significance(
    summaries: dict[str, pd.DataFrame],
    scale_data: pd.DataFrame,
    calculations: list[str],
    confidence: float,
    min_base: int,
    comparison_groups: list[list[str]] | None = None,
) -> pd.DataFrame:
    tables = []
    frequency = summaries["frequency"]
    rm = summaries["rm"]
    if "%" in calculations and not frequency.empty:
        tables.append(
            percentage_significance(
                frequency,
                confidence,
                min_base,
                comparison_groups=comparison_groups,
            )
        )
    for calculation in (
        "RM % Respondentes",
        "RM % Menciones",
    ):
        if calculation not in calculations or rm.empty:
            continue
        mentions = calculation.endswith("Menciones")
        sig_summary = rm.copy()
        if mentions and "base_menciones" in sig_summary:
            sig_summary["base"] = sig_summary["base_menciones"]
        tables.append(
            percentage_significance(
                sig_summary,
                confidence,
                min_base,
                count_column=(
                    "menciones" if mentions else "respondentes"
                ),
                proportion_column=(
                    "pct_menciones"
                    if mentions
                    else "pct_respondentes"
                ),
                comparison_groups=comparison_groups,
            )
        )
    if "Media" in calculations and not scale_data.empty:
        mean_table = mean_significance(
            scale_data,
            confidence,
            min_base,
            comparison_groups=comparison_groups,
        )
        if not mean_table.empty:
            mean_table = mean_table.rename(
                columns={"Indicador": "Respuesta"}
            )
            tables.append(mean_table)
    for calculation, metric in (
        ("Top2Box", "top2box"),
        ("BottomBox", "bottombox"),
    ):
        if calculation not in calculations or scale_data.empty:
            continue
        sig_summary = (
            scale_data.groupby("banner", dropna=False)
            .agg(
                n=(metric, "sum"),
                base=(metric, "count"),
                porcentaje=(metric, "mean"),
            )
            .reset_index()
        )
        sig_summary["respuesta"] = calculation
        tables.append(
            percentage_significance(
                sig_summary,
                confidence,
                min_base,
                comparison_groups=comparison_groups,
            )
        )
    return combine_significance_tables(tables)


def _primary_summary(
    summaries: dict[str, pd.DataFrame],
    calculations: list[str],
) -> pd.DataFrame:
    if any(item.startswith("RM ") for item in calculations):
        return summaries["rm"]
    if "NPS" in calculations:
        return summaries["nps"]
    if any(
        item in calculations
        for item in (
            "Media",
            "Desviación estándar",
            "Top2Box",
            "BottomBox",
        )
    ):
        return summaries["scale"]
    return summaries["frequency"]


def _chart_calculation(calculations: list[str]) -> str:
    for metric in (
        "NPS",
        "Media",
        "Top2Box",
        "BottomBox",
        "RM % Respondentes",
        "RM % Menciones",
    ):
        if metric in calculations:
            return metric
    return "Frecuencia"


def _legacy_calculations(
    calculation: str,
    display_mode: str,
    weighted: bool,
) -> list[str]:
    kind = (calculation or "Frecuencia").lower()
    if "nps" in kind:
        return ["NPS"]
    if "media" in kind:
        return ["Media", "Desviación estándar"]
    if "top" in kind:
        return ["Top2Box", "BottomBox"]
    if "bottom" in kind:
        return ["BottomBox", "Top2Box"]
    if "rm" in kind:
        metrics = ["n", calculation]
    else:
        mode = (display_mode or "n y %").lower()
        metrics = (
            ["n", "%"]
            if mode == "n y %"
            else ["n" if mode == "n" else "%"]
        )
    if weighted:
        metrics.extend(["n ponderado", "% ponderado"])
    return metrics


def _normalize_filters(
    filters: dict[str, list[object]] | None,
    filter_variable: str | None,
    filter_value: object | None,
) -> dict[str, list[object]]:
    if filters is not None:
        return {
            variable: list(values)
            for variable, values in filters.items()
            if values
        }
    if filter_variable and filter_value is not None:
        return {filter_variable: [filter_value]}
    return {}


def _normalize_significance_display(
    value: str | None,
    include_significance: bool,
) -> str:
    if value:
        normalized = value.strip().lower()
        mapping = {
            "integradas en tabla": "integrated",
            "tabla separada": "separate",
            "no mostrar": "none",
            "integrated": "integrated",
            "separate": "separate",
            "none": "none",
        }
        return mapping.get(normalized, "none")
    return "integrated" if include_significance else "none"


def _order_response_summaries(
    summaries: dict[str, pd.DataFrame],
    opciones: pd.DataFrame,
    question_id: str,
    response_order: str,
) -> dict[str, pd.DataFrame]:
    frequency = summaries.get("frequency", pd.DataFrame())
    rm = summaries.get("rm", pd.DataFrame())
    responses = []
    for frame in (frequency, rm):
        if not frame.empty and "respuesta" in frame.columns:
            responses.extend(frame["respuesta"].dropna().astype(str))
    responses = list(dict.fromkeys(responses))
    if not responses:
        return summaries

    mode = (response_order or "").lower()
    if "frecuencia" in mode:
        source = rm if not rm.empty else frequency
        total = source[source["banner"] == "Total"]
        count_column = (
            "menciones"
            if "menciones" in total.columns
            else "n"
        )
        counts = (
            total.set_index("respuesta")[count_column].to_dict()
            if count_column in total.columns
            else {}
        )
        ordered = sorted(
            responses,
            key=lambda response: (
                -float(counts.get(response, 0)),
                response.lower(),
            ),
        )
    else:
        option_order, code_order = _option_orders(
            opciones, question_id
        )
        selected_order = (
            code_order if "código" in mode or "codigo" in mode
            else option_order
        )
        ordered = sorted(
            responses,
            key=lambda response: (
                selected_order.get(response, (2, float("inf"), response)),
                response.lower(),
            ),
        )
    rank = {response: index for index, response in enumerate(ordered)}
    result = summaries.copy()
    for key in ("frequency", "rm"):
        frame = result.get(key, pd.DataFrame())
        if frame.empty or "respuesta" not in frame.columns:
            continue
        work = frame.copy()
        work["_response_rank"] = (
            work["respuesta"].astype(str).map(rank).fillna(len(rank))
        )
        result[key] = (
            work.sort_values(
                ["_response_rank", "respuesta"],
                kind="stable",
            )
            .drop(columns=["_response_rank"])
            .reset_index(drop=True)
        )
    return result


def _option_orders(
    opciones: pd.DataFrame,
    question_id: str,
) -> tuple[dict[str, tuple], dict[str, tuple]]:
    required = {"pregunta_id", "codigo", "label"}
    if opciones.empty or not required.issubset(opciones.columns):
        return {}, {}
    selected = opciones[
        opciones["pregunta_id"].astype(str) == str(question_id)
    ].copy()
    if selected.empty:
        return {}, {}
    selected["_codigo_num"] = pd.to_numeric(
        selected["codigo"], errors="coerce"
    )
    order_values = (
        selected["orden"]
        if "orden" in selected.columns
        else pd.Series(index=selected.index, dtype=float)
    )
    selected["_orden_num"] = pd.to_numeric(
        order_values, errors="coerce"
    )
    option_order = {}
    code_order = {}
    for label, group in selected.groupby("label", sort=False):
        label_text = str(label)
        order_values = group["_orden_num"].dropna()
        code_values = group["_codigo_num"].dropna()
        option_order[label_text] = (
            0 if not order_values.empty else 1,
            float(order_values.min())
            if not order_values.empty
            else float("inf"),
            label_text.lower(),
        )
        code_order[label_text] = (
            0 if not code_values.empty else 1,
            float(code_values.min())
            if not code_values.empty
            else float("inf"),
            label_text.lower(),
        )
    return option_order, code_order


def _method_notes(
    calculations: list[str],
    banner: str | None,
    filter_summary: str,
    ponderador: str | None,
    significance_display: str,
    confidence: float,
    min_base: int,
    summary: pd.DataFrame,
    banner_mode: str = "nested",
) -> list[str]:
    notes = [f"Cálculos: {', '.join(calculations) or 'ninguno'}."]
    notes.append(
        f"Banners: {banner} (valor | etiqueta)."
        if banner
        else "Resultado total, sin banners."
    )
    if banner and banner_mode == "separate":
        notes.append(
            "Tipo de banner: no anidados; cada variable se presenta "
            "como un bloque independiente."
        )
    notes.append(f"Filtros: {filter_summary}.")
    if ponderador:
        notes.append(f"Ponderador aplicado: {ponderador}.")
    if any(item.startswith("RM ") for item in calculations):
        notes.append(
            "En multirrespuesta, el porcentaje de respondentes puede "
            "sumar más de 100%."
        )
    if "RM % Menciones" in calculations:
        notes.append(
            "RM % Menciones usa el total de menciones como "
            "denominador; sus categorías suman 100%."
        )
    if significance_display != "none":
        notes.append(
            "Las letras indican diferencias significativas entre columnas "
            f"al nivel de confianza seleccionado ({confidence:.0%})."
        )
        if banner_mode == "separate":
            notes.append(
                "En banners no anidados, la significancia se compara "
                "solo entre categorías de la misma variable."
            )
        low_bases = insufficient_bases(summary, min_base)
        if low_bases:
            notes.append(
                f"Sin prueba por base menor a {min_base}: "
                f"{', '.join(low_bases)}."
            )
    return notes
