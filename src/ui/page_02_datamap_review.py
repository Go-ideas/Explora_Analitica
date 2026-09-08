from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.database.db_reader import read_table
from src.export.datamap_exporter import save_final_datamap
from src.readers.datamap_reader import (
    build_datamap_import_log,
    get_review_source_sheet,
    normalize_review_datamap,
)
from src.readers.spss_reader import (
    get_missing_ranges,
    get_missing_values,
    get_value_labels,
    get_variable_label,
)
from src.reporter.frequency_profile import build_frequency_profile
from src.utils.constants import (
    CLASSIFICATION_OPTIONS,
    DATAMAP_FINAL_FILENAME,
    REVIEW_COLUMNS,
    CALCULATION_OPTIONS,
)
from src.utils.session_paths import session_file
from src.utils.text_utils import find_column, truthy


def render() -> None:
    st.subheader("Revisar Datamap")
    sheets = st.session_state.get("datamap_sheets")
    df_spss = st.session_state.get("df_spss")
    if sheets is None or df_spss is None:
        st.info("Carga primero la base SPSS y el Datamap.")
        return

    if "review_datamap" not in st.session_state:
        _, source = get_review_source_sheet(sheets)
        st.session_state.review_datamap = normalize_review_datamap(
            source, list(df_spss.columns)
        )
    else:
        st.session_state.review_datamap = _refresh_review_metadata(
            st.session_state.review_datamap,
            sheets,
            list(df_spss.columns),
        )
    st.session_state.datamap_import_log = build_datamap_import_log(
        sheets, st.session_state.review_datamap
    )

    review = st.session_state.review_datamap
    column_config = _review_column_config()
    st.caption(
        "Revisa primero lo esencial. El detalle completo permanece "
        "disponible en la vista técnica."
    )
    _render_import_log(st.session_state.get("datamap_import_log"))

    (
        variables_tab,
        roles_tab,
        factors_tab,
        risks_tab,
        technical_tab,
    ) = st.tabs(
        [
            "Variables principales",
            "Banners y filtros",
            "Factores / scores",
            "Riesgos",
            "Vista técnica completa",
        ]
    )

    with variables_tab:
        main_variables = _main_variables(review)
        selection = st.dataframe(
            main_variables,
            width="stretch",
            height=410,
            hide_index=True,
            key="datamap_main_variables",
            on_select="rerun",
            selection_mode="single-row",
        )
        selected_rows = selection.selection.rows
        if selected_rows:
            variable = str(
                main_variables.iloc[selected_rows[0]]["Variable"]
            ).strip()
            if variable in df_spss.columns:
                _render_variable_frequency(
                    variable,
                    df_spss,
                    st.session_state.get("meta_spss"),
                    review,
                )

    with roles_tab:
        _render_roles_review(review)

    with factors_tab:
        _render_factors_review(sheets)

    with risks_tab:
        _render_risks_review(sheets)

    with technical_tab:
        st.caption(
            "Vista completa para auditoría y edición metodológica."
        )
        editor = st.data_editor(
            review,
            width="stretch",
            height=520,
            hide_index=True,
            num_rows="fixed",
            column_config=column_config,
            key="datamap_editor",
        )

        if st.button("Guardar Datamap final", type="primary"):
            try:
                path = session_file(
                    "processed", DATAMAP_FINAL_FILENAME
                )
                save_final_datamap(
                    path,
                    sheets,
                    editor,
                    df_spss=df_spss,
                    meta_spss=st.session_state.get("meta_spss"),
                )
                st.session_state.review_datamap = editor
                st.session_state.datamap_final_path = path
                st.success(f"Datamap guardado: {path.name}")
            except Exception as exc:
                st.error(
                    f"No fue posible guardar el Datamap: {exc}"
                )


def _main_variables(review: pd.DataFrame) -> pd.DataFrame:
    work = review.copy()
    if "usar_en_dashboard" in work:
        active = work["usar_en_dashboard"].apply(truthy)
        if active.any():
            work = work[active]
    result = pd.DataFrame(
        {
            "Variable": _display_column(work, ["variable"]),
            "Label": _display_column(
                work,
                [
                    "label",
                    "label_opcion_rm",
                    "texto_opcion_rm",
                    "opcion_rm",
                    "display_item_reporteador",
                    "texto_pregunta",
                    "variable",
                ],
            ),
            "Pregunta": _display_column(
                work,
                ["numero_pregunta", "pregunta_id", "variable"],
            ),
            "Texto de la pregunta": _display_column(
                work,
                ["texto_pregunta", "label", "variable"],
            ),
            "Tipo": _display_column(
                work,
                ["tipo_pregunta", "tipo_estructura_grid"],
            ),
            "Rol": _display_column(
                work,
                ["clasificacion_analitica"],
            ),
            "Sección": _section_column(work),
        }
    )
    return result.reset_index(drop=True)


def _display_column(
    frame: pd.DataFrame, candidates: list[str]
) -> pd.Series:
    result = pd.Series([""] * len(frame), index=frame.index, dtype="object")
    for column in candidates:
        if column not in frame:
            continue
        incoming = frame[column]
        empty = result.astype(str).str.strip().isin(
            ["", "nan", "None"]
        )
        fillable = (
            empty
            & incoming.notna()
            & ~incoming.astype(str).str.strip().isin(
                ["", "nan", "None"]
            )
        )
        result.loc[fillable] = incoming.loc[fillable]
    return result


def _section_column(frame: pd.DataFrame) -> pd.Series:
    result = _display_column(
        frame,
        [
            "seccion_cuestionario",
            "seccion",
            "bloque_cuestionario",
            "grupo_menu_reporteador",
            "grupo_menu_reporter",
        ],
    )
    empty = result.astype(str).str.strip().isin(["", "nan", "None"])
    questions = _display_column(
        frame,
        ["pregunta_id", "numero_pregunta", "variable"],
    )
    result.loc[empty] = questions.loc[empty].map(_derive_section_name)
    return result


def _derive_section_name(value: object) -> str:
    text = "" if value is None or pd.isna(value) else str(value).strip()
    prefix = text.split("_", 1)[0] if "_" in text else text[:1]
    return f"Sección {prefix.upper()}" if prefix else "General"


def _render_import_log(log: dict | None) -> None:
    if not log:
        return
    summary = log.get("summary", {})
    fields = log.get("fields")
    with st.expander("Log de importación del Datamap", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Hoja usada", summary.get("hoja_usada") or "Sin hoja")
        c2.metric(
            "RM_DICOTOMICA_LABEL",
            summary.get("rm_dicotomica_label_detectadas", 0),
        )
        c3.metric(
            "GRID_RM_LOOP",
            summary.get("grid_rm_loop_detectadas", 0),
        )
        st.caption(
            "Columnas detectadas: "
            f"{summary.get('columnas_detectadas') or 'Sin columnas'}"
        )
        fallback = summary.get("fallback_hoja")
        if fallback:
            st.caption(f"Fallback de hoja: {fallback}")
        missing = summary.get("columnas_faltantes")
        if missing:
            st.caption(f"Columnas faltantes: {missing}")
        if isinstance(fields, pd.DataFrame) and not fields.empty:
            st.dataframe(fields, hide_index=True, width="stretch")


def _refresh_review_metadata(
    review: pd.DataFrame,
    sheets: dict[str, pd.DataFrame],
    spss_columns: list[str],
) -> pd.DataFrame:
    _, source = get_review_source_sheet(sheets)
    refreshed = normalize_review_datamap(source, spss_columns)
    if review is None or review.empty:
        return refreshed
    if refreshed.empty or "variable" not in review:
        return review

    updated = review.copy()
    refreshed_by_variable = (
        refreshed.drop_duplicates("variable")
        .set_index("variable")
    )
    variables = updated["variable"].fillna("").astype(str)
    metadata_columns = [
        "label",
        "pregunta_id",
        "numero_pregunta",
        "texto_pregunta",
        "tipo_pregunta",
        "tipo_estructura_grid",
        "seccion",
        "seccion_cuestionario",
        "bloque_cuestionario",
        "grupo_menu_reporteador",
        "entidad_loop",
        "opcion_rm",
        "label_opcion_rm",
        "texto_opcion_rm",
        "display_item_reporteador",
        "codigo_opcion_rm",
    ]
    for column in metadata_columns:
        if column not in refreshed_by_variable.columns:
            continue
        if column not in updated.columns:
            updated[column] = ""
        incoming = variables.map(refreshed_by_variable[column])
        empty = updated[column].isna() | updated[
            column
        ].astype(str).str.strip().isin(["", "nan", "None"])
        fillable = (
            empty
            & incoming.notna()
            & ~incoming.astype(str).str.strip().isin(
                ["", "nan", "None"]
            )
        )
        if column == "tipo_pregunta":
            incoming_norm = incoming.fillna("").astype(str).map(
                lambda value: value.strip().lower()
            )
            current_norm = updated[column].fillna("").astype(str).map(
                lambda value: value.strip().lower()
            )
            specific_type = incoming_norm.isin(
                ["rm_dicotomica_label", "grid_rm_loop"]
            )
            fillable = fillable | (
                specific_type & current_norm.ne(incoming_norm)
            )
        if fillable.any():
            updated[column] = updated[column].astype("object")
            updated.loc[fillable, column] = incoming.loc[fillable]
    return updated


def _render_roles_review(review: pd.DataFrame) -> None:
    columns = {
        "variable": "Variable",
        "label": "Label",
        "clasificacion_analitica": "Rol",
        "es_banner_recomendado": "Banner recomendado",
        "es_filtro_recomendado": "Filtro recomendado",
        "prioridad_reporteador": "Prioridad",
        "es_banner": "Usar como banner",
        "es_filtro": "Usar como filtro",
    }
    summary = pd.DataFrame(
        {
            target: (
                review[source]
                if source in review
                else False
                if source.startswith("es_")
                else ""
            )
            for source, target in columns.items()
        }
    )
    recommended = (
        summary["Banner recomendado"].apply(truthy)
        | summary["Filtro recomendado"].apply(truthy)
        | summary["Usar como banner"].apply(truthy)
        | summary["Usar como filtro"].apply(truthy)
    )
    summary = summary[recommended].copy()
    summary["Acción"] = "Revisar selección"
    edited = st.data_editor(
        summary,
        hide_index=True,
        width="stretch",
        height=430,
        disabled=[
            column
            for column in summary.columns
            if column not in {"Usar como banner", "Usar como filtro"}
        ],
        column_config={
            "Banner recomendado": st.column_config.CheckboxColumn(),
            "Filtro recomendado": st.column_config.CheckboxColumn(),
            "Usar como banner": st.column_config.CheckboxColumn(),
            "Usar como filtro": st.column_config.CheckboxColumn(),
        },
        key="datamap_role_editor",
    )
    if st.button(
        "Aplicar selección",
        key="apply_datamap_roles",
        type="primary",
    ):
        updated = review.copy()
        by_variable = edited.set_index("Variable")
        names = updated["variable"].astype(str)
        updated["es_banner"] = names.map(
            by_variable["Usar como banner"]
        ).fillna(updated.get("es_banner", False)).apply(truthy)
        updated["es_filtro"] = names.map(
            by_variable["Usar como filtro"]
        ).fillna(updated.get("es_filtro", False)).apply(truthy)
        st.session_state.review_datamap = updated
        st.success("Selección actualizada para la creación de base.")

    if summary.empty:
        return
    variable = st.selectbox(
        "Consultar recomendación",
        summary["Variable"].astype(str).tolist(),
        format_func=lambda value: _summary_label(
            summary, value
        ),
        key="datamap_role_detail",
    )
    selected = review[
        review["variable"].astype(str).eq(variable)
    ].iloc[0]
    with st.expander("Ver justificación", expanded=False):
        _detail_line(
            "Justificación",
            selected.get("justificacion_banner_filtro"),
        )
        _detail_line(
            "Uso comercial",
            selected.get("uso_comercial_sugerido"),
        )
        _detail_line(
            "Riesgo",
            selected.get("riesgo_uso_analitico"),
        )


def _render_factors_review(
    sheets: dict[str, pd.DataFrame],
) -> None:
    factors = sheets.get("12_Factores_Scores_Recomendados")
    if factors is None or factors.empty:
        st.info("Este Datamap no contiene factores sugeridos.")
        return
    factor_config = _factor_config_lookup()
    rows = []
    for _, row in factors.iterrows():
        question = _sheet_value(
            row, ["Numero_Pregunta", "Pregunta_ID"]
        )
        factor_type = _sheet_value(
            row, ["Tipo_Factor_Recomendado"]
        )
        config = factor_config.get(
            (question.casefold(), factor_type.casefold()), {}
        )
        rows.append(
            {
                "Factor sugerido": " · ".join(
                    value
                    for value in [
                        question,
                        _sheet_value(row, ["Texto_Pregunta"]),
                    ]
                    if value
                ),
                "Variables fuente": _sheet_value(
                    row, ["Variables_Para_Factor"]
                ),
                "Tipo de factor": factor_type,
                "Prioridad": _sheet_value(
                    row, ["Prioridad_Factor"]
                ),
                "Estado": (
                    "Activo"
                    if truthy(config.get("activo"))
                    else "Inactivo"
                ),
                "Acción": "Configurar en Reporteador",
                "_regla": _sheet_value(
                    row, ["Regla_Factor_Sugerida"]
                ),
                "_justificacion": _sheet_value(
                    row, ["Justificacion_Factor"]
                ),
            }
        )
    summary = pd.DataFrame(rows)
    st.dataframe(
        summary[
            [
                "Factor sugerido",
                "Variables fuente",
                "Tipo de factor",
                "Prioridad",
                "Estado",
                "Acción",
            ]
        ],
        hide_index=True,
        width="stretch",
        height=430,
    )
    selected_index = st.selectbox(
        "Consultar factor",
        range(len(summary)),
        format_func=lambda index: summary.iloc[index][
            "Factor sugerido"
        ],
        key="datamap_factor_detail",
    )
    with st.expander("Ver regla y justificación", expanded=False):
        row = summary.iloc[selected_index]
        _detail_line("Regla", row["_regla"])
        _detail_line("Justificación", row["_justificacion"])


def _render_risks_review(
    sheets: dict[str, pd.DataFrame],
) -> None:
    risks = sheets.get("09_Riesgos_Priorizados")
    if risks is None or risks.empty:
        st.success("No hay riesgos metodológicos registrados.")
        return
    aliases = {
        "Variable / pregunta": [
            "Variable",
            "Pregunta_ID",
            "Numero_Pregunta",
        ],
        "Riesgo": [
            "Descripcion",
            "Descripción",
            "Detalle",
            "Hallazgo",
            "Tipo_Riesgo",
        ],
        "Severidad": ["Prioridad", "Nivel", "Severidad"],
        "Recomendación": [
            "Accion_Recomendada",
            "Recomendacion",
        ],
        "Estado": ["Estatus", "Status", "Estado"],
    }
    summary = pd.DataFrame()
    for target, candidates in aliases.items():
        source = find_column(risks.columns, candidates)
        summary[target] = risks[source] if source else ""
    st.dataframe(
        summary,
        hide_index=True,
        width="stretch",
        height=440,
    )


def _factor_config_lookup() -> dict[tuple[str, str], dict]:
    db_value = st.session_state.get("db_path")
    if not db_value:
        return {}
    db_path = Path(db_value)
    if not db_path.exists():
        return {}
    try:
        configured = read_table(db_path, "factores_configurados")
    except Exception:
        return {}
    if configured.empty:
        return {}
    return {
        (
            str(row.get("numero_pregunta") or "").casefold(),
            str(row.get("tipo_factor") or "").casefold(),
        ): row.to_dict()
        for _, row in configured.iterrows()
    }


def _sheet_value(row: pd.Series, aliases: list[str]) -> str:
    column = find_column(row.index, aliases)
    if not column:
        return ""
    value = row.get(column)
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _summary_label(frame: pd.DataFrame, variable: str) -> str:
    selected = frame[
        frame["Variable"].astype(str).eq(str(variable))
    ]
    if selected.empty:
        return str(variable)
    label = str(selected.iloc[0].get("Label") or "").strip()
    return f"{variable} — {label}" if label else str(variable)


def _detail_line(label: str, value: object) -> None:
    text = "" if value is None or pd.isna(value) else str(value).strip()
    st.markdown(f"**{label}:** {text or 'Sin información registrada.'}")


def _review_column_config() -> dict:
    return {
        "clasificacion_analitica": st.column_config.SelectboxColumn(
            "Clasificación analítica",
            options=CLASSIFICATION_OPTIONS,
            required=True,
            width="medium",
        ),
        "tipo_calculo": st.column_config.SelectboxColumn(
            "Tipo de cálculo",
            options=CALCULATION_OPTIONS,
            required=True,
            width="medium",
        ),
        "usar_en_dashboard": st.column_config.CheckboxColumn(
            "Dashboard"
        ),
        "es_banner": st.column_config.CheckboxColumn("Banner"),
        "es_filtro": st.column_config.CheckboxColumn("Filtro"),
        "es_ponderador": st.column_config.CheckboxColumn("Ponderador"),
    }


def _render_variable_frequency(
    variable: str,
    df_spss: pd.DataFrame,
    meta_spss,
    review: pd.DataFrame,
) -> None:
    st.markdown(f"#### Frecuencia simple: `{variable}`")
    if meta_spss is None:
        st.info(
            "Vuelve a procesar los archivos para consultar los "
            "metadatos SPSS."
        )
        return

    review_by_variable = (
        review.drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
    )
    row = review_by_variable.get(variable, {})
    variable_label = (
        get_variable_label(meta_spss, variable)
        or row.get("label", "")
        or row.get("texto_pregunta", "")
    )
    if variable_label:
        st.caption(variable_label)

    table, summary = build_frequency_profile(
        df_spss[variable],
        value_labels=get_value_labels(meta_spss, variable),
        missing_values=get_missing_values(meta_spss, variable),
        missing_ranges=get_missing_ranges(meta_spss, variable),
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casos", f"{summary.total:,}")
    c2.metric("Válidos", f"{summary.valid:,}")
    c3.metric("Perdidos", f"{summary.missing:,}")
    c4.metric(
        "Categorías observadas",
        f"{summary.observed_categories:,}",
    )

    detail_left, detail_right = st.columns(2)
    detail_left.caption(
        "Clasificación: "
        f"{row.get('clasificacion_analitica') or 'Sin definir'}"
    )
    detail_right.caption(
        "Tipo de cálculo: "
        f"{row.get('tipo_calculo') or 'Sin definir'}"
    )

    if summary.unlabeled_codes:
        st.warning(
            f"{summary.unlabeled_codes} código(s) sin Value Label "
            f"afectan {summary.unlabeled_observations} caso(s)."
        )
    else:
        st.success(
            "Todos los códigos observados tienen Value Label."
        )
    if summary.zero_frequency_labels:
        st.info(
            f"{summary.zero_frequency_labels} categoría(s) "
            "etiquetada(s) no tienen casos."
        )

    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        height=min(520, 38 + max(len(table), 1) * 35),
        column_config={
            "Código": st.column_config.TextColumn(width="small"),
            "Value Label": st.column_config.TextColumn(
                width="large"
            ),
            "Frecuencia": st.column_config.NumberColumn(
                format="%d"
            ),
            "% válido": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
            "Estado": st.column_config.TextColumn(width="medium"),
        },
    )
