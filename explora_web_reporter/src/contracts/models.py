from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.contracts.vocabulary import (
    AggregateReleaseState,
    AxisRole,
    CanonicalBaseMeasure,
    ComputationStatus,
    CompletionPolicy,
    DenominatorUnit,
    DuplicatePolicy,
    LegacyCanonicalComparisonStatus,
    MentionScopeType,
    QADomain,
    QAIssueLifecycle,
    QAIssueState,
    QAReleaseStatus,
    QAScopeType,
    ReleaseLifecycle,
    ReleaseMode,
    SampleRelationship,
    StatisticalQAState,
    StatisticalState,
    StorageEncoding,
    ValueStatus,
    ValueUnit,
)


@dataclass(frozen=True)
class ReleaseMetadata:
    state: ReleaseLifecycle
    mode: ReleaseMode
    decided_by: str
    decided_at: str
    policy_id: str
    policy_version: str
    source_hash: str


@dataclass(frozen=True)
class UniverseExpression:
    operator: str
    args: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UniverseRef:
    universe_id: str


@dataclass(frozen=True)
class UniverseSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    expression: UniverseExpression
    referenced_universes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WeightSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    weight_id: str
    variable_ref: str
    provenance: str
    scope: str = "project"
    permitted_analysis_overrides: tuple[str, ...] = field(
        default_factory=tuple
    )
    missing_policy: str = "EXCLUDE_AND_QA"
    non_numeric_policy: str = "EXCLUDE_AND_QA"
    non_finite_policy: str = "FAIL"
    zero_policy: str = "VALID"
    negative_policy: str = "UNSUPPORTED_V1"
    normalization: str = "NONE"
    trimming: str = "NONE"
    weighted_significance: bool = False
    is_project_default: bool = False
    canonical_base_measures: tuple[CanonicalBaseMeasure, ...] = (
        CanonicalBaseMeasure.UNWEIGHTED_N,
        CanonicalBaseMeasure.WEIGHTED_N_RAW,
        CanonicalBaseMeasure.WEIGHTED_N,
        CanonicalBaseMeasure.EFFECTIVE_N,
    )


@dataclass(frozen=True)
class MetricSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    metric_id: str
    formula_id: str
    question_ref: str
    universe_ref: str
    denominator_policy: str
    missing_behavior: str
    denominator_policy_ref: str | None = None
    weight_behavior: str = "unweighted"
    significance_family: str = "none"
    significance_supported: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SignificanceSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    test_id: str
    test_version: str = "B2_V1"
    policy_version: str = "B2_V1"
    confidence: float = 0.95
    alpha: float = 0.05
    sidedness: str = "two_sided"
    minimum_base_rule: str = "unweighted_n>=30"
    proportion_test: str = "pooled_two_proportion_z"
    proportion_test_version: str = "B2_V1"
    mean_test: str = "welch_independent_t"
    mean_test_version: str = "B2_V1"
    expected_count_rule: str = "pooled_expected_success_failure>=5"
    adjustment: str = "HOLM"
    adjustment_version: str = "B2_V1"
    family_scope: str = (
        "same_banner_question_metric_row_or_option_slice"
    )
    total_excluded: bool = True
    sample_relationship: SampleRelationship = (
        SampleRelationship.INDEPENDENT
    )
    unsupported_behavior: str = "EXPLICIT_STATUS"
    weighted_inference: bool = False


@dataclass(frozen=True)
class SignificanceComparison:
    left_member_id: str
    right_member_id: str
    family_id: str
    test_id: str
    test_version: str
    policy_version: str
    confidence: float
    alpha: float
    sidedness: str
    status: StatisticalState
    reason_code: str
    inferential_bases: dict[str, float] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    raw_p_value: float | None = None
    adjusted_p_value: float | None = None
    adjustment_method: str | None = None
    adjustment_version: str | None = None
    direction: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    qa_state: StatisticalQAState = StatisticalQAState.PASS


@dataclass(frozen=True)
class QAIssue:
    issue_id: str
    state: QAIssueState
    lifecycle: QAIssueLifecycle
    layer: str
    message: str
    scope: str = ""


@dataclass(frozen=True)
class QAEnvelope:
    aggregate_state: AggregateReleaseState
    issues: tuple[QAIssue, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProjectSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    project_id: str
    dataset_fingerprint: str
    respondent_id_binding: str
    project_universe_ref: str
    default_weight_ref: str | None = None


@dataclass(frozen=True)
class QuestionSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    question_id: str
    physical_type: str
    analytic_role: str
    universe_ref: str
    metric_refs: tuple[str, ...] = field(default_factory=tuple)
    structure_ref: str | None = None
    category_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StructureMember:
    member_id: str
    label: str = ""
    universe_ref: UniverseRef | None = None
    parent_member_ref: str | None = None


@dataclass(frozen=True)
class StructureAxis:
    axis_id: str
    role: AxisRole | str
    members: tuple[StructureMember, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MentionScopeIdentity:
    schema_version: str
    scope_type: MentionScopeType | str
    scope_ref: str | None


@dataclass(frozen=True)
class VariableBinding:
    binding_id: str
    variable_ref: str
    role: str = "response"
    row_id: str | None = None
    column_id: str | None = None
    option_id: str | None = None
    category_id: str | None = None
    loop_instance_id: str | None = None
    entity_id: str | None = None
    required: bool = True


@dataclass(frozen=True)
class CategoryOptionBinding:
    binding_id: str
    category_id: str
    raw_values: tuple[Any, ...] = field(default_factory=tuple)
    label: str = ""
    option_id: str | None = None
    is_exclusive: bool = False


@dataclass(frozen=True)
class StructureSpec:
    spec_id: str
    version: str
    release: ReleaseMetadata
    structure_id: str
    structure_type: str
    parent_question_ref: str
    axes: tuple[StructureAxis, ...] = field(default_factory=tuple)
    variable_bindings: tuple[VariableBinding, ...] = field(
        default_factory=tuple
    )
    category_bindings: tuple[CategoryOptionBinding, ...] = field(
        default_factory=tuple
    )
    applicability_refs: dict[str, UniverseRef] = field(default_factory=dict)
    selected_values: tuple[Any, ...] = field(default_factory=tuple)
    not_selected_values: tuple[Any, ...] = field(default_factory=tuple)
    ordinary_missing_values: tuple[Any, ...] = field(default_factory=tuple)
    completion_policy: CompletionPolicy | str = (
        CompletionPolicy.EXPLICIT_RESPONSE
    )
    duplicate_policy: DuplicatePolicy | str = DuplicatePolicy.ERROR
    exclusive_option_ids: tuple[str, ...] = field(default_factory=tuple)
    storage_encoding: StorageEncoding | str = StorageEncoding.SINGLE_VARIABLE
    loop_instance_binding: str | None = None
    mention_denominator_scope: MentionScopeIdentity | str | None = None
    structural_zero_provenance: str | None = None
    structural_missing_semantics: str | None = None
    response_state_version: str = "M4_STRUCTURE_V1"


@dataclass(frozen=True)
class CanonicalResultManifest:
    schema_version: str
    core_version: str
    result_fingerprint: str
    ruleset: str
    created_at: str | None = None
    b1_policy_ref: str | None = None
    b2_policy_ref: str | None = None
    b3_policy_ref: str | None = None
    source_spec_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RequestSnapshot:
    request_id: str
    request_fingerprint: str
    question_ids: tuple[str, ...] = field(default_factory=tuple)
    metric_refs: tuple[str, ...] = field(default_factory=tuple)
    banner_config: dict[str, Any] = field(default_factory=dict)
    filters: dict[str, Any] = field(default_factory=dict)
    weight_override: str | None = None
    compatibility_profile: str | None = None
    execution_options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalSlice:
    slice_id: str
    slice_fingerprint: str
    is_total: bool
    banner_dimension_id: str | None = None
    member_id: str | None = None
    filter_refs: tuple[str, ...] = field(default_factory=tuple)
    configuration: dict[str, Any] = field(default_factory=dict)
    label: str | None = None


@dataclass(frozen=True)
class CanonicalBase:
    base_id: str
    question_id: str
    structure_id: str
    slice_id: str
    universe_ref: UniverseRef
    denominator_unit: DenominatorUnit | str
    denominator_ref: str
    denominator_scope_id: str
    unweighted_n: int
    weighted_n_raw: float | None = None
    weighted_n: float | None = None
    effective_n: float | None = None
    active_weight_ref: str | None = None
    base_status: str = "OK"
    row_id: str | None = None
    entity_id: str | None = None
    column_id: str | None = None
    option_id: str | None = None
    loop_instance_id: str | None = None
    qa_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CanonicalValue:
    value_id: str
    question_id: str
    structure_id: str
    slice_id: str
    metric_id: str
    formula_id: str
    formula_version: str
    base_id: str
    value_status: ValueStatus | str
    unit: ValueUnit | str
    estimate: float | int | None
    numerator: float | int | None = None
    denominator: float | int | None = None
    row_id: str | None = None
    entity_id: str | None = None
    column_id: str | None = None
    option_id: str | None = None
    category_id: str | None = None
    loop_instance_id: str | None = None
    significance_refs: tuple[str, ...] = field(default_factory=tuple)
    qa_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    semantic_order: int | None = None


@dataclass(frozen=True)
class SignificanceRelation:
    comparison_id: str
    question_id: str
    metric_id: str
    analytical_scope: str
    family_id: str
    left_slice_id: str
    right_slice_id: str
    test_id: str
    test_version: str
    confidence: float
    status: StatisticalState | str
    left_member_id: str | None = None
    right_member_id: str | None = None
    raw_p_value: float | None = None
    adjusted_p_value: float | None = None
    direction: str | None = None
    qa_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class QAEvent:
    qa_id: str
    qa_domain: QADomain | str
    code: str
    state: QAReleaseStatus | QAIssueState | str
    blocking: bool
    scope_type: QAScopeType | str
    message: str
    related_ids: tuple[str, ...] = field(default_factory=tuple)
    details: dict[str, Any] = field(default_factory=dict)
    source_component: str = ""
    policy_version: str = ""


@dataclass(frozen=True)
class CanonicalReleaseState:
    computation_status: ComputationStatus | str
    qa_release_status: QAReleaseStatus | str
    releasable: bool
    policy_ref: str = "B3"
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FormulaRegistryEntry:
    formula_id: str
    formula_version: str
    input_requirements: tuple[str, ...]
    denominator_requirements: tuple[str, ...]
    supported_structures: tuple[str, ...]
    supported_weight_modes: tuple[str, ...]
    significance_compatible: bool = False


@dataclass(frozen=True)
class LegacyCanonicalComparison:
    classification: LegacyCanonicalComparisonStatus | str
    deltas: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    reason: str = ""
    blocking: bool = False


@dataclass(frozen=True)
class CanonicalResult:
    result_schema_version: str
    result_run_id: str
    project_id: str
    dataset_fingerprint: str
    project_spec_ref: str
    core_version: str
    qa: QAEnvelope
    result_fingerprint: str | None = None
    manifest: CanonicalResultManifest | None = None
    request: RequestSnapshot | None = None
    slices: tuple[CanonicalSlice, ...] = field(default_factory=tuple)
    bases: tuple[CanonicalBase, ...] = field(default_factory=tuple)
    values: tuple[CanonicalValue, ...] = field(default_factory=tuple)
    comparisons: tuple[SignificanceRelation, ...] = field(
        default_factory=tuple
    )
    qa_events: tuple[QAEvent, ...] = field(default_factory=tuple)
    release: CanonicalReleaseState | None = None
    supersedes_result_run_id: str | None = None
    base_records: tuple[dict[str, Any], ...] = field(
        default_factory=tuple
    )
    value_records: tuple[dict[str, Any], ...] = field(
        default_factory=tuple
    )
    significance_records: tuple[SignificanceComparison, ...] = field(
        default_factory=tuple
    )
