from __future__ import annotations

from src.analytics_core.results import base_from_ledger, qa_events_from_envelope
from src.analytics_core.structure import (
    STRUCTURE_RUNTIME_RULES_VERSION,
    DenominatorLedger,
)
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.analytics_core.weights import WeightEvaluationContext, evaluate_weighted_base
from src.contracts.models import QAEnvelope, QAIssue, UniverseRef
from src.contracts.vocabulary import (
    AggregateReleaseState,
    DenominatorUnit,
    QADomain,
    QAIssueLifecycle,
    QAIssueState,
)


def universe_result() -> UniverseEvaluationResult:
    return UniverseEvaluationResult(
        universe_ref=UniverseRef("u1"),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask={"r1": True, "r2": False},
        input_n=2,
        eligible_n=1,
        excluded_n=1,
        status=UniverseEvaluationStatus.PASS,
        traceability={"m2": "trace"},
    )


def ledger() -> DenominatorLedger:
    return DenominatorLedger(
        scope_id="mention:row:row1",
        metric_id="rm_mention",
        denominator_unit=DenominatorUnit.MENTION,
        denominator_n=1,
        valid_n=1,
        selected_n=1,
        not_selected_n=0,
        ordinary_missing_n=0,
        structural_missing_n=0,
        invalid_n=0,
        zero_base_status="NONZERO_BASE",
        traceability={"runtime_rules_version": STRUCTURE_RUNTIME_RULES_VERSION},
    )


def test_m2_universe_mask_is_consumed_without_modification() -> None:
    m2 = universe_result()
    before = dict(m2.respondent_mask)
    m3 = evaluate_weighted_base(
        m2,
        WeightEvaluationContext(respondent_ids=("r1", "r2")),
    )

    assert m2.respondent_mask == before
    assert m3.m2_universe_result.respondent_mask == before


def test_m3_weight_result_is_copied_as_authoritative_base_metadata() -> None:
    m3 = evaluate_weighted_base(
        universe_result(),
        WeightEvaluationContext(respondent_ids=("r1", "r2")),
    )
    base = base_from_ledger(
        ledger(),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        weight_result=m3,
    )

    assert base.unweighted_n == m3.unweighted_n
    assert base.weighted_n_raw == m3.weighted_n_raw
    assert base.effective_n == m3.effective_n


def test_m4_ledger_denominator_reference_is_preserved() -> None:
    base = base_from_ledger(
        ledger(),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )

    assert base.denominator_unit is DenominatorUnit.MENTION
    assert base.denominator_ref == "rm_mention"
    assert base.denominator_scope_id == "mention:row:row1"
    assert STRUCTURE_RUNTIME_RULES_VERSION in base.provenance_refs


def test_upstream_qa_is_transported_not_flattened() -> None:
    envelope = QAEnvelope(
        aggregate_state=AggregateReleaseState.PASS_WITH_WARNINGS,
        issues=(
            QAIssue(
                issue_id="m4-warning-1",
                state=QAIssueState.WARN,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="structure",
                message="upstream warning",
                scope="structure",
            ),
        ),
    )

    events = qa_events_from_envelope(
        envelope,
        domain=QADomain.STRUCTURE,
        source_component="analytics_core.structure",
    )

    assert len(events) == 1
    assert events[0].qa_domain is QADomain.STRUCTURE
    assert events[0].related_ids == ("m4-warning-1",)


def test_upstream_qa_domain_identity_is_preserved() -> None:
    envelope = QAEnvelope(
        aggregate_state=AggregateReleaseState.PASS_WITH_WARNINGS,
        issues=(
            QAIssue(
                issue_id="upstream-warning",
                state=QAIssueState.WARN,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="upstream",
                message="domain warning",
                scope="domain",
            ),
        ),
    )

    for domain in (
        QADomain.UNIVERSE,
        QADomain.WEIGHT,
        QADomain.STRUCTURE,
        QADomain.STATISTICAL,
    ):
        events = qa_events_from_envelope(
            envelope,
            domain=domain,
            source_component=f"source.{domain.value.lower()}",
        )

        assert events[0].qa_domain is domain
        assert events[0].source_component.endswith(domain.value.lower())
