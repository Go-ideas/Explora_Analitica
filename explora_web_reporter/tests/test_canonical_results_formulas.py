from __future__ import annotations

import pytest

from src.analytics_core.formula_registry import (
    FORMULA_REGISTRY,
    FORMULA_REGISTRY_VERSION,
    FormulaRegistryError,
    evaluate_formula,
    get_formula,
)
from src.analytics_core.results import (
    assemble_canonical_result,
    base_from_ledger,
    make_request_snapshot,
    make_slice,
    value_and_qa_from_formula,
)
from src.analytics_core.serialization import to_canonical_json
from src.analytics_core.structure import DenominatorLedger
from src.contracts.models import MetricSpec, ReleaseMetadata, UniverseRef
from src.contracts.vocabulary import (
    DenominatorUnit,
    QAReleaseStatus,
    ReleaseLifecycle,
    ReleaseMode,
)
from src.contracts.vocabulary import ValueStatus, ValueUnit


def test_formula_registry_is_explicit_and_versioned() -> None:
    formula = get_formula("PROPORTION")

    assert formula.entry.formula_version == FORMULA_REGISTRY_VERSION
    assert "released_metric_spec" in formula.entry.input_requirements
    assert "canonical_base" in formula.entry.input_requirements


def test_required_m5_v1_formulas_are_registered() -> None:
    expected = {
        "COUNT",
        "FREQUENCY",
        "PROPORTION",
        "MEAN",
        "STANDARD_DEVIATION",
        "TOP_BOX",
        "BOTTOM_BOX",
        "NPS_DESCRIPTIVE",
        "RM_RESPONDENT_PROPORTION",
        "RM_MENTION_PROPORTION",
        "SCALE_MEAN",
    }

    assert expected.issubset(FORMULA_REGISTRY)


def test_unknown_formula_is_structural_error() -> None:
    with pytest.raises(FormulaRegistryError):
        evaluate_formula("FREE_FORM", structure_type="RU")


def test_known_unsupported_formula_combination_is_value_status_unsupported() -> None:
    result = evaluate_formula(
        "RM_MENTION_PROPORTION",
        structure_type="RM",
        weight_mode="weighted",
        numerator=1,
        denominator=2,
    )

    assert result.value_status is ValueStatus.UNSUPPORTED
    assert result.estimate is None


def test_proportion_is_stored_zero_to_one_not_percent() -> None:
    result = evaluate_formula(
        "PROPORTION",
        structure_type="RU",
        numerator=52,
        denominator=100,
    )

    assert result.value_status is ValueStatus.OK
    assert result.estimate == 0.52
    assert result.unit is ValueUnit.PROPORTION


def test_count_mean_sd_top_bottom_and_nps_are_deterministic() -> None:
    assert evaluate_formula("COUNT", structure_type="RU", numerator=3).estimate == 3
    assert evaluate_formula(
        "MEAN",
        structure_type="RU",
        observations=(1, 2, 3),
    ).estimate == 2
    assert evaluate_formula(
        "STANDARD_DEVIATION",
        structure_type="RU",
        observations=(1, 2, 3),
    ).estimate == 1
    assert evaluate_formula(
        "TOP_BOX",
        structure_type="RU",
        numerator=4,
        denominator=8,
    ).estimate == 0.5
    assert evaluate_formula(
        "BOTTOM_BOX",
        structure_type="RU",
        numerator=2,
        denominator=8,
    ).estimate == 0.25
    assert evaluate_formula(
        "NPS_DESCRIPTIVE",
        structure_type="RU",
        promoters=7,
        detractors=2,
        denominator=10,
    ).estimate == 0.5


def test_loop_numerico_requires_approved_registered_formula() -> None:
    supported = evaluate_formula(
        "SCALE_MEAN",
        structure_type="LOOP_NUMERICO",
        observations=(10, 20),
    )
    unsupported = evaluate_formula(
        "NPS_DESCRIPTIVE",
        structure_type="LOOP_NUMERICO",
        denominator=2,
        promoters=1,
        detractors=0,
    )

    assert supported.value_status is ValueStatus.OK
    assert unsupported.value_status is ValueStatus.UNSUPPORTED


def _release() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="M5",
        policy_version="V1",
        source_hash="hash",
    )


def _metric(formula_id: str) -> MetricSpec:
    return MetricSpec(
        spec_id=f"metric_{formula_id}",
        version="1.0",
        release=_release(),
        metric_id=f"metric_{formula_id}",
        formula_id=formula_id,
        question_ref="q1",
        universe_ref="u1",
        denominator_policy="explicit",
        missing_behavior="exclude",
    )


def _base():
    ledger = DenominatorLedger(
        scope_id="structure",
        metric_id="structure_validity",
        denominator_unit=DenominatorUnit.RESPONDENT,
        denominator_n=2,
        valid_n=2,
        selected_n=1,
        not_selected_n=1,
        ordinary_missing_n=0,
        structural_missing_n=0,
        invalid_n=0,
        zero_base_status="NONZERO_BASE",
    )
    return base_from_ledger(
        ledger,
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_inputs_return_error_status_and_qa(value: float) -> None:
    result, qa = value_and_qa_from_formula(
        _metric("MEAN"),
        _base(),
        structure_type="RU",
        result_run_id="run",
        observations=(1.0, value),
    )

    assert result.value_status is ValueStatus.ERROR
    assert result.estimate is None
    assert qa
    assert qa[0].blocking is True


def test_non_finite_formula_result_returns_error_status_and_qa() -> None:
    result, qa = value_and_qa_from_formula(
        _metric("PROPORTION"),
        _base(),
        structure_type="RU",
        result_run_id="run",
        numerator=1e308,
        denominator=1e-308,
    )

    assert result.value_status is ValueStatus.ERROR
    assert result.estimate is None
    assert qa


def test_unknown_formula_generates_blocking_qa_and_not_releasable_run() -> None:
    value, qa = value_and_qa_from_formula(
        _metric("FREE_FORM"),
        _base(),
        structure_type="RU",
        result_run_id="run",
    )
    canonical = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=make_request_snapshot(question_ids=("q1",)),
        slices=(make_slice(is_total=True),),
        bases=(_base(),),
        values=(value,),
        qa_events=qa,
        result_run_id="run",
        b3_release_evidence=True,
    )

    assert value.value_status is ValueStatus.ERROR
    assert value.estimate is None
    assert qa[0].code == "UNKNOWN_FORMULA_ID"
    assert qa[0].blocking is True
    assert canonical.release.releasable is False
    assert "NaN" not in to_canonical_json(canonical)
    assert "Infinity" not in to_canonical_json(canonical)


def test_known_unsupported_formula_generates_structured_qa() -> None:
    value, qa = value_and_qa_from_formula(
        _metric("RM_MENTION_PROPORTION"),
        _base(),
        structure_type="RM",
        result_run_id="run",
        numerator=1,
        denominator=2,
    )
    weighted_base = _base()
    weighted_base = type(weighted_base)(
        **{**weighted_base.__dict__, "active_weight_ref": "weight"}
    )
    value, qa = value_and_qa_from_formula(
        _metric("RM_MENTION_PROPORTION"),
        weighted_base,
        structure_type="RM",
        result_run_id="run",
        numerator=1,
        denominator=2,
    )

    assert value.value_status is ValueStatus.UNSUPPORTED
    assert value.estimate is None
    assert qa
    assert qa[0].code == "FORMULA_UNSUPPORTED_COMBINATION"
    assert qa[0].state is QAReleaseStatus.REVIEW_REQUIRED
