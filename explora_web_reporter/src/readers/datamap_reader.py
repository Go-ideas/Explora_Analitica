from __future__ import annotations

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


COLUMN_ALIASES = {
    "variable": [
        "variable",
        "Variable",
        "Variable_SPSS",
        "Variable_Item",
        "variable_spss",
        "nombre_variable",
        "Nombre_Variable",
        "var",
        "campo",
    ],
    "label": [
        "label",
        "Label",
        "Variable_Label",
        "Etiqueta_SPSS",
        "Texto_Fila_Grid",
        "variable_label",
        "etiqueta",
        "etiqueta_variable",
        "descripcion",
    ],
    "numero_pregunta": [
        "numero_pregunta",
        "Numero_Pregunta",
        "Número_Pregunta",
        "Pregunta_ID",
        "Pregunta_Padre",
        "Pregunta_Padre_Detectada",
        "Pregunta_Padre_Grid",
    ],
    "pregunta_id": [
        "pregunta_id",
        "Pregunta_ID",
        "Numero_Pregunta",
        "Pregunta_Padre",
        "Pregunta_Padre_Detectada",
        "Grid_ID",
        "pregunta",
        "pregunta_asociada",
        "numero_pregunta",
        "id_pregunta",
        "question_id",
        "codigo_pregunta",
    ],
    "texto_pregunta": [
        "texto_pregunta",
        "Texto_Pregunta",
        "Texto_Pregunta_Padre",
        "Pregunta_Texto",
        "Texto_Fila_Grid",
        "Etiqueta_Menu",
        "pregunta_texto",
        "texto",
        "question_text",
        "label_pregunta",
    ],
    "tipo_pregunta": [
        "tipo_pregunta",
        "Tipo_Pregunta",
        "Tipo_Detectado",
        "Tipo_Final_QA",
        "Tipo_Final",
        "Tipo_Pregunta_Final",
        "Tipo_Estructura_Grid",
        "Tipo_Declarado_QR",
        "Tipo_Detectado_Base",
        "tipo_pregunta_cuestionario",
        "tipo",
        "tipo_variable",
        "question_type",
    ],
    "clasificacion_analitica": [
        "clasificacion_analitica",
        "Clasificacion_Analitica",
        "Rol_Analitico",
        "Rol_Principal",
        "Rol_Analitico_Principal",
        "Clasificacion",
        "clasificacion",
        "uso_analitico",
        "rol_analitico",
        "rol_analitico_principal",
    ],
    "usar_en_dashboard": [
        "usar_en_dashboard",
        "Usar_En_Dashboard",
        "Usar_En_Reporteador",
        "Mostrar_En_Menu_Reporteador",
        "Mostrar_En_Dashboard",
        "usar_dashboard",
        "dashboard",
        "incluir_dashboard",
    ],
    "es_banner": [
        "es_banner",
        "Es_Banner",
        "Usar_Como_Banner",
        "banner",
    ],
    "es_filtro": [
        "es_filtro",
        "Es_Filtro",
        "Usar_Como_Filtro",
        "filtro",
    ],
    "es_ponderador": [
        "es_ponderador",
        "Es_Ponderador",
        "Ponderador",
        "Es_Weight",
        "peso",
        "weight",
    ],
    "tipo_calculo": [
        "tipo_calculo",
        "Tipo_Calculo",
        "Metrica_Recomendada",
        "Metrica_Grid_Recomendada",
        "Metrica_Sugerida",
        "Calculo_Recomendado",
        "calculo",
        "metrica",
        "indicador",
    ],
    "regla_transformacion": ["regla_transformacion", "regla", "transformacion"],
    "observacion_usuario": ["observacion_usuario", "observacion", "comentario", "notas"],
    "seccion": [
        "seccion",
        "seccion_cuestionario",
        "sección",
    ],
    "seccion_cuestionario": [
        "seccion_cuestionario",
        "sección_cuestionario",
        "seccion",
        "sección",
    ],
    "bloque_cuestionario": [
        "bloque_cuestionario",
        "bloque",
    ],
    "orden_cuestionario": [
        "orden_cuestionario",
        "Orden_Cuestionario",
        "Orden_Menu",
        "Orden_Reporteador",
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
        "Prioridad_Reporteador",
        "Prioridad",
        "prioridad_reporter",
    ],
    "es_banner_recomendado": [
        "es_banner_recomendado",
        "Es_Banner_Recomendado",
        "Banner_Recomendado",
        "banner_recomendado",
    ],
    "es_filtro_recomendado": [
        "es_filtro_recomendado",
        "Es_Filtro_Recomendado",
        "Filtro_Recomendado",
        "filtro_recomendado",
    ],
    "nivel_relevancia_comercial": [
        "nivel_relevancia_comercial",
        "Nivel_Relevancia_Comercial",
        "Nivel_Relevancia",
        "Relevancia",
        "relevancia_comercial",
    ],
    "justificacion_banner_filtro": [
        "justificacion_banner_filtro",
        "Justificacion_Banner_Filtro",
        "Justificación_Banner_Filtro",
        "Justificacion",
        "justificación_banner_filtro",
        "justificacion",
    ],
    "uso_comercial_sugerido": [
        "uso_comercial_sugerido",
        "Uso_Comercial_Sugerido",
        "Uso_Comercial",
        "Uso_Sugerido",
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
        "Riesgo_Uso_Analitico",
        "Riesgo_Analitico",
        "Riesgo",
        "riesgo_analitico",
    ],
    "requiere_factor": ["requiere_factor", "Requiere_Factor"],
    "tipo_factor_recomendado": [
        "tipo_factor_recomendado",
        "Tipo_Factor_Recomendado",
        "Factor_Recomendado",
        "Tipo_Score",
        "Tipo_Factor",
    ],
    "variables_para_factor": [
        "variables_para_factor",
        "Variables_Para_Factor",
        "Variables_Fuente",
        "Variables_Items",
        "Variables",
    ],
    "regla_factor_sugerida": [
        "regla_factor_sugerida",
        "Regla_Factor_Sugerida",
        "Regla",
        "Formula_Sugerida",
        "Criterio_Calculo",
    ],
    "justificacion_factor": [
        "justificacion_factor",
        "Justificacion_Factor",
        "Justificacion",
        "Justificacion_Metodologica",
        "justificación_factor",
    ],
    "prioridad_factor": [
        "prioridad_factor",
        "Prioridad_Factor",
        "Prioridad_Reporteador",
        "Prioridad",
    ],
    "grid_id": ["grid_id", "Grid_ID", "Pregunta_Padre", "Numero_Pregunta"],
    "tipo_estructura_grid": [
        "tipo_estructura_grid",
        "Tipo_Estructura_Grid",
        "Tipo_Grid",
        "Tipo_Loop",
        "Tipo_Escala_Columnas",
        "Tipo_Pregunta",
    ],
    "pregunta_padre": [
        "pregunta_padre",
        "Pregunta_Padre",
        "Pregunta_Padre_Detectada",
        "Pregunta_Padre_Grid",
    ],
    "es_grid": ["es_grid", "Es_Grid"],
    "es_item_grid": ["es_item_grid", "Es_Item_Grid"],
    "es_grid_rm_loop": [
        "es_grid_rm_loop",
        "Es_GRID_RM_LOOP",
        "Es_Grid_RM_Loop",
        "GRID_RM_LOOP",
    ],
    "orden_fila_grid": [
        "orden_fila_grid",
        "Orden_Fila_Grid",
        "Orden_Item",
        "Orden_Fila",
        "Orden",
    ],
    "texto_fila_grid": [
        "texto_fila_grid",
        "Texto_Fila_Grid",
        "Texto_Item",
        "Label",
        "Variable_Label",
    ],
    "entidad_loop": [
        "entidad_loop",
        "Entidad_Loop",
        "Entidad",
        "Marca",
        "Canal",
        "Producto",
        "Touchpoint",
    ],
    "codigo_opcion_rm": [
        "codigo_opcion_rm",
        "Codigo_Opcion_RM",
        "Codigo_Opcion",
        "Codigo",
        "Codigo_Respuesta",
    ],
    "label_opcion_rm": [
        "label_opcion_rm",
        "Label_Opcion_RM",
        "Label_Opcion",
        "Opcion_Respuesta",
        "Texto_Opcion",
    ],
    "codigos_columnas_grid": [
        "codigos_columnas_grid",
        "Codigos_Columnas_Grid",
        "Codigos_Escala",
    ],
    "labels_columnas_grid": [
        "labels_columnas_grid",
        "Labels_Columnas_Grid",
        "Labels_Escala",
    ],
    "tipo_escala_columnas": [
        "tipo_escala_columnas",
        "Tipo_Escala_Columnas",
        "Tipo_Escala",
    ],
    "rango_esperado": ["rango_esperado", "Rango_Esperado"],
    "rango_observado": ["rango_observado", "Rango_Observado"],
    "value_labels_compartidos": [
        "value_labels_compartidos",
        "ValueLabels_Compartidos",
        "Value_Labels_Compartidos",
    ],
    "value_label_patron": [
        "value_label_patron",
        "ValueLabel_Patron",
        "Patron_ValueLabels",
    ],
    "patron_label_constante": [
        "patron_label_constante",
        "Patron_Label_Constante",
        "Texto_Constante_Label",
    ],
    "formato_rm": [
        "formato_rm",
        "Formato_RM",
        "Tipo_Formato_RM",
    ],
    "metrica_grid_recomendada": [
        "metrica_grid_recomendada",
        "Metrica_Grid_Recomendada",
        "Metrica_Recomendada",
    ],
    "regla_tabular_recomendada": [
        "regla_tabular_recomendada",
        "Regla_Tabular_Recomendada",
        "Regla_Tabular",
        "Calculo_Recomendado",
    ],
    "riesgo_grid": ["riesgo_grid", "Riesgo_Grid", "Riesgo"],
    "match_confianza": [
        "match_confianza",
        "Mapping_Confidence",
        "Nivel_Confianza",
        "Match_Grid",
    ],
}


REVIEW_SOURCE_PRIORITY = [
    "10_Datamap_Corregido",
    "08_Clasificacion_Analitica",
    "01_Check_Cobertura",
    "Datamap_Preguntas",
    "Variables_SPSS",
]

VARIABLE_LIST_ALIASES = [
    "Variables_Finales",
    "Variables_SPSS_Asociadas",
    "Variables_SPSS_Principales",
    "Variables_Match",
    "Variables_Mapeadas",
    "Variables",
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
    prepared: dict[str, pd.DataFrame] = {}
    for name, frame in sheets.items():
        candidate = _prepare_review_source(frame)
        if candidate is not None and not candidate.empty:
            prepared[name] = candidate

    selected_name = next(
        (
            name
            for name in REVIEW_SOURCE_PRIORITY
            if name in prepared
        ),
        None,
    )
    if selected_name is None and prepared:
        selected_name = next(iter(prepared))
    if selected_name is None:
        raise ValueError(
            "No se encontró una hoja válida con variables SPSS."
        )

    source = prepared[selected_name].copy()
    for name in REVIEW_SOURCE_PRIORITY:
        if name == selected_name or name not in prepared:
            continue
        source = _merge_source_by_variable(source, prepared[name])
    for name, frame in prepared.items():
        if name in REVIEW_SOURCE_PRIORITY or name == selected_name:
            continue
        source = _merge_source_by_variable(source, frame)

    source = _merge_optional_sheet(
        source,
        sheets,
        [
            "11_Banners_Filtros_Recomendados",
            "Banners_Filtros_Recomendados",
        ],
    )
    source = _merge_optional_sheet(
        source,
        sheets,
        [
            "12_Factores_Scores_Recomendados",
            "Factores_Scores_Recomendados",
        ],
        list_aliases=["Variables_Para_Factor", "Variables_Fuente", "Variables"],
    )
    source = _merge_optional_sheet(
        source,
        sheets,
        ["04B_Check_Grids_Loops", "04B_Check_Grids"],
        variable_aliases=["Variable_Item", "Variable", "Variable_SPSS"],
    )
    return selected_name, source


def _prepare_review_source(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    direct = _find_exact_column(df.columns, COLUMN_ALIASES["variable"])
    if direct:
        return df.copy()
    list_column = _find_exact_column(df.columns, VARIABLE_LIST_ALIASES)
    if not list_column:
        return None
    rows = []
    for _, row in df.iterrows():
        variables = _variable_tokens(row.get(list_column))
        for variable in variables:
            item = row.to_dict()
            item["variable"] = variable
            rows.append(item)
    return pd.DataFrame(rows) if rows else None


def _merge_source_by_variable(
    source: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    source_variable = _find_exact_column(
        source.columns, COLUMN_ALIASES["variable"]
    )
    metadata_variable = _find_exact_column(
        metadata.columns, COLUMN_ALIASES["variable"]
    )
    if not source_variable or not metadata_variable:
        return source
    result = source.copy()
    metadata_work = metadata.copy()
    metadata_work["_merge_variable"] = (
        metadata_work[metadata_variable]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )
    metadata_work = metadata_work.drop_duplicates(
        "_merge_variable", keep="first"
    ).set_index("_merge_variable")
    keys = (
        result[source_variable]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )
    for column in metadata.columns:
        if column == metadata_variable:
            continue
        target = _find_exact_column(result.columns, [column]) or column
        mapped = keys.map(metadata_work[column].to_dict())
        if target not in result:
            result[target] = mapped.fillna("")
            continue
        empty = _empty_mask(result[target])
        fillable = empty & ~_empty_mask(mapped)
        if fillable.any():
            result.loc[fillable, target] = mapped.loc[fillable]
    missing = metadata_work[~metadata_work.index.isin(set(keys))]
    if not missing.empty:
        additions = []
        for _, row in missing.iterrows():
            item = {column: "" for column in result.columns}
            item[source_variable] = row.get(metadata_variable, "")
            for column in metadata.columns:
                target = _find_exact_column(result.columns, [column]) or column
                if target not in item:
                    item[target] = ""
                item[target] = row.get(column, "")
            additions.append(item)
        result = pd.concat(
            [result, pd.DataFrame(additions)],
            ignore_index=True,
            sort=False,
        )
    return result


def _merge_optional_sheet(
    source: pd.DataFrame,
    sheets: dict[str, pd.DataFrame],
    names: list[str],
    variable_aliases: list[str] | None = None,
    list_aliases: list[str] | None = None,
) -> pd.DataFrame:
    for name in names:
        frame = sheets.get(name)
        if frame is None or frame.empty:
            continue
        prepared = _prepare_metadata_sheet(
            frame, variable_aliases, list_aliases
        )
        if prepared is not None and not prepared.empty:
            return _merge_source_by_variable(source, prepared)
    return source


def _prepare_metadata_sheet(
    frame: pd.DataFrame,
    variable_aliases: list[str] | None = None,
    list_aliases: list[str] | None = None,
) -> pd.DataFrame | None:
    aliases = variable_aliases or COLUMN_ALIASES["variable"]
    direct = _find_exact_column(frame.columns, aliases)
    if direct:
        result = frame.copy()
        if direct != "variable":
            result["variable"] = result[direct]
        return result
    list_column = _find_exact_column(
        frame.columns, list_aliases or VARIABLE_LIST_ALIASES
    )
    if not list_column:
        return None
    rows = []
    for _, row in frame.iterrows():
        for variable in _variable_tokens(row.get(list_column)):
            item = row.to_dict()
            item["variable"] = variable
            rows.append(item)
    return pd.DataFrame(rows) if rows else None


def _variable_tokens(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    text = str(value)
    tokens = re.findall(r"[A-Za-z@#$][A-Za-z0-9_@#$]*", text)
    return list(dict.fromkeys(token.strip() for token in tokens if token.strip()))


def _review_defaults() -> dict[str, object]:
    return {
        "variable": "",
        "label": "",
        "numero_pregunta": "",
        "pregunta_id": "",
        "texto_pregunta": "",
        "tipo_pregunta": "Sin clasificar",
        "clasificacion_analitica": "",
        "usar_en_dashboard": False,
        "es_banner": False,
        "es_filtro": False,
        "es_ponderador": False,
        "tipo_calculo": "Frecuencia",
        "es_grid": False,
        "es_item_grid": False,
        "es_grid_rm_loop": False,
    }


def _empty_mask(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype=bool)
    return series.isna() | series.astype(str).str.strip().isin(
        ["", "nan", "None"]
    )


def _has_truthy_selection(series: pd.Series | None) -> bool:
    if series is None:
        return False
    return bool(series.apply(truthy).any())


def _infer_weight_variables(base: pd.DataFrame) -> pd.DataFrame:
    result = base.copy()
    variable = result["variable"].fillna("").astype(str).str.upper()
    classification = result["clasificacion_analitica"].fillna("").map(
        normalize_text
    )
    mask = (
        variable.str.contains("POND|PONDERADOR|WEIGHT|FACTOR_EXPANSION|PESO", regex=True)
        | classification.str.contains("ponderador|peso|weight", regex=True)
        | result["es_ponderador"].apply(truthy)
    )
    if mask.any():
        result.loc[mask, "es_ponderador"] = True
        result.loc[mask, "usar_en_dashboard"] = False
        result.loc[mask, "clasificacion_analitica"] = "Ponderador"
    return result


def _normalize_grid_loop_roles(base: pd.DataFrame) -> pd.DataFrame:
    result = base.copy()
    structure = result.get(
        "tipo_estructura_grid", pd.Series("", index=result.index)
    ).map(normalize_text)
    question_type = result.get(
        "tipo_pregunta", pd.Series("", index=result.index)
    ).map(normalize_text)
    combined = structure.str.cat(question_type, sep=" ")
    for column in ("tipo_escala_columnas", "formato_rm"):
        if column in result:
            combined = combined.str.cat(
                result[column].fillna("").map(normalize_text),
                sep=" ",
            )
    all_grid_text = combined.copy()
    for column in ("metrica_grid_recomendada", "regla_tabular_recomendada"):
        if column in result:
            all_grid_text = all_grid_text.str.cat(
                result[column].fillna("").map(normalize_text),
                sep=" ",
            )
    explicit_grid_context = (
        combined.str.contains("grid|loop", regex=True, na=False)
        | result.get("es_grid", pd.Series(False, index=result.index)).apply(truthy)
        | result.get("es_item_grid", pd.Series(False, index=result.index)).apply(truthy)
    )

    grid_rm = combined.str.contains(
        "grid_rm|loop_rm|grid_rm_loop", regex=True, na=False
    ) | (
        explicit_grid_context
        & all_grid_text.str.contains("rm", na=False)
        & all_grid_text.str.contains("loop|opcion|opción", regex=True, na=False)
    )
    grid_scale = combined.str.contains(
        "grid_escala|grid escala", regex=True, na=False
    )
    loop_numeric = combined.str.contains(
        "loop_numerico|loop_numérico|loop numerico|loop numérico",
        regex=True,
        na=False,
    )
    grid_like = grid_rm | grid_scale | result.get(
        "es_grid", pd.Series(False, index=result.index)
    ).apply(truthy)
    item_like = grid_like | result.get(
        "es_item_grid", pd.Series(False, index=result.index)
    ).apply(truthy)

    result.loc[grid_like, "es_grid"] = True
    result.loc[item_like, "es_item_grid"] = True
    result.loc[grid_rm, "es_grid_rm_loop"] = True
    result.loc[grid_rm, "tipo_pregunta"] = "GRID_RM/LOOP_RM"
    result.loc[grid_rm, "tipo_calculo"] = "Multirrespuesta agrupada"
    result.loc[grid_scale, "tipo_pregunta"] = "GRID_ESCALA"
    result.loc[
        grid_scale & result["tipo_calculo"].isin(["Frecuencia", "No aplica"]),
        "tipo_calculo",
    ] = "Distribución grid"
    result.loc[loop_numeric, "tipo_pregunta"] = "LOOP_NUMERICO"
    result.loc[loop_numeric, "tipo_calculo"] = "Media"

    for column in ("grid_id", "pregunta_padre", "numero_pregunta"):
        result[column] = result[column].fillna("").astype(str).str.strip()
    empty_question = result["pregunta_id"].fillna("").astype(str).str.strip().eq("")
    for column in ("grid_id", "pregunta_padre", "numero_pregunta", "variable"):
        fillable = empty_question & result[column].fillna("").astype(str).str.strip().ne("")
        result.loc[fillable, "pregunta_id"] = result.loc[fillable, column]
        empty_question = result["pregunta_id"].fillna("").astype(str).str.strip().eq("")
    return result


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

    for col, default in _review_defaults().items():
        if col not in base.columns:
            base[col] = default
        else:
            empty = _empty_mask(base[col])
            if empty.any():
                base.loc[empty, col] = default
    for col in REVIEW_COLUMNS:
        if col not in base.columns:
            base[col] = ""

    if (
        not _has_truthy_selection(base.get("es_banner"))
        and "es_banner_recomendado" in base
    ):
        base["es_banner"] = base["es_banner_recomendado"]
    if (
        not _has_truthy_selection(base.get("es_filtro"))
        and "es_filtro_recomendado" in base
    ):
        base["es_filtro"] = base["es_filtro_recomendado"]

    if spss_columns and "variable" in base:
        missing_vars = [col for col in spss_columns if col not in set(base["variable"].dropna().astype(str))]
        if missing_vars:
            additions = pd.DataFrame({"variable": missing_vars})
            base = pd.concat([base, additions], ignore_index=True)

    base = base.copy()
    base["variable"] = base["variable"].fillna("").astype(str).str.strip()
    base["label"] = base["label"].fillna("").astype(str)
    base["numero_pregunta"] = base["numero_pregunta"].fillna("").astype(str)
    base["pregunta_id"] = base["pregunta_id"].fillna("").astype(str)
    base.loc[base["pregunta_id"].eq(""), "pregunta_id"] = base.loc[
        base["pregunta_id"].eq(""), "numero_pregunta"
    ]
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
    base = _normalize_grid_loop_roles(base)
    base = _infer_weight_variables(base)
    for order_column in (
        "orden_cuestionario",
        "orden_fila_grid",
        "orden_reporte",
    ):
        if order_column in base.columns:
            base[order_column] = pd.to_numeric(
                base[order_column], errors="coerce"
            )
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


def _dashboard_default(row: pd.Series) -> bool:
    raw_value = row.get("usar_en_dashboard", "")
    classification = row.get("clasificacion_analitica", "")
    excluded = {
        "No usar en dashboard",
        "Variable técnica",
        "Control de calidad",
        "Ponderador",
    }
    if classification in excluded:
        return False
    raw_text = normalize_text(raw_value)
    if raw_text:
        explicit_negative = (
            raw_text.startswith("no")
            or "no_usar" in raw_text
            or "excluir" in raw_text
            or "salvo_auditoria" in raw_text
            or raw_text in {"0", "false", "falso"}
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
        "pregunta_padre_grid": "Pregunta padre grid",
        "grid": "Pregunta padre grid",
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
        "multirrespuesta_agrupada": "Multirrespuesta agrupada",
        "grid_rm": "Multirrespuesta agrupada",
        "loop_rm": "Multirrespuesta agrupada",
        "distribucion_grid": "Distribución grid",
        "distribución_grid": "Distribución grid",
        "media_grid": "Media grid",
        "menciones": "Menciones",
        "porcentaje_respondentes": "% respondentes",
        "pct_respondentes": "% respondentes",
        "porcentaje_menciones": "% menciones",
        "pct_menciones": "% menciones",
    }
    if text in mapping:
        return mapping[text]
    for option in CALCULATION_OPTIONS:
        if normalize_text(option) == text:
            return option
    return "Frecuencia" if not text else "No aplica"


def _enrich_review_source(
    source: pd.DataFrame,
    corrected: pd.DataFrame | None,
) -> pd.DataFrame:
    if corrected is None or corrected.empty or source.empty:
        return source
    variable_col = _find_exact_column(
        source.columns, COLUMN_ALIASES["variable"]
    )
    associated_col = _find_exact_column(
        corrected.columns,
        [
            "variables_spss_asociadas",
            "variables_spss_principales",
            "variables_mapeadas",
            "variables",
        ],
    )
    if not variable_col or not associated_col:
        return source

    known_variables = (
        source[variable_col].dropna().astype(str).str.strip().tolist()
    )
    lookup = {
        variable.casefold(): variable for variable in known_variables
    }
    fields = {
        "pregunta_id": [
            "numero_pregunta",
            "pregunta_id",
            "pregunta",
        ],
        "texto_pregunta": [
            "texto_pregunta",
            "pregunta_texto",
        ],
        "tipo_pregunta": [
            "tipo_pregunta_cuestionario",
            "tipo_detectado",
            "tipo_declarado",
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
    }
    source_columns = {
        key: _find_exact_column(source.columns, aliases)
        for key, aliases in fields.items()
    }
    corrected_columns = {
        key: _find_exact_column(corrected.columns, aliases)
        for key, aliases in fields.items()
    }
    mappings: dict[str, dict[str, object]] = {}
    for _, row in corrected.iterrows():
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
            item = mappings.setdefault(variable, {})
            for key, column in corrected_columns.items():
                if column and key not in item:
                    value = row.get(column)
                    if pd.notna(value) and str(value).strip():
                        item[key] = value

    result = source.copy()
    variable_names = result[variable_col].fillna("").astype(str)
    for key in fields:
        mapped = variable_names.map(
            lambda variable: mappings.get(variable, {}).get(
                key, ""
            )
        )
        source_column = source_columns.get(key)
        if source_column:
            existing = result[source_column]
            empty = existing.isna() | existing.astype(str).str.strip().isin(
                ["", "nan", "None"]
            )
            fillable = (
                empty
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
