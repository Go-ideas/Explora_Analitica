from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.database.db_writer import write_tables
from src.database.db_reader import read_table
from src.database.factor_processor import apply_range_factor
from src.export.excel_exporter import export_revision_excel
from src.builder.abiertas_builder import build_abiertas
from src.builder.escalas_long_builder import build_escalas_long
from src.builder.grid_loop_long_builder import build_grid_loop_long
from src.builder.opciones_builder import build_opciones
from src.builder.preguntas_builder import build_preguntas
from src.builder.recommendations_builder import (
    build_recomendaciones_reporteador,
    clean_commercial_justification,
)
from src.builder.respondentes_builder import build_respondentes
from src.builder.respuestas_long_builder import build_respuestas_long
from src.builder.rm_long_builder import build_rm_long
from src.builder.variables_builder import build_variables
from src.utils.constants import DB_DIR, EXPORTS_DIR, REVISION_EXCEL_FILENAME, SQLITE_FILENAME
from src.utils.text_utils import find_column, truthy
from src.utils.variable_safety import banner_filter_exclusion_reason


FACTOR_CONFIG_COLUMNS = [
    "factor_id",
    "numero_pregunta",
    "texto_pregunta",
    "activo",
    "tipo_factor",
    "variables_fuente",
    "regla_factor",
    "justificacion_factor",
    "uso_comercial",
    "prioridad_factor",
    "configuracion_json",
    "variable_derivada",
    "como_banner",
    "como_filtro",
    "actualizado_en",
]


def build_analytic_database(
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    datamap_sheets: dict[str, pd.DataFrame] | None = None,
    db_path: Path | None = None,
    excel_path: Path | None = None,
    preserve_existing_factors: bool = False,
    export_revision: bool = True,
) -> dict[str, Any]:
    db_path = db_path or DB_DIR / SQLITE_FILENAME
    excel_path = (
        excel_path or EXPORTS_DIR / REVISION_EXCEL_FILENAME
        if export_revision
        else None
    )
    datamap_sheets = datamap_sheets or {}
    saved_factors = (
        _read_saved_factors(db_path)
        if preserve_existing_factors
        else pd.DataFrame(columns=FACTOR_CONFIG_COLUMNS)
    )

    respondentes = build_respondentes(df_spss, datamap_df)
    preguntas = build_preguntas(datamap_df)
    variables = build_variables(df_spss, meta_spss, datamap_df)
    opciones = build_opciones(meta_spss, datamap_df, datamap_sheets.get("03_Check_ValueLabels"))
    respuestas_long = build_respuestas_long(df_spss, meta_spss, datamap_df, respondentes)
    rm_long = build_rm_long(df_spss, meta_spss, datamap_df, respondentes)
    grid_loop_long = build_grid_loop_long(
        df_spss, meta_spss, datamap_df, respondentes
    )
    escalas_long = build_escalas_long(df_spss, meta_spss, datamap_df, respondentes)
    abiertas = build_abiertas(df_spss, datamap_df, respondentes)
    riesgos = build_riesgos(datamap_sheets)
    grids, grid_items = build_grid_tables(datamap_df)
    recomendaciones = build_recomendaciones_reporteador(
        datamap_df,
        datamap_sheets,
        df_spss=df_spss,
        meta_spss=meta_spss,
    )
    estructuras_detectadas = datamap_df.attrs.get(
        "grid_loop_structures", pd.DataFrame()
    )
    configuracion = build_configuracion_dashboard(
        datamap_df, recomendaciones, df_spss=df_spss
    )
    configuracion = _append_factor_decisions(
        configuracion, saved_factors
    )

    tables = {
        "respondentes": respondentes,
        "preguntas": preguntas,
        "variables": variables,
        "opciones": opciones,
        "respuestas_long": respuestas_long,
        "multirrespuesta_long": rm_long,
        "respuestas_grid_loop": grid_loop_long,
        "escalas_long": escalas_long,
        "abiertas": abiertas,
        "riesgos": riesgos,
        "grids": grids,
        "grid_items": grid_items,
        "estructuras_detectadas": estructuras_detectadas,
        "configuracion_dashboard": configuracion,
        "recomendaciones_reporteador": recomendaciones,
        "factores_configurados": (
            saved_factors
            if not saved_factors.empty
            else pd.DataFrame(columns=FACTOR_CONFIG_COLUMNS)
        ),
    }

    write_tables(db_path, tables)
    tables = _rematerialize_active_factors(
        db_path,
        df_spss,
        saved_factors,
        tables,
    )
    if export_revision and excel_path is not None:
        export_revision_excel(
            excel_path, tables, datamap_sheets=datamap_sheets
        )
    return {"db_path": db_path, "excel_path": excel_path, "tables": tables}


def build_riesgos(source: pd.DataFrame | dict[str, pd.DataFrame] | None) -> pd.DataFrame:
    columns = ["variable", "pregunta_id", "tipo_riesgo", "prioridad", "descripcion", "accion_recomendada", "estatus"]
    frames = _risk_source_frames(source)
    if not frames:
        return pd.DataFrame(columns=columns)
    rows = []
    aliases = {
        "prioridad": ["prioridad", "nivel", "severidad"],
        "tipo_riesgo": ["tipo_riesgo", "tipo", "riesgo", "bloque_qa"],
        "descripcion": ["descripcion", "descripción", "detalle", "hallazgo", "riesgo_grid", "riesgo"],
        "variable": ["variable", "variable_spss", "variable_item"],
        "pregunta_id": ["pregunta_id", "pregunta", "pregunta_padre", "numero_pregunta"],
        "accion_recomendada": ["accion_recomendada", "acción_recomendada", "recomendacion", "recomendacion_qa"],
        "estatus": ["estatus", "status", "estado"],
    }
    for source_name, df in frames:
        for _, row in df.iterrows():
            item = {}
            for col, names in aliases.items():
                column = find_column(df.columns, names)
                item[col] = row.get(column, "") if column else ""
            structure = _first_text(
                row.get(find_column(df.columns, ["Tipo_Estructura_Grid"]))
                if find_column(df.columns, ["Tipo_Estructura_Grid"])
                else ""
            )
            if source_name == "04B_Check_Grids":
                grid_risk = _first_text(
                    row.get(find_column(df.columns, ["Riesgo_Grid", "Riesgo"]))
                    if find_column(df.columns, ["Riesgo_Grid", "Riesgo"])
                    else ""
                )
                if not grid_risk:
                    continue
                item["tipo_riesgo"] = (
                    "GRID_RM/LOOP_RM"
                    if "grid_rm" in structure.lower()
                    or "loop_rm" in structure.lower()
                    else "GRID/LOOP"
                )
                item["prioridad"] = _first_text(item.get("prioridad"), "Medio")
                item["descripcion"] = grid_risk
                item["accion_recomendada"] = _first_text(
                    item.get("accion_recomendada"),
                    "Revisar estructura, value labels, entidad/opción y métrica antes de transformar.",
                )
            if not _first_text(item["descripcion"], item["prioridad"], item["tipo_riesgo"]):
                continue
            if not _first_text(item["tipo_riesgo"]):
                item["tipo_riesgo"] = source_name
            item["fuente_hoja"] = source_name
            rows.append(item)
    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=columns + ["fuente_hoja"])
    return result[columns + ["fuente_hoja"]]


def _risk_source_frames(
    source: pd.DataFrame | dict[str, pd.DataFrame] | None,
) -> list[tuple[str, pd.DataFrame]]:
    if isinstance(source, pd.DataFrame):
        return [("09_Riesgos_Priorizados", source)] if not source.empty else []
    if not source:
        return []
    names = [
        "Riesgos",
        "09_Riesgos_Priorizados",
        "04B_Check_Grids",
        "05_Check_RM",
        "06_Check_Filtros_Saltos",
    ]
    return [
        (name, source[name])
        for name in names
        if name in source and source[name] is not None and not source[name].empty
    ]


def build_grid_tables(
    df: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid_columns = [
        "grid_id",
        "pregunta_padre",
        "texto_pregunta",
        "tipo_grid",
        "tipo_estructura_grid",
        "es_grid_rm_loop",
        "tipo_escala_columnas",
        "codigos_columnas_grid",
        "labels_columnas_grid",
        "metrica_grid_recomendada",
        "regla_tabular_recomendada",
        "requiere_factor",
        "tipo_factor_recomendado",
        "regla_factor_sugerida",
        "riesgo_grid",
    ]
    item_columns = [
        "grid_id",
        "variable",
        "orden_fila_grid",
        "texto_fila_grid",
        "entidad_loop",
        "orden_entidad_loop",
        "label_entidad_loop",
        "codigo_opcion_rm",
        "label_opcion_rm",
        "orden_opcion_rm",
        "formato_rm",
        "rango_esperado",
        "rango_observado",
        "value_labels_compartidos",
        "value_label_patron",
        "valores_observados_patron",
        "patron_label_constante",
        "match_grid",
        "evidencia_grid",
    ]
    if df is None or df.empty:
        return (
            pd.DataFrame(columns=grid_columns),
            pd.DataFrame(columns=item_columns),
        )
    aliases = {
        "grid_id": ["grid_id", "Grid_ID", "Pregunta_Padre", "Numero_Pregunta"],
        "pregunta_padre": ["pregunta_padre", "Pregunta_Padre", "Pregunta_Padre_Detectada"],
        "variable": ["variable", "Variable_Item", "Variable", "Variable_SPSS"],
        "tipo_estructura_grid": ["tipo_estructura_grid", "Tipo_Estructura_Grid", "Tipo_Grid", "Tipo_Loop"],
        "es_grid": ["es_grid", "Es_Grid"],
        "es_item_grid": ["es_item_grid", "Es_Item_Grid"],
        "es_grid_rm_loop": ["es_grid_rm_loop", "Es_GRID_RM_LOOP", "Es_Grid_RM_Loop"],
        "orden_fila_grid": ["orden_fila_grid", "Orden_Fila_Grid", "Orden_Item", "Orden"],
        "texto_fila_grid": ["texto_fila_grid", "Texto_Fila_Grid", "Label", "Variable_Label"],
        "entidad_loop": ["entidad_loop", "Entidad_Loop", "Entidad", "Marca", "Canal", "Producto", "Touchpoint"],
        "orden_entidad_loop": ["orden_entidad_loop", "Orden_Entidad_Loop", "Orden_Entidad"],
        "label_entidad_loop": ["label_entidad_loop", "Label_Entidad_Loop", "Entidad_Loop", "Entidad"],
        "codigo_opcion_rm": ["codigo_opcion_rm", "Codigo_Opcion_RM", "Codigo_Opcion", "Codigo"],
        "label_opcion_rm": ["label_opcion_rm", "Label_Opcion_RM", "Label_Opcion", "Opcion_Respuesta", "Texto_Opcion"],
        "orden_opcion_rm": ["orden_opcion_rm", "Orden_Opcion_RM", "Orden_Opcion"],
        "formato_rm": ["formato_rm", "Formato_RM", "Tipo_Formato_RM"],
        "codigos_columnas_grid": ["Codigos_Columnas_Grid", "Codigos_Escala"],
        "labels_columnas_grid": ["Labels_Columnas_Grid", "Labels_Escala"],
        "tipo_escala_columnas": ["Tipo_Escala_Columnas", "Tipo_Escala"],
        "rango_esperado": ["Rango_Esperado"],
        "rango_observado": ["Rango_Observado"],
        "value_labels_compartidos": ["ValueLabels_Compartidos"],
        "value_label_patron": ["value_label_patron", "ValueLabel_Patron", "Patron_ValueLabels"],
        "valores_observados_patron": ["valores_observados_patron", "Valores_Observados_Patron", "Patron_Valores_Observados"],
        "patron_label_constante": ["patron_label_constante", "Patron_Label_Constante", "Texto_Constante_Label"],
        "match_grid": ["Match_Grid"],
        "evidencia_grid": ["Evidencia_Grid"],
        "metrica_grid_recomendada": ["Metrica_Grid_Recomendada", "Metrica_Recomendada"],
        "regla_tabular_recomendada": ["regla_tabular_recomendada", "Regla_Tabular_Recomendada", "Regla_Tabular", "Calculo_Recomendado"],
        "requiere_factor": ["Requiere_Factor"],
        "tipo_factor_recomendado": ["Tipo_Factor_Recomendado"],
        "regla_factor_sugerida": ["Regla_Factor_Sugerida"],
        "riesgo_grid": ["Riesgo_Grid", "Riesgo"],
    }
    normalized = pd.DataFrame()
    for column, names in aliases.items():
        source = find_column(df.columns, names)
        normalized[column] = df[source] if source else ""
    normalized["grid_id"] = normalized["grid_id"].fillna("").astype(str)
    normalized["variable"] = normalized["variable"].fillna("").astype(str)
    normalized["pregunta_padre"] = normalized["pregunta_padre"].fillna("").astype(str)
    normalized.loc[normalized["grid_id"].eq(""), "grid_id"] = normalized.loc[
        normalized["grid_id"].eq(""), "pregunta_padre"
    ]
    normalized["orden_fila_grid"] = pd.to_numeric(
        normalized["orden_fila_grid"], errors="coerce"
    )
    for order_column in ("orden_entidad_loop", "orden_opcion_rm"):
        normalized[order_column] = pd.to_numeric(
            normalized[order_column], errors="coerce"
        )
    normalized["requiere_factor"] = normalized["requiere_factor"].apply(
        lambda value: int(truthy(value))
    )
    grid_mask = (
        normalized["grid_id"].ne("")
        & (
            normalized["es_grid"].apply(truthy)
            | normalized["es_item_grid"].apply(truthy)
            | normalized["tipo_estructura_grid"].fillna("").astype(str).str.strip().ne("")
        )
    )
    item_rows = normalized[
        grid_mask
        & normalized["variable"].ne("")
        & ~normalized["variable"].astype(str).eq(normalized["grid_id"].astype(str))
    ].copy()
    grid_rows = []
    for grid_id, group in item_rows.groupby("grid_id", sort=False):
        first = group.iloc[0]
        grid_rows.append(
            {
                "grid_id": grid_id,
                "pregunta_padre": _first_text(first.get("pregunta_padre"), grid_id),
                "texto_pregunta": _first_text(first.get("pregunta_padre"), grid_id),
                "tipo_grid": _first_text(
                    first.get("tipo_estructura_grid"),
                    first.get("tipo_escala_columnas"),
                ),
                "tipo_estructura_grid": _first_text(first.get("tipo_estructura_grid")),
                "es_grid_rm_loop": int(group["es_grid_rm_loop"].apply(truthy).any()),
                "tipo_escala_columnas": _first_text(first.get("tipo_escala_columnas")),
                "codigos_columnas_grid": _first_text(first.get("codigos_columnas_grid")),
                "labels_columnas_grid": _first_text(first.get("labels_columnas_grid")),
                "metrica_grid_recomendada": _first_text(first.get("metrica_grid_recomendada")),
                "regla_tabular_recomendada": _first_text(first.get("regla_tabular_recomendada")),
                "requiere_factor": int(group["requiere_factor"].astype(bool).any()),
                "tipo_factor_recomendado": _first_text(first.get("tipo_factor_recomendado")),
                "regla_factor_sugerida": _first_text(first.get("regla_factor_sugerida")),
                "riesgo_grid": _first_text(first.get("riesgo_grid")),
            }
        )
    grids = pd.DataFrame(grid_rows, columns=grid_columns)
    items = item_rows[item_columns].drop_duplicates(
        ["grid_id", "variable"], keep="first"
    )
    return grids, items.reset_index(drop=True)


CONFIGURATION_COLUMNS = [
    "tipo_configuracion",
    "variable",
    "pregunta_id",
    "label",
    "es_recomendado",
    "es_banner_recomendado",
    "es_filtro_recomendado",
    "prioridad",
    "nivel_relevancia_comercial",
    "justificacion",
    "justificacion_banner_filtro",
    "uso_comercial_sugerido",
    "distribucion_base",
    "riesgo_uso_analitico",
    "fuente_hoja",
]


def build_configuracion_dashboard(
    datamap_df: pd.DataFrame,
    recommendations: pd.DataFrame | None = None,
    df_spss: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows = []
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=CONFIGURATION_COLUMNS)
    recommendation_lookup = _recommendation_lookup(
        recommendations
    )
    rules = [
        ("banner", _true_mask(datamap_df, "es_banner")),
        ("filtro", _true_mask(datamap_df, "es_filtro")),
        ("ponderador", _true_mask(datamap_df, "es_ponderador")),
        ("pregunta_analizable", datamap_df["clasificacion_analitica"] == "Pregunta analizable"),
        ("abierta", datamap_df["clasificacion_analitica"] == "Abierta"),
        (
            "variable_excluida",
            datamap_df["clasificacion_analitica"].isin(
                [
                    "Variable técnica",
                    "Control de calidad",
                    "No usar en dashboard",
                ]
            ),
        ),
    ]
    for tipo, mask in rules:
        for _, row in datamap_df.loc[mask].iterrows():
            variable = str(row.get("variable") or "")
            exclusion_reason = (
                banner_filter_exclusion_reason(df_spss, variable)
                if df_spss is not None
                and tipo in {"banner", "filtro"}
                else ""
            )
            if exclusion_reason:
                continue
            recommendation = recommendation_lookup.get(
                variable, {}
            )
            banner_recommended = _boolean(
                _first_present(
                    row.get("es_banner_recomendado"),
                    recommendation.get(
                        "es_banner_recomendado"
                    ),
                )
            )
            filter_recommended = _boolean(
                _first_present(
                    row.get("es_filtro_recomendado"),
                    recommendation.get(
                        "es_filtro_recomendado"
                    ),
                )
            )
            recommended = (
                banner_recommended
                if tipo == "banner"
                else (
                    filter_recommended
                    if tipo == "filtro"
                    else False
                )
            )
            commercial_use = _first_text(
                row.get("uso_comercial_sugerido"),
                recommendation.get(
                    "uso_comercial_sugerido"
                ),
            )
            has_commercial_role = bool(
                banner_recommended
                or filter_recommended
                or tipo in {"banner", "filtro"}
            )
            justification = clean_commercial_justification(
                row.get("justificacion_banner_filtro"),
                recommendation.get("justificacion"),
                row.get("label") or variable,
                (
                    "banner y filtro"
                    if banner_recommended
                    and filter_recommended
                    else tipo
                ),
                commercial_use,
                (
                    "banner_filtro"
                    if has_commercial_role
                    else ""
                ),
            )
            rows.append(
                {
                    "tipo_configuracion": tipo,
                    "variable": variable,
                    "pregunta_id": row.get("pregunta_id"),
                    "label": row.get("label"),
                    "es_recomendado": int(recommended),
                    "es_banner_recomendado": int(
                        banner_recommended
                    ),
                    "es_filtro_recomendado": int(
                        filter_recommended
                    ),
                    "prioridad": _first_text(
                        row.get("prioridad_reporteador"),
                        recommendation.get("prioridad_factor"),
                    ),
                    "nivel_relevancia_comercial": _first_text(
                        row.get(
                            "nivel_relevancia_comercial"
                        ),
                        recommendation.get(
                            "nivel_relevancia_comercial"
                        ),
                    ),
                    "justificacion": justification,
                    "justificacion_banner_filtro": (
                        justification
                    ),
                    "uso_comercial_sugerido": commercial_use,
                    "distribucion_base": _first_text(
                        recommendation.get(
                            "distribucion_base"
                        ),
                    ),
                    "riesgo_uso_analitico": _first_text(
                        row.get("riesgo_uso_analitico"),
                        recommendation.get(
                            "riesgo_uso_analitico"
                        ),
                    ),
                    "fuente_hoja": _first_text(
                        recommendation.get("fuente_hoja"),
                        "08_Clasificacion_Analitica",
                    ),
                }
            )
    return pd.DataFrame(rows, columns=CONFIGURATION_COLUMNS)


def _recommendation_lookup(
    recommendations: pd.DataFrame | None,
) -> dict[str, dict]:
    if (
        recommendations is None
        or recommendations.empty
        or "variable" not in recommendations
    ):
        return {}
    work = recommendations.copy()
    if "tipo_recomendacion" in work:
        work["_priority"] = (
            work["tipo_recomendacion"]
            .astype(str)
            .eq("banner_filtro")
            .map({True: 0, False: 1})
        )
        work = work.sort_values("_priority", kind="stable")
    return (
        work.dropna(subset=["variable"])
        .drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
    )


def _true_mask(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df:
        return pd.Series(False, index=df.index)
    return df[column].fillna(False).astype(bool)


def _boolean(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {
        "1",
        "true",
        "sí",
        "si",
        "yes",
        "recomendado",
    }


def _first_text(*values: object) -> str:
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value).strip()
        if text and text.lower() not in {"nan", "none"}:
            return text
    return ""


def _first_present(*values: object) -> object:
    for value in values:
        if value is None or pd.isna(value):
            continue
        return value
    return False


def _read_saved_factors(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    try:
        return read_table(db_path, "factores_configurados")
    except Exception:
        return pd.DataFrame()


def _append_factor_decisions(
    configuration: pd.DataFrame,
    factors: pd.DataFrame,
) -> pd.DataFrame:
    if factors.empty:
        return configuration
    rows = []
    for _, factor in factors.iterrows():
        active = _boolean(factor.get("activo"))
        row = {
            column: None for column in CONFIGURATION_COLUMNS
        }
        row.update(
            {
                "tipo_configuracion": (
                    "factor_score_activo"
                    if active
                    else "factor_score_inactivo"
                ),
                "variable": factor.get("factor_id"),
                "pregunta_id": factor.get("numero_pregunta"),
                "label": factor.get("tipo_factor"),
                "es_recomendado": 1,
                "prioridad": factor.get("prioridad_factor"),
                "justificacion": factor.get(
                    "justificacion_factor"
                ),
                "uso_comercial_sugerido": factor.get(
                    "uso_comercial"
                ),
                "fuente_hoja": (
                    "factores_configurados"
                ),
            }
        )
        rows.append(row)
    return pd.concat(
        [configuration, pd.DataFrame(rows)],
        ignore_index=True,
    )


def _rematerialize_active_factors(
    db_path: Path,
    df_spss: pd.DataFrame,
    factors: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    if factors.empty:
        return tables
    active = factors[
        pd.to_numeric(
            factors["activo"], errors="coerce"
        ).fillna(0).astype(bool)
    ]
    for _, factor in active.iterrows():
        derived = _first_text(factor.get("variable_derivada"))
        source = _first_text(factor.get("variables_fuente"))
        source = source.split(",", 1)[0].strip()
        if not derived or not source:
            continue
        if source not in df_spss:
            raise ValueError(
                f"El factor activo {factor.get('factor_id')} usa "
                f"una variable inexistente: {source}."
            )
        raw_config = _first_text(
            factor.get("configuracion_json")
        )
        try:
            ranges = json.loads(raw_config).get("ranges", [])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Configuración inválida para "
                f"{factor.get('factor_id')}."
            ) from exc
        if not ranges:
            continue
        result = apply_range_factor(
            db_path=db_path,
            source_values=df_spss[source],
            source_variable=source,
            factor_variable=derived,
            factor_label=(
                f"{factor.get('numero_pregunta')} · "
                f"{factor.get('tipo_factor')}"
            ),
            factor_id=str(factor.get("factor_id")),
            ranges=ranges,
            as_banner=_boolean(factor.get("como_banner")),
            as_filter=_boolean(factor.get("como_filtro")),
        )
        tables = result["tables"]
    return tables
