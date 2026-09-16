from __future__ import annotations

from src.analytics_core.results import (
    significance_state_for_request,
    transport_significance,
)
from src.contracts.models import SignificanceComparison
from src.contracts.vocabulary import StatisticalQAState, StatisticalState


def comparison(left: str = "b", right: str = "a") -> SignificanceComparison:
    return SignificanceComparison(
        left_member_id=left,
        right_member_id=right,
        family_id="family",
        test_id="z",
        test_version="B2_V1",
        policy_version="B2_V1",
        confidence=0.95,
        alpha=0.05,
        sidedness="two_sided",
        status=StatisticalState.SIGNIFICANT,
        reason_code="OK",
        raw_p_value=0.01,
        adjusted_p_value=0.02,
        qa_state=StatisticalQAState.PASS,
    )


def test_significance_transport_preserves_b2_decision_without_retesting() -> None:
    relation = transport_significance(
        comparison("a", "b"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="slice_pair",
        left_slice_id="slice-a",
        right_slice_id="slice-b",
    )

    assert relation.status is StatisticalState.SIGNIFICANT
    assert relation.raw_p_value == 0.01
    assert relation.adjusted_p_value == 0.02
    assert relation.test_version == "B2_V1"


def test_two_sided_pair_identity_is_canonicalized() -> None:
    left_right = transport_significance(
        comparison("a", "b"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="scope",
        left_slice_id="slice-a",
        right_slice_id="slice-b",
    )
    right_left = transport_significance(
        comparison("b", "a"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="scope",
        left_slice_id="slice-b",
        right_slice_id="slice-a",
    )

    assert left_right.comparison_id == right_left.comparison_id
    assert left_right.left_slice_id == "slice-a"
    assert right_left.left_slice_id == "slice-a"


def test_significance_not_requested_and_unsupported_states_are_explicit() -> None:
    assert significance_state_for_request(requested=False) is StatisticalState.NOT_TESTED
    assert significance_state_for_request(requested=True, weighted=True) is (
        StatisticalState.UNSUPPORTED
    )
    assert significance_state_for_request(requested=True, rm_mention=True) is (
        StatisticalState.UNSUPPORTED
    )
    assert significance_state_for_request(requested=True, nps=True) is (
        StatisticalState.UNSUPPORTED
    )


def test_ineligible_and_tested_not_significant_states_are_transported() -> None:
    ineligible = transport_significance(
        comparison("a", "b"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="scope",
        left_slice_id="slice-a",
        right_slice_id="slice-b",
    )
    ineligible = type(ineligible)(
        **{**ineligible.__dict__, "status": StatisticalState.INELIGIBLE}
    )
    not_significant = transport_significance(
        comparison("a", "b"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="scope",
        left_slice_id="slice-a",
        right_slice_id="slice-b",
    )
    not_significant = type(not_significant)(
        **{**not_significant.__dict__, "status": StatisticalState.NOT_SIGNIFICANT}
    )

    assert ineligible.status is StatisticalState.INELIGIBLE
    assert not_significant.status is StatisticalState.NOT_SIGNIFICANT


def test_tested_significant_state_is_fixture_transport_not_m5_inference() -> None:
    relation = transport_significance(
        comparison("a", "b"),
        result_run_id="run",
        question_id="q1",
        metric_id="m1",
        analytical_scope="scope",
        left_slice_id="slice-a",
        right_slice_id="slice-b",
    )

    assert relation.status is StatisticalState.SIGNIFICANT
    assert relation.test_id == "z"
