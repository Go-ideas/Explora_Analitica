from __future__ import annotations

from typing import Any

import pandas as pd

from src.readers.spss_reader import get_value_labels
from src.utils.constants import EXCLUSIVE_OPTION_HINTS
from src.utils.text_utils import find_column


OPCIONES_COLUMNS = ["variable", "pregunta_id", "codigo", "label", "es_otro", "es_exclusiva", "orden"]


def build_opciones(meta_spss: Any, datamap_df: pd.DataFrame, value_label_sheet: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    datamap_by_var = {}
    if datamap_df is not None and not datamap_df.empty:
        datamap_by_var = datamap_df.set_index("variable", drop=False).to_dict("index")
    variables = list(datamap_by_var.keys()) or list(getattr(meta_spss, "column_names", []) or [])

    for variable in variables:
        labels = get_value_labels(meta_spss, variable)
        pregunta_id = datamap_by_var.get(variable, {}).get("pregunta_id", variable)
        for order, (code, label) in enumerate(labels.items(), start=1):
            label_text = str(label)
            rows.append(
                {
                    "variable": variable,
                    "pregunta_id": pregunta_id,
                    "codigo": code,
                    "label": label_text,
                    "es_otro": "otro" in label_text.lower(),
                    "es_exclusiva": any(hint in label_text.lower() for hint in EXCLUSIVE_OPTION_HINTS),
                    "orden": order,
                }
            )
        row = datamap_by_var.get(variable, {})
        if row.get("label_opcion_rm") or row.get("codigo_opcion_rm"):
            label_text = str(row.get("label_opcion_rm") or row.get("label") or variable)
            code = row.get("codigo_opcion_rm") or row.get("orden_opcion_rm") or variable
            rows.append(
                {
                    "variable": variable,
                    "pregunta_id": pregunta_id,
                    "codigo": code,
                    "label": label_text,
                    "es_otro": "otro" in label_text.lower(),
                    "es_exclusiva": any(
                        hint in label_text.lower()
                        for hint in EXCLUSIVE_OPTION_HINTS
                    ),
                    "orden": row.get("orden_opcion_rm") or len(rows) + 1,
                }
            )

    if value_label_sheet is not None and not value_label_sheet.empty:
        rows.extend(_rows_from_value_label_sheet(value_label_sheet, datamap_by_var))

    if not rows:
        return pd.DataFrame(columns=OPCIONES_COLUMNS)
    return pd.DataFrame(rows).drop_duplicates(["variable", "codigo", "label"]).reset_index(drop=True)


def _rows_from_value_label_sheet(df: pd.DataFrame, datamap_by_var: dict[str, dict]) -> list[dict]:
    variable_col = find_column(df.columns, ["variable", "variable_spss"])
    code_col = find_column(df.columns, ["codigo", "code", "valor"])
    label_col = find_column(df.columns, ["label", "etiqueta", "value_label", "respuesta"])
    if not variable_col or not code_col or not label_col:
        return []
    rows = []
    for order, row in df.iterrows():
        variable = str(row[variable_col])
        label = str(row[label_col])
        rows.append(
            {
                "variable": variable,
                "pregunta_id": datamap_by_var.get(variable, {}).get("pregunta_id", variable),
                "codigo": row[code_col],
                "label": label,
                "es_otro": "otro" in label.lower(),
                "es_exclusiva": any(hint in label.lower() for hint in EXCLUSIVE_OPTION_HINTS),
                "orden": int(order) + 1,
            }
        )
    return rows
