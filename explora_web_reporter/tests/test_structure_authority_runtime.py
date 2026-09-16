import ast
from pathlib import Path

import pytest

from src.analytics_core.structure import (
    STRUCTURE_RUNTIME_RULES_VERSION,
    StructureEvaluationContext,
    compare_legacy_structure,
    evaluate_structure,
    resolve_structure_authority_mode,
)
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    CategoryOptionBinding,
    ProjectSpec,
    QAEnvelope,
    QuestionSpec,
    ReleaseMetadata,
    StructureAxis,
    StructureMember,
    StructureSpec,
    UniverseRef,
    VariableBinding,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    AxisRole,
    CompletionPolicy,
    DenominatorUnit,
    DuplicatePolicy,
    LegacyStructureComparisonStatus,
    ReleaseLifecycle,
    ReleaseMode,
    ResponseStateValue,
    StructureAuthorityMode,
    StructureExecutionStatus,
    StorageEncoding,
)


RESPONDENTS = ("r1", "r2", "r3")


def release(state=ReleaseLifecycle.RELEASED) -> ReleaseMetadata:
    return ReleaseMetadata(
        state=state,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="M4",
        policy_version="V1",
        source_hash="hash",
    )


def project_spec(state=ReleaseLifecycle.RELEASED) -> ProjectSpec:
    return ProjectSpec(
        spec_id="project_spec",
        version="1.0",
        release=release(state),
        project_id="project",
        dataset_fingerprint="fingerprint",
        respondent_id_binding="respondent_id",
        project_universe_ref="u_project",
    )


def question_spec(**overrides) -> QuestionSpec:
    base = dict(
        spec_id="question_spec",
        version="1.0",
        release=release(),
        question_id="q1",
        physical_type="multiple",
        analytic_role="question",
        universe_ref="u_q1",
        structure_ref="structure",
        category_refs=("a", "b"),
    )
    base.update(overrides)
    return QuestionSpec(**base)


def universe_result(
    universe_id: str = "u_q1",
    mask=None,
    status=UniverseEvaluationStatus.PASS,
) -> UniverseEvaluationResult:
    respondent_mask = (
        {"r1": True, "r2": True, "r3": True}
        if mask is None
        else dict(mask)
    )
    eligible_n = sum(1 for value in respondent_mask.values() if value)
    return UniverseEvaluationResult(
        universe_ref=UniverseRef(universe_id),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask=respondent_mask,
        input_n=len(respondent_mask),
        eligible_n=eligible_n,
        excluded_n=len(respondent_mask) - eligible_n,
        status=status,
        qa=QAEnvelope(aggregate_state=AggregateReleaseState.PASS),
    )


def context(values, universes=None, **overrides) -> StructureEvaluationContext:
    base = dict(
        respondent_ids=RESPONDENTS,
        values_by_variable=values,
        universe_results={"u_q1": universe_result(), **(universes or {})},
        available_variables=set(values),
        universe_ids={"u_q1", "u_row", "u_col", "u_cell", "u_loop"},
    )
    base.update(overrides)
    return StructureEvaluationContext(**base)


def rm_spec(**overrides) -> StructureSpec:
    base = dict(
        spec_id="structure_spec",
        version="1.0",
        release=release(),
        structure_id="structure",
        structure_type="RM",
        parent_question_ref="q1",
        axes=(
            StructureAxis(
                axis_id="options",
                role=AxisRole.OPTION,
                members=(
                    StructureMember("a", "A"),
                    StructureMember("b", "B"),
                ),
            ),
        ),
        variable_bindings=(
            VariableBinding("b_a", "q1_a", option_id="a"),
            VariableBinding("b_b", "q1_b", option_id="b"),
        ),
        applicability_refs={"question": UniverseRef("u_q1")},
        selected_values=(1,),
        not_selected_values=(0,),
        ordinary_missing_values=(99,),
        duplicate_policy=DuplicatePolicy.ERROR,
        completion_policy=CompletionPolicy.EXPLICIT_RESPONSE,
        storage_encoding=StorageEncoding.ONE_COLUMN_PER_OPTION,
        structural_zero_provenance="explicit 0 in released RM variables",
    )
    base.update(overrides)
    return StructureSpec(**base)


def evaluate(spec, ctx):
    return evaluate_structure(
        project_spec=project_spec(),
        question_spec=question_spec(),
        structure_spec=spec,
        context=ctx,
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )


def test_legacy_inference_remains_default() -> None:
    result = evaluate_structure(
        project_spec=project_spec(),
        question_spec=question_spec(),
        structure_spec=rm_spec(),
        context=context({"q1_a": {"r1": 1}, "q1_b": {"r1": 0}}),
    )

    assert resolve_structure_authority_mode(environ={}) == (
        StructureAuthorityMode.LEGACY_INFERENCE
    )
    assert result.authority_mode is StructureAuthorityMode.LEGACY_INFERENCE
    assert result.status is StructureExecutionStatus.REVIEW_REQUIRED


def test_rm_selected_and_not_selected_require_explicit_values() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {
                "q1_a": {"r1": 1, "r2": 0, "r3": 99},
                "q1_b": {"r1": 0, "r2": 1, "r3": None},
            }
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    states = {
        (record.respondent_id, record.option_id): record.response_state
        for record in result.records
    }
    assert states[("r1", "a")] is ResponseStateValue.SELECTED
    assert states[("r1", "b")] is ResponseStateValue.NOT_SELECTED
    assert states[("r3", "a")] is ResponseStateValue.ORDINARY_MISSING
    assert states[("r3", "b")] is ResponseStateValue.ORDINARY_MISSING
    assert result.denominator_ledgers[0].selected_n == 2
    assert result.denominator_ledgers[0].not_selected_n == 2


def test_not_selected_with_applicable_false_becomes_structural_missing() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 0}, "q1_b": {"r1": 0}},
            universes={"u_q1": universe_result(mask={"r1": False})},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert all(record.structural_missing for record in result.records)
    assert not any(record.not_selected for record in result.records)


def test_not_answered_only_inside_question_universe() -> None:
    result = evaluate(
        rm_spec(completion_policy=CompletionPolicy.MISSING_SET_UNANSWERED),
        context(
            {"q1_a": {"r1": None, "r2": None}, "q1_b": {"r1": 0, "r2": 0}},
            universes={"u_q1": universe_result(mask={"r1": True, "r2": False})},
            respondent_ids=("r1", "r2"),
        ),
    )

    states = {
        (record.respondent_id, record.binding_id): record.response_state
        for record in result.records
    }
    assert states[("r1", "b_a")] is ResponseStateValue.NOT_ANSWERED
    assert states[("r2", "b_a")] is ResponseStateValue.STRUCTURAL_MISSING


def test_missing_field_blocks_but_missing_value_is_ordinary_missing() -> None:
    missing_value = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": None}, "q1_b": {"r1": 1}},
            respondent_ids=("r1",),
        ),
    )
    missing_field = evaluate(
        rm_spec(),
        context({"q1_a": {"r1": None}}, respondent_ids=("r1",)),
    )

    assert missing_value.status is StructureExecutionStatus.PASS
    assert any(record.ordinary_missing for record in missing_value.records)
    assert missing_field.status is StructureExecutionStatus.FAIL
    assert "unknown variable_ref" in missing_field.failures[0]


def test_zero_eligible_is_valid_zero_base_not_fail() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}},
            universes={"u_q1": universe_result(mask={"r1": False})},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.denominator_ledgers[0].zero_base_status == "VALID_ZERO_BASE"


def test_invalid_out_of_domain_blocks_execution() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 2}, "q1_b": {"r1": 0}},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.FAIL
    assert result.records[0].invalid


@pytest.mark.parametrize("status", [UniverseEvaluationStatus.FAIL, UniverseEvaluationStatus.UNSUPPORTED])
def test_m2_universe_status_is_consumed_not_repaired(status) -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}},
            universes={"u_q1": universe_result(mask={"r1": True}, status=status)},
            respondent_ids=("r1",),
        ),
    )

    assert result.status in {
        StructureExecutionStatus.FAIL,
        StructureExecutionStatus.REVIEW_REQUIRED,
    }


def test_m2_mask_is_not_modified() -> None:
    m2_result = universe_result(mask={"r1": True, "r2": False})
    before = dict(m2_result.respondent_mask)

    evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 1, "r2": 1}, "q1_b": {"r1": 0, "r2": 0}},
            universes={"u_q1": m2_result},
            respondent_ids=("r1", "r2"),
        ),
    )

    assert m2_result.respondent_mask == before


def test_weights_do_not_change_structure_result() -> None:
    values = {"q1_a": {"r1": 1, "r2": 0}, "q1_b": {"r1": 0, "r2": 1}}
    plain = evaluate(rm_spec(), context(values, respondent_ids=("r1", "r2")))
    weighted_context = context(
        values,
        respondent_ids=("r1", "r2"),
        weight_values={"w": {"r1": float("nan"), "r2": -3}},
    )
    weighted = evaluate(rm_spec(), weighted_context)

    assert weighted.denominator_ledgers == plain.denominator_ledgers
    assert [r.response_state for r in weighted.records] == [
        r.response_state for r in plain.records
    ]


def test_duplicate_policy_keep_vs_deduplicate_vs_error() -> None:
    values = {
        "q1_a": {"r1": 1},
        "q1_a_dup": {"r1": 1},
    }
    bindings = (
        VariableBinding("b_a", "q1_a", option_id="a"),
        VariableBinding("b_a_dup", "q1_a_dup", option_id="a"),
    )

    keep = evaluate(
        rm_spec(
            variable_bindings=bindings,
            duplicate_policy=DuplicatePolicy.KEEP,
            mention_denominator_scope="all_options",
        ),
        context(values, respondent_ids=("r1",)),
    )
    dedup = evaluate(
        rm_spec(
            variable_bindings=bindings,
            duplicate_policy=DuplicatePolicy.DEDUPLICATE_BY_CATEGORY,
        ),
        context(values, respondent_ids=("r1",)),
    )
    error = evaluate(
        rm_spec(variable_bindings=bindings, duplicate_policy=DuplicatePolicy.ERROR),
        context(values, respondent_ids=("r1",)),
    )

    assert keep.denominator_ledgers[0].selected_n == 1
    assert keep.denominator_ledgers[1].selected_n == 2
    assert dedup.denominator_ledgers[0].selected_n == 1
    assert error.status is StructureExecutionStatus.FAIL


def test_exclusive_option_conflict_blocks_without_deleting_records() -> None:
    result = evaluate(
        rm_spec(exclusive_option_ids=("a",)),
        context(
            {"q1_a": {"r1": 1}, "q1_b": {"r1": 1}},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.FAIL
    assert len(result.records) == 2


def test_ru_category_mapping_and_structural_missing() -> None:
    spec = rm_spec(
        structure_type="RU",
        axes=(),
        variable_bindings=(VariableBinding("b_q1", "q1"),),
        category_bindings=(
            CategoryOptionBinding("c_a", "a", raw_values=(1,)),
            CategoryOptionBinding("c_b", "b", raw_values=(2,)),
        ),
        selected_values=(),
        not_selected_values=(),
    )
    result = evaluate(
        spec,
        context({"q1": {"r1": 1, "r2": 2}}, respondent_ids=("r1", "r2")),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.denominator_ledgers[0].denominator_unit is (
        DenominatorUnit.RESPONDENT
    )
    assert all(
        record.response_state is ResponseStateValue.VALID_CATEGORY
        for record in result.records
    )
    assert [record.category_id for record in result.records] == ["a", "b"]


def test_grid_missing_optional_scope_is_no_extra_restriction() -> None:
    spec = rm_spec(
        structure_type="GRID_RM",
        axes=(
            StructureAxis("rows", AxisRole.ROW, (StructureMember("row1"),)),
            StructureAxis("cols", AxisRole.COLUMN, (StructureMember("col1"),)),
        ),
        variable_bindings=(
            VariableBinding("b_cell", "q1_r1_c1", row_id="row1", column_id="col1"),
        ),
    )

    result = evaluate(
        spec,
        context({"q1_r1_c1": {"r1": 1}}, respondent_ids=("r1",)),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.records[0].selected


def test_grid_rm_consumes_row_column_cell_universes() -> None:
    spec = rm_spec(
        structure_type="GRID_RM",
        axes=(
            StructureAxis("rows", AxisRole.ROW, (StructureMember("row1"),)),
            StructureAxis("cols", AxisRole.COLUMN, (StructureMember("col1"),)),
        ),
        variable_bindings=(
            VariableBinding("b_cell", "q1_r1_c1", row_id="row1", column_id="col1"),
        ),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "row": UniverseRef("u_row"),
            "column": UniverseRef("u_col"),
            "cell": UniverseRef("u_cell"),
        },
    )
    result = evaluate(
        spec,
        context(
            {"q1_r1_c1": {"r1": 1, "r2": 1}},
            universes={
                "u_row": universe_result("u_row", {"r1": True, "r2": True}),
                "u_col": universe_result("u_col", {"r1": True, "r2": True}),
                "u_cell": universe_result("u_cell", {"r1": True, "r2": False}),
            },
            respondent_ids=("r1", "r2"),
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.records[0].selected
    assert result.records[1].structural_missing


def test_grid_escala_uses_category_mapping_per_row() -> None:
    spec = rm_spec(
        structure_type="GRID_ESCALA",
        axes=(StructureAxis("rows", AxisRole.ROW, (StructureMember("row1"),)),),
        variable_bindings=(VariableBinding("b_row", "q1_row", row_id="row1"),),
        category_bindings=(CategoryOptionBinding("c_a", "a", raw_values=(5,)),),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "row": UniverseRef("u_row"),
        },
        selected_values=(),
        not_selected_values=(),
    )
    result = evaluate(
        spec,
        context(
            {"q1_row": {"r1": 5}},
            universes={"u_row": universe_result("u_row", {"r1": True})},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.records[0].category_id == "a"


def test_loop_rm_reports_repeated_dependency() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        axes=(StructureAxis("loop", AxisRole.LOOP, (StructureMember("l1"),)),),
        variable_bindings=(
            VariableBinding("b_l1", "q_l1", option_id="a", loop_instance_id="l1"),
            VariableBinding("b_l2", "q_l2", option_id="a", loop_instance_id="l2"),
        ),
        loop_instance_binding="loop_id",
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = evaluate(
        spec,
        context(
            {"q_l1": {"r1": 1}, "q_l2": {"r1": 1}},
            universes={"u_loop": universe_result("u_loop", {"r1": True})},
            respondent_ids=("r1",),
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.denominator_ledgers[0].repeated_dependency


def test_loop_ru_and_loop_numerico_supported_but_not_loop_rango() -> None:
    loop_ru = rm_spec(
        structure_type="LOOP_RU",
        axes=(StructureAxis("loop", AxisRole.LOOP, (StructureMember("l1"),)),),
        variable_bindings=(
            VariableBinding("b_l1", "q_l1", loop_instance_id="l1"),
        ),
        category_bindings=(CategoryOptionBinding("c_a", "a", raw_values=("x",)),),
        loop_instance_binding="loop_id",
        selected_values=(),
        not_selected_values=(),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    loop_num = rm_spec(
        structure_type="LOOP_NUMERICO",
        axes=(StructureAxis("loop", AxisRole.LOOP, (StructureMember("l1"),)),),
        variable_bindings=(
            VariableBinding("b_l1", "q_l1", loop_instance_id="l1"),
        ),
        category_bindings=(),
        loop_instance_binding="loop_id",
        selected_values=(),
        not_selected_values=(),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    ctx = context(
        {"q_l1": {"r1": "x"}},
        universes={"u_loop": universe_result("u_loop", {"r1": True})},
        respondent_ids=("r1",),
    )

    assert evaluate(loop_ru, ctx).status is StructureExecutionStatus.PASS
    assert (
        evaluate(loop_num, context(
            {"q_l1": {"r1": 12.5}},
            universes={"u_loop": universe_result("u_loop", {"r1": True})},
            respondent_ids=("r1",),
        )).status
        is StructureExecutionStatus.PASS
    )
    assert (
        evaluate(rm_spec(structure_type="LOOP_RANGO"), ctx).status
        is StructureExecutionStatus.FAIL
    )


def test_non_released_specs_are_rejected_before_runtime_authority() -> None:
    result = evaluate_structure(
        project_spec=project_spec(ReleaseLifecycle.APPROVED),
        question_spec=question_spec(),
        structure_spec=rm_spec(),
        context=context({"q1_a": {"r1": 1}, "q1_b": {"r1": 0}}, respondent_ids=("r1",)),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )

    assert result.status is StructureExecutionStatus.FAIL
    assert "not RELEASED" in result.failures[0]


def test_detector_disagreement_never_overrides_released_spec() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}},
            respondent_ids=("r1",),
            detector_evidence={"structure_type": "RU"},
        ),
    )

    assert result.status is StructureExecutionStatus.PASS_WITH_WARNINGS
    assert result.structure_type == "RM"
    assert "RELEASED" in result.warnings[0]


def test_result_contains_renderer_neutral_qa_and_traceability() -> None:
    result = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}},
            respondent_ids=("r1",),
            traceability={"run_id": "run"},
        ),
    )

    assert result.runtime_rules_version == STRUCTURE_RUNTIME_RULES_VERSION
    assert result.qa.aggregate_state is AggregateReleaseState.PASS
    assert result.traceability["run_id"] == "run"


def test_legacy_comparison_classifies_declared_methodological_changes() -> None:
    canonical = evaluate(
        rm_spec(),
        context(
            {"q1_a": {"r1": 0}, "q1_b": {"r1": 0}},
            respondent_ids=("r1",),
        ),
    )
    comparison = compare_legacy_structure(
        canonical,
        {"structure": {"denominator_n": 0}},
        declared_difference=LegacyStructureComparisonStatus.INTENDED_CORRECTION,
        reason="legacy drops explicit structural zero option bases",
    )

    assert comparison.status is (
        LegacyStructureComparisonStatus.INTENDED_CORRECTION
    )


def test_structure_core_does_not_import_renderers_persistence_or_significance() -> None:
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src" / "analytics_core" / "structure.py").read_text())
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert not (
        imports
        & {
            "pandas",
            "streamlit",
            "plotly",
            "openpyxl",
            "sqlite3",
            "significance",
        }
    )
