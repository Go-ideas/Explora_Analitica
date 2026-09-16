from __future__ import annotations

from dataclasses import replace

import pytest

from src.analytics_core.execution_adapter import (
    CanonicalExecutionContext,
    ExecutionAdapterError,
    SliceExecutionAuthority,
    execute_canonical_request,
)
from src.analytics_core.results import make_request_snapshot, make_slice
from src.analytics_core.structure import (
    MENTION_SCOPE_IDENTITY_SCHEMA_VERSION,
    StructureEvaluationContext,
    evaluate_structure,
)
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    MentionScopeIdentity,
    MetricSpec,
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
from src.contracts.validators import ContractValidationError, validate_structure_spec
from src.contracts.vocabulary import (
    AggregateReleaseState,
    AxisRole,
    DenominatorUnit,
    DuplicatePolicy,
    MentionScopeType,
    ReleaseLifecycle,
    ReleaseMode,
    StructureAuthorityMode,
    StructureExecutionStatus,
    StorageEncoding,
)


def release() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-16T00:00:00Z",
        policy_id="M4",
        policy_version="MSCOPE_V1",
        source_hash="hash",
    )


def project() -> ProjectSpec:
    return ProjectSpec(
        spec_id="project_spec",
        version="1.0",
        release=release(),
        project_id="project",
        dataset_fingerprint="fingerprint",
        respondent_id_binding="rid",
        project_universe_ref="u",
    )


def question() -> QuestionSpec:
    return QuestionSpec(
        spec_id="question_spec",
        version="1.0",
        release=release(),
        question_id="Q_DELIVERY_APPS",
        physical_type="multiple",
        analytic_role="question",
        universe_ref="u",
        structure_ref="STR_Q_DELIVERY_APPS_RM_V1",
    )


def universe(mask: dict[str, bool] | None = None) -> UniverseEvaluationResult:
    respondent_mask = mask or {"r1": True, "r2": True}
    return UniverseEvaluationResult(
        universe_ref=UniverseRef("u"),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask=respondent_mask,
        input_n=len(respondent_mask),
        eligible_n=sum(1 for value in respondent_mask.values() if value),
        excluded_n=sum(1 for value in respondent_mask.values() if not value),
        status=UniverseEvaluationStatus.PASS,
        qa=QAEnvelope(AggregateReleaseState.PASS),
    )


def scope(
    scope_type: MentionScopeType | str,
    scope_ref: str | None,
    *,
    schema_version: str = MENTION_SCOPE_IDENTITY_SCHEMA_VERSION,
) -> MentionScopeIdentity:
    return MentionScopeIdentity(schema_version, scope_type, scope_ref)


def rm_spec(**overrides) -> StructureSpec:
    base = dict(
        spec_id="structure_spec",
        version="1.0",
        release=release(),
        structure_id="STR_Q_DELIVERY_APPS_RM_V1",
        structure_type="GRID_RM",
        parent_question_ref="Q_DELIVERY_APPS",
        axes=(
            StructureAxis(
                "rows",
                AxisRole.ROW,
                (StructureMember("row1"), StructureMember("row2")),
            ),
            StructureAxis(
                "entities",
                AxisRole.ENTITY,
                (StructureMember("entity1"), StructureMember("entity2")),
            ),
            StructureAxis(
                "options",
                AxisRole.COLUMN,
                (StructureMember("opt_a"), StructureMember("opt_b")),
            ),
        ),
        variable_bindings=(
            VariableBinding(
                "row1_a",
                "row1_a",
                row_id="row1",
                entity_id="entity1",
                option_id="opt_a",
                loop_instance_id="loop1",
            ),
            VariableBinding(
                "row2_b",
                "row2_b",
                row_id="row2",
                entity_id="entity2",
                option_id="opt_b",
                loop_instance_id="loop2",
            ),
        ),
        applicability_refs={"question": UniverseRef("u")},
        selected_values=(1,),
        not_selected_values=(0,),
        duplicate_policy=DuplicatePolicy.ERROR,
        storage_encoding=StorageEncoding.ONE_COLUMN_PER_OPTION,
        mention_denominator_scope=scope(
            MentionScopeType.PARENT_RM,
            "STR_Q_DELIVERY_APPS_RM_V1",
        ),
    )
    base.update(overrides)
    return StructureSpec(**base)


def ctx(values: dict[str, dict[str, int]] | None = None) -> StructureEvaluationContext:
    return StructureEvaluationContext(
        respondent_ids=("r1", "r2"),
        values_by_variable=values
        or {
            "row1_a": {"r1": 1, "r2": 0},
            "row2_b": {"r1": 1, "r2": 1},
        },
        universe_results={"u": universe()},
        available_variables={"row1_a", "row2_b"},
        universe_ids={"u"},
    )


def run(spec: StructureSpec):
    return evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=spec,
        context=ctx(),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )


def metric(expected_scope: object | None = None) -> MetricSpec:
    params = {}
    if expected_scope is not None:
        params["mention_denominator_scope"] = expected_scope
    return MetricSpec(
        spec_id="metric_spec",
        version="1.0",
        release=release(),
        metric_id="M_MENTION",
        formula_id="RM_MENTION_PROPORTION",
        question_ref="Q_DELIVERY_APPS",
        universe_ref="u",
        denominator_policy="released",
        missing_behavior="released",
        parameters=params,
    )


def execute(result, expected_scope: object | None = None):
    return execute_canonical_request(
        CanonicalExecutionContext(
            project_id="project",
            dataset_fingerprint="fingerprint",
            project_spec_ref="project_spec",
            request=make_request_snapshot(
                question_ids=("Q_DELIVERY_APPS",),
            metric_refs=("M_MENTION",),
            execution_options={
                "runtime_fingerprint": "runtime",
                "slice_authority": "explicit_total",
            },
            ),
            question_id="Q_DELIVERY_APPS",
            structure_ref=result.structure_id,
            structure_result=result,
            universe_result=universe(),
            metric_specs=(metric(expected_scope),),
            runtime_fingerprint="runtime",
            slices=(
                SliceExecutionAuthority(
                    make_slice(
                        is_total=True,
                        configuration={"authority": "explicit_total"},
                    ),
                    universe(),
                ),
            ),
            b3_release_evidence=True,
        )
    )


def test_mscope_001_parent_rm_valid_identity_passes() -> None:
    result = run(rm_spec())
    assert result.status is StructureExecutionStatus.PASS


def test_mscope_002_parent_rm_released_structure_ref_creates_mention_ledger() -> None:
    result = run(rm_spec())
    mention = result.denominator_ledgers[1]
    assert mention.denominator_unit is DenominatorUnit.MENTION
    assert mention.resolved_scope_identity == scope(
        MentionScopeType.PARENT_RM,
        "STR_Q_DELIVERY_APPS_RM_V1",
    )


def test_mscope_003_unknown_scope_type_fails_closed() -> None:
    result = run(rm_spec(mention_denominator_scope=scope("UNKNOWN", None)))
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_004_missing_required_parent_rm_scope_ref_fails_closed() -> None:
    result = run(
        rm_spec(
            mention_denominator_scope=scope(MentionScopeType.PARENT_RM, None)
        )
    )
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_005_dangling_structure_ref_fails_closed() -> None:
    result = run(
        rm_spec(
            mention_denominator_scope=scope(
                MentionScopeType.PARENT_RM,
                "STR_MISSING",
            )
        )
    )
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_006_incompatible_ref_type_fails_closed() -> None:
    result = run(
        rm_spec(mention_denominator_scope=scope(MentionScopeType.ROW, "entity1"))
    )
    assert result.status is StructureExecutionStatus.FAIL


@pytest.mark.parametrize("token", ["structure", "parent_structure", "all_options"])
def test_mscope_007_to_009_parent_legacy_compatibility_preserved(token: str) -> None:
    result = run(rm_spec(mention_denominator_scope=token))
    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert mention.resolved_scope_identity == scope(
        MentionScopeType.PARENT_RM,
        "STR_Q_DELIVERY_APPS_RM_V1",
    )


def test_mscope_010_row_compatibility_preserved() -> None:
    result = run(rm_spec(mention_denominator_scope="row:row1"))
    assert result.denominator_ledgers[1].resolved_scope_identity == scope(
        MentionScopeType.ROW,
        "row1",
    )


def test_mscope_011_entity_compatibility_preserved() -> None:
    result = run(rm_spec(mention_denominator_scope="entity:entity1"))
    assert result.denominator_ledgers[1].resolved_scope_identity == scope(
        MentionScopeType.ENTITY,
        "entity1",
    )


def test_mscope_012_loop_instance_compatibility_preserved() -> None:
    result = run(rm_spec(mention_denominator_scope="loop_instance:loop1"))
    assert result.denominator_ledgers[1].resolved_scope_identity == scope(
        MentionScopeType.LOOP_INSTANCE,
        "loop1",
    )


def test_mscope_013_unknown_legacy_token_fails_closed() -> None:
    result = run(rm_spec(mention_denominator_scope="anything"))
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_014_ledger_denominator_unit_is_mention() -> None:
    result = run(rm_spec())
    assert result.denominator_ledgers[1].denominator_unit is DenominatorUnit.MENTION


def test_mscope_015_ledger_preserves_typed_scope_identity() -> None:
    result = run(rm_spec(mention_denominator_scope="row"))
    mention = result.denominator_ledgers[1]
    assert mention.requested_scope_identity == scope(MentionScopeType.ROW, None)
    assert mention.resolved_scope_identity == scope(MentionScopeType.ROW, "row1")


def test_mscope_016_ba03_parent_rm_numerator_base_semantics() -> None:
    result = run(rm_spec())
    canonical = execute(
        result,
        scope(MentionScopeType.PARENT_RM, "STR_Q_DELIVERY_APPS_RM_V1"),
    )
    value = next(item for item in canonical.values if item.option_id == "opt_b")
    assert value.numerator == 2
    assert value.denominator == 3
    base = next(item for item in canonical.bases if item.base_id == value.base_id)
    assert base.denominator_unit is DenominatorUnit.MENTION


def test_mscope_017_rm_respondent_ledger_unchanged() -> None:
    parent = run(rm_spec())
    row = run(rm_spec(mention_denominator_scope="row:row1"))
    assert parent.denominator_ledgers[0] == row.denominator_ledgers[0]


def test_mscope_018_duplicate_policy_unchanged() -> None:
    duplicate_bindings = (
        VariableBinding(
            "dup_a1",
            "row1_a",
            row_id="row1",
            option_id="opt_a",
        ),
        VariableBinding(
            "dup_a2",
            "row1_a",
            row_id="row1",
            option_id="opt_a",
        ),
    )
    values = {
        "row1_a": {"r1": 1, "r2": 0},
    }
    keep = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=rm_spec(
            structure_type="RM",
            axes=(
                StructureAxis(
                    "options",
                    AxisRole.OPTION,
                    (StructureMember("opt_a"),),
                ),
            ),
            variable_bindings=duplicate_bindings,
            mention_denominator_scope="row:row1",
            duplicate_policy=DuplicatePolicy.KEEP,
        ),
        context=ctx(values),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    respondent = keep.denominator_ledgers[0]
    mention = keep.denominator_ledgers[1]

    assert keep.status is StructureExecutionStatus.PASS
    assert respondent.selected_n == 1
    assert respondent.traceability["selected_by_option"] == {"opt_a": 1}
    assert mention.selected_n == 2
    assert mention.traceability["mention_by_option"] == {"opt_a": 2}

    deduplicated = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=rm_spec(
            structure_type="RM",
            axes=(
                StructureAxis(
                    "options",
                    AxisRole.OPTION,
                    (StructureMember("opt_a"),),
                ),
            ),
            variable_bindings=duplicate_bindings,
            mention_denominator_scope="row:row1",
            duplicate_policy=DuplicatePolicy.DEDUPLICATE_BY_CATEGORY,
        ),
        context=ctx(values),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    assert deduplicated.status is StructureExecutionStatus.PASS
    assert deduplicated.denominator_ledgers[1].selected_n == 1

    error = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=rm_spec(
            structure_type="RM",
            axes=(
                StructureAxis(
                    "options",
                    AxisRole.OPTION,
                    (StructureMember("opt_a"),),
                ),
            ),
            variable_bindings=duplicate_bindings,
            mention_denominator_scope="row:row1",
            duplicate_policy=DuplicatePolicy.ERROR,
        ),
        context=ctx(values),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    assert error.status is StructureExecutionStatus.FAIL
    assert "duplicate selected mention" in error.failures[0]


def test_mscope_019_exclusive_policy_unchanged() -> None:
    spec = rm_spec(
        structure_type="RM",
        axes=(
            StructureAxis(
                "options",
                AxisRole.OPTION,
                (StructureMember("opt_a"), StructureMember("opt_b")),
            ),
        ),
        variable_bindings=(
            VariableBinding("a", "row1_a", option_id="opt_a"),
            VariableBinding("b", "row2_b", option_id="opt_b"),
        ),
        exclusive_option_ids=("opt_a",),
    )
    result = run(spec)
    assert result.status is StructureExecutionStatus.FAIL
    assert "exclusive" in result.failures[0]


def test_mscope_020_zero_mention_base_unchanged() -> None:
    zero = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=rm_spec(mention_denominator_scope="row:row1"),
        context=ctx({"row1_a": {"r1": 0, "r2": 0}, "row2_b": {"r1": 1, "r2": 1}}),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    assert zero.denominator_ledgers[1].zero_base_status == "VALID_ZERO_BASE"


def test_mscope_021_unknown_schema_version_fails_closed() -> None:
    result = run(
        rm_spec(
            mention_denominator_scope=scope(
                MentionScopeType.PARENT_RM,
                "STR_Q_DELIVERY_APPS_RM_V1",
                schema_version="OTHER",
            )
        )
    )
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_022_row_entity_alias_maps_to_entity_null() -> None:
    result = run(rm_spec(mention_denominator_scope="row/entity"))
    assert result.denominator_ledgers[1].requested_scope_identity == scope(
        MentionScopeType.ENTITY,
        None,
    )


def test_mscope_023_parent_rm_question_id_token_fails_closed() -> None:
    result = run(rm_spec(mention_denominator_scope="parent_rm:Q_DELIVERY_APPS"))
    assert result.status is StructureExecutionStatus.FAIL


def test_mscope_024_null_expansion_emits_separate_ledgers_not_pooled() -> None:
    row = run(rm_spec(mention_denominator_scope="row"))
    entity = run(rm_spec(mention_denominator_scope="entity"))
    loop = run(rm_spec(mention_denominator_scope="loop_instance"))
    assert [ledger.resolved_scope_identity.scope_ref for ledger in row.denominator_ledgers[1:]] == [
        "row1",
        "row2",
    ]
    assert [ledger.resolved_scope_identity.scope_ref for ledger in entity.denominator_ledgers[1:]] == [
        "entity1",
        "entity2",
    ]
    assert [ledger.resolved_scope_identity.scope_ref for ledger in loop.denominator_ledgers[1:]] == [
        "loop1",
        "loop2",
    ]


def test_mscope_025_scope_registry_only_from_released_structure_spec() -> None:
    spec = rm_spec(
        structure_type="RM",
        axes=(
            StructureAxis(
                "options",
                AxisRole.OPTION,
                (StructureMember("opt_a"),),
            ),
        ),
        variable_bindings=(
            VariableBinding(
                "declared_row_binding",
                "row1_a",
                row_id="declared_binding_row",
                option_id="opt_a",
            ),
        ),
        mention_denominator_scope="row:declared_binding_row",
    )
    empty_context = StructureEvaluationContext(
        respondent_ids=(),
        values_by_variable={"row1_a": {}},
        universe_results={"u": universe({})},
        available_variables={"row1_a"},
        universe_ids={"u"},
    )
    result = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=spec,
        context=empty_context,
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    mention = result.denominator_ledgers[1]
    assert result.status is StructureExecutionStatus.PASS
    assert len(result.records) == 0
    assert mention.resolved_scope_identity == scope(
        MentionScopeType.ROW,
        "declared_binding_row",
    )
    assert mention.zero_base_status == "VALID_ZERO_BASE"

    undeclared = evaluate_structure(
        project_spec=project(),
        question_spec=question(),
        structure_spec=replace(spec, mention_denominator_scope="row:observed_only"),
        context=empty_context,
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    assert undeclared.status is StructureExecutionStatus.FAIL
    assert "unknown mention_denominator_scope row id" in undeclared.failures[0]


def test_mscope_026_m5_parent_rm_matching_uses_exact_typed_identity() -> None:
    result = run(rm_spec())
    canonical = execute(
        result,
        scope(MentionScopeType.PARENT_RM, "STR_Q_DELIVERY_APPS_RM_V1"),
    )
    assert canonical.values


def test_mscope_027_m5_typed_mismatch_fails_closed() -> None:
    result = run(rm_spec())
    with pytest.raises(ExecutionAdapterError):
        execute(result, scope(MentionScopeType.PARENT_RM, "OTHER"))


def test_mscope_028_m5_provenance_preserves_typed_scope_identity() -> None:
    result = run(rm_spec())
    canonical = execute(
        result,
        scope(MentionScopeType.PARENT_RM, "STR_Q_DELIVERY_APPS_RM_V1"),
    )
    refs = canonical.values[0].provenance_refs
    assert "structure:STR_Q_DELIVERY_APPS_RM_V1" in refs
    assert "m4_resolved_scope_type:PARENT_RM" in refs
    assert "m4_resolved_scope_ref:STR_Q_DELIVERY_APPS_RM_V1" in refs


def test_validate_released_group_is_reserved_unsupported_v1() -> None:
    with pytest.raises(ContractValidationError):
        validate_structure_spec(
            rm_spec(
                mention_denominator_scope=scope(
                    MentionScopeType.RELEASED_GROUP,
                    "group",
                )
            ),
            enforce_m4=True,
        )
