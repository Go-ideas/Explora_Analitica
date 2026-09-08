from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.export.report_exporter import report_to_excel_bytes
from src.export.project_exporter import saved_reports_tables_excel_bytes
from src.database.factor_processor import (
    apply_range_factor,
    default_factor_variable,
    load_factor_source,
    synchronize_inactive_factors,
)
from src.reporter.factors import (
    parse_recommended_ranges,
    range_preview,
    recommended_factor_calculations,
    validate_ranges,
)
from src.reporter.filters import config_entries, filter_choices
from src.reporter.multi_metrics import CALCULATION_OPTIONS
from src.reporter.recommendations import (
    factor_decisions,
    load_factor_recommendations,
    load_factor_configurations,
    merge_factor_configurations,
    save_factor_configurations,
)
from src.reporter.report_store import save_report_snapshot
from src.reporter.table_renderer import render_report_table
from src.reporter.tabulator import (
    ReportResult,
    available_questions,
    generate_report,
)
from src.utils.question_order import resolve_datamap_paths
from src.utils.text_utils import normalize_text


SIGNIFICANCE_OPTIONS = [
    "No mostrar",
    "Integradas en tabla",
    "Tabla separada",
]


def render() -> None:
    st.subheader("Análisis")
    st.caption(
        "Selecciona una pregunta, define la comparación y genera "
        "una tabla lista para presentar."
    )
    db_value = st.session_state.get("db_path")
    if not db_value:
        st.info("Carga primero la base generada por la consola.")
        return
    db_path = Path(db_value)
    if not db_path.exists():
        st.info("Carga primero la base generada por la consola.")
        return
    datamap_paths = _reporter_datamap_paths()
    db_token = _db_cache_token(db_path)
    datamap_token = _datamap_cache_token(datamap_paths)
    questions = _cached_available_questions(
        str(db_path), db_token, datamap_token
    )
    if questions.empty:
        st.warning("No hay preguntas analizables en la base.")
        return
    single_tab, batch_tab = st.tabs(
        ["Tabla individual", "Generación múltiple"]
    )
    with single_tab:
        _render_single_analysis(db_path, datamap_paths, questions)
    with batch_tab:
        _render_batch_analysis(db_path, datamap_paths, questions)

    _render_factor_recommendations(
        db_path,
        datamap_paths,
        st.session_state.get("df_spss"),
    )
    _render_project_map(questions)


def _render_single_analysis(
    db_path: Path,
    datamap_paths: list[Path],
    questions: pd.DataFrame,
) -> None:
    with st.container(border=True):
        st.markdown("### Configuración del análisis")
        settings = _report_controls(
            db_path,
            questions,
            key_prefix="report",
            datamap_paths=datamap_paths,
        )
        update = st.button(
            "Generar tabla",
            type="primary",
            key="generate_report",
        )

    if update:
        try:
            with st.spinner("Calculando reporte..."):
                report = generate_report(db_path=db_path, **settings)
            st.session_state.current_report = report
        except Exception as exc:
            st.error(f"No fue posible generar el reporte: {exc}")

    report = st.session_state.get("current_report")
    if report is None:
        st.info(
            "La tabla aparecerá aquí después de seleccionar la "
            "configuración."
        )
    else:
        render_report(report, key_prefix="report")


def _report_controls(
    db_path: Path,
    questions: pd.DataFrame,
    key_prefix: str,
    significance: bool = False,
    datamap_paths=None,
) -> dict:
    section_questions = questions
    question_labels = {
        str(row["pregunta_id"]): (
            f"{row.get('numero_pregunta_reporter') or row['pregunta_id']}"
            f" | {row.get('tipo_pregunta_reporter') or 'Sin tipo'}"
            f" | {str(row.get('texto_pregunta', '')).strip()}"
        )
        for _, row in section_questions.iterrows()
    }
    question_id = st.selectbox(
        "Pregunta",
        list(question_labels),
        format_func=question_labels.get,
        key=f"{key_prefix}_question",
    )
    selected = section_questions[
        section_questions["pregunta_id"].astype(str) == str(question_id)
    ].iloc[0]
    default_calculations = _default_calculations(
        str(selected.get("tipo_calculo") or "Frecuencia"),
        str(selected.get("tipo_pregunta_reporter") or ""),
    )
    (
        default_calculations,
        factor_default_label,
    ) = _factor_calculation_defaults(
        db_path=db_path,
        datamap_paths=datamap_paths,
        question_id=str(question_id),
        question_type=str(
            selected.get("tipo_pregunta_reporter") or ""
        ),
        base_calculations=default_calculations,
    )

    db_token = _db_cache_token(db_path)
    datamap_token = _datamap_cache_token(datamap_paths)
    banner_entries = _cached_config_entries(
        str(db_path), db_token, "banner", datamap_token
    )
    banner_labels = _variable_labels(banner_entries, "Total")
    banner_options = [
        item for item in banner_labels if item
    ]
    filter_entries = _cached_config_entries(
        str(db_path), db_token, "filtro", datamap_token
    )
    filter_labels = _variable_labels(filter_entries, "Sin filtros")
    available_filters = [
        item for item in filter_labels if item
    ]
    control_columns = st.columns(3)
    with control_columns[0]:
        banners = st.multiselect(
            "Comparar por",
            banner_options,
            default=(
                banner_options[:1]
                if significance and banner_options
                else []
            ),
            format_func=banner_labels.get,
            key=f"{key_prefix}_banners",
            help=(
                "Las opciones recomendadas y de alta prioridad "
                "aparecen primero."
            ),
        )
    with control_columns[1]:
        selected_filters = st.multiselect(
            "Filtrar por",
            available_filters,
            format_func=filter_labels.get,
            key=f"{key_prefix}_filter_variables",
        )
    weight_entries = _cached_config_entries(
        str(db_path), db_token, "ponderador", datamap_token
    )
    weight_labels = _variable_labels(
        weight_entries, "Sin ponderación"
    )
    with control_columns[2]:
        ponderador = st.selectbox(
            "Ponderador",
            list(weight_labels),
            format_func=weight_labels.get,
            key=f"{key_prefix}_weight",
        )

    banner_mode = "nested"
    if len(banners) > 1:
        banner_mode_label = st.radio(
            "Tipo de banner",
            ["Anidados", "No anidados"],
            horizontal=True,
            key=f"{key_prefix}_banner_mode",
            help=(
                "Anidados cruza las variables seleccionadas. "
                "No anidados presenta cada variable por separado "
                "contra Total."
            ),
        )
        banner_mode = (
            "separate"
            if banner_mode_label == "No anidados"
            else "nested"
        )

    filters = {}
    selected_filter_labels = {}
    if selected_filters:
        st.caption("Valores de los filtros")
        filter_columns = st.columns(
            min(len(selected_filters), 3)
        )
        for index, variable in enumerate(selected_filters):
            choices = _cached_filter_choices(
                str(db_path), db_token, str(variable)
            )
            with filter_columns[index % len(filter_columns)]:
                selected_choices = st.multiselect(
                    filter_labels.get(variable, variable),
                    choices,
                    format_func=lambda choice: choice.display,
                    key=(
                        f"{key_prefix}_filter_values_{variable}"
                    ),
                )
            if selected_choices:
                filters[variable] = [
                    choice.value for choice in selected_choices
                ]
                selected_filter_labels[variable] = [
                    choice.display for choice in selected_choices
                ]

    calculation_column, significance_column = st.columns([2, 1])
    with calculation_column:
        calculation_options = _calculation_options_for_question(
            str(selected.get("tipo_pregunta_reporter") or "")
        )
        calculations = st.multiselect(
            "Cálculos",
            calculation_options,
            default=[
                item
                for item in default_calculations
                if item in calculation_options
            ],
            key=f"{key_prefix}_calculations_{question_id}_v2",
        )
    default_sig_index = SIGNIFICANCE_OPTIONS.index(
        "Integradas en tabla"
    )
    with significance_column:
        significance_choice = st.selectbox(
            "Significancia",
            SIGNIFICANCE_OPTIONS,
            index=default_sig_index,
            key=f"{key_prefix}_significance_display",
        )
    if factor_default_label:
        st.caption(
            f"Recomendación de cálculo: {factor_default_label}"
        )

    confidence = 0.95
    min_base = 30
    with st.expander("Opciones avanzadas", expanded=False):
        advanced_columns = st.columns(3)
        response_order = advanced_columns[0].selectbox(
            "Orden de respuestas",
            [
                "Orden de Value Labels",
                "Valor/código",
                "Frecuencia descendente",
            ],
            key=f"{key_prefix}_response_order",
        )
        if significance_choice != "No mostrar":
            confidence_label = advanced_columns[1].selectbox(
                "Nivel de confianza",
                ["90%", "95%", "99%"],
                index=1,
                key=f"{key_prefix}_confidence",
            )
            confidence = {
                "90%": 0.90,
                "95%": 0.95,
                "99%": 0.99,
            }[confidence_label]
            min_base = int(
                advanced_columns[2].number_input(
                    "Base mínima por columna",
                    min_value=2,
                    max_value=1000,
                    value=30,
                    step=1,
                    key=f"{key_prefix}_min_base",
                )
            )
        if selected_filters:
            st.button(
                "Limpiar filtros",
                key=f"{key_prefix}_clear_filters",
                on_click=_clear_filter_state,
                args=(key_prefix,),
            )

    recommendation_details = _selected_recommendation_details(
        [
            (banner_entries, banners),
            (filter_entries, selected_filters),
        ]
    )
    return {
        "question_id": question_id,
        "banner": banners,
        "banner_mode": banner_mode,
        "ponderador": ponderador or None,
        "calculations": calculations,
        "response_order": response_order,
        "filters": filters,
        "filter_labels": selected_filter_labels,
        "significance_display": significance_choice,
        "confidence": confidence,
        "min_base": min_base,
        "question_order": (
            float(selected["orden_reporter"])
            if pd.notna(selected.get("orden_reporter"))
            else None
        ),
        "recommended_banners": _recommended_selection(
            banner_entries, banners
        ),
        "recommended_filters": _recommended_selection(
            filter_entries, selected_filters
        ),
        "recommendation_details": recommendation_details,
    }


def _render_batch_analysis(
    db_path: Path,
    datamap_paths: list[Path],
    questions: pd.DataFrame,
) -> None:
    with st.container(border=True):
        st.markdown("### Generación múltiple")
        selected_questions, settings = _batch_controls(
            db_path, questions, datamap_paths
        )
        preview = _batch_preview(
            db_path, datamap_paths, questions, selected_questions
        )
        if not preview.empty:
            st.dataframe(
                preview,
                hide_index=True,
                width="stretch",
                height=min(420, 78 + len(preview) * 35),
            )
        generate = st.button(
            "Generar tablas seleccionadas",
            type="primary",
            disabled=not selected_questions,
            key="batch_generate_reports",
        )

    if generate:
        _run_batch_generation(
            db_path,
            datamap_paths,
            questions,
            selected_questions,
            settings,
        )

    _render_batch_status()


def _batch_controls(
    db_path: Path,
    questions: pd.DataFrame,
    datamap_paths: list[Path],
) -> tuple[list[str], dict]:
    type_options = (
        questions["tipo_pregunta_reporter"]
        .fillna("Sin tipo")
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    selected_types = st.multiselect(
        "Tipos de pregunta",
        type_options,
        default=type_options,
        key="batch_question_types",
    )
    filtered = questions[
        questions["tipo_pregunta_reporter"]
        .fillna("Sin tipo")
        .astype(str)
        .isin(selected_types)
    ].copy()
    question_labels = _question_labels(filtered)
    selected_questions = st.multiselect(
        "Preguntas",
        list(question_labels),
        format_func=question_labels.get,
        key="batch_questions",
    )

    db_token = _db_cache_token(db_path)
    datamap_token = _datamap_cache_token(datamap_paths)
    banner_entries = _cached_config_entries(
        str(db_path), db_token, "banner", datamap_token
    )
    filter_entries = _cached_config_entries(
        str(db_path), db_token, "filtro", datamap_token
    )
    weight_entries = _cached_config_entries(
        str(db_path), db_token, "ponderador", datamap_token
    )
    banner_labels = _variable_labels(banner_entries, "Total")
    filter_labels = _variable_labels(filter_entries, "Sin filtros")
    weight_labels = _variable_labels(weight_entries, "Sin ponderación")

    common = st.columns(3)
    with common[0]:
        banners = st.multiselect(
            "Comparar por",
            [item for item in banner_labels if item],
            format_func=banner_labels.get,
            key="batch_banners",
        )
    with common[1]:
        selected_filters = st.multiselect(
            "Filtrar por",
            [item for item in filter_labels if item],
            format_func=filter_labels.get,
            key="batch_filter_variables",
        )
    with common[2]:
        ponderador = st.selectbox(
            "Ponderador",
            list(weight_labels),
            format_func=weight_labels.get,
            key="batch_weight",
        )

    banner_mode = "nested"
    if len(banners) > 1:
        banner_mode_label = st.radio(
            "Tipo de banner",
            ["Anidados", "No anidados"],
            horizontal=True,
            key="batch_banner_mode",
        )
        banner_mode = (
            "separate"
            if banner_mode_label == "No anidados"
            else "nested"
        )

    filters = {}
    selected_filter_labels = {}
    if selected_filters:
        st.caption("Valores de los filtros")
        filter_columns = st.columns(
            min(len(selected_filters), 3)
        )
        for index, variable in enumerate(selected_filters):
            choices = _cached_filter_choices(
                str(db_path), db_token, str(variable)
            )
            with filter_columns[index % len(filter_columns)]:
                selected_choices = st.multiselect(
                    filter_labels.get(variable, variable),
                    choices,
                    format_func=lambda choice: choice.display,
                    key=f"batch_filter_values_{variable}",
                )
            if selected_choices:
                filters[variable] = [
                    choice.value for choice in selected_choices
                ]
                selected_filter_labels[variable] = [
                    choice.display for choice in selected_choices
                ]

    options = st.columns(4)
    with options[0]:
        response_order = st.selectbox(
            "Orden de respuestas",
            [
                "Orden de Value Labels",
                "Valor/código",
                "Frecuencia descendente",
            ],
            key="batch_response_order",
        )
    with options[1]:
        significance_choice = st.selectbox(
            "Significancia",
            SIGNIFICANCE_OPTIONS,
            index=SIGNIFICANCE_OPTIONS.index("No mostrar"),
            key="batch_significance_display",
        )
    confidence = 0.95
    min_base = 30
    if significance_choice != "No mostrar":
        with options[2]:
            confidence_label = st.selectbox(
                "Nivel de confianza",
                ["90%", "95%", "99%"],
                index=1,
                key="batch_confidence",
            )
            confidence = {
                "90%": 0.90,
                "95%": 0.95,
                "99%": 0.99,
            }[confidence_label]
        with options[3]:
            min_base = int(
                st.number_input(
                    "Base mínima",
                    min_value=2,
                    max_value=1000,
                    value=30,
                    step=1,
                    key="batch_min_base",
                )
            )

    return selected_questions, {
        "banner": banners,
        "banner_mode": banner_mode,
        "ponderador": ponderador or None,
        "response_order": response_order,
        "filters": filters,
        "filter_labels": selected_filter_labels,
        "significance_display": significance_choice,
        "confidence": confidence,
        "min_base": min_base,
        "banner_entries": banner_entries,
        "filter_entries": filter_entries,
    }


def _question_labels(questions: pd.DataFrame) -> dict[str, str]:
    return {
        str(row["pregunta_id"]): (
            f"{row.get('numero_pregunta_reporter') or row['pregunta_id']}"
            f" | {row.get('tipo_pregunta_reporter') or 'Sin tipo'}"
            f" | {str(row.get('texto_pregunta', '')).strip()}"
        )
        for _, row in questions.iterrows()
    }


def _batch_preview(
    db_path: Path,
    datamap_paths: list[Path],
    questions: pd.DataFrame,
    selected_questions: list[str],
) -> pd.DataFrame:
    if not selected_questions:
        return pd.DataFrame()
    rows = []
    selected = questions[
        questions["pregunta_id"].astype(str).isin(selected_questions)
    ]
    for _, row in selected.iterrows():
        question_id = str(row.get("pregunta_id") or "")
        question_type = str(row.get("tipo_pregunta_reporter") or "")
        calculations = _batch_calculations_for_question(
            db_path, datamap_paths, row
        )
        rows.append(
            {
                "Pregunta": question_id,
                "Tipo": question_type,
                "Cálculos": ", ".join(calculations),
                "Sección": row.get("seccion_reporter") or "",
                "Texto": str(row.get("texto_pregunta") or "")[:180],
            }
        )
    return pd.DataFrame(rows)


def _batch_calculations_for_question(
    db_path: Path,
    datamap_paths: list[Path],
    row: pd.Series,
) -> list[str]:
    question_type = str(row.get("tipo_pregunta_reporter") or "")
    base = _default_calculations(
        str(row.get("tipo_calculo") or "Frecuencia"),
        question_type,
    )
    calculations, _ = _factor_calculation_defaults(
        db_path=db_path,
        datamap_paths=datamap_paths,
        question_id=str(row.get("pregunta_id") or ""),
        question_type=question_type,
        base_calculations=base,
    )
    available = _calculation_options_for_question(question_type)
    return [item for item in calculations if item in available]


def _run_batch_generation(
    db_path: Path,
    datamap_paths: list[Path],
    questions: pd.DataFrame,
    selected_questions: list[str],
    settings: dict,
) -> None:
    saved = st.session_state.get("saved_reports", [])
    selected = questions[
        questions["pregunta_id"].astype(str).isin(selected_questions)
    ].copy()
    progress = st.progress(0)
    statuses = []
    for index, (_, row) in enumerate(selected.iterrows(), start=1):
        question_id = str(row.get("pregunta_id") or "")
        try:
            calculations = _batch_calculations_for_question(
                db_path, datamap_paths, row
            )
            report = generate_report(
                db_path=db_path,
                question_id=question_id,
                banner=settings["banner"],
                banner_mode=settings["banner_mode"],
                ponderador=settings["ponderador"],
                calculations=calculations,
                response_order=settings["response_order"],
                filters=settings["filters"],
                filter_labels=settings["filter_labels"],
                significance_display=settings["significance_display"],
                confidence=settings["confidence"],
                min_base=settings["min_base"],
                question_order=(
                    float(row["orden_reporter"])
                    if pd.notna(row.get("orden_reporter"))
                    else None
                ),
                recommended_banners=_recommended_selection(
                    settings["banner_entries"], settings["banner"]
                ),
                recommended_filters=_recommended_selection(
                    settings["filter_entries"],
                    list(settings["filters"]),
                ),
                recommendation_details=_selected_recommendation_details(
                    [
                        (
                            settings["banner_entries"],
                            settings["banner"],
                        ),
                        (
                            settings["filter_entries"],
                            list(settings["filters"]),
                        ),
                    ]
                ),
            )
            if report.table.empty:
                statuses.append(
                    {
                        "Pregunta": question_id,
                        "Estado": "Sin resultados",
                        "Detalle": "No se generó tabla para la selección.",
                    }
                )
            else:
                name = f"{question_id} · {report.title}"[:160]
                saved = save_report_snapshot(saved, report, name)
                statuses.append(
                    {
                        "Pregunta": question_id,
                        "Estado": "Guardada",
                        "Detalle": (
                            f"{report.question_type}; base "
                            f"{report.base:,}; "
                            f"{len(report.table):,} filas"
                        ),
                    }
                )
        except Exception as exc:
            statuses.append(
                {
                    "Pregunta": question_id,
                    "Estado": "Error",
                    "Detalle": str(exc),
                }
            )
        progress.progress(index / max(len(selected), 1))
    st.session_state.saved_reports = saved
    st.session_state.batch_generation_status = statuses
    st.success(
        "Generación múltiple terminada. Las tablas válidas quedaron "
        "guardadas para exportación."
    )


def _render_batch_status() -> None:
    statuses = st.session_state.get("batch_generation_status")
    if not statuses:
        return
    status_df = pd.DataFrame(statuses)
    with st.expander("Resultado de generación múltiple", expanded=True):
        st.dataframe(status_df, hide_index=True, width="stretch")
        saved_reports = st.session_state.get("saved_reports", [])
        if saved_reports:
            st.download_button(
                "Descargar todas las tablas en un solo Excel",
                data=saved_reports_tables_excel_bytes(saved_reports),
                file_name="Todas_las_tablas_Explora.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                type="primary",
                key="batch_download_all_tables_excel",
            )


def render_report(report: ReportResult, key_prefix: str) -> None:
    st.divider()
    with st.container(border=True):
        st.caption(
            f"{report.question_id} · {report.question_type}"
        )
        st.markdown(f"### {report.title}")
        first_row = st.columns(4)
        first_row[0].metric("Base válida", f"{report.base:,}")
        rm_kpis = _rm_summary_kpis(report)
        if rm_kpis:
            first_row[0].caption(
                "Total de menciones: "
                f"{rm_kpis['total_menciones']:,} · "
                "Promedio: "
                f"{rm_kpis['promedio_menciones']:.2f}"
            )
        first_row[1].metric("Sección", report.section or "General")
        first_row[2].metric(
            "Comparar por",
            ", ".join(report.banners) if report.banners else "Total",
        )
        if len(report.banners) > 1:
            first_row[2].caption(
                "No anidados"
                if report.banner_mode == "separate"
                else "Anidados"
            )
        first_row[3].metric(
            "Ponderador", report.ponderador or "Sin ponderación"
        )
        second_row = st.columns(3)
        second_row[0].metric(
            "Filtros aplicados", len(report.filters)
        )
        second_row[1].metric(
            "Cálculos", len(report.calculations)
        )
        second_row[1].caption(
            ", ".join(report.calculations) or "Sin cálculos"
        )
        second_row[2].metric(
            "Significancia",
            {
                "integrated": "Integrada",
                "separate": "Tabla separada",
                "none": "No mostrar",
            }.get(report.significance_display, "No mostrar"),
        )

    for warning in report.warnings:
        st.warning(warning)
    if report.table.empty:
        st.warning("No hay resultados para la selección actual.")
        return

    st.markdown("### Tabla")
    column_letters = {
        str(row["Columna"]): str(row["Letra"])
        for _, row in report.significance_legend.iterrows()
    }
    render_report_table(
        report.table,
        column_letters=column_letters,
    )
    if (
        report.significance_display == "separate"
        and not report.significance.empty
    ):
        render_report_table(
            report.significance,
            title="Diferencias significativas",
        )
        if not report.significance_legend.empty:
            render_report_table(
                report.significance_legend,
                title="Clave de columnas",
            )

    st.markdown("### Gráfico")
    if report.figure is not None:
        st.plotly_chart(
            report.figure,
            width="stretch",
            config={
                "displaylogo": False,
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": f"{report.question_id}_grafico",
                    "scale": 2,
                },
            },
        )
    else:
        st.info("No hay gráfico disponible para esta selección.")

    st.download_button(
        "Exportar análisis ejecutivo",
        data=report_to_excel_bytes(report),
        file_name=f"{report.question_id}_Reporte_Explora.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_download_{report.question_id}",
    )
    _render_save_analysis(report, key_prefix)
    _render_methodology(report)


def _render_save_analysis(
    report: ReportResult, key_prefix: str
) -> None:
    saved = st.session_state.get("saved_reports", [])
    with st.container(border=True):
        st.markdown("**Guardar para exportar después**")
        name_column, action_column = st.columns([4, 1])
        default_name = (
            f"{report.question_id} · {report.title}"
        )[:140]
        name = name_column.text_input(
            "Nombre del análisis",
            value=default_name,
            key=(
                f"{key_prefix}_save_name_"
                f"{report.question_id}"
            ),
        )
        if action_column.button(
            "Guardar tabla y gráfico",
            type="primary",
            key=(
                f"{key_prefix}_save_report_"
                f"{report.question_id}"
            ),
            width="stretch",
        ):
            saved = save_report_snapshot(
                saved, report, name
            )
            st.session_state.saved_reports = saved
            st.success(
                "Análisis guardado. Puedes administrarlo en "
                "Exportar."
            )
        st.caption(
            f"Análisis guardados en esta sesión: {len(saved)}"
        )


def _render_methodology(report: ReportResult) -> None:
    with st.expander(
        "¿Por qué se recomienda este banner?",
        expanded=False,
    ):
        _render_selected_recommendations(
            report, report.banners
        )
    with st.expander(
        "¿Por qué se recomienda este filtro?",
        expanded=False,
    ):
        _render_selected_recommendations(
            report, list(report.filters)
        )
    with st.expander("Notas de cálculo", expanded=False):
        calculation_notes = [
            note
            for note in report.notes
            if "signific" not in normalize_text(note)
        ]
        _render_notes(calculation_notes)
    with st.expander("Notas de significancia", expanded=False):
        if report.significance_display == "none":
            st.caption(
                "No se solicitaron diferencias significativas."
            )
        else:
            st.write(
                f"Nivel de confianza: "
                f"{report.confidence:.0%}."
            )
            st.write(
                f"Base mínima por columna: "
                f"{report.min_base or 0:,}."
            )
            significance_notes = [
                note
                for note in report.notes
                if "signific" in normalize_text(note)
            ]
            _render_notes(significance_notes)
    with st.expander(
        "Base válida y filtros aplicados", expanded=False
    ):
        st.write(f"Base válida: {report.base:,} casos.")
        st.write(
            "Base antes de filtros: "
            f"{(report.base_before_filters or report.base):,} casos."
        )
        st.write(
            f"Filtros: {report.filter_summary or 'Sin filtros'}."
        )
        st.write(
            f"Orden de respuestas: {report.response_order}."
        )
    with st.expander("Riesgos metodológicos", expanded=False):
        risks = []
        for variable in [*report.banners, *report.filters]:
            details = report.recommendation_details.get(
                variable, {}
            )
            risk = str(
                details.get("riesgo_analitico") or ""
            ).strip()
            if risk and risk.lower() not in {"nan", "none"}:
                risks.append(f"{variable}: {risk}")
        risks.extend(report.warnings)
        _render_notes(list(dict.fromkeys(risks)))


def _render_selected_recommendations(
    report: ReportResult, variables: list[str]
) -> None:
    if not variables:
        st.caption("No hay variables seleccionadas.")
        return
    shown = False
    for variable in variables:
        details = report.recommendation_details.get(variable, {})
        justification = str(
            details.get("justificacion") or ""
        ).strip()
        use = str(details.get("uso_comercial") or "").strip()
        if not justification and not use:
            continue
        shown = True
        st.markdown(f"**{variable}**")
        if justification:
            st.write(justification)
        if use:
            st.caption(f"Uso sugerido: {use}")
        distribution = str(
            details.get("distribucion_base") or ""
        ).strip()
        if distribution:
            st.caption(
                f"Base por categoría: {distribution}"
            )
    if not shown:
        st.caption("No hay justificación registrada.")


def _render_notes(notes: list[str]) -> None:
    if not notes:
        st.caption("Sin notas adicionales.")
        return
    for note in notes:
        st.write(f"- {note}")


def _variable_labels(
    entries: pd.DataFrame, empty_label: str
) -> dict[str, str]:
    labels = {"": empty_label}
    if entries.empty:
        return labels
    for _, row in entries.iterrows():
        variable = str(row.get("variable", "")).strip()
        if not variable:
            continue
        label = str(row.get("label", "") or "").strip()
        display = (
            f"{variable} | {label}" if label and label != variable else variable
        )
        markers = []
        if bool(row.get("es_recomendado", False)):
            markers.append("Recomendado")
        relevance = normalize_text(
            row.get("nivel_relevancia")
        )
        if "alta" in relevance:
            markers.append("Alta prioridad")
        risk = str(row.get("riesgo_analitico") or "").strip()
        if risk and normalize_text(risk) not in {
            "sin_riesgo",
            "sin_riesgo_registrado",
            "nan",
            "none",
        }:
            markers.append("⚠ Revisar")
        if markers:
            display = f"{display} · {' · '.join(markers)}"
        labels[variable] = display
    return labels


def _db_cache_token(db_path: Path) -> tuple[int, int]:
    stat = db_path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def _datamap_cache_token(paths) -> tuple[tuple[str, int, int], ...]:
    token = []
    for path in paths or []:
        path = Path(path)
        if path.exists():
            stat = path.stat()
            token.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(token)


def _paths_from_token(
    token: tuple[tuple[str, int, int], ...],
) -> list[Path]:
    return [Path(path) for path, _, _ in token]


@st.cache_data(show_spinner=False)
def _cached_available_questions(
    db_path: str,
    db_token: tuple[int, int],
    datamap_token: tuple[tuple[str, int, int], ...],
) -> pd.DataFrame:
    return available_questions(
        Path(db_path), _paths_from_token(datamap_token)
    )


@st.cache_data(show_spinner=False)
def _cached_config_entries(
    db_path: str,
    db_token: tuple[int, int],
    kind: str,
    datamap_token: tuple[tuple[str, int, int], ...],
) -> pd.DataFrame:
    return config_entries(
        Path(db_path), kind, _paths_from_token(datamap_token)
    )


@st.cache_data(show_spinner=False)
def _cached_filter_choices(
    db_path: str,
    db_token: tuple[int, int],
    variable: str,
) -> list:
    return filter_choices(Path(db_path), variable)


@st.cache_data(show_spinner=False)
def _cached_factor_recommendations(
    datamap_token: tuple[tuple[str, int, int], ...],
) -> pd.DataFrame:
    return load_factor_recommendations(_paths_from_token(datamap_token))


@st.cache_data(show_spinner=False)
def _cached_factor_configurations(
    db_path: str,
    db_token: tuple[int, int],
) -> pd.DataFrame:
    return load_factor_configurations(Path(db_path))


@st.cache_data(show_spinner=False)
def _cached_factor_decisions(
    db_path: str,
    db_token: tuple[int, int],
) -> dict[str, bool]:
    return factor_decisions(Path(db_path))


def _render_recommendation_explanations(
    entries: pd.DataFrame,
    selected_variables: list[str],
    kind: str,
) -> None:
    if entries.empty or not selected_variables:
        return
    selected = entries[
        entries["variable"].astype(str).isin(selected_variables)
        & entries["es_recomendado"].astype(bool)
    ]
    if selected.empty:
        return
    label = (
        "¿Por qué se recomienda este banner?"
        if kind == "banner"
        else "¿Por qué se recomienda este filtro?"
    )
    with st.expander(label):
        for _, row in selected.iterrows():
            st.markdown(f"**{row['variable']}**")
            details = [
                ("Justificación", row.get("justificacion")),
                ("Uso comercial", row.get("uso_comercial")),
                (
                    "Base por categoría",
                    row.get("distribucion_base"),
                ),
                ("Relevancia", row.get("nivel_relevancia")),
                ("Riesgo analítico", row.get("riesgo_analitico")),
            ]
            shown = False
            for detail_label, value in details:
                text = str(value or "").strip()
                if text and text.lower() not in {"nan", "none"}:
                    st.caption(f"{detail_label}: {text}")
                    shown = True
            if not shown:
                st.caption(
                    "Recomendado por la configuración analítica "
                    "vigente."
                )


def _recommended_selection(
    entries: pd.DataFrame, selected: list[str]
) -> list[str]:
    if entries.empty or not selected:
        return []
    return (
        entries.loc[
            entries["variable"].astype(str).isin(selected)
            & entries["es_recomendado"].astype(bool),
            "variable",
        ]
        .astype(str)
        .tolist()
    )


def _selected_recommendation_details(
    selections: list[tuple[pd.DataFrame, list[str]]],
) -> dict[str, dict[str, str]]:
    details = {}
    for entries, selected in selections:
        if entries.empty:
            continue
        for _, row in entries[
            entries["variable"].astype(str).isin(selected)
        ].iterrows():
            variable = str(row["variable"])
            details[variable] = {
                "recomendado": (
                    "Sí"
                    if bool(row.get("es_recomendado", False))
                    else "No"
                ),
                "justificacion": str(
                    row.get("justificacion") or ""
                ),
                "uso_comercial": str(
                    row.get("uso_comercial") or ""
                ),
                "distribucion_base": str(
                    row.get("distribucion_base") or ""
                ),
                "nivel_relevancia": str(
                    row.get("nivel_relevancia") or ""
                ),
                "riesgo_analitico": str(
                    row.get("riesgo_analitico") or ""
                ),
            }
    return details


def _render_factor_recommendations(
    db_path: Path,
    datamap_paths: list[Path],
    df_spss: pd.DataFrame | None = None,
) -> None:
    with st.expander(
        "Factores y scores sugeridos", expanded=False
    ):
        db_token = _db_cache_token(db_path)
        datamap_token = _datamap_cache_token(datamap_paths)
        factors = _cached_factor_recommendations(datamap_token)
        if factors.empty:
            st.caption(
                "El Datamap actual no contiene recomendaciones de "
                "factores o scores."
            )
            return
        saved = _cached_factor_configurations(str(db_path), db_token)
        factors = merge_factor_configurations(factors, saved)
        decisions = _cached_factor_decisions(str(db_path), db_token)
        summary = pd.DataFrame(
            {
                "_factor_id": factors["_factor_id"].astype(str),
                "Activo": factors["_factor_id"]
                .astype(str)
                .map(
                    lambda factor_id: bool(
                        decisions.get(factor_id, False)
                    )
                ),
                "Nombre del factor": factors.apply(
                    _factor_display_name, axis=1
                ),
                "Tipo": factors.get(
                    "Tipo_Factor_Recomendado", ""
                ),
                "Prioridad": factors.get(
                    "Prioridad_Factor", ""
                ),
            }
        )
        summary["Estado"] = summary["Activo"].map(
            {True: "Activo", False: "Inactivo"}
        )
        edited_summary = st.data_editor(
            summary,
            column_order=[
                "Activo",
                "Nombre del factor",
                "Tipo",
                "Prioridad",
                "Estado",
            ],
            hide_index=True,
            width="stretch",
            height=min(460, 78 + len(summary) * 35),
            disabled=[
                "Nombre del factor",
                "Tipo",
                "Prioridad",
                "Estado",
            ],
            column_config={
                "Activo": st.column_config.CheckboxColumn(
                    "Activar", width="small",
                ),
            },
            key="factor_score_editor",
        )
        st.caption(
            "Activar registra la decisión. Los factores solo se "
            "materializan cuando confirmas su procesamiento."
        )

        editor = factors.copy()
        active_by_id = edited_summary.set_index("_factor_id")[
            "Activo"
        ].to_dict()
        editor.insert(
            0,
            "Activo",
            editor["_factor_id"]
            .astype(str)
            .map(active_by_id)
            .fillna(False)
            .astype(bool),
        )
        factor_labels = {
            str(row["_factor_id"]): _factor_display_name(row)
            for _, row in editor.iterrows()
        }
        selected_factor_id = st.selectbox(
            "Consultar o editar factor",
            list(factor_labels),
            format_func=factor_labels.get,
            key="factor_detail_selector",
        )
        selected_mask = editor["_factor_id"].astype(str).eq(
            selected_factor_id
        )
        selected_index = editor.index[selected_mask][0]
        show_detail = st.toggle(
            "Ver o editar regla y justificación",
            value=False,
            key="show_factor_detail",
        )
        if show_detail:
            st.markdown("**Detalle del factor**")
            detail_fields = [
                (
                    "Variables fuente",
                    "Variables_Para_Factor",
                ),
                (
                    "Regla",
                    "Regla_Factor_Sugerida",
                ),
                (
                    "Justificación",
                    "Justificacion_Factor",
                ),
                (
                    "Uso comercial sugerido",
                    "Uso_Comercial_Sugerido",
                ),
            ]
            for label, column in detail_fields:
                if column not in editor:
                    editor[column] = ""
                editor.at[selected_index, column] = st.text_area(
                    label,
                    value=str(
                        editor.at[selected_index, column] or ""
                    ),
                    key=(
                        f"factor_detail_"
                        f"{normalize_text(selected_factor_id)}_"
                        f"{normalize_text(column)}"
                    ),
                    height=70,
                )

        saved_lookup = (
            saved.set_index("factor_id").to_dict("index")
            if not saved.empty
            else {}
        )
        range_configurations: dict[
            str, list[dict[str, object]]
        ] = {}
        active_factors = editor[
            editor["Activo"].fillna(False).astype(bool)
        ]
        for index, row in active_factors.iterrows():
            factor_id = str(row["_factor_id"])
            factor_type = str(
                row.get("Tipo_Factor_Recomendado") or ""
            )
            if "rango" not in normalize_text(factor_type):
                continue
            show_processor = st.toggle(
                f"Configurar rangos: "
                f"{factor_labels.get(factor_id, factor_id)}",
                value=False,
                key=f"show_processor_{normalize_text(factor_id)}",
            )
            if show_processor:
                _render_numeric_range_factor(
                    db_path=db_path,
                    df_spss=df_spss,
                    factor_row=row,
                    row_index=index,
                    saved_row=saved_lookup.get(factor_id, {}),
                    all_factors=editor,
                    range_configurations=range_configurations,
                )

        if st.button(
            "Guardar configuración de factores/scores",
            key="save_factor_score_decisions",
            type="primary",
        ):
            try:
                save_factor_configurations(
                    db_path,
                    editor,
                    range_configurations,
                )
                synchronized = synchronize_inactive_factors(
                    db_path
                )
                if synchronized["tables"]:
                    st.session_state.analytic_tables = (
                        synchronized["tables"]
                    )
                st.success(
                    "Configuraciones y decisiones guardadas."
                )
            except Exception as exc:
                st.error(
                    "No fue posible guardar la configuración: "
                    f"{exc}"
                )


def _factor_display_name(row: pd.Series) -> str:
    number = str(row.get("Numero_Pregunta") or "").strip()
    text = str(row.get("Texto_Pregunta") or "").strip()
    factor_type = str(
        row.get("Tipo_Factor_Recomendado") or ""
    ).strip()
    title = " · ".join(
        value for value in [number, text] if value
    )
    return title or factor_type or "Factor sugerido"


def _render_numeric_range_factor(
    db_path: Path,
    df_spss: pd.DataFrame | None,
    factor_row: pd.Series,
    row_index: int,
    saved_row: dict,
    all_factors: pd.DataFrame,
    range_configurations: dict[str, list[dict[str, object]]],
) -> None:
    factor_id = str(factor_row["_factor_id"])
    question = str(
        factor_row.get("Numero_Pregunta") or factor_id
    )
    factor_type = str(
        factor_row.get("Tipo_Factor_Recomendado")
        or "Factor por rangos"
    )
    source_text = str(
        factor_row.get("Variables_Para_Factor") or ""
    )
    source_variable = next(
        (
            item.strip()
            for item in source_text.replace(";", ",").split(",")
            if item.strip()
        ),
        "",
    )
    widget_key = f"{normalize_text(factor_id)}_{row_index}"
    with st.container(border=True):
        st.markdown(f"#### Configurar {question} · {factor_type}")
        st.caption(
            str(factor_row.get("Regla_Factor_Sugerida") or "")
        )

        default_ranges = _saved_factor_ranges(saved_row)
        if not default_ranges:
            default_ranges = parse_recommended_ranges(
                factor_row.get("Regla_Factor_Sugerida")
            )
        if not default_ranges:
            default_ranges = [
                {
                    "Incluir": True,
                    "Etiqueta": "Rango 1",
                    "Mínimo": None,
                    "Máximo": None,
                }
            ]
        ranges_editor = st.data_editor(
            pd.DataFrame(default_ranges),
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            column_order=[
                "Incluir",
                "Etiqueta",
                "Mínimo",
                "Máximo",
            ],
            column_config={
                "Incluir": st.column_config.CheckboxColumn(
                    width="small"
                ),
                "Etiqueta": st.column_config.TextColumn(
                    width="medium", required=True
                ),
                "Mínimo": st.column_config.NumberColumn(
                    format="%.2f"
                ),
                "Máximo": st.column_config.NumberColumn(
                    format="%.2f"
                ),
            },
            key=f"factor_ranges_{widget_key}",
        )

        valid_ranges = None
        try:
            valid_ranges = validate_ranges(ranges_editor)
            range_configurations[factor_id] = valid_ranges
            source_values = load_factor_source(
                db_path, source_variable, df_spss
            )
            preview = range_preview(source_values, valid_ranges)
            st.dataframe(
                preview,
                hide_index=True,
                width="stretch",
                column_config={
                    "Frecuencia": st.column_config.NumberColumn(
                        format="%d"
                    ),
                    "%": st.column_config.NumberColumn(
                        format="%.1f%%"
                    ),
                },
            )
        except Exception as exc:
            source_values = None
            st.warning(f"Revisa la configuración: {exc}")

        default_variable = (
            str(saved_row.get("variable_derivada") or "")
            or default_factor_variable(source_variable or question)
        )
        name_col, role_col = st.columns([2, 1])
        factor_variable = name_col.text_input(
            "Nombre de variable derivada",
            value=default_variable,
            key=f"factor_variable_{widget_key}",
        )
        factor_label = name_col.text_input(
            "Etiqueta del factor",
            value=f"{question} · {factor_type}",
            key=f"factor_label_{widget_key}",
        )
        as_banner = role_col.checkbox(
            "Disponible como banner",
            value=_saved_bool(saved_row, "como_banner", True),
            key=f"factor_banner_{widget_key}",
        )
        as_filter = role_col.checkbox(
            "Disponible como filtro",
            value=_saved_bool(saved_row, "como_filtro", True),
            key=f"factor_filter_{widget_key}",
        )

        if st.button(
            "Procesar y agregar como pregunta al reporteador",
            key=f"process_factor_{widget_key}",
            disabled=valid_ranges is None or source_values is None,
        ):
            try:
                save_factor_configurations(
                    db_path,
                    all_factors,
                    range_configurations,
                )
                synchronize_inactive_factors(db_path)
                result = apply_range_factor(
                    db_path=db_path,
                    source_values=source_values,
                    source_variable=source_variable,
                    factor_variable=factor_variable.strip(),
                    factor_label=factor_label.strip(),
                    factor_id=factor_id,
                    ranges=valid_ranges,
                    as_banner=as_banner,
                    as_filter=as_filter,
                )
                st.session_state.analytic_tables = result["tables"]
                st.success(
                    f"{result['variable']} creada con "
                    f"{result['validos']:,} casos válidos."
                )
            except Exception as exc:
                st.error(f"No fue posible procesar el factor: {exc}")


def _saved_factor_ranges(saved_row: dict) -> list[dict]:
    raw = str(saved_row.get("configuracion_json") or "").strip()
    if not raw:
        return []
    try:
        value = json.loads(raw)
        ranges = value.get("ranges", [])
        return ranges if isinstance(ranges, list) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _saved_bool(
    saved_row: dict, key: str, default: bool
) -> bool:
    value = saved_row.get(key)
    if value is None or pd.isna(value):
        return default
    return bool(value)


def _default_calculations(
    calculation: str,
    question_type: str = "",
) -> list[str]:
    if normalize_text(question_type) in {
        "rm",
        "rm_dicotomica_label",
        "grid_rm_loop",
    }:
        return [
            "n",
            "RM % Respondentes",
            "RM % Menciones",
        ]
    if question_type == "NPS":
        return ["NPS"]
    if question_type == "Escala" and calculation.lower() == "frecuencia":
        return ["Media", "Top2Box", "BottomBox"]
    kind = calculation.lower()
    if "nps" in kind:
        return ["NPS"]
    if "media" in kind:
        return ["Media", "Desviación estándar"]
    if "top" in kind:
        return ["Top2Box", "BottomBox"]
    if "bottom" in kind:
        return ["BottomBox", "Top2Box"]
    if "rm" in kind:
        return ["n", calculation]
    return ["n", "%"]


def _calculation_options_for_question(
    question_type: str,
) -> list[str]:
    if normalize_text(question_type) in {
        "rm",
        "rm_dicotomica_label",
        "grid_rm_loop",
    }:
        return [
            "n",
            "n ponderado",
            "% ponderado",
            "RM % Respondentes",
            "RM % Menciones",
        ]
    return [
        option
        for option in CALCULATION_OPTIONS
        if not option.startswith("RM ")
    ]


def _rm_summary_kpis(
    report: ReportResult,
) -> dict[str, float | int]:
    if normalize_text(report.question_type) not in {
        "rm",
        "rm_dicotomica_label",
        "grid_rm_loop",
    }:
        return {}
    summary = report.summaries.get("rm", pd.DataFrame())
    if summary.empty:
        return {}
    total = summary[
        summary["banner"].astype(str).eq("Total")
    ]
    if (
        total.empty
        or "base_menciones" not in total
        or "base" not in total
    ):
        return {}
    total_mentions = pd.to_numeric(
        total.get("base_menciones"), errors="coerce"
    ).dropna()
    bases = pd.to_numeric(
        total.get("base"), errors="coerce"
    ).dropna()
    if total_mentions.empty or bases.empty:
        return {}
    mentions = int(total_mentions.iloc[0])
    base = int(bases.iloc[0])
    return {
        "total_menciones": mentions,
        "promedio_menciones": (
            mentions / base if base else 0.0
        ),
    }


def _factor_calculation_defaults(
    db_path: Path,
    datamap_paths,
    question_id: str,
    question_type: str,
    base_calculations: list[str],
) -> tuple[list[str], str]:
    db_token = _db_cache_token(db_path)
    datamap_token = _datamap_cache_token(datamap_paths)
    factors = _cached_factor_recommendations(datamap_token)
    if factors.empty:
        return base_calculations, ""
    factors = merge_factor_configurations(
        factors, _cached_factor_configurations(str(db_path), db_token)
    )
    question_column = next(
        (
            column
            for column in factors.columns
            if normalize_text(column)
            in {"numero_pregunta", "pregunta_id"}
        ),
        None,
    )
    if not question_column:
        return base_calculations, ""
    selected = factors[
        factors[question_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(str(question_id).strip())
    ]
    if selected.empty:
        return base_calculations, ""
    calculations = recommended_factor_calculations(
        question_type,
        base_calculations,
        selected,
    )
    type_column = next(
        (
            column
            for column in selected.columns
            if normalize_text(column)
            == "tipo_factor_recomendado"
        ),
        None,
    )
    labels = (
        selected[type_column]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda values: values.ne("")]
        .drop_duplicates()
        .tolist()
        if type_column
        else []
    )
    return calculations, ", ".join(labels)


def _render_project_map(questions: pd.DataFrame) -> None:
    with st.expander(
        "Vista del proyecto",
        expanded=False,
    ):
        c1, c2 = st.columns(2)
        c1.metric("Preguntas", len(questions))
        c2.metric(
            "Secciones", questions["seccion_reporter"].nunique()
        )
        summary = (
            questions.groupby(
                ["seccion_reporter", "tipo_pregunta_reporter"]
            )
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .rename(columns={"seccion_reporter": "Sección"})
        )
        st.dataframe(
            summary,
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "RU: respuesta única · RM: respuesta múltiple · "
            "Escala/NPS: métricas numéricas."
        )


def _clear_filter_state(key_prefix: str) -> None:
    st.session_state[f"{key_prefix}_filter_variables"] = []
    value_prefix = f"{key_prefix}_filter_values_"
    for key in list(st.session_state):
        if key.startswith(value_prefix):
            del st.session_state[key]


def _reporter_datamap_paths() -> list[Path]:
    requested = []
    for key in ("datamap_final_path", "datamap_path"):
        value = st.session_state.get(key)
        if value:
            requested.append(Path(value))
    return resolve_datamap_paths(requested)
