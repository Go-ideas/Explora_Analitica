from __future__ import annotations

import pandas as pd

from src.reporter.calculations import weight_series
from src.utils.constants import NO_RESPONSE_TEXTS
from src.utils.text_utils import clean_open_text, normalize_text


ABIERTAS_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "variable",
    "texto_original",
    "texto_limpio",
    "ponderador",
]


def build_abiertas(
    df_spss: pd.DataFrame,
    datamap_df: pd.DataFrame,
    respondentes: pd.DataFrame,
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=ABIERTAS_COLUMNS)
    weights = weight_series(datamap_df, df_spss)
    open_rows = datamap_df[datamap_df.apply(_is_open_row, axis=1)]
    rows = []
    for _, item in open_rows.iterrows():
        variable = item.get("variable")
        if variable not in df_spss.columns:
            continue
        for idx, value in df_spss[variable].dropna().items():
            original = clean_open_text(value)
            if normalize_text(original) in {normalize_text(text) for text in NO_RESPONSE_TEXTS}:
                continue
            rows.append(
                {
                    "id_respondente": respondentes.loc[idx, "id_respondente"],
                    "pregunta_id": item.get("pregunta_id") or variable,
                    "variable": variable,
                    "texto_original": original,
                    "texto_limpio": normalize_text(original).replace("_", " "),
                    "ponderador": weights.loc[idx],
                }
            )
    return pd.DataFrame(rows, columns=ABIERTAS_COLUMNS)


def _is_open_row(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('clasificacion_analitica', '')} {row.get('tipo_calculo', '')}")
    return "abierta" in text or "texto_abierto" in text
