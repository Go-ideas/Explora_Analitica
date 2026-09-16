from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.builder.analytic_db_builder import build_riesgos
from src.database.db_reader import read_table
from src.export.datamap_exporter import save_final_datamap
from src.readers.datamap_reader import (
    get_review_source_sheet,
    normalize_review_datamap,
)
from src.readers.spss_reader import (
    get_missing_ranges,
    get_missing_values,
    get_value_labels,
    get_variable_label,
)
from src.structure.grid_loop_detector import (
    enrich_datamap_with_spss_structure,
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
        st.session_state.review_datamap = (
            enrich_datamap_with_spss_structure(
                review=st.session_state.review_datamap,
                df_spss=df_spss,
                meta_spss=st.session_state.get("meta_spss"),
                datamap_sheets=sheets,
            )
        )
        st.session_state.grid_loop_structures = (
            st.session_state.review_datamap.attrs.get(
                "grid_loop_structures"
            )
        )

    review = st.session_state.review_datamap
    column_config = _review_column_config()
    st.caption(
        "Revisa primero lo esencial. El detalle completo permanece "
        "disponible en la vista técnica."
    )

    (
        variables_tab,
        roles_tab,
        structures_tab,
        factors_tab,
        risks_tab,
        technical_tab,
    ) = st.tabs(
        [
            "Variables principales",
            "Banners y filtros",
            "Estructuras detectadas",
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

    with structures_tab:
        _render_detected_structures()

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
    columns = {
        "variable": "Variable",
        "label": "Label",
        "numero_pregunta": "Pregunta",
        "texto_pregunta": "Texto de la pregunta",
        "tipo_pregunta": "Tipo",
        "clasificacion_analitica": "Rol",
        "seccion_cuestionario": "Sección",
    }
    result = pd.DataFrame()
    for source, target in columns.items():
        result[target] = (
            work[source] if source in work else ""
        )
    return result.reset_index(drop=True)


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
            row,
            [
                "Numero_Pregunta",
                "Pregunta_ID",
                "Pregunta_Padre",
                "Pregunta_Padre_Detectada",
                "Grid_ID",
            ],
        )
        factor_type = _sheet_value(
            row,
            [
                "Tipo_Factor_Recomendado",
                "Factor_Recomendado",
                "Tipo_Score",
                "Tipo_Factor",
            ],
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
                        _sheet_value(
                            row,
                            [
                                "Texto_Pregunta",
                                "Texto_Pregunta_Padre",
                                "Pregunta_Texto",
                                "Factor_Recomendado",
                            ],
                        ),
                    ]
                    if value
                ),
                "Variables fuente": _sheet_value(
                    row,
                    [
                        "Variables_Para_Factor",
                        "Variables_Fuente",
                        "Variables_Items",
                        "Variables",
                    ],
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
                    row,
                    [
                        "Regla_Factor_Sugerida",
                        "Regla",
                        "Formula_Sugerida",
                        "Criterio_Calculo",
                    ],
                ),
                "_justificacion": _sheet_value(
                    row,
                    [
                        "Justificacion_Factor",
                        "Justificacion",
                        "Justificacion_Metodologica",
                    ],
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
    risks = build_riesgos(sheets)
    if risks is None or risks.empty:
        st.success("No hay riesgos metodológicos registrados.")
        return
    summary = pd.DataFrame(
        {
            "Variable / pregunta": risks["variable"].where(
                risks["variable"].astype(str).str.strip().ne(""),
                risks["pregunta_id"],
            ),
            "Tipo de riesgo": risks["tipo_riesgo"],
            "Severidad": risks["prioridad"],
            "Descripción": risks["descripcion"],
            "Acción recomendada": risks["accion_recomendada"],
            "Estado": risks["estatus"],
            "Fuente": risks.get("fuente_hoja", ""),
        }
    )
    summary["_orden"] = summary["Severidad"].map(_severity_order)
    summary = summary.sort_values(["_orden"], kind="stable").drop(
        columns="_orden"
    )
    st.dataframe(
        summary,
        hide_index=True,
        width="stretch",
        height=440,
    )


def _render_detected_structures() -> None:
    structures = st.session_state.get("grid_loop_structures")
    if structures is None or structures.empty:
        st.info(
            "No hay estructuras GRID/LOOP detectadas automáticamente "
            "en esta sesión."
        )
        return
    metric_cols = st.columns(6)
    metric_cols[0].metric("Estructuras", len(structures))
    for index, kind in enumerate(
        [
            "GRID_RM/LOOP_RM",
            "GRID_ESCALA",
            "LOOP_RU",
            "LOOP_NUMERICO",
            "Abierta",
        ],
        start=1,
    ):
        metric_cols[index].metric(
            kind,
            int(
                structures["tipo_estructura_detectada"]
                .astype(str)
                .eq(kind)
                .sum()
            ),
        )

    filters = st.columns(2)
    type_options = [
        "Todas",
        *sorted(
            structures["tipo_estructura_detectada"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
    ]
    selected_type = filters[0].selectbox(
        "Tipo de estructura",
        type_options,
        key="detected_structure_type_filter",
    )
    confidence_options = [
        "Todos",
        *sorted(
            structures["nivel_confianza"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
    ]
    selected_confidence = filters[1].selectbox(
        "Nivel de confianza",
        confidence_options,
        key="detected_structure_confidence_filter",
    )
    filtered = structures.copy()
    if selected_type != "Todas":
        filtered = filtered[
            filtered["tipo_estructura_detectada"].astype(str).eq(
                selected_type
            )
        ]
    if selected_confidence != "Todos":
        filtered = filtered[
            filtered["nivel_confianza"].astype(str).eq(
                selected_confidence
            )
        ]

    columns = {
        "pregunta_padre": "Pregunta padre",
        "tipo_estructura_detectada": "Tipo detectado",
        "filas_detectadas": "Filas",
        "columnas_detectadas": "Columnas",
        "variables_numericas": "Variables numéricas",
        "variables_abiertas_asociadas": "Variables abiertas asociadas",
        "formato_valores": "Formato valores",
        "value_label_patron": "Value label patrón",
        "base_valida_db": "Base válida DB",
        "nivel_confianza": "Nivel de confianza",
        "riesgo": "Riesgo",
        "accion_recomendada": "Acción recomendada",
    }
    visible = pd.DataFrame()
    for source, target in columns.items():
        visible[target] = filtered[source] if source in filtered else ""
    st.dataframe(
        visible,
        hide_index=True,
        width="stretch",
        height=430,
    )
    download_cols = st.columns(2)
    download_cols[0].download_button(
        "Descargar CSV",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="Estructuras_Detectadas.csv",
        mime="text/csv",
        key="download_detected_structures_csv",
    )
    download_cols[1].download_button(
        "Descargar Excel",
        data=_structures_excel_bytes(filtered),
        file_name="Estructuras_Detectadas.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        key="download_detected_structures_xlsx",
    )
    warnings = []
    for _, row in structures.iterrows():
        parent = str(row.get("pregunta_padre") or "").strip()
        risk = str(row.get("riesgo") or "").strip()
        structure = str(row.get("tipo_estructura_detectada") or "").strip()
        opens = str(row.get("variables_abiertas_asociadas") or "").strip()
        if structure == "GRID_RM/LOOP_RM" and opens:
            warnings.append(
                f"{parent}: tiene OT/Otro asociado, pero la pregunta "
                "principal se mantiene como GRID_RM/LOOP_RM."
            )
        if risk:
            warnings.append(f"{parent}: {risk}")
    for warning in dict.fromkeys(warnings):
        st.warning(warning)


def _structures_excel_bytes(frame: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        frame.to_excel(
            writer, sheet_name="Estructuras_Detectadas", index=False
        )
    return output.getvalue()


def _severity_order(value: object) -> int:
    text = str(value or "").strip().casefold()
    mapping = {
        "crítico": 1,
        "critico": 1,
        "alto": 2,
        "alta": 2,
        "medio": 3,
        "media": 3,
        "bajo": 4,
        "baja": 4,
    }
    return mapping.get(text, 99)


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
