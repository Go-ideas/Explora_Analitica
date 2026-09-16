from __future__ import annotations

from dataclasses import replace

from src.analytics_core.results import (
    assemble_canonical_result,
    base_from_ledger,
    make_request_snapshot,
    make_slice,
    qa_event,
    transport_significance,
    value_from_formula,
)
from src.analytics_core.result_identity import result_fingerprint
from src.analytics_core.structure import DenominatorLedger
from src.contracts.models import MetricSpec, ReleaseMetadata, SignificanceComparison, UniverseRef
from src.contracts.vocabulary import (
    DenominatorUnit,
    QADomain,
    QAIssueState,
    QAScopeType,
    ReleaseLifecycle,
    ReleaseMode,
    StatisticalState,
)


def _result(run_id: str = "run-a", *, label: str = "Total"):
    request = make_request_snapshot(
        question_ids=("q1",),
        metric_refs=("metric_prop",),
        banner_config={"dimension_id": "age", "label": "Age"},
        filters={"region": {"values": ("north",), "label": "North"}},
        execution_options={"structure_authority": "released_spec"},
    )
    total = make_slice(is_total=True, label=label)
    return assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=request,
        slices=(total,),
        bases=(),
        values=(),
        result_run_id=run_id,
    )


def _with_release_reasons(result, reasons: tuple[str, ...], *, run_id: str | None = None):
    return replace(
        result,
        result_run_id=run_id or result.result_run_id,
        release=replace(result.release, reasons=reasons),
        result_fingerprint=None,
        manifest=None,
    )


def test_result_run_id_is_unique_but_not_fingerprint_material() -> None:
    first = _result("run-a")
    second = _result("run-b")

    assert first.result_run_id != second.result_run_id
    assert first.result_fingerprint == second.result_fingerprint


def test_result_run_id_with_release_reasons_is_not_fingerprint_material() -> None:
    first = _with_release_reasons(_result("run-a"), ("R1", "R2"))
    second = _with_release_reasons(_result("run-b"), ("R2", "R1"))

    assert first.result_run_id != second.result_run_id
    assert result_fingerprint(first) == result_fingerprint(second)


def test_execution_timestamp_with_release_reasons_is_not_fingerprint_material() -> None:
    first = replace(
        _with_release_reasons(_result("run-a"), ("R1", "R2")),
        base_records=({"metric": "m1", "execution_timestamp": "2026-09-14T00:00:00Z"},),
    )
    second = replace(
        _with_release_reasons(_result("run-b"), ("R2", "R1")),
        base_records=({"metric": "m1", "execution_timestamp": "2026-09-15T00:00:00Z"},),
    )

    assert result_fingerprint(first) == result_fingerprint(second)


def test_material_analytical_change_changes_result_fingerprint() -> None:
    first = _result("run-a")
    changed = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset-v2",
        project_spec_ref="project_spec",
        core_version="m5",
        request=first.request,
        slices=first.slices,
        bases=(),
        values=(),
        result_run_id="run-b",
    )

    assert first.result_fingerprint != changed.result_fingerprint


def test_label_only_slice_change_does_not_change_fingerprint() -> None:
    first = _result("run-a", label="Total")
    relabeled = replace(first.slices[0], label="Todos")
    second = replace(
        first,
        result_run_id="run-b",
        slices=(relabeled,),
        result_fingerprint=None,
        manifest=None,
    )

    assert result_fingerprint(first) == result_fingerprint(second)


def test_request_identity_ignores_labels_but_preserves_semantics() -> None:
    first = make_request_snapshot(
        question_ids=("q1",),
        metric_refs=("m1",),
        banner_config={"dimension_id": "age", "label": "Age"},
    )
    second = make_request_snapshot(
        question_ids=("q1",),
        metric_refs=("m1",),
        banner_config={"dimension_id": "age", "label": "Edad"},
    )
    changed = make_request_snapshot(
        question_ids=("q2",),
        metric_refs=("m1",),
        banner_config={"dimension_id": "age", "label": "Age"},
    )

    assert first.request_fingerprint == second.request_fingerprint
    assert first.request_fingerprint != changed.request_fingerprint


def test_slice_identity_ignores_visual_label_and_order_metadata() -> None:
    first = make_slice(
        is_total=False,
        banner_dimension_id="age",
        member_id="18_24",
        configuration={"sort_label": "A"},
        label="18-24",
    )
    second = make_slice(
        is_total=False,
        banner_dimension_id="age",
        member_id="18_24",
        configuration={"sort_label": "A"},
        label="18 a 24",
    )

    assert first.slice_id == second.slice_id
    assert first.slice_fingerprint == second.slice_fingerprint


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


def _metric() -> MetricSpec:
    return MetricSpec(
        spec_id="metric_spec",
        version="1.0",
        release=_release(),
        metric_id="metric",
        formula_id="PROPORTION",
        question_ref="q1",
        universe_ref="u1",
        denominator_policy="explicit",
        missing_behavior="exclude",
    )


def _ledger(scope: str, n: int) -> DenominatorLedger:
    return DenominatorLedger(
        scope_id=scope,
        metric_id=scope,
        denominator_unit=DenominatorUnit.RESPONDENT,
        denominator_n=n,
        valid_n=n,
        selected_n=n,
        not_selected_n=0,
        ordinary_missing_n=0,
        structural_missing_n=0,
        invalid_n=0,
        zero_base_status="NONZERO_BASE",
    )


def test_result_fingerprint_is_permutation_invariant_for_collections() -> None:
    request = make_request_snapshot(question_ids=("q1",), metric_refs=("metric",))
    slice_a = make_slice(is_total=False, banner_dimension_id="age", member_id="a")
    slice_b = make_slice(is_total=False, banner_dimension_id="age", member_id="b")
    base_a = base_from_ledger(
        _ledger("scope-a", 10),
        result_run_id="run-a",
        question_id="q1",
        structure_id="s1",
        slice_id=slice_a.slice_id,
        universe_ref=UniverseRef("u1"),
    )
    base_b = base_from_ledger(
        _ledger("scope-b", 10),
        result_run_id="run-a",
        question_id="q1",
        structure_id="s1",
        slice_id=slice_b.slice_id,
        universe_ref=UniverseRef("u1"),
    )
    value_a = value_from_formula(
        _metric(),
        base_a,
        structure_type="RU",
        result_run_id="run-a",
        numerator=1,
        denominator=10,
    )
    value_b = value_from_formula(
        _metric(),
        base_b,
        structure_type="RU",
        result_run_id="run-a",
        numerator=2,
        denominator=10,
    )
    qa_a = qa_event(
        qa_domain=QADomain.METRIC,
        code="A",
        state=QAIssueState.WARN,
        blocking=False,
        scope_type=QAScopeType.VALUE,
        message="a",
    )
    qa_b = qa_event(
        qa_domain=QADomain.METRIC,
        code="B",
        state=QAIssueState.WARN,
        blocking=False,
        scope_type=QAScopeType.VALUE,
        message="b",
    )
    comparison = SignificanceComparison(
        left_member_id="a",
        right_member_id="b",
        family_id="f",
        test_id="z",
        test_version="B2_V1",
        policy_version="B2_V1",
        confidence=0.95,
        alpha=0.05,
        sidedness="two_sided",
        status=StatisticalState.NOT_SIGNIFICANT,
        reason_code="OK",
    )
    relation = transport_significance(
        comparison,
        result_run_id="run-a",
        question_id="q1",
        metric_id="metric",
        analytical_scope="scope",
        left_slice_id=slice_a.slice_id,
        right_slice_id=slice_b.slice_id,
    )

    first = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=request,
        slices=(slice_a, slice_b),
        bases=(base_a, base_b),
        values=(value_a, value_b),
        comparisons=(relation,),
        qa_events=(qa_a, qa_b),
        result_run_id="run-a",
    )
    second = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=request,
        slices=(slice_b, slice_a),
        bases=(base_b, base_a),
        values=(value_b, value_a),
        comparisons=(relation,),
        qa_events=(qa_b, qa_a),
        result_run_id="run-b",
    )

    assert first.result_fingerprint == second.result_fingerprint


def test_release_reason_order_is_not_fingerprint_material() -> None:
    first = _with_release_reasons(_result("run-a"), ("R1", "R2"))
    second = _with_release_reasons(_result("run-b"), ("R2", "R1"))

    assert result_fingerprint(first) == result_fingerprint(second)


def test_release_reason_semantic_change_changes_fingerprint() -> None:
    first = _with_release_reasons(_result("run-a"), ("R1", "R2"))
    changed = _with_release_reasons(_result("run-b"), ("R1", "R3"))

    assert result_fingerprint(first) != result_fingerprint(changed)


def test_qa_event_and_release_reason_order_are_independently_canonicalized() -> None:
    qa_a = qa_event(
        qa_domain=QADomain.METRIC,
        code="A",
        state=QAIssueState.WARN,
        blocking=False,
        scope_type=QAScopeType.VALUE,
        message="a",
    )
    qa_b = qa_event(
        qa_domain=QADomain.METRIC,
        code="B",
        state=QAIssueState.WARN,
        blocking=False,
        scope_type=QAScopeType.VALUE,
        message="b",
    )
    first = replace(
        _with_release_reasons(_result("run-a"), ("R1", "R2")),
        qa_events=(qa_a, qa_b),
    )
    second = replace(
        _with_release_reasons(_result("run-b"), ("R2", "R1")),
        qa_events=(qa_b, qa_a),
    )

    assert result_fingerprint(first) == result_fingerprint(second)
