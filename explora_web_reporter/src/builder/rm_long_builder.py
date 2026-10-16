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
        if "usar_en_dashboard" in item and not truthy(item["usar_en_dashboard"]):
            continue
        labels = get_value_labels(meta_spss, variable)
        series = df_spss[variable].dropna()
        non_missing = series[~series.astype(str).str.strip().eq("")]
        unique_values = set(pd.to_numeric(non_missing, errors="coerce").dropna().unique().tolist())
        is_dichotomous = unique_values and unique_values.issubset({0, 1})
        if _coded_option_layout(item):
            code, label = _coded_option(item, non_missing, labels)
            for idx, value in non_missing.items():
                if float(value) == code:
                    rows.append({
                        "id_respondente": respondentes.loc[idx, "id_respondente"],
                        "pregunta_id": item.get("pregunta_id") or variable,
                        "variable_origen": variable,
                        "codigo_respuesta": code,
                        "respuesta_label": label,
                        "formato_rm": "codigo_por_opcion",
                        "ponderador": weights.loc[idx],
                    })
        elif normalize_text(item.get("formato_rm")) in {"menciones", "mentions"}:
            rows.extend(_build_mentions_rows(non_missing, item, variable, labels, respondentes, weights))
        elif len(labels) == 1:
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


def _coded_option_layout(item: pd.Series) -> bool:
    declared = normalize_text(item.get("formato_rm"))
    if declared:
        return declared in {"codigo_por_opcion", "code_per_option"}
    return normalize_text(item.get("tipo_eje_fila")) == "opcion_rm"


def _coded_option(item: pd.Series, series: pd.Series, labels: dict) -> tuple[float, str]:
    variable = item.get("variable")
    code = pd.to_numeric(item.get("codigo_opcion_rm"), errors="coerce")
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise ValueError(f"La opción RM {variable} requiere códigos numéricos explícitos.")
    observed = set(numeric[numeric.ne(0)].unique())
    if pd.isna(code):
        if len(observed) != 1:
            raise ValueError(f"Declare codigo_opcion_rm para {variable}; no hay un código de selección único.")
        code = next(iter(observed))
    if code == 0 or not observed.issubset({code}):
        raise ValueError(f"La opción RM {variable} contiene códigos incompatibles con su selección declarada.")
    label = item.get("label_opcion_rm")
    if label is None or pd.isna(label) or not str(label).strip():
        label = next((value for key, value in labels.items()
                      if pd.to_numeric(key, errors="coerce") == code), None)
    if label is None or not str(label).strip():
        raise ValueError(f"Falta la etiqueta del código de selección de {variable}.")
    return float(code), str(label)


def build_rm_bases(df_spss: pd.DataFrame, datamap: pd.DataFrame, respondents: pd.DataFrame) -> pd.DataFrame:
    """Keep observed zero-selection evaluations in explicitly option-coded RM bases."""
    rows = []
    if datamap is None or datamap.empty or "pregunta_id" not in datamap:
        return pd.DataFrame(columns=["id_respondente", "pregunta_id"])
    for question, group in datamap.groupby("pregunta_id", sort=False):
        items = group[group.apply(lambda row: _is_rm_row(row) and truthy(row.get("usar_en_dashboard", True)), axis=1)]
        if items.empty or not items.apply(_coded_option_layout, axis=1).all():
            continue
        variables = [str(item.variable) for _, item in items.iterrows()
                     if item.variable in df_spss and truthy(item.get("usar_en_dashboard", True))]
        if not variables:
            continue
        observed = df_spss[variables].notna() & df_spss[variables].astype(str).apply(
            lambda column: column.str.strip().ne("")
        )
        eligible = observed.any(axis=1)
        rows.extend({"id_respondente": respondents.loc[index, "id_respondente"], "pregunta_id": question}
                    for index in df_spss.index[eligible])
    return pd.DataFrame(rows, columns=["id_respondente", "pregunta_id"])


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
