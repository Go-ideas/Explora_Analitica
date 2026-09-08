from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

import pandas as pd

from src.utils.constants import (
    CALCULATION_OPTIONS,
    CLASSIFICATION_OPTIONS,
    EXPECTED_DATAMAP_SHEETS,
    KEY_DATAMAP_SHEETS,
    REVIEW_COLUMNS,
)
from src.utils.text_utils import find_column, normalize_text, truthy


LOGGER = logging.getLogger(__name__)


COLUMN_ALIASES = {
    "variable": [
        "variable_spss",
        "variable",
        "variable_item",
        "nombre_variable",
        "var",
        "campo",
    ],
    "label": [
        "label_spss",
        "label",
        "label_variable",
        "variable_label",
        "texto_opcion_rm",
        "label_opcion_rm",
        "opcion_extraida_label",
        "display_item_reporteador",
        "variable_label",
        "etiqueta",
        "etiqueta_variable",
        "descripcion",
    ],
    "pregunta_id": [
        "numero_pregunta",
        "pregunta_padre",
        "pregunta_id",
        "pregunta",
        "pregunta_asociada",
        "id_pregunta",
        "question_id",
        "codigo_pregunta",
    ],
    "texto_pregunta": [
        "texto_pregunta",
        "texto_pregunta_padre",
        "pregunta_texto",
        "texto",
        "question_text",
        "label_pregunta",
        "label_spss",
    ],
    "tipo_pregunta": [
        "tipo_final",
        "tipo_pregunta",
        "tipo_pregunta_cuestionario",
        "tipo_estructura_grid",
        "tipo_estructura_corregido",
        "tipo",
        "tipo_variable",
        "question_type",
    ],
    "clasificacion_analitica": [
        "clasificacion_analitica",
        "clasificacion",
        "uso_analitico",
        "rol_analitico",
        "rol_analitico_principal",
    ],
    "usar_en_dashboard": ["usar_en_dashboard", "usar_dashboard", "dashboard", "incluir_dashboard"],
    "es_banner": ["es_banner", "banner"],
    "es_filtro": ["es_filtro", "filtro"],
    "es_ponderador": ["es_ponderador", "ponderador", "peso", "weight"],
    "tipo_calculo": ["tipo_calculo", "calculo", "metrica", "indicador"],
    "regla_transformacion": ["regla_transformacion", "regla", "transformacion"],
    "observacion_usuario": ["observacion_usuario", "observacion", "comentario", "notas"],
    "seccion": [
        "seccion_cuestionario",
        "bloque_cuestionario",
        "grupo_menu_reporteador",
        "seccion",
        "sección",
    ],
    "seccion_cuestionario": [
        "seccion_cuestionario",
        "sección_cuestionario",
        "bloque_cuestionario",
        "grupo_menu_reporteador",
        "seccion",
        "sección",
    ],
    "bloque_cuestionario": [
        "bloque_cuestionario",
        "bloque",
    ],
    "numero_pregunta": [
        "numero_pregunta",
        "número_pregunta",
    ],
    "orden_cuestionario": [
        "orden_cuestionario",
        "orden_reporte",
        "orden",
    ],
    "grupo_menu_reporter": [
        "grupo_menu_reporter",
        "grupo_menu_reporteador",
    ],
    "grupo_menu_reporteador": [
        "grupo_menu_reporteador",
        "grupo_menu_reporter",
    ],
    "mostrar_en_menu_reporter": [
        "mostrar_en_menu_reporter",
        "mostrar_en_menu_reporteador",
    ],
    "mostrar_en_menu_reporteador": [
        "mostrar_en_menu_reporteador",
        "mostrar_en_menu_reporter",
    ],
    "prioridad_reporteador": [
        "prioridad_reporteador",
        "prioridad_reporter",
    ],
    "es_banner_recomendado": [
        "es_banner_recomendado",
        "banner_recomendado",
    ],
    "es_filtro_recomendado": [
        "es_filtro_recomendado",
        "filtro_recomendado",
    ],
    "nivel_relevancia_comercial": [
        "nivel_relevancia_comercial",
        "relevancia_comercial",
    ],
    "justificacion_banner_filtro": [
        "justificacion_banner_filtro",
        "justificación_banner_filtro",
        "justificacion",
    ],
    "uso_comercial_sugerido": [
        "uso_comercial_sugerido",
        "uso_comercial",
    ],
    "distribucion_base": [
        "distribucion_base",
        "distribución_base",
        "base_categorias_obs",
        "base_por_categoria",
    ],
    "riesgo_uso_analitico": [
        "riesgo_uso_analitico",
        "riesgo_analitico",
    ],
    "requiere_factor": ["requiere_factor"],
    "tipo_factor_recomendado": [
        "tipo_factor_recomendado",
    ],
    "variables_para_factor": ["variables_para_factor"],
    "regla_factor_sugerida": ["regla_factor_sugerida"],
    "justificacion_factor": [
        "justificacion_factor",
        "justificación_factor",
    ],
    "prioridad_factor": ["prioridad_factor"],
    "tipo_estructura_grid": [
        "tipo_estructura_grid",
        "tipo_estructura_corregido",
        "tipo_final",
    ],
    "entidad_loop": ["entidad_loop"],
    "opcion_rm": [
        "opcion_rm",
        "opcion_extraida_label",
        "texto_fila_opcion",
        "texto_fila/opcion",
    ],
    "label_opcion_rm": [
        "label_opcion_rm",
        "texto_opcion_rm",
        "opcion_extraida_label",
        "display_item_reporteador",
    ],
    "texto_opcion_rm": [
        "texto_opcion_rm",
        "texto_fila_opcion",
        "texto_fila/opcion",
        "opcion_extraida_label",
    ],
    "display_item_reporteador": ["display_item_reporteador"],
    "codigo_opcion_rm": [
        "codigo_opcion_rm",
        "codigo_opcion",
    ],
}

REVIEW_SOURCE_PRIORITY = [
    "10_Datamap_Corregido",
    "08_Clasificacion_Analitica",
    "Datamap_Preguntas",
]

REFERENCE_SHEETS = [
    "99_RM_Dicotomicas_Labels",
    "04_Check_Escalas",
    "04B_Check_Grids",
    "05_Check_RM",
    "Variables_SPSS",
    "Datamap_Preguntas",
    "10_Datamap_Corregido",
    "08_Clasificacion_Analitica",
]


def read_datamap(path: Path) -> dict[str, pd.DataFrame]:
    try:
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(f"No se pudo leer el Datamap Validado: {exc}") from exc
    return {name: df for name, df in sheets.items()}


def datamap_summary(sheets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    found = list(sheets.keys())
    missing_expected = [sheet for sheet in EXPECTED_DATAMAP_SHEETS if sheet not in sheets]
    missing_key = [sheet for sheet in KEY_DATAMAP_SHEETS if sheet not in sheets]
    qa_status = extract_qa_status(sheets.get("00_Resumen_QA"))
    risks = summarize_risks(sheets.get("09_Riesgos_Priorizados"))
    return {
        "found_sheets": found,
        "missing_expected": missing_expected,
        "missing_key": missing_key,
        "qa_status": qa_status,
        "risk_counts": risks,
    }


def extract_qa_status(df: pd.DataFrame | None) -> str | None:
    if df is None or df.empty:
        return None
    flat_values = [str(value) for value in df.to_numpy().ravel() if pd.notna(value)]
    status_words = ["verde", "amarillo", "rojo", "aprobado", "observado", "critico", "crítico"]
    for value in flat_values:
        norm = normalize_text(value)
        if any(word in norm for word in [normalize_text(word) for word in status_words]):
            return value
    return flat_values[0] if flat_values else None


def summarize_risks(df: pd.DataFrame | None) -> dict[str, int]:
    counts = {"criticos": 0, "altos": 0, "medios": 0, "bajos": 0}
    if df is None or df.empty:
        return counts
    priority_col = find_column(df.columns, ["prioridad", "nivel", "severidad", "riesgo"])
    if not priority_col:
        return counts
    values = df[priority_col].dropna().map(normalize_text)
    counts["criticos"] = int(values.str.contains("crit").sum())
    counts["altos"] = int(values.str.contains("alto|alta").sum())
    counts["medios"] = int(values.str.contains("medio|media").sum())
    counts["bajos"] = int(values.str.contains("bajo|baja").sum())
    return counts


def get_review_source_sheet(sheets: dict[str, pd.DataFrame]) -> tuple[str | None, pd.DataFrame | None]:
    source_name, source = _select_review_source(sheets)
    if source_name and source is not None:
        source = source.copy()
        for reference_name in REFERENCE_SHEETS:
            if reference_name == source_name:
                continue
            source = _enrich_review_source(
                source, sheets.get(reference_name)
            )
        return source_name, source
    return None, None


def _select_review_source(
    sheets: dict[str, pd.DataFrame]
) -> tuple[str | None, pd.DataFrame | None]:
    for name in REVIEW_SOURCE_PRIORITY:
        frame = sheets.get(name)
        if frame is None or frame.empty:
            continue
        candidate = _usable_reference(frame)
        if _find_exact_column(candidate.columns, COLUMN_ALIASES["variable"]):
            return name, candidate.copy()
    for name in REVIEW_SOURCE_PRIORITY:
        frame = sheets.get(name)
        if frame is not None and not frame.empty:
            return name, _usable_reference(frame).copy()
    return None, None


def normalize_review_datamap(df: pd.DataFrame, spss_columns: list[str] | None = None) -> pd.DataFrame:
    if df is None or df.empty:
        base = pd.DataFrame({"variable": spss_columns or []})
    else:
        base = pd.DataFrame()
        for canonical, aliases in COLUMN_ALIASES.items():
            source = _find_exact_column(df.columns, aliases)
            base[canonical] = df[source] if source else ""

        used_sources = {
            _find_exact_column(df.columns, aliases)
            for aliases in COLUMN_ALIASES.values()
        }
        for original_col in df.columns:
            if original_col not in used_sources and normalize_text(original_col) not in base.columns:
                base[original_col] = df[original_col]

    for col in REVIEW_COLUMNS:
        if col not in base.columns:
            base[col] = ""

    if spss_columns and "variable" in base:
        missing_vars = [col for col in spss_columns if col not in set(base["variable"].dropna().astype(str))]
        if missing_vars:
            additions = pd.DataFrame({"variable": missing_vars})
            base = pd.concat([base, additions], ignore_index=True)

    base = base.copy()
    base["variable"] = base["variable"].fillna("").astype(str).str.strip()
    base["label"] = base["label"].fillna("").astype(str)
    base["pregunta_id"] = base["pregunta_id"].fillna("").astype(str)
    base.loc[base["pregunta_id"].eq(""), "pregunta_id"] = base.loc[
        base["pregunta_id"].eq(""), "variable"
    ]
    base["texto_pregunta"] = base["texto_pregunta"].fillna(base["label"]).replace("", pd.NA)
    base["texto_pregunta"] = base["texto_pregunta"].fillna(base["label"]).fillna("")
    raw_classification = base["clasificacion_analitica"].map(
        normalize_text
    )
    base["clasificacion_analitica"] = base[
        "clasificacion_analitica"
    ].apply(normalize_classification)
    base["tipo_calculo"] = base["tipo_calculo"].apply(normalize_calculation)
    base = _normalize_question_roles(base, raw_classification)
    for order_column in (
        "orden_cuestionario",
        "orden_reporte",
    ):
        if order_column in base.columns:
            base[order_column] = pd.to_numeric(
                base[order_column], errors="coerce"
            ).astype("Int64")
    base["usar_en_dashboard"] = base.apply(_dashboard_default, axis=1)
    base["es_banner"] = base.apply(
        lambda row: bool(truthy(row.get("es_banner")) or row.get("clasificacion_analitica") == "Banner"),
        axis=1,
    )
    base["es_filtro"] = base.apply(
        lambda row: bool(truthy(row.get("es_filtro")) or row.get("clasificacion_analitica") == "Filtro"),
        axis=1,
    )
    base["es_ponderador"] = base.apply(
        lambda row: bool(
            truthy(row.get("es_ponderador")) or row.get("clasificacion_analitica") == "Ponderador"
        ),
        axis=1,
    )
    return base[REVIEW_COLUMNS + [col for col in base.columns if col not in REVIEW_COLUMNS]]


def build_datamap_import_log(
    sheets: dict[str, pd.DataFrame],
    review: pd.DataFrame,
) -> dict[str, Any]:
    source_name, source = _select_review_source(sheets)
    source = source if source is not None else pd.DataFrame()
    source_columns = list(source.columns)
    field_rows = []
    log_fields = {
        "Variable": COLUMN_ALIASES["variable"],
        "Label": COLUMN_ALIASES["label"],
        "Pregunta": COLUMN_ALIASES["pregunta_id"],
        "Texto de la pregunta": COLUMN_ALIASES["texto_pregunta"],
        "Tipo": COLUMN_ALIASES["tipo_pregunta"],
        "Rol": COLUMN_ALIASES["clasificacion_analitica"],
        "Sección": COLUMN_ALIASES["seccion_cuestionario"],
    }
    canonical_columns = {
        "Variable": "variable",
        "Label": "label",
        "Pregunta": "pregunta_id",
        "Texto de la pregunta": "texto_pregunta",
        "Tipo": "tipo_pregunta",
        "Rol": "clasificacion_analitica",
        "Sección": "seccion_cuestionario",
    }
    for field, aliases in log_fields.items():
        detected = _find_exact_column(source_columns, aliases)
        canonical = canonical_columns[field]
        filled = (
            int(review[canonical].astype(str).str.strip().ne("").sum())
            if canonical in review
            else 0
        )
        field_rows.append(
            {
                "campo": field,
                "columna_detectada_en_hoja_base": detected or "",
                "fallback_aplicado": "Sí" if not detected and filled else "No",
                "filas_con_valor": filled,
                "aliases_buscados": ", ".join(aliases),
            }
        )
    metadata = _normalized_metadata(review)
    rm_count = int(metadata.str.contains("rm_dicotomica_label").sum())
    grid_count = int(metadata.str.contains("grid_rm_loop").sum())
    missing = [
        row["campo"]
        for row in field_rows
        if row["filas_con_valor"] == 0
    ]
    summary = {
        "hoja_usada": source_name or "",
        "fallback_hoja": _source_fallback_note(sheets, source_name),
        "columnas_detectadas": ", ".join(map(str, source_columns)),
        "columnas_faltantes": ", ".join(missing),
        "rm_dicotomica_label_detectadas": rm_count,
        "grid_rm_loop_detectadas": grid_count,
        "filas_datamap": int(len(review)) if review is not None else 0,
    }
    LOGGER.info("Datamap import log: %s", summary)
    return {
        "summary": summary,
        "fields": pd.DataFrame(field_rows),
    }


def _source_fallback_note(
    sheets: dict[str, pd.DataFrame],
    selected_name: str | None,
) -> str:
    if selected_name == "10_Datamap_Corregido":
        return ""
    preferred = sheets.get("10_Datamap_Corregido")
    if preferred is None or preferred.empty:
        return "10_Datamap_Corregido no existe o está vacía."
    preferred = _usable_reference(preferred)
    if not _find_exact_column(preferred.columns, COLUMN_ALIASES["variable"]):
        return (
            "10_Datamap_Corregido existe, pero no trae "
            "Variable_SPSS/Variable; se aplicó fallback."
        )
    return "Se aplicó fallback a la hoja disponible más completa."


def _dashboard_default(row: pd.Series) -> bool:
    raw_value = row.get("usar_en_dashboard", "")
    classification = row.get("clasificacion_analitica", "")
    excluded = {"No usar en dashboard", "Variable técnica", "Control de calidad"}
    if classification in excluded:
        return False
    raw_text = normalize_text(raw_value)
    if raw_text:
        explicit_negative = (
            raw_text.startswith("no")
            or "no_usar" in raw_text
            or "excluir" in raw_text
            or "salvo_auditoria" in raw_text
        )
        if explicit_negative:
            return False
        positive_hint = any(
            token in raw_text
            for token in [
                "lista_para_analisis",
                "analisis",
                "util",
                "segmentacion",
                "recodificar",
                "usar",
                "metrica",
                "dashboard",
            ]
        )
        if truthy(raw_value) or positive_hint:
            return True
        return True
    return True


def normalize_classification(value: object) -> str:
    text = normalize_text(value)
    mapping = {
        "pregunta_analizable": "Pregunta analizable",
        "analizable": "Pregunta analizable",
        "banner": "Banner",
        "filtro": "Filtro",
        "ponderador": "Ponderador",
        "peso": "Ponderador",
        "variable_tecnica": "Variable técnica",
        "tecnica": "Variable técnica",
        "abierta": "Abierta",
        "abierta_codificada": "Pregunta analizable",
        "texto_abierto": "Abierta",
        "derivada": "Derivada",
        "derivada_cuota": "Derivada",
        "cuota": "Cuota",
        "control_calidad": "Control de calidad",
        "control_de_calidad": "Control de calidad",
        "no_usar": "No usar en dashboard",
        "no_usar_en_dashboard": "No usar en dashboard",
        "requiere_validacion": "Requiere validación",
    }
    if text in mapping:
        return mapping[text]
    for option in CLASSIFICATION_OPTIONS:
        if normalize_text(option) == text:
            return option
    return "Requiere validación" if text else "Pregunta analizable"


def normalize_calculation(value: object) -> str:
    text = normalize_text(value)
    mapping = {
        "frecuencia": "Frecuencia",
        "porcentaje": "Porcentaje",
        "media": "Media",
        "promedio": "Media",
        "top2box": "Top2Box",
        "top_2_box": "Top2Box",
        "bottom2box": "Bottom2Box",
        "bottom_2_box": "Bottom2Box",
        "nps": "NPS",
        "rm_respondentes": "RM % Respondentes",
        "rm_porcentaje_respondentes": "RM % Respondentes",
        "rm_menciones": "RM % Menciones",
        "rm_porcentaje_menciones": "RM % Menciones",
        "texto_abierto": "Texto abierto",
        "abierta": "Texto abierto",
        "no_aplica": "No aplica",
    }
    if text in mapping:
        return mapping[text]
    if "rm_dicotomica_label" in text or "grid_rm_loop" in text:
        return "RM % Respondentes"
    for option in CALCULATION_OPTIONS:
        if normalize_text(option) == text:
            return option
    return "Frecuencia" if not text else "No aplica"


def _enrich_review_source(
    source: pd.DataFrame,
    reference: pd.DataFrame | None,
) -> pd.DataFrame:
    reference = _usable_reference(reference)
    if reference is None or reference.empty or source.empty:
        return source
    variable_col = _find_exact_column(
        source.columns, COLUMN_ALIASES["variable"]
    )
    if not variable_col:
        return source
    reference_variable_col = _find_exact_column(
        reference.columns, COLUMN_ALIASES["variable"]
    )
    associated_col = _find_exact_column(
        reference.columns,
        [
            "variables_spss_asociadas",
            "variables_spss_principales",
            "variables_mapeadas",
            "variables_asociadas",
            "variables_0_1",
            "variables_opciones",
            "variables",
        ],
    )
    source_question_col = _find_exact_column(
        source.columns,
        ["numero_pregunta", "pregunta_id", "pregunta"],
    )
    reference_question_col = _find_exact_column(
        reference.columns,
        ["numero_pregunta", "pregunta_id", "pregunta"],
    )
    if (
        not reference_variable_col
        and not associated_col
        and not (source_question_col and reference_question_col)
    ):
        return source

    known_variables = (
        source[variable_col].dropna().astype(str).str.strip().tolist()
    )
    lookup = {
        variable.casefold(): variable for variable in known_variables
    }
    fields = {
        "label": [
            "label_spss",
            "label",
            "label_variable",
            "texto_opcion_rm",
            "label_opcion_rm",
            "opcion_extraida_label",
            "display_item_reporteador",
            "variable_label",
            "etiqueta",
            "descripcion",
        ],
        "pregunta_id": [
            "numero_pregunta",
            "pregunta_padre",
            "pregunta_id",
            "pregunta",
        ],
        "texto_pregunta": [
            "texto_pregunta",
            "texto_pregunta_padre",
            "pregunta_texto",
            "label_spss",
        ],
        "tipo_pregunta": [
            "tipo_final",
            "tipo_pregunta_cuestionario",
            "tipo_detectado",
            "tipo_declarado",
            "tipo_estructura_grid",
            "tipo_estructura_corregido",
            "tipo_pregunta",
        ],
        "seccion": [
            "seccion_cuestionario",
            "sección",
            "seccion",
        ],
        "seccion_cuestionario": [
            "seccion_cuestionario",
            "sección_cuestionario",
            "sección",
            "seccion",
        ],
        "bloque_cuestionario": [
            "bloque_cuestionario",
            "bloque",
        ],
        "numero_pregunta": [
            "numero_pregunta",
            "pregunta_id",
        ],
        "orden_cuestionario": [
            "orden_cuestionario",
            "orden_reporte",
            "orden",
        ],
        "grupo_menu_reporter": [
            "grupo_menu_reporter",
            "grupo_menu_reporteador",
        ],
        "grupo_menu_reporteador": [
            "grupo_menu_reporteador",
            "grupo_menu_reporter",
        ],
        "mostrar_en_menu_reporter": [
            "mostrar_en_menu_reporter",
            "mostrar_en_menu_reporteador",
        ],
        "mostrar_en_menu_reporteador": [
            "mostrar_en_menu_reporteador",
            "mostrar_en_menu_reporter",
        ],
        "prioridad_reporteador": [
            "prioridad_reporteador",
            "prioridad_reporter",
        ],
        "es_banner_recomendado": [
            "es_banner_recomendado",
        ],
        "es_filtro_recomendado": [
            "es_filtro_recomendado",
        ],
        "nivel_relevancia_comercial": [
            "nivel_relevancia_comercial",
        ],
        "justificacion_banner_filtro": [
            "justificacion_banner_filtro",
            "justificación_banner_filtro",
        ],
        "uso_comercial_sugerido": [
            "uso_comercial_sugerido",
        ],
        "distribucion_base": [
            "distribucion_base",
            "base_categorias_obs",
            "base_por_categoria",
        ],
        "riesgo_uso_analitico": [
            "riesgo_uso_analitico",
        ],
        "requiere_factor": ["requiere_factor"],
        "tipo_factor_recomendado": [
            "tipo_factor_recomendado",
        ],
        "variables_para_factor": [
            "variables_para_factor",
        ],
        "regla_factor_sugerida": [
            "regla_factor_sugerida",
        ],
        "justificacion_factor": [
            "justificacion_factor",
        ],
        "prioridad_factor": ["prioridad_factor"],
        "base_valida": [
            "base_valida_documentada",
            "base_valida",
        ],
        "regla_transformacion": [
            "regla_factor_sugerida",
            "correccion_qa",
        ],
        "tipo_estructura_grid": [
            "tipo_estructura_grid",
            "tipo_estructura_corregido",
            "tipo_final",
        ],
        "entidad_loop": ["entidad_loop"],
        "opcion_rm": [
            "opcion_rm",
            "opcion_extraida_label",
            "texto_fila_opcion",
            "texto_fila/opcion",
        ],
        "label_opcion_rm": [
            "label_opcion_rm",
            "texto_opcion_rm",
            "opcion_extraida_label",
            "display_item_reporteador",
        ],
        "texto_opcion_rm": [
            "texto_opcion_rm",
            "texto_fila_opcion",
            "texto_fila/opcion",
            "opcion_extraida_label",
        ],
        "display_item_reporteador": [
            "display_item_reporteador",
        ],
        "codigo_opcion_rm": [
            "codigo_opcion_rm",
            "codigo_opcion",
        ],
    }
    source_columns = {
        key: _find_exact_column(source.columns, aliases)
        for key, aliases in fields.items()
    }
    corrected_columns = {
        key: _find_exact_column(reference.columns, aliases)
        for key, aliases in fields.items()
    }
    mappings: dict[str, dict[str, object]] = {}
    question_mappings: dict[str, dict[str, object]] = {}
    for _, row in reference.iterrows():
        if reference_variable_col:
            variable = lookup.get(_key(row.get(reference_variable_col)))
            if variable:
                _merge_mapping_row(
                    mappings.setdefault(variable, {}),
                    row,
                    corrected_columns,
                )
        if associated_col:
            associated = str(row.get(associated_col, "") or "")
            tokens = {
                token.casefold()
                for token in re.findall(
                    r"[A-Za-z][A-Za-z0-9_]*", associated
                )
            }
            for token in tokens:
                variable = lookup.get(token)
                if not variable:
                    continue
                _merge_mapping_row(
                    mappings.setdefault(variable, {}),
                    row,
                    corrected_columns,
                )
        if reference_question_col:
            question = _key(row.get(reference_question_col))
            if question:
                _merge_mapping_row(
                    question_mappings.setdefault(question, {}),
                    row,
                    corrected_columns,
                )

    result = source.copy()
    variable_names = result[variable_col].fillna("").astype(str)
    question_names = (
        result[source_question_col].fillna("").astype(str)
        if source_question_col
        else pd.Series([""] * len(result), index=result.index)
    )
    for key in fields:
        mapped = variable_names.map(
            lambda variable: mappings.get(variable, {}).get(
                key, ""
            )
        )
        if question_mappings:
            by_question = question_names.map(
                lambda question: question_mappings.get(
                    _key(question), {}
                ).get(key, "")
            )
            mapped_empty = _empty_series(mapped)
            mapped.loc[mapped_empty] = by_question.loc[mapped_empty]
        source_column = source_columns.get(key)
        if source_column:
            existing = result[source_column]
            empty = _empty_series(existing)
            replace_specific = _specific_type_replacement(
                key, existing, mapped
            )
            fillable = (
                (empty | replace_specific)
                & mapped.notna()
                & ~mapped.astype(str).str.strip().isin(
                    ["", "nan", "None"]
                )
            )
            if fillable.any():
                result[source_column] = result[
                    source_column
                ].astype("object")
                result.loc[fillable, source_column] = mapped.loc[
                    fillable
                ]
        else:
            result[key] = mapped
    return result


def _usable_reference(
    reference: pd.DataFrame | None,
) -> pd.DataFrame | None:
    if reference is None or reference.empty:
        return reference
    if _has_known_columns(reference.columns):
        return reference
    best_row: tuple[int, int] | None = None
    for row_index in range(min(len(reference), 12)):
        row = reference.iloc[row_index]
        values = [
            "" if pd.isna(value) else str(value).strip()
            for value in row.tolist()
        ]
        normalized = {normalize_text(value) for value in values if value}
        hits = normalized.intersection(_HEADER_HINTS())
        if len(hits) < 2:
            continue
        score = len(hits)
        if hits.intersection({"variable", "variable_spss", "variable_item"}):
            score += 10
        if best_row is None or score > best_row[0]:
            best_row = (score, row_index)
    if best_row is not None:
        row_index = best_row[1]
        row = reference.iloc[row_index]
        values = [
            "" if pd.isna(value) else str(value).strip()
            for value in row.tolist()
        ]
        promoted = reference.iloc[row_index + 1 :].copy()
        promoted.columns = [
            value if value else f"unnamed_{index}"
            for index, value in enumerate(values)
        ]
        promoted = promoted.dropna(how="all").reset_index(drop=True)
        return promoted
    return reference


def _has_known_columns(columns) -> bool:
    normalized = {normalize_text(column) for column in columns}
    return bool(normalized.intersection(_HEADER_HINTS()))


def _HEADER_HINTS() -> set[str]:
    return {
        "variable",
        "variable_spss",
        "variable_item",
        "numero_pregunta",
        "pregunta_padre",
        "texto_pregunta",
        "label_spss",
        "tipo_final",
        "tipo_estructura_grid",
        "tipo_estructura_corregido",
        "rol_analitico",
        "entidad_loop",
        "opcion_extraida_label",
    }


def _merge_mapping_row(
    item: dict[str, object],
    row: pd.Series,
    columns: dict[str, str | None],
) -> None:
    for key, column in columns.items():
        if column and key not in item:
            value = row.get(column)
            if pd.notna(value) and str(value).strip():
                item[key] = value


def _key(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip().casefold()


def _empty_series(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().isin(
        ["", "nan", "None"]
    )


def _specific_type_replacement(
    key: str,
    existing: pd.Series,
    incoming: pd.Series,
) -> pd.Series:
    if key != "tipo_pregunta":
        return pd.Series(False, index=existing.index)
    incoming_norm = incoming.map(normalize_text)
    existing_norm = existing.map(normalize_text)
    specific = incoming_norm.isin(
        {"rm_dicotomica_label", "grid_rm_loop"}
    )
    return specific & existing_norm.ne(incoming_norm)


def _normalized_metadata(review: pd.DataFrame) -> pd.Series:
    if review is None or review.empty:
        return pd.Series(dtype=str)
    columns = [
        column
        for column in (
            "tipo_pregunta",
            "tipo_calculo",
            "tipo_estructura_grid",
        )
        if column in review
    ]
    if not columns:
        return pd.Series([""] * len(review), index=review.index)
    return review[columns].fillna("").astype(str).agg(" ".join, axis=1).map(
        normalize_text
    )


def _normalize_question_roles(
    base: pd.DataFrame, roles: pd.Series
) -> pd.DataFrame:
    result = base.copy()
    coded_open = roles.eq("abierta_codificada")
    pure_open = roles.eq("abierta")
    result.loc[coded_open, "tipo_pregunta"] = "RM codificada"
    result.loc[pure_open, "tipo_pregunta"] = "Abierta"

    calculation_missing = result["tipo_calculo"].isin(
        ["Frecuencia", "No aplica"]
    )
    question_type = result["tipo_pregunta"].map(normalize_text)
    result.loc[
        calculation_missing & question_type.str.contains("nps"),
        "tipo_calculo",
    ] = "NPS"
    result.loc[
        calculation_missing
        & question_type.str.contains("escala|grid"),
        "tipo_calculo",
    ] = "Media"
    result.loc[
        calculation_missing
        & question_type.str.contains("rm|multiple"),
        "tipo_calculo",
    ] = "RM % Respondentes"
    result.loc[pure_open, "tipo_calculo"] = "Texto abierto"
    return result


def _find_exact_column(
    columns, candidates: list[str]
) -> str | None:
    normalized = {normalize_text(column): column for column in columns}
    for candidate in candidates:
        found = normalized.get(normalize_text(candidate))
        if found is not None:
            return found
    return None
