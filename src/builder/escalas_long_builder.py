from __future__ import annotations

from typing import Any

import pandas as pd

from src.readers.spss_reader import get_value_labels
from src.reporter.calculations import (
    bottom2box,
    nps_group,
    top2box,
    weight_series,
)
from src.utils.text_utils import normalize_text


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
        labels = get_value_labels(meta_spss, variable)
        values = pd.to_numeric(df_spss[variable], errors="coerce")
        valid = values.dropna()
        if valid.empty:
            continue
        scale_min = float(valid.min())
        scale_max = float(valid.max())
        if 0 in set(valid.unique()) and scale_max <= 5:
            valid = valid[valid != 0]
            scale_min = float(valid.min()) if not valid.empty else 1.0
        if scale_max <= 5 and scale_min >= 1:
            scale_min, scale_max = 1.0, 5.0
        elif scale_max <= 10:
            scale_min, scale_max = 0.0, 10.0

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
                    "top2box": top2box(value, scale_min, scale_max),
                    "bottombox": bottom2box(value, scale_min, scale_max),
                    "nps_grupo": nps_group(value) if _is_nps_row(item) or scale_max == 10 else "",
                    "ponderador": weights.loc[idx],
                }
            )
    return pd.DataFrame(rows, columns=ESCALAS_COLUMNS)


def _is_scale_row(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
    if "grid_rm_loop" in text or "rm_dicotomica_label" in text:
        return False
    return any(token in text for token in ["escala", "grid", "media", "top2box", "bottom2box", "nps"])


def _is_nps_row(row: pd.Series) -> bool:
    return "nps" in normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
