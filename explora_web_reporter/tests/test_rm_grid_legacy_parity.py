from src.analytics_core.structure import (
    StructureEvaluationContext,
    compare_legacy_structure,
    evaluate_structure,
)
from src.analytics_core.universe import (
    UNIVERSE_EVALUATOR_RULES_VERSION,
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
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
    DuplicatePolicy,
    LegacyStructureComparisonStatus,
    ReleaseLifecycle,
    ReleaseMode,
    StructureAuthorityMode,
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


def build_result(values):
    project = ProjectSpec(
        spec_id="project_spec",
        version="1.0",
        release=release(),
        project_id="project",
        dataset_fingerprint="fingerprint",
        respondent_id_binding="respondent_id",
        project_universe_ref="u_q1",
    )
    question = QuestionSpec(
        spec_id="question_spec",
        version="1.0",
        release=release(),
        question_id="q1",
        physical_type="multiple",
        analytic_role="question",
        universe_ref="u_q1",
    )
    structure = StructureSpec(
        spec_id="structure_spec",
        version="1.0",
        release=release(),
        structure_id="rm",
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
    m2 = UniverseEvaluationResult(
        universe_ref=UniverseRef("u_q1"),
        universe_spec_version="1.0",
        evaluator_rules_version=UNIVERSE_EVALUATOR_RULES_VERSION,
        respondent_mask={"r1": True},
        input_n=1,
        eligible_n=1,
        excluded_n=0,
        status=UniverseEvaluationStatus.PASS,
        qa=QAEnvelope(aggregate_state=AggregateReleaseState.PASS),
    )
    return evaluate_structure(
        project_spec=project,
        question_spec=question,
        structure_spec=structure,
        context=StructureEvaluationContext(
            respondent_ids=("r1",),
            values_by_variable=values,
            universe_results={"u_q1": m2},
            available_variables=set(values),
            universe_ids={"u_q1"},
        ),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )


def test_legacy_parity_is_declared_only_when_ledgers_match() -> None:
    canonical = build_result({"q1_a": {"r1": 1}, "q1_b": {"r1": 0}})
    legacy = {
        "structure": {
            "denominator_n": 2,
            "valid_n": 2,
            "selected_n": 1,
            "not_selected_n": 1,
            "invalid_n": 0,
        }
    }

    comparison = compare_legacy_structure(canonical, legacy)

    assert comparison.status is LegacyStructureComparisonStatus.PARITY


def test_legacy_difference_requires_declared_classification() -> None:
    canonical = build_result({"q1_a": {"r1": 0}, "q1_b": {"r1": 0}})
    legacy = {
        "structure": {
            "denominator_n": 0,
            "valid_n": 0,
            "selected_n": 0,
            "not_selected_n": 0,
            "invalid_n": 0,
        }
    }

    unknown = compare_legacy_structure(canonical, legacy)
    declared = compare_legacy_structure(
        canonical,
        legacy,
        declared_difference=LegacyStructureComparisonStatus.INTENDED_CORRECTION,
    )

    assert unknown.status is LegacyStructureComparisonStatus.REVIEW_REQUIRED
    assert declared.status is LegacyStructureComparisonStatus.INTENDED_CORRECTION
