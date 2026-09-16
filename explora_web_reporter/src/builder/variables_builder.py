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
    "clasificacion_analitica",
    "usar_en_dashboard",
    "mostrar_en_menu_reporteador",
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
    "grid_id",
    "pregunta_padre",
    "tipo_estructura_grid",
    "es_grid",
    "es_item_grid",
    "es_grid_rm_loop",
    "orden_fila_grid",
    "texto_fila_grid",
    "entidad_loop",
    "orden_entidad_loop",
    "label_entidad_loop",
    "codigo_opcion_rm",
    "label_opcion_rm",
    "orden_opcion_rm",
    "formato_rm",
    "value_label_patron",
    "valores_observados_patron",
    "es_abierta_asociada",
    "base_valida_pregunta_padre",
    "base_valida_fila",
    "base_valida_columna",
    "regla_base_valida",
    "metrica_grid_recomendada",
    "regla_tabular_recomendada",
    "riesgo_grid",
    "match_confianza",
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
                "clasificacion_analitica": row.get("clasificacion_analitica", "Requiere validación"),
                "usar_en_dashboard": bool(row.get("usar_en_dashboard", False)),
                "mostrar_en_menu_reporteador": _text(
                    row.get("mostrar_en_menu_reporteador")
                ),
                "es_banner": bool(row.get("es_banner", False)),
                "es_filtro": bool(row.get("es_filtro", False)),
                "es_ponderador": bool(row.get("es_ponderador", False)),
                "tipo_calculo": _calculation(row),
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
                "grid_id": _text(row.get("grid_id")),
                "pregunta_padre": _text(row.get("pregunta_padre")),
                "tipo_estructura_grid": _text(
                    row.get("tipo_estructura_grid")
                ),
                "es_grid": int(truthy(row.get("es_grid"))),
                "es_item_grid": int(truthy(row.get("es_item_grid"))),
                "es_grid_rm_loop": int(
                    truthy(row.get("es_grid_rm_loop"))
                ),
                "orden_fila_grid": row.get("orden_fila_grid"),
                "texto_fila_grid": _text(row.get("texto_fila_grid")),
                "entidad_loop": _text(row.get("entidad_loop")),
                "orden_entidad_loop": row.get("orden_entidad_loop"),
                "label_entidad_loop": _text(
                    row.get("label_entidad_loop")
                ),
                "codigo_opcion_rm": _text(row.get("codigo_opcion_rm")),
                "label_opcion_rm": _text(row.get("label_opcion_rm")),
                "orden_opcion_rm": row.get("orden_opcion_rm"),
                "formato_rm": _text(row.get("formato_rm")),
                "value_label_patron": _text(row.get("value_label_patron")),
                "valores_observados_patron": _text(
                    row.get("valores_observados_patron")
                ),
                "es_abierta_asociada": int(
                    truthy(row.get("es_abierta_asociada"))
                ),
                "base_valida_pregunta_padre": row.get(
                    "base_valida_pregunta_padre"
                ),
                "base_valida_fila": row.get("base_valida_fila"),
                "base_valida_columna": row.get("base_valida_columna"),
                "regla_base_valida": _text(row.get("regla_base_valida")),
                "metrica_grid_recomendada": _text(
                    row.get("metrica_grid_recomendada")
                ),
                "regla_tabular_recomendada": _text(
                    row.get("regla_tabular_recomendada")
                ),
                "riesgo_grid": _text(row.get("riesgo_grid")),
                "match_confianza": _text(row.get("match_confianza")),
            }
        )
    return pd.DataFrame(rows, columns=VARIABLE_COLUMNS)


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text


def _calculation(row: dict) -> str:
    value = _text(row.get("tipo_calculo"))
    structure = _text(row.get("tipo_estructura_grid")).upper()
    if value:
        return value
    if truthy(row.get("es_grid_rm_loop")):
        return "Multirrespuesta agrupada"
    if structure == "GRID_ESCALA":
        return "Distribución grid"
    if structure == "LOOP_NUMERICO":
        return "Media"
    return "Frecuencia"


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
