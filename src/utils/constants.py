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
    "05_Check_RM",
    "06_Check_Filtros_Saltos",
    "07_Check_Abiertas",
    "08_Clasificacion_Analitica",
    "09_Riesgos_Priorizados",
    "10_Datamap_Corregido",
]

KEY_DATAMAP_SHEETS = [
    "00_Resumen_QA",
    "08_Clasificacion_Analitica",
    "09_Riesgos_Priorizados",
]

REVIEW_COLUMNS = [
    "variable",
    "label",
    "pregunta_id",
    "texto_pregunta",
    "tipo_pregunta",
    "clasificacion_analitica",
    "usar_en_dashboard",
    "es_banner",
    "es_filtro",
    "es_ponderador",
    "tipo_calculo",
    "regla_transformacion",
    "observacion_usuario",
]

CLASSIFICATION_OPTIONS = [
    "Pregunta analizable",
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
