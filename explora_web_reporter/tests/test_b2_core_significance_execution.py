from dataclasses import replace
import math

import pytest
from statsmodels.stats.proportion import proportions_ztest

from src.analytics_core.execution_adapter import CanonicalExecutionContext, SliceExecutionAuthority, execute_canonical_request
from src.analytics_core.results import make_slice
from src.analytics_core.significance import (
    ENGINE_VERSION, ProportionComparisonInput, ProportionFamilyRequest,
    SignificanceExecutionError, execute_proportion_family,
)
from src.contracts.models import ReleaseMetadata, SignificanceSpec
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode, SampleRelationship, StatisticalState
from test_m5_execution_adapter import metric, request, ru_result, universe


def spec(confidence=0.95):
    release = ReleaseMetadata(ReleaseLifecycle.RELEASED, ReleaseMode.REVIEW, "B2_REVIEW",
                              "2026-09-19", "B2", "B2_V1", "b2-policy")
    return SignificanceSpec("B2_QUALIFICATION", "1.0.0", release, "pooled_z",
                            confidence=confidence, alpha=1-confidence)


def item(left=70, right=30, left_n=100, right_n=100, **kwargs):
    values = dict(left_member_id="A", right_member_id="B", left_slice_id="slice_a",
                  right_slice_id="slice_b", left_numerator=left, right_numerator=right,
                  left_unweighted_n=left_n, right_unweighted_n=right_n)
    values.update(kwargs)
    return ProportionComparisonInput(**values)


def execute(*items, confidence=0.95):
    return execute_proportion_family(spec=spec(confidence), result_run_id="run", question_id="Q",
        metric_id="M", analytical_scope="banner", family_id="family", comparisons=tuple(items))


@pytest.mark.parametrize("confidence", [0.90, 0.95, 0.99])
def test_supported_confidences_are_significant(confidence):
    relation = execute(item(), confidence=confidence)[0]
    assert relation.status is StatisticalState.SIGNIFICANT
    assert relation.confidence == confidence


def test_numerical_result_matches_independent_oracle():
    relation = execute(item(left=61, right=44))[0]
    _, expected = proportions_ztest([61, 44], [100, 100])
    assert relation.raw_p_value == pytest.approx(expected, abs=1e-15)
    assert relation.adjusted_p_value == pytest.approx(expected, abs=1e-15)


def test_eligible_non_significant():
    assert execute(item(left=52, right=48))[0].status is StatisticalState.NOT_SIGNIFICANT


def test_unweighted_minimum_base_is_ineligible():
    relation = execute(item(left=20, right=15, left_n=29, right_n=30))[0]
    assert relation.status is StatisticalState.INELIGIBLE
    assert "INELIGIBLE_MINIMUM_BASE" in relation.provenance_refs[2]


def test_expected_count_is_ineligible():
    relation = execute(item(left=1, right=0))[0]
    assert relation.status is StatisticalState.INELIGIBLE
    assert "INELIGIBLE_EXPECTED_COUNT" in relation.provenance_refs[2]


def test_degenerate_variance_is_ineligible():
    assert execute(item(left=0, right=0))[0].status is StatisticalState.INELIGIBLE


def test_direction_and_swap_are_explicit():
    forward = execute(item(left=70, right=30))[0]
    reverse = execute(item(left=30, right=70))[0]
    assert forward.direction == "LEFT_GREATER"
    assert reverse.direction == "RIGHT_GREATER"
    assert forward.raw_p_value == reverse.raw_p_value


def test_holm_adjustment_is_family_scoped_and_deterministic():
    second = item(left_member_id="C", right_member_id="D", left_slice_id="slice_c",
                  right_slice_id="slice_d", left=60, right=45)
    first = execute(item(), second)
    again = execute(item(), second)
    assert first == again
    assert first[0].adjusted_p_value >= first[0].raw_p_value
    assert first[1].adjusted_p_value >= first[1].raw_p_value


@pytest.mark.parametrize("confidence", [0.0, 0.92, 0.97, 1.0])
def test_unsupported_confidence_fails_closed(confidence):
    with pytest.raises(ValueError):
        execute(item(), confidence=confidence)


@pytest.mark.parametrize("change", [
    {"left_numerator": -1}, {"left_numerator": 101}, {"left_unweighted_n": 0},
    {"left_member_id": ""}, {"right_slice_id": "slice_a"},
])
def test_malformed_inputs_fail_closed(change):
    with pytest.raises(SignificanceExecutionError):
        execute(item(**change))


def test_duplicate_identity_fails_closed():
    with pytest.raises(SignificanceExecutionError, match="Duplicate"):
        execute(item(), item())


@pytest.mark.parametrize("change", [
    {"weighted_inference": True},
    {"sample_relationship": SampleRelationship.UNKNOWN},
    {"respondent_binary": False},
])
def test_unsupported_semantics_are_explicit(change):
    assert execute(item(**change))[0].status is StatisticalState.UNSUPPORTED


def test_core_execution_adapter_emits_canonical_relation():
    slices = (
        SliceExecutionAuthority(make_slice(is_total=False, banner_ref="B", member_ids=("A",),
            configuration={"authority": "qualification", "member": "A"}), universe()),
        SliceExecutionAuthority(make_slice(is_total=False, banner_ref="B", member_ids=("B",),
            configuration={"authority": "qualification", "member": "B"}), universe()),
    )
    comparison = replace(item(), left_slice_id=slices[0].slice.slice_id,
                         right_slice_id=slices[1].slice.slice_id)
    family = ProportionFamilyRequest(spec(), "Q_RU", "M_PROP", "banner", "family", (comparison,))
    result = execute_canonical_request(CanonicalExecutionContext(
        project_id="P", dataset_fingerprint="dataset", project_spec_ref="PROJECT_SPEC",
        request=replace(request(), question_ids=("Q_RU",), metric_refs=("M_PROP",)),
        question_id="Q_RU", structure_ref="STR_RU", structure_result=ru_result(),
        universe_result=universe(), metric_specs=(metric("M_PROP", "proportion/v1"),),
        runtime_fingerprint="runtime", slices=slices, significance_families=(family,),
        result_run_id="run", b3_release_evidence=True))
    assert len(result.comparisons) == 1
    assert result.comparisons[0].status is StatisticalState.SIGNIFICANT
    assert f"engine:{ENGINE_VERSION}" in result.comparisons[0].provenance_refs


def test_engine_has_no_reporter_or_excel_dependency():
    source = __import__("inspect").getsource(__import__("src.analytics_core.significance", fromlist=["x"]))
    assert "src.reporter" not in source and "excel" not in source.lower()
