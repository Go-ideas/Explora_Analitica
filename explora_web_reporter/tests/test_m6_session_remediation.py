from __future__ import annotations

from src.contracts.vocabulary import ExecutionMode
from src.web_canonical.request_binding import web_request_from_settings
from src.web_canonical.session import (
    analysis_session_binding,
    begin_analysis_execution,
    current_analysis_matches,
    mark_analysis_failure,
    record_rollback_event,
    store_current_analysis_binding,
)


def _binding(mode: str, question_id: str):
    request = web_request_from_settings(question_id, {"metric_refs": ("m",)})
    return analysis_session_binding(
        execution_mode=mode,
        request_identity=question_id,
        request=request,
    )


def test_failed_execution_invalidates_stale_current_result() -> None:
    state = {"current_report": "legacy_q1"}
    q2 = _binding(ExecutionMode.CANONICAL_V1.value, "Q2")
    begin_analysis_execution(state, q2)
    mark_analysis_failure(state, q2, RuntimeError("canonical failed"))
    assert "current_report" not in state
    assert current_analysis_matches(state, q2) is False
    assert state["last_execution_error"]["error_type"] == "RuntimeError"


def test_mode_switch_failure_does_not_show_previous_canonical_result() -> None:
    state = {"current_canonical_projection": "canonical_q1"}
    q2 = _binding(ExecutionMode.LEGACY.value, "Q2")
    begin_analysis_execution(state, q2)
    mark_analysis_failure(state, q2, RuntimeError("legacy failed"))
    assert "current_canonical_projection" not in state
    assert current_analysis_matches(state, q2) is False


def test_current_result_must_match_request_and_mode() -> None:
    state = {}
    q1 = _binding(ExecutionMode.CANONICAL_V1.value, "Q1")
    q2 = _binding(ExecutionMode.CANONICAL_V1.value, "Q2")
    store_current_analysis_binding(state, q1)
    assert current_analysis_matches(state, q1) is True
    assert current_analysis_matches(state, q2) is False


def test_explicit_rollback_records_observability_event() -> None:
    state = {}
    failed = _binding(ExecutionMode.CANONICAL_V1.value, "Q1")
    rollback = _binding(ExecutionMode.LEGACY.value, "Q1")
    record_rollback_event(state, from_binding=failed, to_binding=rollback)
    event = state["analysis_observability_events"][0]
    assert event["event"] == "explicit_rollback"
    assert event["from_execution_mode"] == "CANONICAL_V1"
    assert event["to_execution_mode"] == "LEGACY"
