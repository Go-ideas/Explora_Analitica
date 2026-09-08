from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.reporter.tabulator import generate_report
from src.ui.page_04_reporter import (
    _cached_available_questions,
    _cached_config_entries,
    _datamap_cache_token,
    _db_cache_token,
    _report_controls,
    _reporter_datamap_paths,
    render_report,
)


def render() -> None:
    st.subheader("Diferencias significativas")
    db_value = st.session_state.get("db_path")
    if not db_value:
        st.info("Crea primero la base analítica.")
        return
    db_path = Path(db_value)
    if not db_path.exists():
        st.info("Crea primero la base analítica.")
        return
    datamap_paths = _reporter_datamap_paths()
    db_token = _db_cache_token(db_path)
    datamap_token = _datamap_cache_token(datamap_paths)
    questions = _cached_available_questions(
        str(db_path), db_token, datamap_token
    )
    if questions.empty:
        st.warning("No hay preguntas analizables.")
        return
    if _cached_config_entries(
        str(db_path), db_token, "banner", datamap_token
    ).empty:
        st.warning(
            "No hay variables banner configuradas en el Datamap."
        )
        return

    with st.sidebar:
        st.divider()
        st.markdown("### Configuración estadística")
        settings = _report_controls(
            db_path,
            questions,
            key_prefix="sig",
            significance=True,
            datamap_paths=datamap_paths,
        )
        calculate = st.button(
            "Calcular diferencias",
            type="primary",
            width="stretch",
        )

    if calculate:
        try:
            with st.spinner("Calculando pruebas estadísticas..."):
                report = generate_report(db_path=db_path, **settings)
            st.session_state.significance_report = report
            st.session_state.current_report = report
        except Exception as exc:
            st.error(f"No fue posible calcular significancia: {exc}")

    report = st.session_state.get("significance_report")
    if report is None:
        st.info(
            "Selecciona una pregunta y un banner para comparar columnas."
        )
        return
    render_report(report, key_prefix="significance")
    if (
        report.significance_display != "none"
        and report.significance.empty
    ):
        st.warning(
            "No se detectaron diferencias o no hubo base suficiente."
        )
