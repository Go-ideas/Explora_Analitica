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
from src.utils.text_utils import truthy


RM_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "variable_origen",
    "codigo_respuesta",
    "respuesta_label",
    "formato_rm",
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
        if len(labels) == 1:
            rows.extend(
                _build_unitary_label_rows(
                    non_missing,
                    item,
                    variable,
                    labels,
                    respondentes,
                    weights,
                )
            )
        elif is_dichotomous:
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
    if row.get("clasificacion_analitica") == "Abierta" or truthy(
        row.get("es_abierta_asociada")
    ):
        return False
    text = normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
    return "rm" in text or "multiple" in text or "multirrespuesta" in text


def _build_dichotomous_rows(series, item, variable, labels, respondentes, weights) -> list[dict]:
    rows = []
    variable_label = item.get("label") or variable
    option_code = _suffix_code(variable)
    for idx, value in series.items():
        if pd.to_numeric(value, errors="coerce") == 1:
            rows.append(
                {
                    "id_respondente": respondentes.loc[idx, "id_respondente"],
                    "pregunta_id": item.get("pregunta_id") or variable,
                    "variable_origen": variable,
                    "codigo_respuesta": option_code,
                    "respuesta_label": variable_label,
                    "formato_rm": "dicotomica_por_opcion",
                    "ponderador": weights.loc[idx],
                }
            )
    return rows


def _build_unitary_label_rows(
    series,
    item,
    variable,
    labels,
    respondentes,
    weights,
) -> list[dict]:
    rows = []
    option_code, option_label = next(iter(labels.items()))
    numeric_option = pd.to_numeric(option_code, errors="coerce")
    for idx, value in series.items():
        numeric = pd.to_numeric(value, errors="coerce")
        selected = False
        if pd.notna(numeric) and pd.notna(numeric_option):
            selected = numeric == numeric_option or numeric == 1
        else:
            selected = normalize_text(value) in {
                "si",
                "sí",
                "yes",
                "seleccionado",
                "selected",
            }
        if not selected:
            continue
        rows.append(
            {
                "id_respondente": respondentes.loc[idx, "id_respondente"],
                "pregunta_id": item.get("pregunta_id") or variable,
                "variable_origen": variable,
                "codigo_respuesta": option_code,
                "respuesta_label": option_label,
                "formato_rm": "unitaria_por_opcion",
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
                "ponderador": weights.loc[idx],
            }
        )
    return rows


def _suffix_code(variable: str) -> str:
    parts = str(variable).replace("-", "_").split("_")
    return parts[-1] if len(parts) > 1 else variable
