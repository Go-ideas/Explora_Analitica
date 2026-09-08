from __future__ import annotations

from typing import Any

import pandas as pd

from src.reporter.calculations import weight_series
from src.readers.spss_reader import get_value_labels
from src.utils.text_utils import normalize_text


RESPUESTAS_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "variable",
    "tipo_pregunta",
    "codigo_respuesta",
    "respuesta_label",
    "valor_numerico",
    "respuesta_texto",
    "ponderador",
    "base_valida",
]


def build_respuestas_long(
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    respondentes: pd.DataFrame,
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=RESPUESTAS_COLUMNS)

    weights = weight_series(datamap_df, df_spss)
    rows = []
    classifications = datamap_df[
        "clasificacion_analitica"
    ].fillna("")
    question_types = datamap_df["tipo_pregunta"].fillna(
        ""
    ).astype(str).str.strip()
    reportable = question_types.ne("") | classifications.eq(
        "Pregunta analizable"
    )
    candidates = datamap_df[
        (datamap_df["usar_en_dashboard"] == True)
        & reportable
        & ~classifications.isin(
            {
                "Variable técnica",
                "Control de calidad",
                "No usar en dashboard",
                "Abierta",
            }
        )
    ]
    for _, item in candidates.iterrows():
        variable = item.get("variable")
        if variable not in df_spss.columns or _is_rm(item) or _is_scale(item) or _is_open(item):
            continue
        labels = get_value_labels(meta_spss, variable)
        series = df_spss[variable]
        for idx, value in series.dropna().items():
            label = labels.get(value, labels.get(str(value), ""))
            rows.append(
                {
                    "id_respondente": respondentes.loc[idx, "id_respondente"],
                    "pregunta_id": item.get("pregunta_id") or variable,
                    "variable": variable,
                    "tipo_pregunta": item.get("tipo_pregunta", ""),
                    "codigo_respuesta": value,
                    "respuesta_label": label or str(value),
                    "valor_numerico": pd.to_numeric(value, errors="coerce"),
                    "respuesta_texto": "" if pd.notna(pd.to_numeric(value, errors="coerce")) else str(value),
                    "ponderador": weights.loc[idx],
                    "base_valida": True,
                }
            )
    return pd.DataFrame(rows, columns=RESPUESTAS_COLUMNS)


def _is_rm(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
    return "rm" in text or "multiple" in text or "multirrespuesta" in text


def _is_scale(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('tipo_pregunta', '')} {row.get('tipo_calculo', '')}")
    if "grid_rm_loop" in text or "rm_dicotomica_label" in text:
        return False
    return any(token in text for token in ["escala", "grid", "media", "top2box", "bottom2box", "nps"])


def _is_open(row: pd.Series) -> bool:
    text = normalize_text(f"{row.get('clasificacion_analitica', '')} {row.get('tipo_calculo', '')}")
    return "abierta" in text or "texto_abierto" in text
