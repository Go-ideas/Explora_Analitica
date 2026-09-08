from __future__ import annotations

import pandas as pd


BASE_PIVOT_COLUMNS = [
    "id_respondente",
    "pregunta_id",
    "pregunta",
    "variable",
    "tipo_pregunta",
    "tipo_calculo",
    "item",
    "codigo",
    "respuesta",
    "valor",
    "ponderador",
]

FILTER_COLUMNS = [
    "filtro_1",
    "filtro_2",
]


def build_pivot_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    preguntas = tables.get("preguntas", pd.DataFrame())
    respondentes = tables.get("respondentes", pd.DataFrame())
    config = tables.get("configuracion_dashboard", pd.DataFrame())
    pregunta_lookup = {}
    if not preguntas.empty:
        pregunta_lookup = preguntas.set_index("pregunta_id").to_dict("index")

    pieces = [
        _from_respuestas(tables.get("respuestas_long", pd.DataFrame()), pregunta_lookup),
        _from_rm(tables.get("multirrespuesta_long", pd.DataFrame()), pregunta_lookup),
        _from_escalas(tables.get("escalas_long", pd.DataFrame()), pregunta_lookup),
        _from_abiertas(tables.get("abiertas", pd.DataFrame()), pregunta_lookup),
    ]
    pivot = pd.concat([piece for piece in pieces if not piece.empty], ignore_index=True) if any(not p.empty for p in pieces) else pd.DataFrame(columns=BASE_PIVOT_COLUMNS)
    pivot = _attach_banners_filters(pivot, respondentes, config)
    banner_columns = [
        target for target, _ in _banner_assignments(config, respondentes)
    ]
    output_columns = BASE_PIVOT_COLUMNS + banner_columns + FILTER_COLUMNS
    for col in output_columns:
        if col not in pivot:
            pivot[col] = ""
    return pivot[output_columns]


def _question_info(pregunta_lookup: dict, pregunta_id: str) -> dict:
    return pregunta_lookup.get(pregunta_id, {})


def _from_respuestas(df: pd.DataFrame, pregunta_lookup: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        info = _question_info(pregunta_lookup, row.get("pregunta_id"))
        rows.append(
            {
                "id_respondente": row.get("id_respondente"),
                "pregunta_id": row.get("pregunta_id"),
                "pregunta": info.get("texto_pregunta", ""),
                "variable": row.get("variable"),
                "tipo_pregunta": row.get("tipo_pregunta") or info.get("tipo_pregunta", ""),
                "tipo_calculo": info.get("tipo_calculo", ""),
                "item": "",
                "codigo": row.get("codigo_respuesta"),
                "respuesta": row.get("respuesta_label"),
                "valor": row.get("valor_numerico"),
                "ponderador": row.get("ponderador"),
            }
        )
    return pd.DataFrame(rows)


def _from_rm(df: pd.DataFrame, pregunta_lookup: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        info = _question_info(pregunta_lookup, row.get("pregunta_id"))
        rows.append(
            {
                "id_respondente": row.get("id_respondente"),
                "pregunta_id": row.get("pregunta_id"),
                "pregunta": info.get("texto_pregunta", ""),
                "variable": row.get("variable_origen"),
                "tipo_pregunta": "RM",
                "tipo_calculo": info.get("tipo_calculo", "RM % Respondentes"),
                "item": "",
                "codigo": row.get("codigo_respuesta"),
                "respuesta": row.get("respuesta_label"),
                "valor": 1,
                "ponderador": row.get("ponderador"),
            }
        )
    return pd.DataFrame(rows)


def _from_escalas(df: pd.DataFrame, pregunta_lookup: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        info = _question_info(pregunta_lookup, row.get("pregunta_id"))
        rows.append(
            {
                "id_respondente": row.get("id_respondente"),
                "pregunta_id": row.get("pregunta_id"),
                "pregunta": info.get("texto_pregunta", ""),
                "variable": row.get("variable"),
                "tipo_pregunta": info.get("tipo_pregunta", "Escala"),
                "tipo_calculo": info.get("tipo_calculo", "Media"),
                "item": row.get("item_texto"),
                "codigo": row.get("valor"),
                "respuesta": row.get("respuesta_label"),
                "valor": row.get("valor"),
                "ponderador": row.get("ponderador"),
            }
        )
    return pd.DataFrame(rows)


def _from_abiertas(df: pd.DataFrame, pregunta_lookup: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        info = _question_info(pregunta_lookup, row.get("pregunta_id"))
        rows.append(
            {
                "id_respondente": row.get("id_respondente"),
                "pregunta_id": row.get("pregunta_id"),
                "pregunta": info.get("texto_pregunta", ""),
                "variable": row.get("variable"),
                "tipo_pregunta": "Abierta",
                "tipo_calculo": "Texto abierto",
                "item": "",
                "codigo": "",
                "respuesta": row.get("texto_limpio"),
                "valor": "",
                "ponderador": row.get("ponderador"),
            }
        )
    return pd.DataFrame(rows)


def _attach_banners_filters(pivot: pd.DataFrame, respondentes: pd.DataFrame, config: pd.DataFrame) -> pd.DataFrame:
    if pivot.empty:
        return pivot
    result = pivot.copy()
    filtros = _config_variables(config, "filtro")[:2]
    assignments = _banner_assignments(config, respondentes) + [
        (f"filtro_{index}", variable)
        for index, variable in enumerate(filtros, start=1)
    ]
    source_variables = list(
        dict.fromkeys(
            variable
            for _, variable in assignments
            if variable in respondentes.columns
        )
    )
    if respondentes.empty or not source_variables:
        return result

    lookup_variables = [
        variable for variable in source_variables if variable != "id_respondente"
    ]
    temp_names = {
        variable: f"__respondent_attribute_{index}"
        for index, variable in enumerate(lookup_variables)
    }
    respondent_lookup = respondentes.loc[
        :, ~respondentes.columns.duplicated()
    ][["id_respondente", *lookup_variables]].rename(columns=temp_names)
    respondent_lookup = respondent_lookup.drop_duplicates(
        "id_respondente", keep="first"
    )
    result = result.merge(
        respondent_lookup,
        on="id_respondente",
        how="left",
        validate="many_to_one",
    )

    for target, variable in assignments:
        source = (
            "id_respondente"
            if variable == "id_respondente"
            else temp_names.get(variable)
        )
        if source:
            result[target] = result[source]

    return result.drop(columns=list(temp_names.values()), errors="ignore")


def _banner_assignments(
    config: pd.DataFrame, respondentes: pd.DataFrame
) -> list[tuple[str, str]]:
    if respondentes is None or respondentes.empty:
        return []
    reserved = set(BASE_PIVOT_COLUMNS + FILTER_COLUMNS)
    assignments = []
    for variable in _config_variables(config, "banner"):
        if variable not in respondentes.columns:
            continue
        target = variable if variable not in reserved else f"banner_{variable}"
        while target in reserved:
            target = f"banner_{target}"
        reserved.add(target)
        assignments.append((target, variable))
    return assignments


def _config_variables(config: pd.DataFrame, tipo: str) -> list[str]:
    if config is None or config.empty:
        return []
    filtered = config[config["tipo_configuracion"] == tipo]
    variables = [
        variable
        for variable in filtered["variable"].dropna().astype(str).str.strip()
        if variable
    ]
    return list(dict.fromkeys(variables))
