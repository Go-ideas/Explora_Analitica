from __future__ import annotations

from typing import Any

import pandas as pd

from src.readers.spss_reader import get_value_labels
from src.reporter.calculations import (
    deduplicate_rm,
    remove_exclusive_combinations,
    weight_series,
)
from src.utils.constants import EXCLUSIVE_OPTION_HINTS
from src.utils.text_utils import normalize_text


RM_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "variable_origen",
    "codigo_respuesta",
    "respuesta_label",
    "formato_rm",
    "entidad_loop",
    "opcion_rm",
    "tipo_estructura",
    "ponderador",
]


def build_rm_long(
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    respondentes: pd.DataFrame,
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=RM_COLUMNS)

    weights = weight_series(datamap_df, df_spss)
    rm_rows = datamap_df[datamap_df.apply(_is_rm_row, axis=1)]
    rows = []
    for _, item in rm_rows.iterrows():
        variable = item.get("variable")
        if variable not in df_spss.columns:
            continue
        labels = get_value_labels(meta_spss, variable)
        series = df_spss[variable].dropna()
        non_missing = series[~series.astype(str).str.strip().eq("")]
        unique_values = set(pd.to_numeric(non_missing, errors="coerce").dropna().unique().tolist())
        is_dichotomous = unique_values and unique_values.issubset({0, 1})
        if is_dichotomous:
            rows.extend(_build_dichotomous_rows(non_missing, item, variable, labels, respondentes, weights))
        elif non_missing.empty:
            continue
        else:
            rows.extend(_build_mentions_rows(non_missing, item, variable, labels, respondentes, weights))

    result = pd.DataFrame(rows, columns=RM_COLUMNS)
    if result.empty:
        return result
    result = deduplicate_rm(result)
    result = remove_exclusive_combinations(result, EXCLUSIVE_OPTION_HINTS)
    return result.reset_index(drop=True)


def _is_rm_row(row: pd.Series) -> bool:
    text = _metadata_text(row)
    classification = normalize_text(row.get("clasificacion_analitica", ""))
    calculation = normalize_text(row.get("tipo_calculo", ""))
    if (
        "abierta" in classification
        or "texto_abierto" in calculation
        or row.get("usar_en_dashboard") is False
    ):
        return False
    return "rm" in text or "multiple" in text or "multirrespuesta" in text


def _build_dichotomous_rows(series, item, variable, labels, respondentes, weights) -> list[dict]:
    rows = []
    option_label = _rm_option_label(item, variable)
    entity = _clean_text(item.get("entidad_loop"))
    option = _clean_text(
        item.get("opcion_rm")
        or item.get("label_opcion_rm")
        or item.get("texto_opcion_rm")
        or option_label
    )
    is_grid = _is_grid_rm_loop(item)
    option_code = (
        variable
        if is_grid
        else _clean_text(item.get("codigo_opcion_rm")) or _suffix_code(variable)
    )
    display_label = (
        f"{entity} | {option}" if is_grid and entity and option else option_label
    )
    for idx, value in series.items():
        if pd.to_numeric(value, errors="coerce") == 1:
            rows.append(
                {
                    "id_respondente": respondentes.loc[idx, "id_respondente"],
                    "pregunta_id": item.get("pregunta_id") or variable,
                    "variable_origen": variable,
                    "codigo_respuesta": option_code,
                    "respuesta_label": display_label,
                    "formato_rm": (
                        "grid_rm_loop"
                        if is_grid
                        else "rm_dicotomica_label"
                    ),
                    "entidad_loop": entity,
                    "opcion_rm": option,
                    "tipo_estructura": _structure_type(item),
                    "ponderador": weights.loc[idx],
                }
            )
    return rows


def _build_mentions_rows(series, item, variable, labels, respondentes, weights) -> list[dict]:
    rows = []
    for idx, value in series.items():
        numeric = pd.to_numeric(value, errors="coerce")
        code = numeric if pd.notna(numeric) else value
        label = labels.get(value, labels.get(code, labels.get(str(value), str(value))))
        rows.append(
            {
                "id_respondente": respondentes.loc[idx, "id_respondente"],
                "pregunta_id": item.get("pregunta_id") or variable,
                "variable_origen": variable,
                "codigo_respuesta": code,
                "respuesta_label": label,
                "formato_rm": "menciones" if labels else "requiere_validacion",
                "entidad_loop": _clean_text(item.get("entidad_loop")),
                "opcion_rm": _clean_text(
                    item.get("opcion_rm")
                    or item.get("label_opcion_rm")
                    or item.get("texto_opcion_rm")
                ),
                "tipo_estructura": _structure_type(item),
                "ponderador": weights.loc[idx],
            }
        )
    return rows


def _suffix_code(variable: str) -> str:
    if "#" in str(variable):
        return str(variable).rsplit("#", 1)[-1]
    parts = str(variable).replace("-", "_").split("_")
    return parts[-1] if len(parts) > 1 else variable


def _metadata_text(row: pd.Series) -> str:
    return normalize_text(
        " ".join(
            str(row.get(column) or "")
            for column in (
                "tipo_pregunta",
                "tipo_calculo",
                "tipo_estructura_grid",
                "formato_rm",
            )
        )
    )


def _is_grid_rm_loop(row: pd.Series) -> bool:
    return "grid_rm_loop" in _metadata_text(row)


def _structure_type(row: pd.Series) -> str:
    text = _metadata_text(row)
    if "grid_rm_loop" in text:
        return "GRID_RM_LOOP"
    if "rm_dicotomica_label" in text:
        return "RM_DICOTOMICA_LABEL"
    if "rm" in text:
        return "RM"
    return ""


def _rm_option_label(row: pd.Series, variable: str) -> str:
    for column in (
        "label_opcion_rm",
        "texto_opcion_rm",
        "opcion_rm",
        "display_item_reporteador",
        "label",
    ):
        value = _clean_text(row.get(column))
        if value:
            return _clean_label_prefix(value, row, variable)
    return variable


def _clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text


def _clean_label_prefix(
    label: str,
    row: pd.Series,
    variable: str,
) -> str:
    question = _clean_text(row.get("texto_pregunta"))
    if question and question in label:
        label = label.replace(question, "").strip(" -_")
    parent = _clean_text(row.get("pregunta_id"))
    for prefix in (variable, parent):
        if prefix and label.startswith(prefix):
            label = label[len(prefix) :].strip(" -_|")
    return label or variable
