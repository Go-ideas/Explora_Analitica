from __future__ import annotations

from typing import Any

import pandas as pd

from src.readers.spss_reader import get_value_labels
from src.reporter.calculations import weight_series
from src.utils.text_utils import normalize_text, truthy


GRID_LOOP_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "grid_id",
    "variable",
    "entidad_loop",
    "orden_entidad_loop",
    "codigo_opcion",
    "label_opcion",
    "orden_opcion",
    "valor",
    "seleccionado",
    "base_valida",
    "missing_estructural",
    "peso",
]


def build_grid_loop_long(
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    respondentes: pd.DataFrame,
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=GRID_LOOP_COLUMNS)
    weights = weight_series(datamap_df, df_spss)
    items = datamap_df[datamap_df.apply(_is_grid_rm_item, axis=1)]
    rows = []
    for _, item in items.iterrows():
        variable = str(item.get("variable") or "").strip()
        if variable not in df_spss.columns:
            continue
        labels = get_value_labels(meta_spss, variable)
        code = _first_text(item.get("codigo_opcion_rm"), _single_label_code(labels))
        label = _first_text(
            item.get("label_opcion_rm"),
            _single_label_text(labels),
            item.get("label"),
            variable,
        )
        for index, value in df_spss[variable].items():
            missing = _is_missing(value)
            rows.append(
                {
                    "id_respondente": respondentes.loc[index, "id_respondente"],
                    "pregunta_id": _first_text(
                        item.get("pregunta_padre"),
                        item.get("grid_id"),
                        item.get("pregunta_id"),
                        variable,
                    ),
                    "grid_id": _first_text(
                        item.get("grid_id"),
                        item.get("pregunta_padre"),
                        item.get("pregunta_id"),
                    ),
                    "variable": variable,
                    "entidad_loop": _first_text(
                        item.get("label_entidad_loop"),
                        item.get("entidad_loop"),
                        item.get("texto_fila_grid"),
                    ),
                    "orden_entidad_loop": item.get("orden_entidad_loop"),
                    "codigo_opcion": code,
                    "label_opcion": label,
                    "orden_opcion": item.get("orden_opcion_rm"),
                    "valor": value,
                    "seleccionado": int(
                        (not missing) and _is_selected(value, code)
                    ),
                    "base_valida": int(not missing),
                    "missing_estructural": int(missing),
                    "peso": weights.loc[index],
                }
            )
    result = pd.DataFrame(rows, columns=GRID_LOOP_COLUMNS)
    result = _reconstruct_structural_base(result)
    return result.reset_index(drop=True)


def _reconstruct_structural_base(result: pd.DataFrame) -> pd.DataFrame:
    if result.empty:
        return result
    work = result.copy()
    work["_has_value"] = ~work["valor"].apply(_is_missing)
    keys = [
        "id_respondente",
        "pregunta_id",
        "grid_id",
        "entidad_loop",
    ]
    work["_base_valid_group"] = work.groupby(keys, dropna=False)[
        "_has_value"
    ].transform("any")
    work["base_valida"] = work["_base_valid_group"].astype(int)
    work["missing_estructural"] = (~work["_base_valid_group"]).astype(int)
    work.loc[~work["_base_valid_group"], "seleccionado"] = 0
    return work.drop(columns=["_has_value", "_base_valid_group"])


def _is_grid_rm_item(row: pd.Series) -> bool:
    if truthy(row.get("es_abierta_asociada")):
        return False
    if truthy(row.get("es_grid_rm_loop")):
        return bool(str(row.get("variable") or "").strip())
    text = normalize_text(
        f"{row.get('tipo_pregunta', '')} {row.get('tipo_estructura_grid', '')}"
    )
    return (
        ("grid_rm" in text or "loop_rm" in text)
        and bool(str(row.get("variable") or "").strip())
    )


def _is_selected(value: object, code: object) -> bool:
    normalized = normalize_text(value)
    if normalized in {"si", "yes", "selected", "seleccionado"}:
        return True
    numeric = pd.to_numeric(value, errors="coerce")
    numeric_code = pd.to_numeric(code, errors="coerce")
    if pd.notna(numeric):
        if numeric == 1:
            return True
        if pd.notna(numeric_code) and numeric == numeric_code:
            return True
    return bool(str(code).strip() and str(value).strip() == str(code).strip())


def _is_missing(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return normalize_text(value) in {"", "nan", "none", "null"}


def _single_label_code(labels: dict[Any, str]) -> str:
    if len(labels) != 1:
        return ""
    return str(next(iter(labels.keys()))).strip()


def _single_label_text(labels: dict[Any, str]) -> str:
    if len(labels) != 1:
        return ""
    return str(next(iter(labels.values()))).strip()


def _first_text(*values: object) -> str:
    for value in values:
        if value is None:
            continue
        try:
            if pd.isna(value):
                continue
        except (TypeError, ValueError):
            pass
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none"}:
            return text
    return ""
