from __future__ import annotations

import pandas as pd

from src.reporter.banners import banner_order
from src.utils.formatting import normalize_metric_name


CALCULATION_OPTIONS = [
    "n",
    "%",
    "n ponderado",
    "% ponderado",
    "Media",
    "Desviación estándar",
    "Top2Box",
    "BottomBox",
    "NPS",
    "RM % Respondentes",
    "RM % Menciones",
]


def validate_calculations_for_question(
    question_type: str,
    selected_calculations: list[str],
) -> tuple[list[str], list[str]]:
    text = str(question_type or "").lower()
    is_grid_rm_loop = "grid_rm_loop" in text
    is_rm_dicotomica_label = "rm_dicotomica_label" in text
    is_rm = is_grid_rm_loop or is_rm_dicotomica_label or any(
        token in text
        for token in ("__rm__", "multirrespuesta", "multiple", " rm")
    )
    is_scale = any(
        token in text
        for token in (
            "__scale__",
            "escala",
            "grid",
            "media",
            "top2box",
            "bottom2box",
            "nps",
        )
    ) and not (is_grid_rm_loop or is_rm_dicotomica_label)
    is_nps = "__nps__" in text or "nps" in text
    valid = []
    warnings = []

    for raw_calculation in selected_calculations:
        calculation = normalize_metric_name(raw_calculation)
        if is_rm and calculation == "%":
            calculation = "RM % Respondentes"
            warning = (
                "En preguntas RM, % equivale a RM % "
                "Respondentes; se consolidó en un solo indicador."
            )
            if warning not in warnings:
                warnings.append(warning)
        applies = True
        if calculation.startswith("RM "):
            applies = is_rm
        elif calculation in {
            "Media",
            "Desviación estándar",
            "Top2Box",
            "BottomBox",
        }:
            applies = is_scale
        elif calculation == "NPS":
            applies = is_nps
        if applies:
            if calculation not in valid:
                valid.append(calculation)
        else:
            warnings.append(
                f"{calculation} no aplica al tipo de pregunta y fue omitido."
            )
    return valid, warnings


def build_multi_metric_table(
    question_id: str,
    banner: str | list[str] | tuple[str, ...] | None = None,
    filters: dict[str, list[object]] | None = None,
    weight: str | None = None,
    calculations: list[str] | None = None,
    *,
    summaries: dict[str, pd.DataFrame] | None = None,
    significance: pd.DataFrame | None = None,
    significance_mode: str = "none",
) -> pd.DataFrame:
    del question_id, banner, filters
    calculations = [
        normalize_metric_name(item) for item in (calculations or ["n", "%"])
    ]
    summaries = summaries or {}
    frequency = summaries.get("frequency", pd.DataFrame())
    rm = summaries.get("rm", pd.DataFrame())
    scale = summaries.get("scale", pd.DataFrame())
    nps = summaries.get("nps", pd.DataFrame())
    source = rm if any(item.startswith("RM ") for item in calculations) else frequency
    if source.empty:
        source = rm if not rm.empty else frequency

    order = _available_banner_order([source, scale, nps])
    response_metrics = _response_metric_specs(
        calculations, source, is_rm_source=source is rm, weighted=bool(weight)
    )
    output = _response_rows(source, order, response_metrics)
    scalar_rows, has_scalar_metrics = _scalar_rows(
        scale, nps, order, calculations
    )

    all_columns = _identity_columns(output)
    for category in order:
        all_columns.extend(
            f"{category} | {label}" for label, _ in response_metrics
        )
        if has_scalar_metrics:
            all_columns.append(f"{category} | Valor")
    all_columns = list(dict.fromkeys(all_columns))
    output = output.reindex(columns=all_columns)
    if scalar_rows:
        scalar_df = pd.DataFrame(scalar_rows).reindex(columns=all_columns)
        output = pd.concat([output, scalar_df], ignore_index=True)
    output = output.fillna("")

    if significance_mode == "integrated" and significance is not None:
        output = merge_significance_into_table(
            output, significance, mode="columns"
        )
    return output


def merge_significance_into_table(
    main_table: pd.DataFrame,
    sig_table: pd.DataFrame,
    mode: str = "columns",
) -> pd.DataFrame:
    if (
        main_table.empty
        or sig_table is None
        or sig_table.empty
        or mode != "columns"
    ):
        return main_table.copy()
    key_column = sig_table.columns[0]
    indexed = sig_table.set_index(key_column)
    result = main_table.copy()
    response_column = (
        "Respuesta" if "Respuesta" in result.columns else result.columns[0]
    )
    categories = []
    for column in result.columns[1:]:
        category, _ = _split_metric_column(str(column))
        if category != "Total" and category not in categories:
            categories.append(category)

    for category in categories:
        if category not in indexed.columns:
            continue
        result[f"{category} | Sig."] = [
            indexed.at[value, category] if value in indexed.index else ""
            for value in result[response_column]
        ]

    ordered = [
        column
        for column in ("Entidad", "Opción", response_column)
        if column in result.columns
    ]
    for column in main_table.columns[1:]:
        if column in ordered:
            continue
        ordered.append(column)
        category, _ = _split_metric_column(str(column))
        category_columns = [
            item
            for item in main_table.columns[1:]
            if _split_metric_column(str(item))[0] == category
        ]
        sig_column = f"{category} | Sig."
        if column == category_columns[-1] and sig_column in result.columns:
            ordered.append(sig_column)
    return result[ordered]


def _response_metric_specs(
    calculations: list[str],
    source: pd.DataFrame,
    is_rm_source: bool,
    weighted: bool,
) -> list[tuple[str, str]]:
    specs = []
    for calculation in calculations:
        if calculation == "n":
            column = "respondentes" if is_rm_source else "n"
        elif calculation == "%":
            column = "pct_respondentes" if is_rm_source else "porcentaje"
        elif calculation == "n ponderado":
            column = (
                "menciones_ponderadas" if is_rm_source else "n_ponderado"
            )
        elif calculation == "% ponderado":
            column = (
                "pct_respondentes_ponderado"
                if is_rm_source
                else "porcentaje_ponderado"
            )
        elif calculation == "RM % Respondentes":
            column = "pct_respondentes"
        elif calculation == "RM % Menciones":
            column = "pct_menciones"
        else:
            continue
        if column in source.columns and (weighted or "ponderado" not in calculation):
            specs.append((calculation, column))
    return specs


def _response_rows(
    source: pd.DataFrame,
    order: list[str],
    metrics: list[tuple[str, str]],
) -> pd.DataFrame:
    if source.empty or not metrics or "respuesta" not in source.columns:
        return pd.DataFrame(columns=["Respuesta"])
    responses = list(dict.fromkeys(source["respuesta"].astype(str).tolist()))
    output = pd.DataFrame({"Respuesta": responses})
    if _has_grid_metadata(source):
        metadata = (
            source.drop_duplicates("respuesta")
            .set_index("respuesta")
        )
        output.insert(
            0,
            "Entidad",
            output["Respuesta"].map(metadata["entidad_loop"]).fillna(""),
        )
        output.insert(
            1,
            "Opción",
            output["Respuesta"].map(metadata["opcion_rm"]).fillna(""),
        )
    for category in order:
        selected = source[source["banner"].astype(str) == str(category)]
        indexed = selected.set_index("respuesta")
        for label, value_column in metrics:
            values = []
            for response in responses:
                value = (
                    indexed.at[response, value_column]
                    if response in indexed.index
                    else 0
                )
                if label in {
                    "%",
                    "% ponderado",
                    "RM % Respondentes",
                    "RM % Menciones",
                }:
                    value = float(value) * 100
                values.append(value)
            output[f"{category} | {label}"] = values
    return output


def _identity_columns(output: pd.DataFrame) -> list[str]:
    if {"Entidad", "Opción", "Respuesta"}.issubset(output.columns):
        return ["Entidad", "Opción", "Respuesta"]
    return ["Respuesta"]


def _has_grid_metadata(source: pd.DataFrame) -> bool:
    if not {"entidad_loop", "opcion_rm"}.issubset(source.columns):
        return False
    entity = source["entidad_loop"].fillna("").astype(str).str.strip()
    option = source["opcion_rm"].fillna("").astype(str).str.strip()
    return bool(entity.ne("").any() and option.ne("").any())


def _scalar_rows(
    scale: pd.DataFrame,
    nps: pd.DataFrame,
    order: list[str],
    calculations: list[str],
) -> tuple[list[dict], bool]:
    mapping = {
        "Media": (scale, "media", False),
        "Desviación estándar": (scale, "desviacion_estandar", False),
        "Top2Box": (scale, "top2box", True),
        "BottomBox": (scale, "bottombox", True),
        "NPS": (nps, "nps", False),
    }
    rows = []
    for calculation in calculations:
        if calculation not in mapping:
            continue
        source, value_column, percentage = mapping[calculation]
        if source.empty or value_column not in source.columns:
            continue
        row = {"Respuesta": calculation}
        indexed = source.set_index("banner")
        for category in order:
            value = (
                indexed.at[category, value_column]
                if category in indexed.index
                else ""
            )
            if percentage and value != "":
                value = float(value) * 100
            row[f"{category} | Valor"] = value
        rows.append(row)
    return rows, bool(rows)


def _available_banner_order(
    frames: list[pd.DataFrame],
) -> list[str]:
    for frame in frames:
        if not frame.empty and "banner" in frame.columns:
            return banner_order(frame["banner"])
    return ["Total"]


def _split_metric_column(column: str) -> tuple[str, str]:
    if " | " not in column:
        return column, ""
    return tuple(column.rsplit(" | ", 1))
