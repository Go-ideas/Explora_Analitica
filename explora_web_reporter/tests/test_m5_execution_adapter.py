from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.analytics_core.execution_adapter import (
    CanonicalExecutionContext,
    ExecutionAdapterError,
    SliceExecutionAuthority,
    execute_canonical_request,
)
from src.analytics_core.results import make_request_snapshot, make_slice
from src.analytics_core.structure import (
    AnalyticalRecord,
    DenominatorLedger,
    StructureExecutionResult,
)
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    MetricSpec,
    QAEnvelope,
    QAEvent,
    ReleaseMetadata,
    RequestSnapshot,
    UniverseRef,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    DenominatorUnit,
    ReleaseLifecycle,
    ReleaseMode,
    ResponseStateValue,
    StructureAuthorityMode,
    StructureExecutionStatus,
    ValueStatus,
)


RESPONDENTS = ("r1", "r2", "r3", "r4")


def release(state: ReleaseLifecycle = ReleaseLifecycle.RELEASED) -> ReleaseMetadata:
    return ReleaseMetadata(
        state=state,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-15T00:00:00Z",
        policy_id="M5",
        policy_version="V1",
        source_hash="hash",
    )


def metric(
    metric_id: str,
    formula_id: str,
    *,
    question_ref: str = "Q_RU",
    universe_ref: str = "U",
    weight_behavior: str = "unweighted",
    parameters: dict[str, object] | None = None,
    state: ReleaseLifecycle = ReleaseLifecycle.RELEASED,
) -> MetricSpec:
    return MetricSpec(
        spec_id=f"spec_{metric_id}",
        version="1.0",
        release=release(state),
        metric_id=metric_id,
        formula_id=formula_id,
        question_ref=question_ref,
        universe_ref=universe_ref,
        denominator_policy="released",
        missing_behavior="released",
        weight_behavior=weight_behavior,
        parameters=dict(parameters or {}),
    )


def universe(mask: dict[str, bool] | None = None) -> UniverseEvaluationResult:
    respondent_mask = mask or {respondent: True for respondent in RESPONDENTS}
    return UniverseEvaluationResult(
        universe_ref=UniverseRef("U"),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask=respondent_mask,
        input_n=len(respondent_mask),
        eligible_n=sum(1 for value in respondent_mask.values() if value),
        excluded_n=sum(1 for value in respondent_mask.values() if not value),
        status=UniverseEvaluationStatus.PASS,
    )


def ledger(
    unit: DenominatorUnit,
    n: int,
    scope: str,
) -> DenominatorLedger:
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
        traceability={"duplicate_policy": "error"},
    )


def ru_result() -> StructureExecutionResult:
    return StructureExecutionResult(
        structure_id="STR_RU",
        structure_version="1.0",
        structure_type="RU",
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
        runtime_rules_version="M4",
        status=StructureExecutionStatus.PASS,
        records=(
            AnalyticalRecord("r1", "STR_RU", "Q_RU", "b", "Q_RU", ResponseStateValue.VALID_CATEGORY, category_id="A"),
            AnalyticalRecord("r2", "STR_RU", "Q_RU", "b", "Q_RU", ResponseStateValue.VALID_CATEGORY, category_id="B"),
            AnalyticalRecord("r3", "STR_RU", "Q_RU", "b", "Q_RU", ResponseStateValue.ORDINARY_MISSING, ordinary_missing=True),
            AnalyticalRecord("r4", "STR_RU", "Q_RU", "b", "Q_RU", ResponseStateValue.INVALID_OUT_OF_DOMAIN, invalid=True),
        ),
        denominator_ledgers=(ledger(DenominatorUnit.RESPONDENT, 2, "structure"),),
        qa=QAEnvelope(AggregateReleaseState.PASS),
    )


def rm_result(*, include_mention: bool = True) -> StructureExecutionResult:
    ledgers = [ledger(DenominatorUnit.RESPONDENT_OPTION, 4, "respondent")]
    if include_mention:
        ledgers.append(ledger(DenominatorUnit.MENTION, 2, "mention:parent_rm:Q_RM"))
    return StructureExecutionResult(
        structure_id="STR_RM",
        structure_version="1.0",
        structure_type="RM",
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
        runtime_rules_version="M4",
        status=StructureExecutionStatus.PASS,
        records=(
            AnalyticalRecord("r1", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.SELECTED, option_id="A", selected=True),
            AnalyticalRecord("r1", "STR_RM", "Q_RM", "b", "Q_RM#2", ResponseStateValue.NOT_SELECTED, option_id="B", not_selected=True),
            AnalyticalRecord("r2", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.NOT_SELECTED, option_id="A", not_selected=True),
            AnalyticalRecord("r2", "STR_RM", "Q_RM", "b", "Q_RM#2", ResponseStateValue.SELECTED, option_id="B", selected=True),
            AnalyticalRecord("r3", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.STRUCTURAL_MISSING, option_id="A", applicable=False, structural_missing=True),
            AnalyticalRecord("r4", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.ORDINARY_MISSING, option_id="A", ordinary_missing=True),
        ),
        denominator_ledgers=tuple(ledgers),
        qa=QAEnvelope(AggregateReleaseState.PASS),
    )


def request(request_id: str = "REQ") -> RequestSnapshot:
    snapshot = make_request_snapshot(
        question_ids=("Q",),
        metric_refs=("M",),
        execution_options={
            "runtime_fingerprint": "runtime",
            "slice_authority": "explicit_total",
        },
    )
    return replace(snapshot, request_id=request_id)


def run_result(
    structure: StructureExecutionResult,
    *metrics: MetricSpec,
    question_id: str = "Q_RU",
    slices: tuple[SliceExecutionAuthority, ...] = (),
    request_id: str = "REQ",
    request_snapshot: RequestSnapshot | None = None,
):
    effective_slices = slices or (
        SliceExecutionAuthority(
            make_slice(
                is_total=True,
                configuration={"authority": "explicit_total"},
            ),
            universe(),
        ),
    )
    if request_snapshot is None:
        snapshot = replace(
            request(request_id),
            question_ids=(question_id,),
            metric_refs=tuple(item.metric_id for item in metrics),
        )
    else:
        snapshot = request_snapshot
    return execute_canonical_request(
        CanonicalExecutionContext(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=snapshot,
            question_id=question_id,
            structure_ref=structure.structure_id,
            structure_result=structure,
            universe_result=universe(),
            metric_specs=tuple(metrics),
            runtime_fingerprint="runtime-fp",
            slices=effective_slices,
            result_run_id="run",
            b3_release_evidence=True,
        )
    )


def estimates(result):
    return {
        (value.metric_id, value.category_id or value.option_id, value.slice_id): value
        for value in result.values
    }


def test_m5a_001_ru_count_derivation() -> None:
    result = run_result(ru_result(), metric("M_COUNT", "count/v1"))

    assert estimates(result)[("M_COUNT", "A", result.slices[0].slice_id)].estimate == 1


def test_m5a_002_ru_proportion_derivation() -> None:
    result = run_result(ru_result(), metric("M_PROP", "proportion/v1"))

    assert estimates(result)[("M_PROP", "A", result.slices[0].slice_id)].estimate == 0.5


def test_m5a_003_ru_invalid_missing_follows_m4() -> None:
    result = run_result(ru_result(), metric("M_PROP", "PROPORTION"))

    value = estimates(result)[("M_PROP", "B", result.slices[0].slice_id)]
    assert value.denominator == 2
    assert value.numerator == 1


def test_m5a_004_rm_respondent_selected_numerator() -> None:
    result = run_result(rm_result(), metric("M_RM", "rm_respondent_proportion/v1", question_ref="Q_RM"), question_id="Q_RM")

    value = estimates(result)[("M_RM", "A", result.slices[0].slice_id)]
    assert value.numerator == 1


def test_m5a_005_rm_respondent_valid_denominator() -> None:
    result = run_result(rm_result(), metric("M_RM", "RM_RESPONDENT_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")

    value = estimates(result)[("M_RM", "A", result.slices[0].slice_id)]
    assert value.denominator == 2


def test_m5a_006_all_zero_valid_respondent_remains_denominator() -> None:
    structure = replace(
        rm_result(),
        records=(
            AnalyticalRecord("r1", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.NOT_SELECTED, option_id="A", not_selected=True),
            AnalyticalRecord("r2", "STR_RM", "Q_RM", "a", "Q_RM#1", ResponseStateValue.NOT_SELECTED, option_id="A", not_selected=True),
        ),
    )
    result = run_result(structure, metric("M_RM", "RM_RESPONDENT_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")

    value = result.values[0]
    assert value.numerator == 0
    assert value.denominator == 2
    assert value.value_status is ValueStatus.OK


def test_m5a_007_structural_ordinary_missing_excluded() -> None:
    result = run_result(rm_result(), metric("M_RM", "RM_RESPONDENT_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")

    assert estimates(result)[("M_RM", "A", result.slices[0].slice_id)].denominator == 2


def test_m5a_008_rm_mention_numerator() -> None:
    result = run_result(rm_result(), metric("M_MENTION", "rm_mention_proportion/v1", question_ref="Q_RM"), question_id="Q_RM")

    assert estimates(result)[("M_MENTION", "A", result.slices[0].slice_id)].numerator == 1


def test_m5a_009_rm_mention_denominator() -> None:
    result = run_result(rm_result(), metric("M_MENTION", "RM_MENTION_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")

    assert estimates(result)[("M_MENTION", "A", result.slices[0].slice_id)].denominator == 2


def test_m5a_010_respondent_vs_mention_separation() -> None:
    respondent = run_result(rm_result(), metric("M_RM", "RM_RESPONDENT_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")
    mention = run_result(rm_result(), metric("M_MENTION", "RM_MENTION_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")

    assert respondent.bases[0].denominator_unit is DenominatorUnit.RESPONDENT
    assert mention.bases[0].denominator_unit is DenominatorUnit.MENTION


def test_m5a_011_missing_mention_scope_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="missing required denominator ledger"):
        run_result(rm_result(include_mention=False), metric("M_MENTION", "RM_MENTION_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")


def test_m5a_012_event_category_proportion() -> None:
    result = run_result(ru_result(), metric("M_PROP", "PROPORTION", parameters={"category_id": "B"}))

    assert len(result.values) == 1
    assert result.values[0].category_id == "B"
    assert result.values[0].estimate == 0.5


def test_m5a_013_filtered_slice_uses_m2_authority() -> None:
    slice_a = SliceExecutionAuthority(
        make_slice(is_total=False, member_id="member", filter_refs=("FILTER",)),
        universe({"r1": True, "r2": False, "r3": False, "r4": False}),
    )
    result = run_result(
        ru_result(),
        metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}),
        slices=(slice_a,),
    )

    assert result.values[0].denominator == 1
    assert result.values[0].estimate == 1


def test_m5a_014_banner_slices_remain_separate() -> None:
    seg_a = SliceExecutionAuthority(make_slice(is_total=False, banner_dimension_id="SEG", member_id="A"), universe({"r1": True, "r2": False, "r3": False, "r4": False}))
    seg_b = SliceExecutionAuthority(make_slice(is_total=False, banner_dimension_id="SEG", member_id="B"), universe({"r1": False, "r2": True, "r3": False, "r4": False}))
    result = run_result(
        ru_result(),
        metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}),
        slices=(seg_a, seg_b),
    )

    assert len(result.slices) == 2
    assert [value.estimate for value in result.values] == [1, 0]


def test_m5a_015_unweighted_execution() -> None:
    result = run_result(ru_result(), metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}))

    assert result.bases[0].active_weight_ref is None
    assert result.bases[0].weighted_n is None


def test_m5a_016_weighted_request_without_m3_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="weighted request requires M3 result"):
        run_result(ru_result(), metric("M_PROP", "PROPORTION", weight_behavior="weighted"))


def test_m5a_017_unsupported_metric_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="unsupported adapter formula"):
        run_result(ru_result(), metric("M_BAD", "UNKNOWN_FORMULA"))


def test_m5a_018_metric_structure_incompatibility_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="metric/structure incompatibility"):
        run_result(ru_result(), metric("M_RM", "RM_RESPONDENT_PROPORTION", question_ref="Q_RM"), question_id="Q_RM")


def test_m5a_019_missing_upstream_authority_fails_closed() -> None:
    bad_universe = replace(universe(), status=UniverseEvaluationStatus.FAIL)
    with pytest.raises(ExecutionAdapterError, match="M2 universe status"):
        execute_canonical_request(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=replace(
                request(),
                question_ids=("Q_RU",),
                metric_refs=("M_PROP",),
            ),
            question_id="Q_RU",
            structure_ref="STR_RU",
            structure_result=ru_result(),
            universe_result=bad_universe,
            metric_specs=(metric("M_PROP", "PROPORTION"),),
            runtime_fingerprint="runtime-fp",
            slices=(
                SliceExecutionAuthority(
                    make_slice(
                        is_total=True,
                        configuration={"authority": "explicit_total"},
                    ),
                    universe(),
                ),
            ),
        )


def test_m5a_020_no_legacy_fallback() -> None:
    tree = ast.parse(Path("src/analytics_core/execution_adapter.py").read_text())
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(item.startswith("src.reporter") for item in imports)


def test_m5a_021_no_web_calculation_dependency() -> None:
    tree = ast.parse(Path("src/analytics_core/execution_adapter.py").read_text())
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(item.startswith("src.web_canonical") for item in imports)


def test_m5a_022_deterministic_execution_input() -> None:
    kwargs = (ru_result(), metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}))
    first = run_result(*kwargs)
    second = run_result(*kwargs)

    assert first.result_fingerprint == second.result_fingerprint


def test_m5a_023_complete_provenance() -> None:
    result = run_result(
        ru_result(),
        metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}),
        request_id="REQ-P",
    )

    refs = set(result.values[0].provenance_refs)
    assert "runtime_fp:runtime-fp" in refs
    assert f"request_fp:{result.request.request_fingerprint}" in refs
    assert "request:REQ-P" in refs
    assert "question:Q_RU" in refs
    assert "structure_ref:STR_RU" in refs
    assert "universe_ref:U" in refs
    assert "metric:M_PROP" in refs
    assert "formula:PROPORTION" in refs
    assert f"slice:{result.slices[0].slice_id}" in refs
    assert "denominator_unit:respondent" in refs
    assert "denominator_scope:structure:category:A" in refs
    assert "m2:U" in refs
    assert "m4_source_ledger:structure" in refs
    assert "weight_ref:UNWEIGHTED" in refs


def test_m5a_024_ba_01_adapter_path() -> None:
    result = run_result(ru_result(), metric("MET_Q_TOP_LEVER_COUNT_V1", "count/v1"), metric("MET_Q_TOP_LEVER_PROP_V1", "proportion/v1"), request_id="BA-01")

    assert result.request.request_id == "BA-01"
    assert len(result.values) == 4


def test_m5a_025_ba_02_adapter_path() -> None:
    result = run_result(rm_result(), metric("MET_Q_DELIVERY_APPS_RESP_PROP_V1", "rm_respondent_proportion/v1", question_ref="Q_RM"), question_id="Q_RM", request_id="BA-02")

    assert result.request.request_id == "BA-02"
    assert all(value.formula_id == "RM_RESPONDENT_PROPORTION" for value in result.values)


def test_m5a_026_ba_03_adapter_path() -> None:
    result = run_result(rm_result(), metric("MET_Q_DELIVERY_APPS_MENTION_PROP_V1", "rm_mention_proportion/v1", question_ref="Q_RM"), question_id="Q_RM", request_id="BA-03")

    assert result.request.request_id == "BA-03"
    assert all(value.formula_id == "RM_MENTION_PROPORTION" for value in result.values)


def test_m5a_027_ba_04_adapter_path() -> None:
    filtered = SliceExecutionAuthority(make_slice(is_total=False, filter_refs=("FILTER_MEMBERSHIP_V1:UBER_ONE_MEMBER",)), universe({"r1": True, "r2": False, "r3": False, "r4": False}))
    result = run_result(ru_result(), metric("MET_Q_TOP_LEVER_PROP_V1", "proportion/v1", parameters={"category_id": "A"}), slices=(filtered,), request_id="BA-04")

    assert result.request.request_id == "BA-04"
    assert result.slices[0].filter_refs == ("FILTER_MEMBERSHIP_V1:UBER_ONE_MEMBER",)


def test_m5a_028_ba_05_adapter_path() -> None:
    seg_1 = SliceExecutionAuthority(make_slice(is_total=False, banner_dimension_id="SEGMENTO", member_id="SEG_1"), universe({"r1": True, "r2": False, "r3": False, "r4": False}))
    seg_2 = SliceExecutionAuthority(make_slice(is_total=False, banner_dimension_id="SEGMENTO", member_id="SEG_2"), universe({"r1": False, "r2": True, "r3": False, "r4": False}))
    result = run_result(
        ru_result(),
        metric("MET_Q_UE_CON_POST_VERY_PROB_PROP_V1", "proportion/v1", parameters={"category_id": "A"}),
        slices=(seg_1, seg_2),
        request_id="BA-05",
    )

    assert result.request.request_id == "BA-05"
    assert [slice_.member_id for slice_ in result.slices] == ["SEG_1", "SEG_2"]


def test_corrective_explicit_total_request_and_slice_passes() -> None:
    result = run_result(
        ru_result(),
        metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}),
    )

    assert result.slices[0].is_total
    assert result.values[0].estimate == 0.5


def test_corrective_missing_slice_authority_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="missing authoritative slice"):
        execute_canonical_request(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=replace(request(), metric_refs=("M_PROP",), question_ids=("Q_RU",)),
            question_id="Q_RU",
            structure_ref="STR_RU",
            structure_result=ru_result(),
            universe_result=universe(),
            metric_specs=(metric("M_PROP", "PROPORTION"),),
            runtime_fingerprint="runtime-fp",
            slices=(),
        )


def test_corrective_filtered_request_missing_slice_fails_closed() -> None:
    filtered_request = replace(
        request(),
        metric_refs=("M_PROP",),
        question_ids=("Q_RU",),
        filters={"FILTER_MEMBERSHIP_V1": ("UBER_ONE_MEMBER",)},
        execution_options={},
    )
    with pytest.raises(ExecutionAdapterError, match="missing authoritative slice"):
        execute_canonical_request(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=filtered_request,
            question_id="Q_RU",
            structure_ref="STR_RU",
            structure_result=ru_result(),
            universe_result=universe(),
            metric_specs=(metric("M_PROP", "PROPORTION"),),
            runtime_fingerprint="runtime-fp",
            slices=(),
        )


def test_corrective_banner_request_missing_slice_fails_closed() -> None:
    banner_request = replace(
        request(),
        metric_refs=("M_PROP",),
        question_ids=("Q_RU",),
        banner_config={"banner_ref": "BANNER_SEGMENTO_V1"},
        execution_options={},
    )
    with pytest.raises(ExecutionAdapterError, match="missing authoritative slice"):
        execute_canonical_request(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=banner_request,
            question_id="Q_RU",
            structure_ref="STR_RU",
            structure_result=ru_result(),
            universe_result=universe(),
            metric_specs=(metric("M_PROP", "PROPORTION"),),
            runtime_fingerprint="runtime-fp",
            slices=(),
        )


@pytest.mark.parametrize(
    ("field_name", "message"),
    (
        ("question_id", "question_id is required"),
        ("runtime_fingerprint", "runtime_fingerprint is required"),
        ("structure_ref", "structure_ref is required"),
    ),
)
def test_corrective_required_context_identity_fails_closed(field_name: str, message: str) -> None:
    kwargs = dict(
        project_id="P",
        dataset_fingerprint="dataset",
        project_spec_ref="PROJECT_SPEC",
        request=replace(request(), metric_refs=("M_PROP",), question_ids=("Q_RU",)),
        question_id="Q_RU",
        structure_ref="STR_RU",
        structure_result=ru_result(),
        universe_result=universe(),
        metric_specs=(metric("M_PROP", "PROPORTION"),),
        runtime_fingerprint="runtime-fp",
        slices=(
            SliceExecutionAuthority(
                make_slice(is_total=True, configuration={"authority": "explicit_total"}),
                universe(),
            ),
        ),
    )
    kwargs[field_name] = ""

    with pytest.raises(ExecutionAdapterError, match=message):
        execute_canonical_request(**kwargs)


def test_corrective_missing_request_fingerprint_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="request_fingerprint is required"):
        run_result(
            ru_result(),
            metric("M_PROP", "PROPORTION"),
            request_snapshot=replace(
                request(),
                metric_refs=("M_PROP",),
                question_ids=("Q_RU",),
                request_fingerprint="",
            ),
        )


def test_corrective_missing_universe_ref_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="universe_ref is required"):
        run_result(
            ru_result(),
            metric(
                "M_PROP",
                "PROPORTION",
                parameters={"category_id": "A"},
                universe_ref="",
            ),
        )


def test_corrective_missing_metric_ref_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="metric_ref is not in request snapshot"):
        run_result(
            ru_result(),
            metric("M_PROP", "PROPORTION"),
            request_snapshot=replace(request(), metric_refs=("OTHER",)),
        )


def test_corrective_missing_formula_ref_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="formula_ref is required"):
        run_result(ru_result(), metric("M_PROP", ""))


def test_corrective_missing_m4_upstream_reference_fails_closed() -> None:
    no_ledger = replace(ru_result(), denominator_ledgers=())

    with pytest.raises(ExecutionAdapterError, match="missing required denominator ledger"):
        run_result(no_ledger, metric("M_PROP", "PROPORTION"))


def test_corrective_missing_required_m3_reference_on_weighted_request_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="weighted request requires M3 result"):
        run_result(ru_result(), metric("M_PROP", "PROPORTION", weight_behavior="weighted"))


def test_corrective_qa_refs_are_preserved() -> None:
    qa = QAEvent(
        qa_id="qa-upstream-1",
        qa_domain="STRUCTURE",
        code="UPSTREAM_QA",
        state="PASS",
        blocking=False,
        scope_type="REQUEST",
        message="upstream QA",
    )
    result = execute_canonical_request(
        CanonicalExecutionContext(
            project_id="P",
            dataset_fingerprint="dataset",
            project_spec_ref="PROJECT_SPEC",
            request=replace(request(), metric_refs=("M_PROP",), question_ids=("Q_RU",)),
            question_id="Q_RU",
            structure_ref="STR_RU",
            structure_result=ru_result(),
            universe_result=universe(),
            metric_specs=(metric("M_PROP", "PROPORTION", parameters={"category_id": "A"}),),
            runtime_fingerprint="runtime-fp",
            slices=(
                SliceExecutionAuthority(
                    make_slice(is_total=True, configuration={"authority": "explicit_total"}),
                    universe(),
                ),
            ),
            qa_events=(qa,),
            result_run_id="run",
            b3_release_evidence=True,
        )
    )

    assert "qa-upstream-1" in result.values[0].qa_refs
    assert "qa_ref:qa-upstream-1" in result.values[0].provenance_refs


def test_corrective_incomplete_slice_provenance_fails_closed() -> None:
    bad_slice = replace(
        make_slice(is_total=True, configuration={"authority": "explicit_total"}),
        slice_fingerprint="",
    )
    with pytest.raises(ExecutionAdapterError, match="slice fingerprint is required"):
        run_result(
            ru_result(),
            metric("M_PROP", "PROPORTION"),
            slices=(SliceExecutionAuthority(bad_slice, universe()),),
        )


def test_corrective_mention_scope_incompatible_fails_closed() -> None:
    with pytest.raises(ExecutionAdapterError, match="mention denominator scope is incompatible"):
        run_result(
            rm_result(),
            metric(
                "M_MENTION",
                "RM_MENTION_PROPORTION",
                question_ref="Q_RM",
                parameters={"mention_denominator_scope": "parent_rm:OTHER"},
            ),
            question_id="Q_RM",
        )
