from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.analytics_core.runner import generate_report
from src.contracts.vocabulary import ExecutionMode
from src.ui.page_04_reporter import (
    _cached_available_questions,
    _cached_config_entries,
    _canonical_result_for_settings,
    _datamap_cache_token,
    _db_cache_token,
    _report_controls,
    _reporter_datamap_paths,
    _store_analysis_result,
    _analysis_binding,
    render_report,
    render_canonical_projection,
)
from src.utils.text_utils import normalize_text
from src.web_canonical.request_binding import web_request_from_settings
from src.web_canonical.session import (
    begin_analysis_execution,
    current_analysis_matches,
    mark_analysis_failure,
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
    execution_mode = str(
        settings.get("execution_mode") or ExecutionMode.LEGACY.value
    )
    current_request = web_request_from_settings(
        str(settings["question_id"]),
        settings,
    )
    current_binding = _analysis_binding(
        execution_mode,
        current_request,
    )

    if calculate:
        begin_analysis_execution(st.session_state, current_binding)
        try:
            with st.spinner("Calculando pruebas estadísticas..."):
                request_settings = dict(settings)
                request_settings.pop("execution_mode", None)
                if execution_mode in {
                    ExecutionMode.CANONICAL_V1.value,
                    ExecutionMode.DUAL_RUN.value,
                }:
                    canonical_result = _canonical_result_for_settings(
                        str(settings["question_id"])
                    )
                    if canonical_result is not None:
                        request_settings["canonical_result"] = (
                            canonical_result
                        )
                report = generate_report(
                    db_path=db_path,
                    mode=execution_mode,
                    **request_settings,
                )
            _store_analysis_result(report, execution_mode, current_binding)
            if execution_mode == ExecutionMode.LEGACY.value:
                st.session_state.significance_report = report
            else:
                st.session_state.significance_report = None
        except Exception as exc:
            mark_analysis_failure(st.session_state, current_binding, exc)
            st.error(f"No fue posible calcular significancia: {exc}")

    projection = st.session_state.get("current_canonical_projection")
    contract = st.session_state.get("current_result_contract")
    if (
        contract in {"canonical_v1", "dual_run"}
        and projection is not None
        and current_analysis_matches(st.session_state, current_binding)
    ):
        render_canonical_projection(projection, key_prefix="significance")
        return

    report = st.session_state.get("significance_report")
    if report is None or not current_analysis_matches(
        st.session_state,
        current_binding,
    ):
        st.info(
            "Selecciona una pregunta y un banner para comparar columnas."
        )
        return
    render_report(report, key_prefix="significance")
    if normalize_text(report.question_type) in {
        "grid_rm_loop_rm",
        "grid_rm",
        "loop_rm",
        "grid_rm_loop",
        "grid_rm_loop_rm",
        "grid_rm_loop_rm",
    }:
        st.warning(
            "La significancia para GRID_RM/LOOP_RM aplica sobre "
            "proporciones de selección, no sobre textos abiertos ni "
            "rankings derivados."
        )
    if (
        report.significance_display != "none"
        and report.significance.empty
    ):
        st.warning(
            "No se detectaron diferencias o no hubo base suficiente."
        )
