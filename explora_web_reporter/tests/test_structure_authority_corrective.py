from src.analytics_core.structure import (
    StructureEvaluationContext,
    evaluate_structure,
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
    DenominatorUnit,
    DuplicatePolicy,
    ReleaseLifecycle,
    ReleaseMode,
    ResponseStateValue,
    StructureAuthorityMode,
    StructureExecutionStatus,
    StorageEncoding,
)


def release() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="M4",
        policy_version="V1",
        source_hash="hash",
    )


def project() -> ProjectSpec:
    return ProjectSpec(
        spec_id="project_spec",
        version="1.0",
        release=release(),
        project_id="project",
        dataset_fingerprint="fingerprint",
        respondent_id_binding="respondent_id",
        project_universe_ref="u_q1",
    )


def question(**overrides) -> QuestionSpec:
    base = dict(
        spec_id="question_spec",
        version="1.0",
        release=release(),
        question_id="q1",
        physical_type="multiple",
        analytic_role="question",
        universe_ref="u_q1",
        structure_ref="structure",
    )
    base.update(overrides)
    return QuestionSpec(**base)


def universe(
    universe_id: str,
    mask: dict[str, bool],
    status=UniverseEvaluationStatus.PASS,
) -> UniverseEvaluationResult:
    eligible_n = sum(1 for value in mask.values() if value)
    return UniverseEvaluationResult(
        universe_ref=UniverseRef(universe_id),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask=dict(mask),
        input_n=len(mask),
        eligible_n=eligible_n,
        excluded_n=len(mask) - eligible_n,
        status=status,
        qa=QAEnvelope(aggregate_state=AggregateReleaseState.PASS),
    )


def ctx(respondents, values, universes=None) -> StructureEvaluationContext:
    return StructureEvaluationContext(
        respondent_ids=tuple(respondents),
        values_by_variable=values,
        universe_results={
            "u_q1": universe("u_q1", {rid: True for rid in respondents}),
            **(universes or {}),
        },
        available_variables=set(values),
        universe_ids={
            "u_q1",
            "u_row1",
            "u_row2",
            "u_col_a",
            "u_col_b",
            "u_cell_row2_b",
            "u_loop",
        },
    )


def run(spec, context, question_spec=None):
    return evaluate_structure(
        project_spec=project(),
        question_spec=question_spec or question(),
        structure_spec=spec,
        context=context,
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )


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
                "options",
                AxisRole.OPTION,
                (StructureMember("a"), StructureMember("b")),
            ),
        ),
        variable_bindings=(
            VariableBinding("b_a", "q1_a", option_id="a"),
            VariableBinding("b_b", "q1_b", option_id="b"),
        ),
        applicability_refs={"question": UniverseRef("u_q1")},
        selected_values=(1,),
        not_selected_values=(0,),
        duplicate_policy=DuplicatePolicy.ERROR,
        storage_encoding=StorageEncoding.ONE_COLUMN_PER_OPTION,
    )
    base.update(overrides)
    return StructureSpec(**base)


def test_duplicate_keep_separates_respondent_and_mention_counts() -> None:
    spec = rm_spec(
        variable_bindings=(
            VariableBinding("b_a1", "q1_a1", option_id="a"),
            VariableBinding("b_a2", "q1_a2", option_id="a"),
        ),
        duplicate_policy=DuplicatePolicy.KEEP,
        mention_denominator_scope="all_options",
    )
    result = run(
        spec,
        ctx(("r1",), {"q1_a1": {"r1": 1}, "q1_a2": {"r1": 1}}),
    )

    respondent = result.denominator_ledgers[0]
    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert respondent.denominator_unit is DenominatorUnit.RESPONDENT_OPTION
    assert respondent.denominator_n == 1
    assert respondent.selected_n == 1
    assert respondent.traceability["selected_by_option"] == {"a": 1}
    assert mention.denominator_unit is DenominatorUnit.MENTION
    assert mention.selected_n == 2
    assert mention.traceability["mention_by_option"] == {"a": 2}


def test_grid_member_specific_and_cell_applicability_compose() -> None:
    spec = rm_spec(
        structure_type="GRID_RM",
        axes=(
            StructureAxis(
                "rows",
                AxisRole.ROW,
                (
                    StructureMember("row1", universe_ref=UniverseRef("u_row1")),
                    StructureMember("row2", universe_ref=UniverseRef("u_row2")),
                ),
            ),
            StructureAxis(
                "cols",
                AxisRole.COLUMN,
                (
                    StructureMember("a", universe_ref=UniverseRef("u_col_a")),
                    StructureMember("b", universe_ref=UniverseRef("u_col_b")),
                ),
            ),
        ),
        variable_bindings=(
            VariableBinding("r1a", "r1a", row_id="row1", column_id="a"),
            VariableBinding("r1b", "r1b", row_id="row1", column_id="b"),
            VariableBinding("r2a", "r2a", row_id="row2", column_id="a"),
            VariableBinding("r2b", "r2b", row_id="row2", column_id="b"),
        ),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "cell:row2:b": UniverseRef("u_cell_row2_b"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1", "r2"),
            {
                "r1a": {"r1": 1, "r2": 1},
                "r1b": {"r1": 1, "r2": 1},
                "r2a": {"r1": 1, "r2": 1},
                "r2b": {"r1": 1, "r2": 1},
            },
            {
                "u_row1": universe("u_row1", {"r1": True, "r2": False}),
                "u_row2": universe("u_row2", {"r1": False, "r2": True}),
                "u_col_a": universe("u_col_a", {"r1": True, "r2": True}),
                "u_col_b": universe("u_col_b", {"r1": True, "r2": True}),
                "u_cell_row2_b": universe(
                    "u_cell_row2_b", {"r1": True, "r2": False}
                ),
            },
        ),
    )

    selected = [
        (record.respondent_id, record.row_id, record.column_id)
        for record in result.records
        if record.selected
    ]
    structural_missing = [
        (record.respondent_id, record.row_id, record.column_id)
        for record in result.records
        if record.structural_missing
    ]
    assert result.status is StructureExecutionStatus.PASS
    assert ("r1", "row1", "a") in selected
    assert ("r1", "row1", "b") in selected
    assert ("r2", "row2", "a") in selected
    assert ("r2", "row2", "b") in structural_missing
    assert result.denominator_ledgers[0].selected_n == 3


def test_grid_missing_optional_row_column_cell_rules_add_no_restriction() -> None:
    spec = rm_spec(
        structure_type="GRID_RM",
        axes=(
            StructureAxis("rows", AxisRole.ROW, (StructureMember("row1"),)),
            StructureAxis("cols", AxisRole.COLUMN, (StructureMember("a"),)),
        ),
        variable_bindings=(
            VariableBinding("r1a", "r1a", row_id="row1", column_id="a"),
        ),
    )
    result = run(spec, ctx(("r1",), {"r1a": {"r1": 1}}))

    assert result.status is StructureExecutionStatus.PASS
    assert result.denominator_ledgers[0].selected_n == 1


def test_loop_duplicate_identity_includes_loop_instance() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1", "l1", option_id="a", loop_instance_id="l1"),
            VariableBinding("l2", "l2", option_id="a", loop_instance_id="l2"),
        ),
        loop_instance_binding="loop_id",
        mention_denominator_scope="loop_instance",
        duplicate_policy=DuplicatePolicy.ERROR,
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1",),
            {"l1": {"r1": 1}, "l2": {"r1": 1}},
            {"u_loop": universe("u_loop", {"r1": True})},
        ),
    )

    assert result.status is StructureExecutionStatus.PASS
    assert result.denominator_ledgers[0].repeated_dependency
    assert result.denominator_ledgers[0].selected_n == 2


def test_loop_duplicate_policy_applies_inside_same_loop_instance() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1a", "l1a", option_id="a", loop_instance_id="l1"),
            VariableBinding("l1b", "l1b", option_id="a", loop_instance_id="l1"),
        ),
        loop_instance_binding="loop_id",
        duplicate_policy=DuplicatePolicy.ERROR,
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1",),
            {"l1a": {"r1": 1}, "l1b": {"r1": 1}},
            {"u_loop": universe("u_loop", {"r1": True})},
        ),
    )

    assert result.status is StructureExecutionStatus.FAIL
    assert "duplicate" in result.failures[0]


def test_exclusive_scope_respects_loop_instance() -> None:
    different_instances = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1a", "l1a", option_id="a", loop_instance_id="l1"),
            VariableBinding("l2b", "l2b", option_id="b", loop_instance_id="l2"),
        ),
        loop_instance_binding="loop_id",
        exclusive_option_ids=("a",),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    same_instance = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1a", "l1a", option_id="a", loop_instance_id="l1"),
            VariableBinding("l1b", "l1b", option_id="b", loop_instance_id="l1"),
        ),
        loop_instance_binding="loop_id",
        exclusive_option_ids=("a",),
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    loop_ctx = ctx(
        ("r1",),
        {
            "l1a": {"r1": 1},
            "l1b": {"r1": 1},
            "l2b": {"r1": 1},
        },
        {"u_loop": universe("u_loop", {"r1": True})},
    )

    assert run(different_instances, loop_ctx).status is StructureExecutionStatus.PASS
    assert run(same_instance, loop_ctx).status is StructureExecutionStatus.FAIL


def test_released_question_structure_reference_integrity() -> None:
    spec = rm_spec()

    assert run(spec, ctx(("r1",), {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}})).status is (
        StructureExecutionStatus.PASS
    )
    assert run(
        spec,
        ctx(("r1",), {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}}),
        question(structure_ref="other_structure"),
    ).status is StructureExecutionStatus.FAIL


def test_released_question_universe_consistency() -> None:
    spec = rm_spec()

    assert run(
        spec,
        ctx(("r1",), {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}}),
        question(universe_ref="u_q1"),
    ).status is StructureExecutionStatus.PASS
    assert run(
        spec,
        ctx(("r1",), {"q1_a": {"r1": 1}, "q1_b": {"r1": 0}}),
        question(universe_ref="other_universe"),
    ).status is StructureExecutionStatus.FAIL


def test_detector_disagreement_loses_to_consistent_released_chain() -> None:
    result = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=rm_spec(),
        context=StructureEvaluationContext(
            respondent_ids=("r1",),
            values_by_variable={"q1_a": {"r1": 1}, "q1_b": {"r1": 0}},
            universe_results={"u_q1": universe("u_q1", {"r1": True})},
            available_variables={"q1_a", "q1_b"},
            universe_ids={"u_q1"},
            detector_evidence={"structure_type": "RU"},
        ),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )

    assert result.status is StructureExecutionStatus.PASS_WITH_WARNINGS
    assert result.structure_type == "RM"


def test_ru_response_states_use_valid_category_and_distinct_missing_states() -> None:
    spec = rm_spec(
        structure_type="RU",
        axes=(),
        variable_bindings=(VariableBinding("ru", "ru"),),
        category_bindings=(CategoryOptionBinding("c1", "a", raw_values=(1,)),),
        selected_values=(),
        not_selected_values=(),
    )
    result = run(
        spec,
        ctx(
            ("r1", "r2", "r3", "r4"),
            {"ru": {"r1": 1, "r2": None, "r3": 1, "r4": 9}},
            {
                "u_q1": universe(
                    "u_q1",
                    {"r1": True, "r2": True, "r3": False, "r4": True},
                )
            },
        ),
    )

    states = {
        record.respondent_id: record.response_state for record in result.records
    }
    assert result.status is StructureExecutionStatus.FAIL
    assert states["r1"] is ResponseStateValue.VALID_CATEGORY
    assert states["r2"] is ResponseStateValue.ORDINARY_MISSING
    assert states["r3"] is ResponseStateValue.STRUCTURAL_MISSING
    assert states["r4"] is ResponseStateValue.INVALID_OUT_OF_DOMAIN


def grid_scope_spec(scope: str, bindings=None) -> StructureSpec:
    return rm_spec(
        structure_type="GRID_RM",
        axes=(
            StructureAxis(
                "rows",
                AxisRole.ROW,
                (StructureMember("row1"), StructureMember("row2")),
            ),
            StructureAxis(
                "cols",
                AxisRole.COLUMN,
                (StructureMember("a"), StructureMember("b")),
            ),
        ),
        variable_bindings=bindings
        or (
            VariableBinding("row1_a", "row1_a", row_id="row1", column_id="a"),
            VariableBinding("row2_a", "row2_a", row_id="row2", column_id="a"),
        ),
        mention_denominator_scope=scope,
        duplicate_policy=DuplicatePolicy.KEEP,
    )


def test_grid_rm_row_scope_filters_mentions_to_row1_only() -> None:
    result = run(
        grid_scope_spec("row:row1"),
        ctx(
            ("r1",),
            {"row1_a": {"r1": 1}, "row2_a": {"r1": 1}},
        ),
    )

    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert mention.scope_id == "mention:row:row1"
    assert mention.denominator_n == 1
    assert mention.traceability["mention_by_option"] == {"a": 1}


def test_grid_rm_row2_scope_is_independent() -> None:
    result = run(
        grid_scope_spec("row:row2"),
        ctx(
            ("r1",),
            {"row1_a": {"r1": 1}, "row2_a": {"r1": 1}},
        ),
    )

    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert mention.scope_id == "mention:row:row2"
    assert mention.denominator_n == 1


def test_grid_rm_generic_row_scope_emits_independent_row_ledgers() -> None:
    result = run(
        grid_scope_spec("row"),
        ctx(
            ("r1",),
            {"row1_a": {"r1": 1}, "row2_a": {"r1": 1}},
        ),
    )

    ledgers = {ledger.scope_id: ledger for ledger in result.denominator_ledgers}
    assert result.status is StructureExecutionStatus.PASS
    assert ledgers["mention:row:row1"].denominator_n == 1
    assert ledgers["mention:row:row2"].denominator_n == 1


def test_duplicate_keep_operates_inside_mention_scope_only() -> None:
    bindings = (
        VariableBinding("row1_a1", "row1_a1", row_id="row1", column_id="a"),
        VariableBinding("row1_a2", "row1_a2", row_id="row1", column_id="a"),
        VariableBinding("row2_a", "row2_a", row_id="row2", column_id="a"),
    )
    result = run(
        grid_scope_spec("row:row1", bindings),
        ctx(
            ("r1",),
            {
                "row1_a1": {"r1": 1},
                "row1_a2": {"r1": 1},
                "row2_a": {"r1": 1},
            },
        ),
    )

    respondent = result.denominator_ledgers[0]
    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert respondent.selected_n == 2
    assert mention.selected_n == 2
    assert mention.traceability["mention_by_option"] == {"a": 2}


def test_same_option_across_rows_does_not_merge_mention_scopes() -> None:
    result = run(
        grid_scope_spec("row"),
        ctx(
            ("r1", "r2"),
            {
                "row1_a": {"r1": 1, "r2": 0},
                "row2_a": {"r1": 0, "r2": 1},
            },
        ),
    )

    ledgers = {ledger.scope_id: ledger for ledger in result.denominator_ledgers}
    assert ledgers["mention:row:row1"].selected_n == 1
    assert ledgers["mention:row:row2"].selected_n == 1


def test_loop_rm_loop_instance_scope_filters_mentions() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1", "l1", option_id="a", loop_instance_id="l1"),
            VariableBinding("l2", "l2", option_id="b", loop_instance_id="l2"),
        ),
        loop_instance_binding="loop_id",
        mention_denominator_scope="loop_instance:l1",
        duplicate_policy=DuplicatePolicy.KEEP,
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1",),
            {"l1": {"r1": 1}, "l2": {"r1": 1}},
            {"u_loop": universe("u_loop", {"r1": True})},
        ),
    )

    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert mention.scope_id == "mention:loop_instance:l1"
    assert mention.denominator_n == 1
    assert mention.traceability["mention_by_option"] == {"a": 1}


def test_loop_rm_generic_loop_instance_scope_emits_independent_ledgers() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding("l1", "l1", option_id="a", loop_instance_id="l1"),
            VariableBinding("l2", "l2", option_id="b", loop_instance_id="l2"),
        ),
        loop_instance_binding="loop_id",
        mention_denominator_scope="loop_instance",
        duplicate_policy=DuplicatePolicy.KEEP,
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1",),
            {"l1": {"r1": 1}, "l2": {"r1": 1}},
            {"u_loop": universe("u_loop", {"r1": True})},
        ),
    )

    ledgers = {ledger.scope_id: ledger for ledger in result.denominator_ledgers}
    assert result.status is StructureExecutionStatus.PASS
    assert ledgers["mention:loop_instance:l1"].denominator_n == 1
    assert ledgers["mention:loop_instance:l2"].denominator_n == 1


def test_loop_rm_entity_scope_keeps_entities_distinct() -> None:
    spec = rm_spec(
        structure_type="LOOP_RM",
        variable_bindings=(
            VariableBinding(
                "e1_l1",
                "e1_l1",
                option_id="a",
                entity_id="e1",
                loop_instance_id="l1",
            ),
            VariableBinding(
                "e2_l1",
                "e2_l1",
                option_id="a",
                entity_id="e2",
                loop_instance_id="l1",
            ),
        ),
        loop_instance_binding="loop_id",
        mention_denominator_scope="entity",
        duplicate_policy=DuplicatePolicy.KEEP,
        applicability_refs={
            "question": UniverseRef("u_q1"),
            "loop_instance": UniverseRef("u_loop"),
        },
    )
    result = run(
        spec,
        ctx(
            ("r1",),
            {"e1_l1": {"r1": 1}, "e2_l1": {"r1": 1}},
            {"u_loop": universe("u_loop", {"r1": True})},
        ),
    )

    ledgers = {ledger.scope_id: ledger for ledger in result.denominator_ledgers}
    assert result.status is StructureExecutionStatus.PASS
    assert ledgers["mention:entity:e1"].denominator_n == 1
    assert ledgers["mention:entity:e2"].denominator_n == 1


def test_zero_valid_mentions_in_declared_scope_do_not_borrow_denominator() -> None:
    result = run(
        grid_scope_spec("row:row2"),
        ctx(
            ("r1",),
            {"row1_a": {"r1": 1}, "row2_a": {"r1": 0}},
        ),
    )

    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert mention.denominator_n == 0
    assert mention.zero_base_status == "VALID_ZERO_BASE"


def test_unknown_mention_scope_id_does_not_fall_back_to_structure() -> None:
    result = run(
        grid_scope_spec("row:missing"),
        ctx(
            ("r1",),
            {"row1_a": {"r1": 1}, "row2_a": {"r1": 1}},
        ),
    )

    assert result.status is StructureExecutionStatus.FAIL
    assert "unknown mention_denominator_scope row id" in result.failures[0]


def test_mention_scope_change_does_not_change_respondent_ledger() -> None:
    values = {"row1_a": {"r1": 1}, "row2_a": {"r1": 1}}
    row1 = run(grid_scope_spec("row:row1"), ctx(("r1",), values))
    row2 = run(grid_scope_spec("row:row2"), ctx(("r1",), values))

    assert row1.denominator_ledgers[0] == row2.denominator_ledgers[0]
    assert row1.denominator_ledgers[1].scope_id == "mention:row:row1"
    assert row2.denominator_ledgers[1].scope_id == "mention:row:row2"
