from __future__ import annotations

from typing import Any

import pandas as pd

from src.readers.spss_reader import get_value_labels
from src.readers.scale_definition import scale_bounds
from src.reporter.calculations import (
    bottom2box,
    nps_group,
    top2box,
    weight_series,
)
from src.utils.text_utils import normalize_text
from src.utils.text_utils import truthy


ESCALAS_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "variable",
    "item_texto",
    "valor",
    "respuesta_label",
    "escala_min",
    "escala_max",
    "top2box",
    "bottombox",
    "nps_grupo",
    "ponderador",
]


def build_escalas_long(
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    respondentes: pd.DataFrame,
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=ESCALAS_COLUMNS)

    weights = weight_series(datamap_df, df_spss)
    scale_rows = datamap_df[datamap_df.apply(_is_scale_row, axis=1)]
    rows = []
    for _, item in scale_rows.iterrows():
        variable = item.get("variable")
        if variable not in df_spss.columns:
            continue
        if "usar_en_dashboard" in item and not truthy(item["usar_en_dashboard"]):
            continue
        labels = get_value_labels(meta_spss, variable)
        values = pd.to_numeric(df_spss[variable], errors="coerce")
        valid = values.dropna()
        if valid.empty:
            continue
        scale_min, scale_max = scale_bounds(item, labels)
        if scale_min is not None and not valid.between(scale_min, scale_max).all():
            raise ValueError(f"La variable {variable} contiene valores fuera de su escala declarada.")

        for idx, value in valid.items():
            label = labels.get(value, labels.get(str(value), ""))
            rows.append(
                {
                    "id_respondente": respondentes.loc[idx, "id_respondente"],
                    "pregunta_id": item.get("pregunta_id") or variable,
                    "variable": variable,
                    "item_texto": item.get("label") or item.get("texto_pregunta") or variable,
                    "valor": value,
                    "respuesta_label": label or str(value),
                    "escala_min": scale_min,
                    "escala_max": scale_max,
                    "top2box": top2box(value, scale_min, scale_max) if scale_min is not None else None,
                    "bottombox": bottom2box(value, scale_min, scale_max) if scale_min is not None else None,
                    "nps_grupo": nps_group(value) if _is_nps_row(item) else "",
                    "ponderador": weights.loc[idx],
                }
            )
    return pd.DataFrame(rows, columns=ESCALAS_COLUMNS)


def _is_scale_row(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
    return any(token in text for token in ["escala", "grid", "media", "top2box", "bottom2box", "nps"])


def _is_nps_row(row: pd.Series) -> bool:
    return "nps" in normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
