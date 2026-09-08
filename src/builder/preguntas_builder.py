from __future__ import annotations

import pandas as pd


PREGUNTA_COLUMNS = [
    "pregunta_id",
    "seccion",
    "numero_pregunta",
    "texto_pregunta",
    "tipo_pregunta",
    "tipo_estructura_grid",
    "tipo_calculo",
    "base_valida",
    "regla_transformacion",
    "usar_en_dashboard",
    "orden_cuestionario",
    "seccion_cuestionario",
    "bloque_cuestionario",
    "grupo_menu_reporteador",
    "mostrar_en_menu_reporteador",
    "prioridad_reporteador",
]


def build_preguntas(datamap_df: pd.DataFrame) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=PREGUNTA_COLUMNS)
    work = datamap_df.copy()
    for col in PREGUNTA_COLUMNS:
        if col not in work:
            work[col] = ""
    work["pregunta_id"] = work["pregunta_id"].fillna(work["variable"]).astype(str)
    rows = []
    for pregunta_id, group in work.groupby(
        "pregunta_id", sort=False
    ):
        row = {"pregunta_id": pregunta_id}
        for column in PREGUNTA_COLUMNS[1:]:
            row[column] = _representative_value(group[column])
        row["orden_cuestionario"] = _numeric_representative(
            group["orden_cuestionario"]
        )
        row["usar_en_dashboard"] = bool(
            group["usar_en_dashboard"].fillna(False).astype(bool).any()
        )
        if not row["seccion"]:
            row["seccion"] = row["seccion_cuestionario"]
        if not row["seccion_cuestionario"]:
            row["seccion_cuestionario"] = row["seccion"]
        if not row["numero_pregunta"]:
            row["numero_pregunta"] = pregunta_id
        if not row["mostrar_en_menu_reporteador"]:
            row["mostrar_en_menu_reporteador"] = (
                "Sí" if row["usar_en_dashboard"] else "No"
            )
        rows.append(row)
    return pd.DataFrame(rows, columns=PREGUNTA_COLUMNS)


def _representative_value(series: pd.Series) -> object:
    values = series.dropna()
    if values.empty:
        return ""
    text = values.astype(str).str.strip()
    non_empty = values[text.ne("")]
    if non_empty.empty:
        return ""
    counts = non_empty.astype(str).value_counts()
    return counts.index[0]


def _numeric_representative(series: pd.Series) -> object:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    value = float(values.min())
    return int(value) if value.is_integer() else value
