from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, MutableMapping

from src.contracts.vocabulary import ExecutionMode
from src.web_canonical.request_binding import WebCanonicalRequest


CURRENT_ANALYSIS_KEYS = (
    "current_report",
    "current_report_legacy",
    "current_canonical_result",
    "current_canonical_projection",
    "current_dual_run",
    "current_result_contract",
    "current_analysis_binding",
)


@dataclass(frozen=True)
class AnalysisSessionBinding:
    execution_mode: str
    request_identity: str
    question_ids: tuple[str, ...]
    request_fingerprint: str | None = None
    result_run_id: str | None = None
    result_fingerprint: str | None = None


def analysis_session_binding(
    *,
    execution_mode: ExecutionMode | str,
    request_identity: str,
    request: WebCanonicalRequest,
    result_run_id: str | None = None,
    result_fingerprint: str | None = None,
) -> AnalysisSessionBinding:
    return AnalysisSessionBinding(
        execution_mode=str(getattr(execution_mode, "value", execution_mode)),
        request_identity=request_identity,
        question_ids=request.question_ids,
        request_fingerprint=request.request_fingerprint,
        result_run_id=result_run_id,
        result_fingerprint=result_fingerprint,
    )


def begin_analysis_execution(
    state: MutableMapping[str, Any],
    binding: AnalysisSessionBinding,
) -> None:
    clear_current_analysis(state)
    state["pending_analysis_binding"] = binding
    state["last_execution_error"] = None


def store_current_analysis_binding(
    state: MutableMapping[str, Any],
    binding: AnalysisSessionBinding,
) -> None:
    state["current_analysis_binding"] = binding
    state["pending_analysis_binding"] = None
    state["last_execution_error"] = None


def mark_analysis_failure(
    state: MutableMapping[str, Any],
    binding: AnalysisSessionBinding,
    error: Exception,
) -> None:
    clear_current_analysis(state)
    state["failed_analysis_binding"] = binding
    state["pending_analysis_binding"] = None
    state["last_execution_error"] = {
        "binding": binding,
        "error_type": type(error).__name__,
        "message": str(error),
    }


def current_analysis_matches(
    state: MutableMapping[str, Any],
    binding: AnalysisSessionBinding,
) -> bool:
    current = state.get("current_analysis_binding")
    if not isinstance(current, AnalysisSessionBinding):
        return False
    return (
        current.execution_mode == binding.execution_mode
        and current.request_identity == binding.request_identity
        and current.question_ids == binding.question_ids
        and current.request_fingerprint == binding.request_fingerprint
    )


def clear_current_analysis(state: MutableMapping[str, Any]) -> None:
    for key in CURRENT_ANALYSIS_KEYS:
        state.pop(key, None)


def record_rollback_event(
    state: MutableMapping[str, Any],
    *,
    from_binding: AnalysisSessionBinding | None,
    to_binding: AnalysisSessionBinding,
) -> None:
    events = list(state.get("analysis_observability_events") or [])
    events.append(
        {
            "event": "explicit_rollback",
            "from_execution_mode": (
                from_binding.execution_mode if from_binding else None
            ),
            "to_execution_mode": to_binding.execution_mode,
            "question_ids": to_binding.question_ids,
            "request_fingerprint": to_binding.request_fingerprint,
        }
    )
    state["analysis_observability_events"] = events
