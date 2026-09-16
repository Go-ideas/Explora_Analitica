from __future__ import annotations

from src.canonical_materialization.models import CanonicalRuntimeInput, MaterializationError, MaterializationQAEvent


def assert_pre_m2_qa_pass(runtime: CanonicalRuntimeInput) -> None:
    failures = [event.message for event in runtime.qa_events if event.blocking]
    if failures:
        raise MaterializationError("; ".join(failures))


def qa_summary(runtime: CanonicalRuntimeInput) -> dict[str, int]:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for event in runtime.qa_events:
        counts[event.state] = counts.get(event.state, 0) + 1
    return counts


def fail_closed_event(code: str, message: str) -> MaterializationQAEvent:
    return MaterializationQAEvent(code, "FAIL", message, blocking=True)
