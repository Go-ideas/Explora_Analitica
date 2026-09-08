TABLE_SCHEMAS = {
    "respondentes": """
        CREATE TABLE IF NOT EXISTS respondentes (
            id_respondente TEXT PRIMARY KEY,
            id_original TEXT,
            row_index INTEGER
        )
    """,
    "preguntas": """
        CREATE TABLE IF NOT EXISTS preguntas (
            pregunta_id TEXT PRIMARY KEY,
            seccion TEXT,
            numero_pregunta TEXT,
            texto_pregunta TEXT,
            tipo_pregunta TEXT,
            tipo_calculo TEXT,
            base_valida TEXT,
            regla_transformacion TEXT,
            usar_en_dashboard INTEGER,
            orden_cuestionario REAL,
            seccion_cuestionario TEXT,
            bloque_cuestionario TEXT,
            grupo_menu_reporteador TEXT,
            mostrar_en_menu_reporteador TEXT,
            prioridad_reporteador TEXT
        )
    """,
    "variables": """
        CREATE TABLE IF NOT EXISTS variables (
            variable TEXT PRIMARY KEY,
            label TEXT,
            tipo_spss TEXT,
            pregunta_id TEXT,
            tipo_pregunta TEXT,
            clasificacion_analitica TEXT,
            usar_en_dashboard INTEGER,
            es_banner INTEGER,
            es_filtro INTEGER,
            es_ponderador INTEGER,
            tipo_calculo TEXT,
            n_validos INTEGER,
            n_missing INTEGER,
            valores_unicos INTEGER,
            min REAL,
            max REAL,
            es_banner_recomendado INTEGER,
            es_filtro_recomendado INTEGER,
            nivel_relevancia_comercial TEXT,
            justificacion_banner_filtro TEXT,
            uso_comercial_sugerido TEXT,
            distribucion_base TEXT,
            riesgo_uso_analitico TEXT,
            requiere_factor INTEGER,
            tipo_factor_recomendado TEXT,
            variables_para_factor TEXT,
            regla_factor_sugerida TEXT,
            justificacion_factor TEXT,
            prioridad_factor TEXT
        )
    """,
    "configuracion_dashboard": """
        CREATE TABLE IF NOT EXISTS configuracion_dashboard (
            tipo_configuracion TEXT,
            variable TEXT,
            pregunta_id TEXT,
            label TEXT,
            es_recomendado INTEGER,
            es_banner_recomendado INTEGER,
            es_filtro_recomendado INTEGER,
            prioridad TEXT,
            nivel_relevancia_comercial TEXT,
            justificacion TEXT,
            justificacion_banner_filtro TEXT,
            uso_comercial_sugerido TEXT,
            distribucion_base TEXT,
            riesgo_uso_analitico TEXT,
            fuente_hoja TEXT
        )
    """,
    "recomendaciones_reporteador": """
        CREATE TABLE IF NOT EXISTS recomendaciones_reporteador (
            tipo_recomendacion TEXT,
            variable TEXT,
            variable_label TEXT,
            pregunta_id TEXT,
            numero_pregunta TEXT,
            texto_pregunta TEXT,
            seccion_cuestionario TEXT,
            rol_recomendado TEXT,
            es_banner_recomendado INTEGER,
            es_filtro_recomendado INTEGER,
            nivel_relevancia_comercial TEXT,
            justificacion TEXT,
            uso_comercial_sugerido TEXT,
            distribucion_base TEXT,
            riesgo_uso_analitico TEXT,
            requiere_factor INTEGER,
            tipo_factor_recomendado TEXT,
            variables_para_factor TEXT,
            regla_factor_sugerida TEXT,
            justificacion_factor TEXT,
            prioridad_factor TEXT,
            fuente_hoja TEXT
        )
    """,
}


EXPECTED_TABLES = [
    "respondentes",
    "preguntas",
    "variables",
    "opciones",
    "respuestas_long",
    "multirrespuesta_long",
    "escalas_long",
    "abiertas",
    "riesgos",
    "configuracion_dashboard",
    "recomendaciones_reporteador",
    "factores_configurados",
]
