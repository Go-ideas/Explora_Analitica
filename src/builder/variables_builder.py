from __future__ import annotations

from typing import Any

import pandas as pd

from src.builder.recommendations_builder import (
    clean_commercial_justification,
    format_base_distribution,
)
from src.readers.spss_reader import (
    get_value_labels,
    get_variable_label,
)
from src.utils.text_utils import truthy


VARIABLE_COLUMNS = [
    "variable",
    "label",
    "tipo_spss",
    "pregunta_id",
    "tipo_pregunta",
    "tipo_estructura_grid",
    "clasificacion_analitica",
    "usar_en_dashboard",
    "es_banner",
    "es_filtro",
    "es_ponderador",
    "tipo_calculo",
    "n_validos",
    "n_missing",
    "valores_unicos",
    "min",
    "max",
    "es_banner_recomendado",
    "es_filtro_recomendado",
    "nivel_relevancia_comercial",
    "justificacion_banner_filtro",
    "uso_comercial_sugerido",
    "distribucion_base",
    "riesgo_uso_analitico",
    "requiere_factor",
    "tipo_factor_recomendado",
    "variables_para_factor",
    "regla_factor_sugerida",
    "justificacion_factor",
    "prioridad_factor",
    "entidad_loop",
    "opcion_rm",
    "label_opcion_rm",
    "texto_opcion_rm",
    "display_item_reporteador",
    "codigo_opcion_rm",
]


def build_variables(df_spss: pd.DataFrame, meta_spss: Any, datamap_df: pd.DataFrame) -> pd.DataFrame:
    datamap_by_var = {}
    if datamap_df is not None and not datamap_df.empty:
        datamap_by_var = datamap_df.set_index("variable", drop=False).to_dict("index")

    rows = []
    for variable in df_spss.columns:
        series = df_spss[variable]
        numeric = pd.to_numeric(series, errors="coerce")
        row = datamap_by_var.get(variable, {})
        is_numeric = pd.api.types.is_numeric_dtype(series) or (
            series.notna().sum() > 0 and numeric.notna().sum() == series.notna().sum()
        )
        rows.append(
            {
                "variable": variable,
                "label": row.get("label") or get_variable_label(meta_spss, variable),
                "tipo_spss": "numeric" if is_numeric else "text",
                "pregunta_id": row.get("pregunta_id") or variable,
                "tipo_pregunta": row.get("tipo_pregunta", ""),
                "tipo_estructura_grid": row.get(
                    "tipo_estructura_grid", ""
                ),
                "clasificacion_analitica": row.get("clasificacion_analitica", "Requiere validación"),
                "usar_en_dashboard": bool(row.get("usar_en_dashboard", False)),
                "es_banner": bool(row.get("es_banner", False)),
                "es_filtro": bool(row.get("es_filtro", False)),
                "es_ponderador": bool(row.get("es_ponderador", False)),
                "tipo_calculo": row.get("tipo_calculo", "No aplica"),
                "n_validos": int(series.notna().sum()),
                "n_missing": int(series.isna().sum()),
                "valores_unicos": int(series.nunique(dropna=True)),
                "min": numeric.min() if numeric.notna().any() else None,
                "max": numeric.max() if numeric.notna().any() else None,
                "es_banner_recomendado": int(
                    truthy(row.get("es_banner_recomendado"))
                ),
                "es_filtro_recomendado": int(
                    truthy(row.get("es_filtro_recomendado"))
                ),
                "nivel_relevancia_comercial": _text(
                    row.get("nivel_relevancia_comercial")
                ),
                "justificacion_banner_filtro": (
                    clean_commercial_justification(
                        row.get(
                            "justificacion_banner_filtro"
                        ),
                        "",
                        row.get("label") or variable,
                        _recommended_role(row),
                        row.get("uso_comercial_sugerido"),
                        (
                            "banner_filtro"
                            if _has_commercial_role(row)
                            else ""
                        ),
                    )
                ),
                "uso_comercial_sugerido": _text(
                    row.get("uso_comercial_sugerido")
                ),
                "distribucion_base": (
                    format_base_distribution(
                        series,
                        get_value_labels(meta_spss, variable),
                    )
                    if any(
                        truthy(row.get(field))
                        for field in (
                            "es_banner",
                            "es_filtro",
                            "es_banner_recomendado",
                            "es_filtro_recomendado",
                        )
                    )
                    else ""
                ),
                "riesgo_uso_analitico": _text(
                    row.get("riesgo_uso_analitico")
                ),
                "requiere_factor": int(
                    truthy(row.get("requiere_factor"))
                ),
                "tipo_factor_recomendado": _text(
                    row.get("tipo_factor_recomendado")
                ),
                "variables_para_factor": _text(
                    row.get("variables_para_factor")
                ),
                "regla_factor_sugerida": _text(
                    row.get("regla_factor_sugerida")
                ),
                "justificacion_factor": _text(
                    row.get("justificacion_factor")
                ),
                "prioridad_factor": _text(
                    row.get("prioridad_factor")
                ),
                "entidad_loop": _text(row.get("entidad_loop")),
                "opcion_rm": _text(row.get("opcion_rm")),
                "label_opcion_rm": _text(row.get("label_opcion_rm")),
                "texto_opcion_rm": _text(row.get("texto_opcion_rm")),
                "display_item_reporteador": _text(
                    row.get("display_item_reporteador")
                ),
                "codigo_opcion_rm": _text(row.get("codigo_opcion_rm")),
            }
        )
    return pd.DataFrame(rows, columns=VARIABLE_COLUMNS)


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text


def _has_commercial_role(row: dict) -> bool:
    return any(
        truthy(row.get(field))
        for field in (
            "es_banner",
            "es_filtro",
            "es_banner_recomendado",
            "es_filtro_recomendado",
        )
    )


def _recommended_role(row: dict) -> str:
    banner = truthy(row.get("es_banner_recomendado")) or truthy(
        row.get("es_banner")
    )
    filter_ = truthy(row.get("es_filtro_recomendado")) or truthy(
        row.get("es_filtro")
    )
    if banner and filter_:
        return "banner y filtro"
    if banner:
        return "banner"
    if filter_:
        return "filtro"
    return "variable de análisis"
