from __future__ import annotations

from pathlib import Path
import re
from typing import Any
from uuid import uuid4

import pandas as pd

from src.builder.preguntas_builder import PREGUNTA_COLUMNS
from src.database.db_reader import list_tables, read_table
from src.database.db_writer import write_tables
from src.reporter.factors import apply_numeric_ranges, validate_ranges


def default_factor_variable(source_variable: str) -> str:
    clean = re.sub(
        r"[^A-Za-z0-9_]+", "_", str(source_variable)
    ).strip("_")
    if not clean or clean[0].isdigit():
        clean = f"V_{clean}"
    return f"FACTOR_{clean}".upper()


def load_factor_source(
    db_path: Path,
    source_variable: str,
    df_spss: pd.DataFrame | None = None,
) -> pd.Series:
    if (
        df_spss is not None
        and source_variable in df_spss.columns
    ):
        return df_spss[source_variable].reset_index(drop=True)

    respondents = read_table(db_path, "respondentes")
    if source_variable in respondents:
        return _series_by_row_index(
            respondents, respondents[source_variable]
        )

    responses = read_table(db_path, "respuestas_long")
    if (
        not responses.empty
        and {"id_respondente", "variable"}.issubset(
            responses.columns
        )
    ):
        selected = responses[
            responses["variable"].astype(str).eq(source_variable)
        ].drop_duplicates("id_respondente")
        if not selected.empty:
            value_column = (
                "valor_numerico"
                if "valor_numerico" in selected
                else "codigo_respuesta"
            )
            values = respondents["id_respondente"].astype(str).map(
                selected.assign(
                    id_respondente=selected[
                        "id_respondente"
                    ].astype(str)
                )
                .set_index("id_respondente")[value_column]
                .to_dict()
            )
            return _series_by_row_index(respondents, values)
    raise ValueError(
        f"No se encontraron valores para {source_variable}."
    )


def apply_range_factor(
    db_path: Path,
    source_values: pd.Series,
    source_variable: str,
    factor_variable: str,
    factor_label: str,
    factor_id: str,
    ranges,
    *,
    as_banner: bool = True,
    as_filter: bool = True,
) -> dict[str, Any]:
    validated_ranges = validate_ranges(ranges)
    _validate_variable_name(factor_variable)
    if not db_path.exists():
        raise FileNotFoundError("La base analítica no existe.")

    tables = {
        name: read_table(db_path, name)
        for name in list_tables(db_path)
    }
    respondents = tables.get("respondentes", pd.DataFrame()).copy()
    variables = tables.get("variables", pd.DataFrame()).copy()
    config = tables.get(
        "configuracion_dashboard", pd.DataFrame()
    ).copy()
    options = tables.get("opciones", pd.DataFrame()).copy()
    questions = tables.get("preguntas", pd.DataFrame()).copy()
    responses = tables.get(
        "respuestas_long", pd.DataFrame()
    ).copy()
    if respondents.empty or "row_index" not in respondents:
        raise ValueError(
            "La tabla respondentes no contiene row_index."
        )

    existing = variables[
        variables["variable"].astype(str).eq(factor_variable)
    ]
    if (
        not existing.empty
        and not existing["clasificacion_analitica"]
        .astype(str)
        .eq("Derivada")
        .all()
    ):
        raise ValueError(
            f"{factor_variable} ya existe y no es una derivada."
        )

    derived_source = apply_numeric_ranges(
        source_values, validated_ranges
    )
    row_indexes = pd.to_numeric(
        respondents["row_index"], errors="coerce"
    )
    respondents[factor_variable] = [
        (
            derived_source.iloc[int(index)]
            if pd.notna(index)
            and 0 <= int(index) < len(derived_source)
            else pd.NA
        )
        for index in row_indexes
    ]
    tables["respondentes"] = respondents

    variables = variables[
        ~variables["variable"].astype(str).eq(factor_variable)
    ].copy()
    source_row = variables[
        variables["variable"].astype(str).eq(source_variable)
    ]
    source_question_id = (
        str(source_row.iloc[0].get("pregunta_id") or source_variable)
        if not source_row.empty
        else source_variable
    )
    question_id = factor_variable
    variable_row = {
        column: None for column in variables.columns
    }
    variable_row.update(
        {
            "variable": factor_variable,
            "label": factor_label,
            "tipo_spss": "text",
            "pregunta_id": question_id,
            "tipo_pregunta": "Factor derivado",
            "clasificacion_analitica": "Derivada",
            "usar_en_dashboard": 1,
            "es_banner": int(as_banner),
            "es_filtro": int(as_filter),
            "es_ponderador": 0,
            "tipo_calculo": "Frecuencia",
            "n_validos": int(
                respondents[factor_variable].notna().sum()
            ),
            "n_missing": int(
                respondents[factor_variable].isna().sum()
            ),
            "valores_unicos": int(
                respondents[factor_variable].nunique(dropna=True)
            ),
        }
    )
    variables = _append_aligned_row(
        variables, variable_row
    )
    tables["variables"] = variables

    questions = _upsert_factor_question(
        questions,
        source_question_id=source_question_id,
        factor_question_id=question_id,
        factor_label=factor_label,
        factor_id=factor_id,
    )
    tables["preguntas"] = questions

    responses = _upsert_factor_responses(
        responses,
        respondents,
        factor_variable=factor_variable,
        question_id=question_id,
    )
    tables["respuestas_long"] = responses

    if not config.empty:
        config = config[
            ~(
                config["variable"].astype(str).eq(factor_variable)
                & config["tipo_configuracion"].isin(
                    ["banner", "filtro"]
                )
            )
        ].copy()
    config_rows = []
    for kind, enabled in (
        ("banner", as_banner),
        ("filtro", as_filter),
    ):
        if enabled:
            config_rows.append(
                {
                    "tipo_configuracion": kind,
                    "variable": factor_variable,
                    "pregunta_id": question_id,
                    "label": factor_label,
                }
            )
    if config_rows:
        config = pd.concat(
            [config, pd.DataFrame(config_rows)],
            ignore_index=True,
        )
    tables["configuracion_dashboard"] = config

    if not options.empty:
        options = options[
            ~options["variable"].astype(str).eq(factor_variable)
        ].copy()
    option_rows = [
        {
            "variable": factor_variable,
            "pregunta_id": question_id,
            "codigo": row["Etiqueta"],
            "label": row["Etiqueta"],
            "es_otro": False,
            "es_exclusiva": False,
            "orden": index,
        }
        for index, row in enumerate(validated_ranges, start=1)
    ]
    tables["opciones"] = pd.concat(
        [options, pd.DataFrame(option_rows)],
        ignore_index=True,
    )

    configured = tables.get(
        "factores_configurados", pd.DataFrame()
    ).copy()
    if not configured.empty and "factor_id" in configured:
        mask = configured["factor_id"].astype(str).eq(factor_id)
        configured.loc[mask, "activo"] = 1
        configured.loc[mask, "variable_derivada"] = factor_variable
        configured.loc[mask, "como_banner"] = int(as_banner)
        configured.loc[mask, "como_filtro"] = int(as_filter)
        tables["factores_configurados"] = configured
        decision_mask = (
            config["variable"].astype(str).eq(factor_id)
            & config["tipo_configuracion"].isin(
                ["factor_score_activo", "factor_score_inactivo"]
            )
        )
        config = config[~decision_mask].copy()
        decision_row = {
            column: None for column in config.columns
        }
        decision_row.update(
            {
                "tipo_configuracion": "factor_score_activo",
                "variable": factor_id,
                "pregunta_id": question_id,
                "label": "Factor/score materializado",
            }
        )
        config = pd.concat(
            [
                config.astype("object"),
                pd.DataFrame([decision_row]).astype("object"),
            ],
            ignore_index=True,
        )
        tables["configuracion_dashboard"] = config

    temp_path = db_path.with_name(
        f".{db_path.stem}.{uuid4().hex}.factor{db_path.suffix}"
    )
    try:
        write_tables(temp_path, tables)
        validated = read_table(temp_path, "respondentes")
        if factor_variable not in validated:
            raise RuntimeError(
                "La variable derivada no se guardó en respondentes."
            )
        validated_questions = read_table(
            temp_path, "preguntas"
        )
        if not validated_questions[
            "pregunta_id"
        ].astype(str).eq(question_id).any():
            raise RuntimeError(
                "El factor no se guardó como pregunta reportable."
            )
        temp_path.replace(db_path)
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "variable": factor_variable,
        "label": factor_label,
        "validos": int(
            respondents[factor_variable].notna().sum()
        ),
        "tables": tables,
    }


def synchronize_inactive_factors(
    db_path: Path,
) -> dict[str, Any]:
    if not db_path.exists():
        return {"removed": [], "tables": {}}
    try:
        configured = read_table(
            db_path, "factores_configurados"
        )
    except Exception:
        return {"removed": [], "tables": {}}
    if configured.empty:
        return {"removed": [], "tables": {}}

    inactive = configured[
        ~pd.to_numeric(
            configured["activo"], errors="coerce"
        ).fillna(0).astype(bool)
    ]
    derived_variables = (
        inactive["variable_derivada"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    derived_variables = [
        value for value in derived_variables if value
    ]
    if not derived_variables:
        return {"removed": [], "tables": {}}

    tables = {
        name: read_table(db_path, name)
        for name in list_tables(db_path)
    }
    respondents = tables.get("respondentes", pd.DataFrame()).copy()
    tables["respondentes"] = respondents.drop(
        columns=[
            variable
            for variable in derived_variables
            if variable in respondents
        ],
        errors="ignore",
    )
    for table_name in ("variables", "opciones"):
        frame = tables.get(table_name, pd.DataFrame()).copy()
        if not frame.empty and "variable" in frame:
            frame = frame[
                ~frame["variable"]
                .astype(str)
                .isin(derived_variables)
            ].copy()
        tables[table_name] = frame
    if "preguntas" in tables:
        questions = tables["preguntas"].copy()
        if not questions.empty and "pregunta_id" in questions:
            questions = questions[
                ~questions["pregunta_id"]
                .astype(str)
                .isin(derived_variables)
            ].copy()
        tables["preguntas"] = questions
    if "respuestas_long" in tables:
        responses = tables["respuestas_long"].copy()
        if not responses.empty:
            remove = pd.Series(
                False, index=responses.index
            )
            if "variable" in responses:
                remove |= responses["variable"].astype(str).isin(
                    derived_variables
                )
            if "pregunta_id" in responses:
                remove |= responses[
                    "pregunta_id"
                ].astype(str).isin(derived_variables)
            responses = responses[~remove].copy()
        tables["respuestas_long"] = responses
    config = tables.get(
        "configuracion_dashboard", pd.DataFrame()
    ).copy()
    if not config.empty:
        active_role = config["tipo_configuracion"].isin(
            ["banner", "filtro"]
        )
        derived = config["variable"].astype(str).isin(
            derived_variables
        )
        config = config[~(active_role & derived)].copy()
    tables["configuracion_dashboard"] = config

    temp_path = db_path.with_name(
        f".{db_path.stem}.{uuid4().hex}.sync{db_path.suffix}"
    )
    try:
        write_tables(temp_path, tables)
        temp_path.replace(db_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"removed": derived_variables, "tables": tables}


def _validate_variable_name(value: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(
            "El nombre de la variable debe iniciar con letra o "
            "guion bajo y usar solo letras, números o guion bajo."
        )


def _upsert_factor_question(
    questions: pd.DataFrame,
    *,
    source_question_id: str,
    factor_question_id: str,
    factor_label: str,
    factor_id: str,
) -> pd.DataFrame:
    if questions.empty and len(questions.columns) == 0:
        questions = pd.DataFrame(columns=PREGUNTA_COLUMNS)
    result = questions[
        ~questions["pregunta_id"]
        .astype(str)
        .eq(factor_question_id)
    ].copy()
    source = result[
        result["pregunta_id"]
        .astype(str)
        .eq(source_question_id)
    ]
    source_row = (
        source.iloc[0].to_dict() if not source.empty else {}
    )
    row = {column: None for column in result.columns}
    row.update(source_row)
    row.update(
        {
            "pregunta_id": factor_question_id,
            "numero_pregunta": factor_question_id,
            "texto_pregunta": factor_label,
            "tipo_pregunta": "RU derivada",
            "tipo_calculo": "Frecuencia",
            "regla_transformacion": factor_id,
            "usar_en_dashboard": 1,
            "mostrar_en_menu_reporteador": "Sí",
        }
    )
    if "orden_cuestionario" in result:
        source_order = pd.to_numeric(
            pd.Series([source_row.get("orden_cuestionario")]),
            errors="coerce",
        ).iloc[0]
        row["orden_cuestionario"] = (
            float(source_order) + 0.001
            if pd.notna(source_order)
            else None
        )
    return _append_aligned_row(result, row)


def _upsert_factor_responses(
    responses: pd.DataFrame,
    respondents: pd.DataFrame,
    *,
    factor_variable: str,
    question_id: str,
) -> pd.DataFrame:
    default_columns = [
        "id_respondente",
        "pregunta_id",
        "variable",
        "tipo_pregunta",
        "codigo_respuesta",
        "respuesta_label",
        "valor_numerico",
        "respuesta_texto",
        "ponderador",
        "base_valida",
    ]
    if responses.empty and len(responses.columns) == 0:
        responses = pd.DataFrame(columns=default_columns)
    result = responses.copy()
    if "variable" in result:
        result = result[
            ~result["variable"]
            .astype(str)
            .eq(factor_variable)
        ].copy()
    if "pregunta_id" in result:
        result = result[
            ~result["pregunta_id"]
            .astype(str)
            .eq(question_id)
        ].copy()
    rows = []
    for _, respondent in respondents.iterrows():
        value = respondent.get(factor_variable)
        if value is None or pd.isna(value):
            continue
        label = str(value)
        row = {column: None for column in result.columns}
        row.update(
            {
                "id_respondente": str(
                    respondent.get("id_respondente")
                ),
                "pregunta_id": question_id,
                "variable": factor_variable,
                "tipo_pregunta": "RU derivada",
                "codigo_respuesta": label,
                "respuesta_label": label,
                "valor_numerico": None,
                "respuesta_texto": label,
                "ponderador": 1.0,
                "base_valida": 1,
            }
        )
        rows.append(row)
    if not rows:
        return result
    additions = pd.DataFrame(rows, columns=result.columns)
    if result.empty:
        return additions.reset_index(drop=True)
    return pd.concat(
        [
            result.astype("object"),
            additions.astype("object"),
        ],
        ignore_index=True,
    )


def _append_aligned_row(
    frame: pd.DataFrame, row: dict[str, Any]
) -> pd.DataFrame:
    result = frame.reset_index(drop=True).copy()
    addition = pd.DataFrame(
        [
            [
                row.get(column)
                for column in result.columns
            ]
        ],
        columns=result.columns,
    )
    if result.empty:
        return addition
    return pd.concat(
        [
            result.astype("object"),
            addition.astype("object"),
        ],
        ignore_index=True,
    )


def _series_by_row_index(
    respondents: pd.DataFrame, values: pd.Series
) -> pd.Series:
    indexes = pd.to_numeric(
        respondents["row_index"], errors="coerce"
    )
    valid_indexes = indexes.dropna().astype(int)
    if valid_indexes.empty:
        return values.reset_index(drop=True)
    result = pd.Series(
        pd.NA,
        index=range(int(valid_indexes.max()) + 1),
        dtype="object",
    )
    for position, row_index in enumerate(indexes):
        if pd.notna(row_index):
            result.iloc[int(row_index)] = values.iloc[position]
    return result
