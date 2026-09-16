from __future__ import annotations

from dataclasses import replace

from src.contracts.models import (
    CanonicalBase,
    CanonicalReleaseState,
    CanonicalResult,
    CanonicalResultManifest,
    CanonicalSlice,
    CanonicalValue,
    QAEnvelope,
    QAEvent,
    RequestSnapshot,
    SignificanceRelation,
    UniverseRef,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    ComputationStatus,
    DenominatorUnit,
    QADomain,
    QAReleaseStatus,
    QAScopeType,
    StatisticalState,
    ValueStatus,
    ValueUnit,
)


def canonical_result(
    *,
    structure_id: str = "RU",
    status: ValueStatus = ValueStatus.OK,
    estimate: float | None = 0.5,
    unit: ValueUnit = ValueUnit.PROPORTION,
    denominator_unit: DenominatorUnit = DenominatorUnit.RESPONDENT,
    weighted: bool = False,
    releasable: bool = True,
    schema_version: str = "M5_CANONICAL_RESULT_V1",
    result_run_id: str = "run_m6_fixture",
) -> CanonicalResult:
    total = CanonicalSlice(
        slice_id="slice_total",
        slice_fingerprint="slice_fp_total",
        is_total=True,
        filter_refs=("filter_region_north",),
        label="Total",
    )
    banner = CanonicalSlice(
        slice_id="slice_banner_a",
        slice_fingerprint="slice_fp_banner_a",
        is_total=False,
        banner_dimension_id="segment",
        member_id="segment_a",
        filter_refs=("filter_region_north",),
        label="Segment A",
    )
    banner_b = CanonicalSlice(
        slice_id="slice_banner_b",
        slice_fingerprint="slice_fp_banner_b",
        is_total=False,
        banner_dimension_id="segment",
        member_id="segment_b",
        filter_refs=("filter_region_north",),
        label="Segment B",
    )
    base = CanonicalBase(
        base_id="base_total",
        question_id="Q1",
        structure_id=structure_id,
        slice_id=total.slice_id,
        universe_ref=UniverseRef("u_project"),
        denominator_unit=denominator_unit,
        denominator_ref="denom_ref",
        denominator_scope_id="scope_resp",
        unweighted_n=10,
        weighted_n_raw=12.0 if weighted else None,
        weighted_n=12.0 if weighted else None,
        effective_n=9.5 if weighted else None,
        active_weight_ref="weight_main" if weighted else None,
        row_id="row_1" if "GRID" in structure_id else None,
        column_id="col_1" if structure_id == "GRID_ESCALA" else None,
        option_id="opt_1" if structure_id in {"RM", "GRID_RM", "LOOP_RM"} else None,
        loop_instance_id="loop_1" if structure_id.startswith("LOOP") else None,
    )
    value = CanonicalValue(
        value_id="value_total",
        question_id=base.question_id,
        structure_id=structure_id,
        slice_id=total.slice_id,
        metric_id="metric_1",
        formula_id="formula_1",
        formula_version="v1",
        base_id=base.base_id,
        value_status=status,
        unit=unit,
        estimate=estimate if status is ValueStatus.OK else None,
        numerator=5 if status is ValueStatus.OK else None,
        denominator=10 if status is ValueStatus.OK else None,
        row_id=base.row_id,
        column_id=base.column_id,
        option_id=base.option_id,
        loop_instance_id=base.loop_instance_id,
        semantic_order=1,
    )
    qa_event = QAEvent(
        qa_id="qa_warning",
        qa_domain=QADomain.RESULT,
        code="M6_FIXTURE",
        state=QAReleaseStatus.PASS_WITH_WARNINGS,
        blocking=False,
        scope_type=QAScopeType.RESULT,
        message="Fixture QA warning",
        related_ids=(value.value_id,),
        source_component="tests.m6_fixtures",
        policy_version="M6_TEST",
    )
    release = CanonicalReleaseState(
        computation_status=ComputationStatus.COMPLETE,
        qa_release_status=(
            QAReleaseStatus.PASS if releasable else QAReleaseStatus.REVIEW_REQUIRED
        ),
        releasable=releasable,
        reasons=() if releasable else ("qa_warning",),
    )
    request = RequestSnapshot(
        request_id="request_m6",
        request_fingerprint="request_fp_m6",
        question_ids=("Q1",),
        metric_refs=("metric_1",),
        banner_config={"segment": ("segment_a",)},
        filters={"region": ("north",)},
        execution_options={"structure_id": structure_id},
    )
    manifest = CanonicalResultManifest(
        schema_version=schema_version,
        core_version="M5_TEST_CORE",
        result_fingerprint="result_fp_m6",
        ruleset="M5_CANONICAL_RESULTS_V1",
        b1_policy_ref="B1",
        b2_policy_ref="B2",
        b3_policy_ref="B3",
        source_spec_refs=("project_spec",),
    )
    result = CanonicalResult(
        result_schema_version=schema_version,
        result_run_id=result_run_id,
        project_id="project_m6",
        dataset_fingerprint="dataset_fp",
        project_spec_ref="project_spec",
        core_version="M5_TEST_CORE",
        qa=QAEnvelope(AggregateReleaseState.PASS_WITH_WARNINGS),
        result_fingerprint="result_fp_m6",
        manifest=manifest,
        request=request,
        slices=(total, banner, banner_b),
        bases=(base,),
        values=(value,),
        qa_events=(qa_event,),
        release=release,
    )
    return result


def result_with_significance(status: StatisticalState) -> CanonicalResult:
    result = canonical_result()
    relation = SignificanceRelation(
        comparison_id="comparison_1",
        question_id="Q1",
        metric_id="metric_1",
        analytical_scope="banner",
        family_id="family_1",
        left_slice_id="slice_banner_a",
        right_slice_id="slice_banner_b",
        test_id="test_1",
        test_version="B2_V1",
        confidence=0.95,
        status=status,
        raw_p_value=0.01 if status is StatisticalState.SIGNIFICANT else 0.6,
        adjusted_p_value=0.02 if status is StatisticalState.SIGNIFICANT else 0.6,
    )
    return replace(result, comparisons=(relation,))
