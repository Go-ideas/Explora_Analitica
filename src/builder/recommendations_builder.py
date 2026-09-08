from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.utils.text_utils import (
    find_column,
    first_existing,
    truthy,
)


RECOMMENDATION_COLUMNS = [
    "tipo_recomendacion",
    "variable",
    "variable_label",
    "pregunta_id",
    "numero_pregunta",
    "texto_pregunta",
    "seccion_cuestionario",
    "rol_recomendado",
    "es_banner_recomendado",
    "es_filtro_recomendado",
    "nivel_relevancia_comercial",
    "justificacion",
    "uso_comercial_sugerido",
    "distribucion_base",
    "riesgo_uso_analitico",
    "requiere_factor",
    "tipo_factor_recomendado",
    "variables_para_factor",
    "regla_factor_sugerida",
    "justificacion_factor",
    "prioridad_factor",
    "fuente_hoja",
]


def build_recomendaciones_reporteador(
    datamap_df: pd.DataFrame,
    sheets: dict[str, pd.DataFrame] | None = None,
    df_spss: pd.DataFrame | None = None,
    meta_spss: Any | None = None,
) -> pd.DataFrame:
    sheets = dict(sheets or {})
    if datamap_df is not None and not datamap_df.empty:
        sheets.setdefault(
            "08_Clasificacion_Analitica", datamap_df
        )
        sheets.setdefault("10_Datamap_Corregido", datamap_df)
    rows: list[dict[str, Any]] = []
    variable_lookup, question_lookup = _lookups(datamap_df)

    banner_sheet = _first_sheet(
        sheets,
        [
            "11_Banners_Filtros_Recomendados",
            "Banners_Filtros_Recomendados",
        ],
    )
    factor_sheet = _first_sheet(
        sheets,
        [
            "12_Factores_Scores_Recomendados",
            "Factores_Scores_Recomendados",
        ],
    )
    order_sheet = _first_sheet(
        sheets,
        ["13_Orden_Menu_Reporteador"],
    )

    if banner_sheet is not None:
        name, frame = banner_sheet
        rows.extend(
            _records(
                frame,
                "banner_filtro",
                name,
                variable_lookup,
                question_lookup,
            )
        )
    else:
        rows.extend(
            _fallback_records(
                sheets,
                "banner_filtro",
                variable_lookup,
                question_lookup,
            )
        )

    if factor_sheet is not None:
        name, frame = factor_sheet
        rows.extend(
            _records(
                frame,
                "factor_score",
                name,
                variable_lookup,
                question_lookup,
            )
        )
    else:
        rows.extend(
            _fallback_records(
                sheets,
                "factor_score",
                variable_lookup,
                question_lookup,
            )
        )

    if order_sheet is not None:
        name, frame = order_sheet
        rows.extend(
            _records(
                frame,
                "orden_menu",
                name,
                variable_lookup,
                question_lookup,
            )
        )
    else:
        rows.extend(
            _fallback_records(
                sheets,
                "orden_menu",
                variable_lookup,
                question_lookup,
            )
        )

    if not rows:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)
    result = pd.DataFrame(rows, columns=RECOMMENDATION_COLUMNS)
    result = result.drop_duplicates(
        [
            "tipo_recomendacion",
            "variable",
            "pregunta_id",
            "tipo_factor_recomendado",
            "fuente_hoja",
        ],
        keep="first",
    ).reset_index(drop=True)
    return _apply_commercial_cleaning(
        result, df_spss, meta_spss
    )


def _records(
    frame: pd.DataFrame,
    recommendation_type: str,
    source_name: str,
    variable_lookup: dict[str, dict],
    question_lookup: dict[str, dict],
) -> list[dict[str, Any]]:
    rows = []
    for _, source in frame.iterrows():
        variable = _value(
            source,
            [
                "Variable",
                "Variable_SPSS",
                "Variables_SPSS_Asociadas",
                "Variables_Para_Factor",
            ],
        )
        variable = _first_variable(variable)
        question_id = _value(
            source,
            [
                "Pregunta_ID",
                "Numero_Pregunta",
                "Pregunta",
            ],
        )
        variable_meta = variable_lookup.get(variable, {})
        if not question_id:
            question_id = _clean(
                variable_meta.get("pregunta_id")
            )
        question_meta = question_lookup.get(question_id, {})
        banner = _boolean_value(
            source,
            ["Es_Banner_Recomendado", "Es_Banner"],
        )
        filter_ = _boolean_value(
            source,
            ["Es_Filtro_Recomendado", "Es_Filtro"],
        )
        role = _value(
            source,
            ["Rol_Recomendado", "Rol_Analitico_Principal"],
        )
        if not role:
            if banner and filter_:
                role = "Banner y filtro"
            elif banner:
                role = "Banner"
            elif filter_:
                role = "Filtro"
        use = _value(source, ["Uso_Comercial_Sugerido"])
        raw_justification = _exact_value(
            source,
            [
                "Justificacion_Banner_Filtro",
                "Justificación_Banner_Filtro",
                "Justificacion",
            ],
        )
        justification = clean_commercial_justification(
            raw_justification,
            variable_meta.get("justificacion_banner_filtro"),
            _coalesce(
                _value(
                    source,
                    ["Variable_Label", "Label", "Etiqueta"],
                ),
                variable_meta.get("label"),
                variable,
            ),
            role,
            use,
            recommendation_type,
        )

        rows.append(
            {
                "tipo_recomendacion": recommendation_type,
                "variable": variable,
                "variable_label": _coalesce(
                    _value(
                        source,
                        ["Variable_Label", "Label", "Etiqueta"],
                    ),
                    variable_meta.get("label"),
                ),
                "pregunta_id": question_id,
                "numero_pregunta": _coalesce(
                    _value(
                        source,
                        ["Numero_Pregunta", "Pregunta_ID"],
                    ),
                    question_id,
                ),
                "texto_pregunta": _coalesce(
                    _value(
                        source,
                        ["Texto_Pregunta", "Pregunta_Texto"],
                    ),
                    question_meta.get("texto_pregunta"),
                    variable_meta.get("texto_pregunta"),
                ),
                "seccion_cuestionario": _coalesce(
                    _value(
                        source,
                        [
                            "Seccion_Cuestionario",
                            "Sección_Cuestionario",
                            "Seccion",
                        ],
                    ),
                    question_meta.get("seccion_cuestionario"),
                    question_meta.get("seccion"),
                ),
                "rol_recomendado": role,
                "es_banner_recomendado": int(banner),
                "es_filtro_recomendado": int(filter_),
                "nivel_relevancia_comercial": _value(
                    source, ["Nivel_Relevancia_Comercial"]
                ),
                "justificacion": justification,
                "uso_comercial_sugerido": use,
                "distribucion_base": _exact_value(
                    source,
                    [
                        "Distribucion_Base",
                        "Distribución_Base",
                        "Base_Categorias_Obs",
                    ],
                )
                or (
                    raw_justification
                    if is_distribution_text(raw_justification)
                    else ""
                ),
                "riesgo_uso_analitico": _value(
                    source, ["Riesgo_Uso_Analitico"]
                ),
                "requiere_factor": int(
                    _boolean_value(
                        source, ["Requiere_Factor"]
                    )
                ),
                "tipo_factor_recomendado": _value(
                    source, ["Tipo_Factor_Recomendado"]
                ),
                "variables_para_factor": _value(
                    source, ["Variables_Para_Factor"]
                ),
                "regla_factor_sugerida": _value(
                    source, ["Regla_Factor_Sugerida"]
                ),
                "justificacion_factor": _value(
                    source, ["Justificacion_Factor"]
                ),
                "prioridad_factor": _value(
                    source, ["Prioridad_Factor"]
                ),
                "fuente_hoja": source_name,
            }
        )
    return rows


def _fallback_records(
    sheets: dict[str, pd.DataFrame],
    recommendation_type: str,
    variable_lookup: dict[str, dict],
    question_lookup: dict[str, dict],
) -> list[dict[str, Any]]:
    names = (
        ["08_Clasificacion_Analitica", "10_Datamap_Corregido"]
        if recommendation_type == "banner_filtro"
        else ["10_Datamap_Corregido", "08_Clasificacion_Analitica"]
    )
    rows = []
    for name in names:
        frame = sheets.get(name)
        if frame is None or frame.empty:
            continue
        records = _records(
            frame,
            recommendation_type,
            name,
            variable_lookup,
            question_lookup,
        )
        for record in records:
            if recommendation_type == "banner_filtro" and not (
                record["es_banner_recomendado"]
                or record["es_filtro_recomendado"]
            ):
                continue
            if recommendation_type == "factor_score" and not (
                record["requiere_factor"]
                or record["tipo_factor_recomendado"]
            ):
                continue
            rows.append(record)
        if rows:
            break
    return rows


def _lookups(
    datamap_df: pd.DataFrame,
) -> tuple[dict[str, dict], dict[str, dict]]:
    if datamap_df is None or datamap_df.empty:
        return {}, {}
    variable_lookup = (
        datamap_df.drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
        if "variable" in datamap_df
        else {}
    )
    question_lookup = (
        datamap_df.drop_duplicates("pregunta_id")
        .set_index("pregunta_id")
        .to_dict("index")
        if "pregunta_id" in datamap_df
        else {}
    )
    return variable_lookup, question_lookup


def _first_sheet(
    sheets: dict[str, pd.DataFrame], names: list[str]
) -> tuple[str, pd.DataFrame] | None:
    for name in names:
        frame = sheets.get(name)
        if frame is not None and not frame.empty:
            return name, frame
    return None


def _value(row: pd.Series, aliases: list[str]) -> str:
    column = find_column(row.index, aliases)
    return _clean(row.get(column)) if column else ""


def _exact_value(row: pd.Series, aliases: list[str]) -> str:
    column = first_existing(row.index, aliases)
    return _clean(row.get(column)) if column else ""


def _boolean_value(
    row: pd.Series, aliases: list[str]
) -> bool:
    column = find_column(row.index, aliases)
    return truthy(row.get(column)) if column else False


def _first_variable(value: object) -> str:
    text = _clean(value)
    if not text:
        return ""
    match = re.search(r"[A-Za-z@#$][A-Za-z0-9_@#$]*", text)
    return match.group(0) if match else text


def _coalesce(*values: object) -> str:
    for value in values:
        clean = _clean(value)
        if clean:
            return clean
    return ""


def is_distribution_text(value: object) -> bool:
    text = _clean(value)
    if not text:
        return False
    pairs = re.findall(
        r"(?:^|;|\s)(-?\d+(?:\.\d+)?)\s*:\s*([\d,]+)",
        text,
    )
    return bool(pairs)


def format_base_distribution(
    values: pd.Series,
    value_labels: dict[Any, str] | None = None,
) -> str:
    labels = value_labels or {}
    counts = values.value_counts(dropna=False, sort=False)
    ordered = sorted(
        counts.items(),
        key=lambda item: _distribution_sort_key(item[0]),
    )
    parts = []
    for value, count in ordered:
        if pd.isna(value):
            display = "Sin respuesta"
        else:
            label = _value_label(labels, value)
            if label:
                display = label
            elif isinstance(value, (int, float)):
                display = f"Código {_format_code(value)}"
            else:
                display = str(value)
        parts.append(f"{display} n={int(count):,}")
    return "; ".join(parts)


def normalize_base_distribution(
    value: object,
    value_labels: dict[Any, str] | None = None,
) -> str:
    text = _clean(value)
    if not text:
        return ""
    pairs = re.findall(
        r"(-?\d+(?:\.\d+)?)\s*:\s*([\d,]+)",
        text,
    )
    if not pairs:
        return text
    labels = value_labels or {}
    parts = []
    for raw_code, raw_count in pairs:
        code = float(raw_code)
        label = _value_label(labels, code)
        display = label or f"Código {_format_code(code)}"
        count = int(raw_count.replace(",", ""))
        parts.append(f"{display} n={count:,}")
    return "; ".join(parts)


def _apply_commercial_cleaning(
    recommendations: pd.DataFrame,
    df_spss: pd.DataFrame | None,
    meta_spss: Any | None,
) -> pd.DataFrame:
    result = recommendations.copy()
    labels_by_variable = (
        getattr(meta_spss, "variable_value_labels", {}) or {}
    )
    banner_rows = result["tipo_recomendacion"].eq(
        "banner_filtro"
    )
    for index, row in result[banner_rows].iterrows():
        variable = str(row.get("variable") or "")
        labels = labels_by_variable.get(variable, {}) or {}
        if (
            df_spss is not None
            and variable
            and variable in df_spss
        ):
            distribution = format_base_distribution(
                df_spss[variable], labels
            )
        else:
            distribution = normalize_base_distribution(
                row.get("distribucion_base"), labels
            )
        result.at[index, "distribucion_base"] = distribution
        if is_distribution_text(row.get("justificacion")):
            result.at[index, "justificacion"] = (
                clean_commercial_justification(
                    "",
                    "",
                    row.get("variable_label") or variable,
                    row.get("rol_recomendado"),
                    row.get("uso_comercial_sugerido"),
                    "banner_filtro",
                )
            )
    return result


def clean_commercial_justification(
    source_value: object,
    metadata_value: object,
    label: object,
    role: object,
    use: object,
    recommendation_type: str,
) -> str:
    if recommendation_type != "banner_filtro":
        return ""
    for candidate in (source_value, metadata_value):
        text = _clean(candidate)
        if text and not is_distribution_text(text):
            return text
    clean_label = _clean(label) or "Esta variable"
    clean_role = _clean(role).lower() or "variable de análisis"
    clean_use = _clean(use)
    if clean_use:
        return (
            f"{clean_label} se recomienda como {clean_role} "
            "porque permite una lectura comercial clara y "
            f"accionable. {clean_use}"
        )
    return (
        f"{clean_label} se recomienda como {clean_role} porque "
        "permite comparar segmentos relevantes de forma clara y "
        "accionable."
    )


def _value_label(
    labels: dict[Any, str], value: object
) -> str:
    candidates = [value]
    try:
        numeric = float(value)
        candidates.extend([numeric, int(numeric)])
    except (TypeError, ValueError, OverflowError):
        pass
    for candidate in candidates:
        if candidate in labels:
            return _clean(labels[candidate])
    return ""


def _format_code(value: object) -> str:
    try:
        numeric = float(value)
        return (
            str(int(numeric))
            if numeric.is_integer()
            else str(numeric)
        )
    except (TypeError, ValueError):
        return str(value)


def _distribution_sort_key(value: object) -> tuple[int, object]:
    if pd.isna(value):
        return (2, "")
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, str(value).casefold())


def _clean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text
