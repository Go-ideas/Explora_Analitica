from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"
EXPORTS_DIR = DATA_DIR / "exports"

DATAMAP_FINAL_FILENAME = "Datamap_Final.xlsx"
SQLITE_FILENAME = "BD_Analitica_Explora.db"
REVISION_EXCEL_FILENAME = "BD_Analitica_Revision.xlsx"

EXPECTED_DATAMAP_SHEETS = [
    "00_Resumen_QA",
    "01_Check_Cobertura",
    "02_Check_Tipos",
    "03_Check_ValueLabels",
    "04_Check_Escalas",
    "04B_Check_Grids",
    "05_Check_RM",
    "06_Check_Filtros_Saltos",
    "07_Check_Abiertas",
    "08_Clasificacion_Analitica",
    "09_Riesgos_Priorizados",
    "10_Datamap_Corregido",
    "11_Banners_Filtros_Recomendados",
    "12_Factores_Scores_Recomendados",
    "13_Orden_Menu_Reporteador",
]

KEY_DATAMAP_SHEETS = [
    "00_Resumen_QA",
    "08_Clasificacion_Analitica",
    "09_Riesgos_Priorizados",
]

REVIEW_COLUMNS = [
    "variable",
    "label",
    "numero_pregunta",
    "pregunta_id",
    "texto_pregunta",
    "tipo_pregunta",
    "clasificacion_analitica",
    "tipo_calculo",
    "seccion_cuestionario",
    "bloque_cuestionario",
    "orden_cuestionario",
    "grupo_menu_reporteador",
    "mostrar_en_menu_reporteador",
    "prioridad_reporteador",
    "usar_en_dashboard",
    "es_banner",
    "es_filtro",
    "es_ponderador",
    "es_banner_recomendado",
    "es_filtro_recomendado",
    "nivel_relevancia_comercial",
    "justificacion_banner_filtro",
    "uso_comercial_sugerido",
    "riesgo_uso_analitico",
    "requiere_factor",
    "tipo_factor_recomendado",
    "grid_id",
    "pregunta_padre",
    "es_grid",
    "es_item_grid",
    "es_grid_rm_loop",
    "tipo_estructura_grid",
    "orden_fila_grid",
    "texto_fila_grid",
    "entidad_loop",
    "codigo_opcion_rm",
    "label_opcion_rm",
    "codigos_columnas_grid",
    "labels_columnas_grid",
    "tipo_escala_columnas",
    "rango_esperado",
    "rango_observado",
    "value_labels_compartidos",
    "value_label_patron",
    "patron_label_constante",
    "formato_rm",
    "metrica_grid_recomendada",
    "regla_tabular_recomendada",
    "riesgo_grid",
    "match_confianza",
    "regla_transformacion",
    "observacion_usuario",
]

CLASSIFICATION_OPTIONS = [
    "Pregunta analizable",
    "Pregunta padre grid",
    "Banner",
    "Filtro",
    "Ponderador",
    "Variable técnica",
    "Abierta",
    "Derivada",
    "Cuota",
    "Control de calidad",
    "No usar en dashboard",
    "Requiere validación",
]

CALCULATION_OPTIONS = [
    "Frecuencia",
    "Porcentaje",
    "Media",
    "Top2Box",
    "Bottom2Box",
    "NPS",
    "RM % Respondentes",
    "RM % Menciones",
    "Texto abierto",
    "No aplica",
    "Multirrespuesta agrupada",
    "% respondentes",
    "Menciones",
    "% menciones",
    "Ranking opciones por entidad",
    "Ranking entidades por opción",
    "Multiplicidad promedio",
    "Distribución grid",
    "Media grid",
]

RESPONDENT_CLASSIFICATIONS = {
    "Banner",
    "Filtro",
    "Ponderador",
    "Derivada",
    "Cuota",
    "Control de calidad",
}

NO_RESPONSE_TEXTS = {
    "",
    "nan",
    "none",
    "null",
    "na",
    "n/a",
    "no aplica",
    "no se",
    "no sé",
    "ninguno",
    "ninguna",
}

EXCLUSIVE_OPTION_HINTS = [
    "ninguna",
    "ninguno",
    "no aplica",
    "no recuerdo",
    "no recuerda",
    "no hubo mensajes",
    "no sabe",
    "no contesta",
]

ID_CANDIDATES = [
    "id",
    "folio",
    "respondent_id",
    "idgd",
    "record",
    "entrevista",
    "serial",
]
