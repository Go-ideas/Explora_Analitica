from __future__ import annotations

from collections.abc import Iterable
from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

import pandas as pd

from src.builder.recommendations_builder import (
    is_distribution_text,
    normalize_base_distribution,
)
from src.database.db_reader import read_table
from src.utils.question_order import resolve_datamap_paths
from src.utils.text_utils import find_column, normalize_text, truthy


RECOMMENDATION_COLUMNS = [
    "variable",
    "label",
    "pregunta_id",
    "es_recomendado",
    "justificacion",
    "uso_comercial",
    "distribucion_base",
    "nivel_relevancia",
    "riesgo_analitico",
]

FACTOR_SHEET_NAMES = [
    "12_Factores_Scores_Recomendados",
    "Factores_Scores_Recomendados",
]

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


def configuration_entries(
    db_path: Path,
    kind: str,
    datamap_paths: Path
    | str
    | Iterable[Path | str]
    | None = None,
) -> pd.DataFrame:
    kind = normalize_text(kind)
    if kind not in {"banner", "filtro", "ponderador"}:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)
    try:
        config = read_table(db_path, "configuracion_dashboard")
        variables = read_table(db_path, "variables")
        respondents = read_table(db_path, "respondentes")
    except Exception:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)

    system_columns = {
        "id_respondente",
        "id_original",
        "row_index",
    }
    available = [
        column
        for column in respondents.columns
        if column not in system_columns
    ]
    variable_lookup = (
        variables.drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
        if not variables.empty and "variable" in variables
        else {}
    )
    configured = set()
    if not config.empty:
        configured = set(
            config.loc[
                config["tipo_configuracion"].astype(str).eq(kind),
                "variable",
            ]
            .dropna()
            .astype(str)
        )
    recommendations = {}
    if kind in {"banner", "filtro"}:
        recommendations = (
            _load_database_role_recommendations(
                db_path, kind
            )
        )
        if not recommendations:
            recommendations = _load_role_recommendations(
                resolve_datamap_paths(datamap_paths), kind
            )

    rows = []
    for variable in available:
        metadata = variable_lookup.get(variable, {})
        recommendation = recommendations.get(variable, {})
        recommended = (
            variable in configured
            or bool(recommendation.get("es_recomendado"))
        )
        rows.append(
            {
                "variable": variable,
                "label": (
                    recommendation.get("label")
                    or metadata.get("label")
                    or variable
                ),
                "pregunta_id": (
                    recommendation.get("pregunta_id")
                    or metadata.get("pregunta_id")
                    or variable
                ),
                "es_recomendado": recommended,
                "justificacion": recommendation.get(
                    "justificacion",
                    metadata.get(
                        "justificacion_banner_filtro", ""
                    ),
                ),
                "uso_comercial": recommendation.get(
                    "uso_comercial",
                    metadata.get(
                        "uso_comercial_sugerido", ""
                    ),
                ),
                "distribucion_base": recommendation.get(
                    "distribucion_base",
                    metadata.get("distribucion_base", ""),
                ),
                "nivel_relevancia": recommendation.get(
                    "nivel_relevancia",
                    metadata.get(
                        "nivel_relevancia_comercial", ""
                    ),
                ),
                "riesgo_analitico": recommendation.get(
                    "riesgo_analitico",
                    metadata.get("riesgo_uso_analitico", ""),
                ),
            }
        )
    result = pd.DataFrame(rows, columns=RECOMMENDATION_COLUMNS)
    if result.empty:
        return result
    if kind == "ponderador":
        result = result[
            result["variable"].astype(str).isin(configured)
        ].copy()
        if result.empty:
            return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)
    result["_recommended_sort"] = (
        ~result["es_recomendado"].astype(bool)
    )
    return (
        result.sort_values(
            ["_recommended_sort", "variable"], kind="stable"
        )
        .drop(columns="_recommended_sort")
        .reset_index(drop=True)
    )


def load_factor_recommendations(
    datamap_paths: Path
    | str
    | Iterable[Path | str]
    | None = None,
) -> pd.DataFrame:
    for path in resolve_datamap_paths(datamap_paths):
        try:
            sheets = pd.read_excel(
                path, sheet_name=None, engine="openpyxl"
            )
        except Exception:
            continue
        for name in FACTOR_SHEET_NAMES:
            frame = sheets.get(name)
            if frame is not None and not frame.empty:
                result = frame.copy()
                if "_factor_id" not in result:
                    question_col = find_column(
                        result.columns,
                        ["Numero_Pregunta", "Pregunta_ID"],
                    )
                    type_col = find_column(
                        result.columns,
                        ["Tipo_Factor_Recomendado"],
                    )
                    result["_factor_id"] = [
                        "::".join(
                            [
                                str(row.get(question_col, "")).strip(),
                                str(row.get(type_col, "")).strip(),
                                str(index),
                            ]
                        )
                        for index, row in result.iterrows()
                    ]
                return result
    return pd.DataFrame()


def factor_decisions(
    db_path: Path,
) -> dict[str, bool]:
    saved = load_factor_configurations(db_path)
    if not saved.empty:
        return {
            str(row["factor_id"]): bool(row["activo"])
            for _, row in saved.iterrows()
        }
    try:
        config = read_table(db_path, "configuracion_dashboard")
    except Exception:
        return {}
    if config.empty:
        return {}
    decisions = {}
    for _, row in config[
        config["tipo_configuracion"].isin(
            ["factor_score_activo", "factor_score_inactivo"]
        )
    ].iterrows():
        decisions[str(row.get("variable", ""))] = (
            row["tipo_configuracion"] == "factor_score_activo"
        )
    return decisions


def load_factor_configurations(db_path: Path) -> pd.DataFrame:
    try:
        saved = read_table(db_path, "factores_configurados")
    except Exception:
        return pd.DataFrame(columns=FACTOR_CONFIG_COLUMNS)
    for column in FACTOR_CONFIG_COLUMNS:
        if column not in saved:
            saved[column] = None
    return saved[FACTOR_CONFIG_COLUMNS]


def merge_factor_configurations(
    factors: pd.DataFrame,
    saved: pd.DataFrame,
) -> pd.DataFrame:
    if factors.empty or saved.empty:
        return factors.copy()
    result = factors.copy()
    lookup = saved.drop_duplicates("factor_id").set_index(
        "factor_id"
    )
    mappings = {
        "Tipo_Factor_Recomendado": "tipo_factor",
        "Variables_Para_Factor": "variables_fuente",
        "Regla_Factor_Sugerida": "regla_factor",
        "Justificacion_Factor": "justificacion_factor",
        "Uso_Comercial_Sugerido": "uso_comercial",
        "Prioridad_Factor": "prioridad_factor",
    }
    for target, source in mappings.items():
        if target not in result:
            result[target] = ""
        saved_values = result["_factor_id"].astype(str).map(
            lookup[source]
        )
        present = saved_values.notna() & saved_values.astype(
            str
        ).str.strip().ne("")
        result.loc[present, target] = saved_values.loc[present]
    return result


def save_factor_configurations(
    db_path: Path,
    factors: pd.DataFrame,
    range_configurations: dict[str, list[dict[str, Any]]]
    | None = None,
) -> None:
    range_configurations = range_configurations or {}
    existing = load_factor_configurations(db_path)
    existing_lookup = (
        existing.set_index("factor_id").to_dict("index")
        if not existing.empty
        else {}
    )
    rows = []
    decisions = []
    for _, row in factors.iterrows():
        factor_id = str(row.get("_factor_id", "")).strip()
        if not factor_id:
            continue
        prior = existing_lookup.get(factor_id, {})
        ranges = range_configurations.get(factor_id)
        configuration_json = (
            json.dumps(
                {"ranges": ranges},
                ensure_ascii=False,
            )
            if ranges is not None
            else str(prior.get("configuracion_json") or "")
        )
        active = bool(row.get("Activo", False))
        number = _clean(
            row.get("Numero_Pregunta")
            or factor_id.split("::", 1)[0]
        )
        rows.append(
            (
                factor_id,
                number,
                _clean(row.get("Texto_Pregunta")),
                int(active),
                _clean(row.get("Tipo_Factor_Recomendado")),
                _clean(row.get("Variables_Para_Factor")),
                _clean(row.get("Regla_Factor_Sugerida")),
                _clean(row.get("Justificacion_Factor")),
                _clean(row.get("Uso_Comercial_Sugerido")),
                _clean(row.get("Prioridad_Factor")),
                configuration_json,
                _clean(prior.get("variable_derivada")),
                int(bool(prior.get("como_banner", 0))),
                int(bool(prior.get("como_filtro", 0))),
                datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
            )
        )
        decisions.append(
            (
                (
                    "factor_score_activo"
                    if active
                    else "factor_score_inactivo"
                ),
                factor_id,
                number,
                "Configuración editable de factor/score",
            )
        )

    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS factores_configurados (
                    factor_id TEXT PRIMARY KEY,
                    numero_pregunta TEXT,
                    texto_pregunta TEXT,
                    activo INTEGER,
                    tipo_factor TEXT,
                    variables_fuente TEXT,
                    regla_factor TEXT,
                    justificacion_factor TEXT,
                    uso_comercial TEXT,
                    prioridad_factor TEXT,
                    configuracion_json TEXT,
                    variable_derivada TEXT,
                    como_banner INTEGER,
                    como_filtro INTEGER,
                    actualizado_en TEXT
                )
                """
            )
            conn.execute("DELETE FROM factores_configurados")
            conn.executemany(
                "INSERT INTO factores_configurados VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.execute(
                "DELETE FROM configuracion_dashboard "
                "WHERE tipo_configuracion IN "
                "('factor_score_activo', 'factor_score_inactivo')"
            )
            conn.executemany(
                "INSERT INTO configuracion_dashboard "
                "(tipo_configuracion, variable, pregunta_id, label) "
                "VALUES (?, ?, ?, ?)",
                decisions,
            )


def save_factor_decisions(
    db_path: Path, decisions: dict[str, bool]
) -> None:
    rows = [
        (
            "factor_score_activo"
            if active
            else "factor_score_inactivo",
            factor_id,
            factor_id.split("::", 1)[0],
            "Decisión de factor/score sugerido",
        )
        for factor_id, active in decisions.items()
    ]
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute(
                "DELETE FROM configuracion_dashboard "
                "WHERE tipo_configuracion IN "
                "('factor_score_activo', 'factor_score_inactivo')"
            )
            conn.executemany(
                "INSERT INTO configuracion_dashboard "
                "(tipo_configuracion, variable, pregunta_id, label) "
                "VALUES (?, ?, ?, ?)",
                rows,
            )


def _load_role_recommendations(
    paths: list[Path], kind: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            sheets = pd.read_excel(
                path, sheet_name=None, engine="openpyxl"
            )
        except Exception:
            continue
        frames = []
        for name in [
            "11_Banners_Filtros_Recomendados",
            "Banners_Filtros_Recomendados",
            "08_Clasificacion_Analitica",
            "10_Datamap_Corregido",
        ]:
            frame = sheets.get(name)
            if frame is not None and not frame.empty:
                frames.append(frame)
        for frame in frames:
            _collect_recommendations(frame, kind, result)
    return result


def _load_database_role_recommendations(
    db_path: Path, kind: str
) -> dict[str, dict[str, Any]]:
    try:
        frame = read_table(
            db_path, "recomendaciones_reporteador"
        )
    except Exception:
        return {}
    if frame.empty or "variable" not in frame:
        return {}
    if "tipo_recomendacion" in frame:
        frame = frame[
            frame["tipo_recomendacion"]
            .astype(str)
            .eq("banner_filtro")
        ]
    flag = (
        "es_banner_recomendado"
        if kind == "banner"
        else "es_filtro_recomendado"
    )
    if flag in frame:
        active = pd.to_numeric(
            frame[flag], errors="coerce"
        ).fillna(0).astype(bool)
        frame = frame[active]
    result = {}
    for _, row in frame.iterrows():
        variable = _clean(row.get("variable"))
        if not variable:
            continue
        result[variable] = {
            "es_recomendado": True,
            "label": _clean(row.get("variable_label")),
            "pregunta_id": _clean(row.get("pregunta_id")),
            "justificacion": _clean(
                row.get("justificacion")
            ),
            "uso_comercial": _clean(
                row.get("uso_comercial_sugerido")
            ),
            "distribucion_base": _clean(
                row.get("distribucion_base")
            ),
            "nivel_relevancia": _clean(
                row.get("nivel_relevancia_comercial")
            ),
            "riesgo_analitico": _clean(
                row.get("riesgo_uso_analitico")
            ),
        }
    return result


def _collect_recommendations(
    frame: pd.DataFrame,
    kind: str,
    result: dict[str, dict[str, Any]],
) -> None:
    variable_col = find_column(
        frame.columns,
        ["variable", "Variable_SPSS", "nombre_variable"],
    )
    if not variable_col:
        return
    flag_col = find_column(
        frame.columns,
        (
            [
                "Es_Banner_Recomendado",
                "banner_recomendado",
                "es_banner",
            ]
            if kind == "banner"
            else [
                "Es_Filtro_Recomendado",
                "filtro_recomendado",
                "es_filtro",
            ]
        ),
    )
    role_col = find_column(
        frame.columns,
        ["Tipo_Recomendacion", "Tipo", "Rol_Analitico"],
    )
    for _, row in frame.iterrows():
        variable = _clean(row.get(variable_col))
        if not variable:
            continue
        recommended = (
            truthy(row.get(flag_col)) if flag_col else False
        )
        if role_col:
            role = normalize_text(row.get(role_col))
            recommended = recommended or kind in role
        if not recommended:
            continue
        current = result.setdefault(variable, {})
        current["es_recomendado"] = True
        aliases = {
            "label": ["Label", "Variable_Label", "Etiqueta"],
            "pregunta_id": [
                "Pregunta_ID",
                "Numero_Pregunta",
            ],
            "justificacion": [
                "Justificacion_Banner_Filtro",
                "Justificación_Banner_Filtro",
                "Justificacion",
            ],
            "uso_comercial": ["Uso_Comercial_Sugerido"],
            "distribucion_base": [
                "Distribucion_Base",
                "Distribución_Base",
                "Base_Categorias_Obs",
            ],
            "nivel_relevancia": [
                "Nivel_Relevancia_Comercial"
            ],
            "riesgo_analitico": ["Riesgo_Uso_Analitico"],
        }
        for key, candidates in aliases.items():
            column = find_column(frame.columns, candidates)
            value = _clean(row.get(column)) if column else ""
            if value and not current.get(key):
                current[key] = value
        justification = _clean(
            current.get("justificacion")
        )
        if is_distribution_text(justification):
            current["distribucion_base"] = (
                current.get("distribucion_base")
                or normalize_base_distribution(justification)
            )
            current["justificacion"] = ""
        if not current.get("justificacion"):
            label = current.get("label") or variable
            use = current.get("uso_comercial") or ""
            current["justificacion"] = (
                f"{label} se recomienda para apoyar una lectura "
                "comercial clara y accionable."
                + (f" {use}" if use else "")
            )


def _clean(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text
