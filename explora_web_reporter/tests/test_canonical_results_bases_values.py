from __future__ import annotations

from dataclasses import replace

import pytest

from src.analytics_core.results import (
    assemble_canonical_result,
    base_from_ledger,
    make_request_snapshot,
    make_slice,
    value_from_formula,
)
from src.analytics_core.structure import DenominatorLedger
from src.analytics_core.weights import WeightEvaluationContext, evaluate_weighted_base
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    CanonicalBase,
    CanonicalValue,
    MetricSpec,
    ReleaseMetadata,
    UniverseRef,
)
from src.contracts.validators import ContractValidationError, validate_canonical_result
from src.contracts.models import CanonicalResult, QAEnvelope
from src.contracts.vocabulary import (
    AggregateReleaseState,
    DenominatorUnit,
    ReleaseLifecycle,
    ReleaseMode,
    ValueStatus,
    ValueUnit,
)


def release() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="M5",
        policy_version="V1",
        source_hash="hash",
    )


def metric(formula_id: str = "PROPORTION") -> MetricSpec:
    return MetricSpec(
        spec_id="metric_spec",
        version="1.0",
        release=release(),
        metric_id="metric",
        formula_id=formula_id,
        question_ref="q1",
        universe_ref="u1",
        denominator_policy="explicit",
        missing_behavior="exclude",
    )


def ledger(unit: DenominatorUnit, n: int, scope: str) -> DenominatorLedger:
    return DenominatorLedger(
        scope_id=scope,
        metric_id=f"{unit.value}_{scope}",
        denominator_unit=unit,
        denominator_n=n,
        valid_n=n,
        selected_n=0,
        not_selected_n=0,
        ordinary_missing_n=0,
        structural_missing_n=0,
        invalid_n=0,
        zero_base_status="VALID_ZERO_BASE" if n == 0 else "NONZERO_BASE",
    )


def universe(mask=None) -> UniverseEvaluationResult:
    respondent_mask = mask or {"r1": True, "r2": True}
    return UniverseEvaluationResult(
        universe_ref=UniverseRef("u1"),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask=respondent_mask,
        input_n=len(respondent_mask),
        eligible_n=sum(respondent_mask.values()),
        excluded_n=len(respondent_mask) - sum(respondent_mask.values()),
        status=UniverseEvaluationStatus.PASS,
    )


def test_respondent_and_mention_denominators_have_distinct_base_identity() -> None:
    respondent = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 100, "respondent"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )
    mention = base_from_ledger(
        ledger(DenominatorUnit.MENTION, 100, "mention:row:r1"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )

    assert respondent.base_id != mention.base_id
    assert respondent.denominator_unit is DenominatorUnit.RESPONDENT
    assert mention.denominator_unit is DenominatorUnit.MENTION


def test_valid_zero_value_is_ok_and_not_no_valid_base() -> None:
    base = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 5, "structure"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )

    value = value_from_formula(
        metric(),
        base,
        structure_type="RU",
        result_run_id="run",
        numerator=0,
        denominator=5,
    )

    assert value.value_status is ValueStatus.OK
    assert value.estimate == 0
    assert value.unit is ValueUnit.PROPORTION


def test_no_valid_base_yields_null_estimate_not_zero() -> None:
    base = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 0, "structure"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )
    value = value_from_formula(
        metric(),
        base,
        structure_type="RU",
        result_run_id="run",
        numerator=0,
        denominator=0,
    )

    assert value.value_status is ValueStatus.NO_VALID_BASE
    assert value.estimate is None


def test_non_ok_value_with_estimate_fails_contract_validation() -> None:
    value = CanonicalValue(
        value_id="value",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        metric_id="metric",
        formula_id="PROPORTION",
        formula_version="v1",
        base_id="base",
        value_status=ValueStatus.INELIGIBLE,
        unit=ValueUnit.PROPORTION,
        estimate=0.1,
    )
    base = CanonicalBase(
        base_id="base",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        denominator_unit=DenominatorUnit.RESPONDENT,
        denominator_ref="respondent",
        denominator_scope_id="structure",
        unweighted_n=1,
    )
    result = CanonicalResult(
        result_schema_version="M5",
        result_run_id="run",
        project_id="p",
        dataset_fingerprint="d",
        project_spec_ref="ps",
        core_version="m5",
        qa=QAEnvelope(AggregateReleaseState.PASS),
        bases=(base,),
        values=(value,),
    )

    with pytest.raises(ContractValidationError):
        validate_canonical_result(result)


def test_weighted_base_consumes_m3_fields_without_recomputing_them() -> None:
    m3 = evaluate_weighted_base(
        universe(),
        WeightEvaluationContext(
            respondent_ids=("r1", "r2"),
            weight_specs=(),
        ),
    )
    base = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 99, "structure"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        weight_result=m3,
    )

    assert base.unweighted_n == m3.unweighted_n
    assert base.weighted_n_raw == m3.weighted_n_raw


def test_base_identity_distinguishes_loop_instance_scope() -> None:
    first = base_from_ledger(
        ledger(DenominatorUnit.INSTANCE, 1, "loop_instance:l1"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        loop_instance_id="l1",
    )
    second = replace(first, base_id="x", loop_instance_id="l2")
    regenerated = base_from_ledger(
        ledger(DenominatorUnit.INSTANCE, 1, "loop_instance:l2"),
        result_run_id="run",
        question_id="q1",
        structure_id="s1",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        loop_instance_id="l2",
    )

    assert first.base_id != regenerated.base_id
    assert second.loop_instance_id == "l2"


def test_ru_canonical_count_mean_sd_and_box_metrics() -> None:
    base = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 4, "structure"),
        result_run_id="run",
        question_id="q1",
        structure_id="ru",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )
    count = value_from_formula(
        metric("COUNT"),
        base,
        structure_type="RU",
        result_run_id="run",
        numerator=4,
    )
    mean_value = value_from_formula(
        metric("MEAN"),
        base,
        structure_type="RU",
        result_run_id="run",
        observations=(1, 2, 3, 4),
    )
    sd_value = value_from_formula(
        metric("STANDARD_DEVIATION"),
        base,
        structure_type="RU",
        result_run_id="run",
        observations=(1, 2, 3),
    )
    top_box = value_from_formula(
        metric("TOP_BOX"),
        base,
        structure_type="RU",
        result_run_id="run",
        numerator=2,
        denominator=4,
    )
    bottom_box = value_from_formula(
        metric("BOTTOM_BOX"),
        base,
        structure_type="RU",
        result_run_id="run",
        numerator=1,
        denominator=4,
    )

    assert count.estimate == 4
    assert mean_value.estimate == 2.5
    assert sd_value.value_status is ValueStatus.OK
    assert top_box.estimate == 0.5
    assert bottom_box.estimate == 0.25


def test_rm_respondent_and_mention_canonical_assembly_use_m4_ledgers() -> None:
    respondent = base_from_ledger(
        ledger(DenominatorUnit.RESPONDENT, 100, "respondent"),
        result_run_id="run",
        question_id="q1",
        structure_id="rm",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )
    mention = base_from_ledger(
        ledger(DenominatorUnit.MENTION, 100, "mention:structure"),
        result_run_id="run",
        question_id="q1",
        structure_id="rm",
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
    )
    respondent_value = value_from_formula(
        metric("RM_RESPONDENT_PROPORTION"),
        respondent,
        structure_type="RM",
        result_run_id="run",
        numerator=20,
        denominator=100,
    )
    mention_value = value_from_formula(
        metric("RM_MENTION_PROPORTION"),
        mention,
        structure_type="RM",
        result_run_id="run",
        numerator=20,
        denominator=100,
    )

    assert respondent.base_id != mention.base_id
    assert respondent_value.base_id == respondent.base_id
    assert mention_value.base_id == mention.base_id
    assert respondent_value.estimate == mention_value.estimate == 0.2


@pytest.mark.parametrize(
    ("structure_type", "row_id", "column_id", "option_id", "loop_instance_id"),
    (
        ("GRID_ESCALA", "row1", None, None, None),
        ("GRID_RM", "row1", "col1", "col1", None),
        ("LOOP_RU", None, None, None, "loop1"),
        ("LOOP_RM", None, None, "opt1", "loop1"),
        ("LOOP_NUMERICO", None, None, None, "loop1"),
    ),
)
def test_grid_and_loop_canonical_identity_preserves_m4_scope(
    structure_type: str,
    row_id: str | None,
    column_id: str | None,
    option_id: str | None,
    loop_instance_id: str | None,
) -> None:
    unit = (
        DenominatorUnit.INSTANCE
        if structure_type.startswith("LOOP")
        else DenominatorUnit.RESPONDENT
    )
    base = base_from_ledger(
        ledger(unit, 3, f"{structure_type}:scope"),
        result_run_id="run",
        question_id="q1",
        structure_id=structure_type.lower(),
        slice_id="slice",
        universe_ref=UniverseRef("u1"),
        row_id=row_id,
        column_id=column_id,
        option_id=option_id,
        loop_instance_id=loop_instance_id,
    )
    formula_id = "SCALE_MEAN" if structure_type == "LOOP_NUMERICO" else "COUNT"
    value = value_from_formula(
        metric(formula_id),
        base,
        structure_type=structure_type,
        result_run_id="run",
        numerator=3,
        observations=(1, 2, 3),
    )
    result = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=make_request_snapshot(question_ids=("q1",)),
        slices=(make_slice(is_total=True),),
        bases=(base,),
        values=(value,),
        result_run_id="run",
    )

    assert result.bases[0].row_id == row_id
    assert result.bases[0].column_id == column_id
    assert result.bases[0].option_id == option_id
    assert result.bases[0].loop_instance_id == loop_instance_id
    assert result.values[0].base_id == base.base_id


def test_loop_rango_is_not_registered_as_authorized_structure_formula() -> None:
    result = value_from_formula(
        metric("SCALE_MEAN"),
        base_from_ledger(
            ledger(DenominatorUnit.INSTANCE, 1, "loop_rango"),
            result_run_id="run",
            question_id="q1",
            structure_id="loop_rango",
            slice_id="slice",
            universe_ref=UniverseRef("u1"),
        ),
        structure_type="LOOP_RANGO",
        result_run_id="run",
        observations=(1,),
    )

    assert result.value_status is ValueStatus.UNSUPPORTED
