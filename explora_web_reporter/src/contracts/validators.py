from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

from src.contracts.models import (
    CanonicalBase,
    CanonicalResult,
    CanonicalSlice,
    CanonicalValue,
    CategoryOptionBinding,
    QAEvent,
    MetricSpec,
    ProjectSpec,
    QAEnvelope,
    QuestionSpec,
    ReleaseMetadata,
    StructureAxis,
    StructureMember,
    SignificanceSpec,
    StructureSpec,
    UniverseExpression,
    UniverseRef,
    UniverseSpec,
    VariableBinding,
    WeightSpec,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    AxisRole,
    CanonicalBaseMeasure,
    ComputationStatus,
    CompletionPolicy,
    DuplicatePolicy,
    QAReleaseStatus,
    ReleaseLifecycle,
    SampleRelationship,
    StorageEncoding,
    ValueStatus,
)


class ContractValidationError(ValueError):
    pass


def _fail(message: str) -> None:
    raise ContractValidationError(message)


def _require_text(value: object, name: str) -> None:
    if not str(value or "").strip():
        _fail(f"{name} is required")


def validate_release_metadata(release: ReleaseMetadata) -> ReleaseMetadata:
    if release.state is not ReleaseLifecycle.RELEASED:
        _fail("only RELEASED specs may enter canonical execution")
    _require_text(release.decided_by, "release.decided_by")
    _require_text(release.decided_at, "release.decided_at")
    _require_text(release.policy_id, "release.policy_id")
    _require_text(release.policy_version, "release.policy_version")
    _require_text(release.source_hash, "release.source_hash")
    return release


def validate_ai_release_guard(spec: object) -> object:
    release = getattr(spec, "release", None)
    if not isinstance(release, ReleaseMetadata):
        _fail("spec.release metadata is required")
    validate_release_metadata(release)
    return spec


def validate_project_spec(spec: ProjectSpec) -> ProjectSpec:
    validate_ai_release_guard(spec)
    for field_name in (
        "spec_id",
        "version",
        "project_id",
        "dataset_fingerprint",
        "respondent_id_binding",
        "project_universe_ref",
    ):
        _require_text(getattr(spec, field_name), field_name)
    return spec


def validate_question_spec(spec: QuestionSpec) -> QuestionSpec:
    validate_ai_release_guard(spec)
    for field_name in (
        "spec_id",
        "version",
        "question_id",
        "physical_type",
        "analytic_role",
        "universe_ref",
    ):
        _require_text(getattr(spec, field_name), field_name)
    return spec


SUPPORTED_STRUCTURE_TYPES_V1 = {
    "RU",
    "RM",
    "GRID_ESCALA",
    "GRID_RM",
    "LOOP_RM",
    "LOOP_RU",
    "LOOP_NUMERICO",
}

SUPPORTED_APPLICABILITY_SCOPES_V1 = {
    "question",
    "row",
    "column",
    "cell",
    "respondent",
    "loop_instance",
}


def validate_structure_spec(
    spec: StructureSpec,
    *,
    available_variables: set[str] | None = None,
    category_ids: set[str] | None = None,
    universe_ids: set[str] | None = None,
    enforce_m4: bool = False,
) -> StructureSpec:
    validate_ai_release_guard(spec)
    for field_name in (
        "spec_id",
        "version",
        "structure_id",
        "structure_type",
        "parent_question_ref",
    ):
        _require_text(getattr(spec, field_name), field_name)
    structure_type = str(spec.structure_type)
    has_m4_shape = bool(
        spec.axes
        or spec.variable_bindings
        or spec.category_bindings
        or spec.applicability_refs
    )
    if structure_type not in SUPPORTED_STRUCTURE_TYPES_V1:
        if enforce_m4 or has_m4_shape or structure_type == "LOOP_RANGO":
            _fail(f"unsupported structure_type: {structure_type}")
        return spec
    _validate_structure_enums(spec)
    _validate_structure_axes(spec.axes)
    _validate_variable_bindings(
        spec.variable_bindings,
        available_variables=available_variables,
    )
    _validate_category_bindings(
        spec.category_bindings,
        category_ids=category_ids,
    )
    _validate_applicability_refs(
        spec.applicability_refs,
        universe_ids=universe_ids,
    )
    _validate_exclusive_options(spec)
    if enforce_m4:
        _validate_structure_type_shape(spec)
    return spec


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _validate_structure_enums(spec: StructureSpec) -> None:
    allowed_storage = {item.value for item in StorageEncoding}
    if _enum_value(spec.storage_encoding) not in allowed_storage:
        _fail("storage_encoding is not supported in M4 V1")
    allowed_completion = {item.value for item in CompletionPolicy}
    if _enum_value(spec.completion_policy) not in allowed_completion:
        _fail("completion_policy is not supported in M4 V1")
    allowed_duplicate = {item.value for item in DuplicatePolicy}
    if _enum_value(spec.duplicate_policy) not in allowed_duplicate:
        _fail("duplicate_policy is not supported in M4 V1")


def _validate_structure_axes(axes: tuple[StructureAxis, ...]) -> None:
    axis_ids: set[str] = set()
    allowed_roles = {item.value for item in AxisRole}
    for axis in axes:
        if not isinstance(axis, StructureAxis):
            _fail("axes must contain StructureAxis values")
        _require_text(axis.axis_id, "axis.axis_id")
        if axis.axis_id in axis_ids:
            _fail(f"duplicate axis_id: {axis.axis_id}")
        axis_ids.add(axis.axis_id)
        if _enum_value(axis.role) not in allowed_roles:
            _fail(f"unsupported axis role: {axis.role}")
        _validate_structure_members(axis.members, axis.axis_id)


def _validate_structure_members(
    members: tuple[StructureMember, ...],
    axis_id: str,
) -> None:
    member_ids: set[str] = set()
    for member in members:
        if not isinstance(member, StructureMember):
            _fail("axis members must contain StructureMember values")
        _require_text(member.member_id, f"{axis_id}.member_id")
        if member.member_id in member_ids:
            _fail(f"duplicate member_id on {axis_id}: {member.member_id}")
        member_ids.add(member.member_id)
        if member.universe_ref is not None and not isinstance(
            member.universe_ref, UniverseRef
        ):
            _fail("member.universe_ref must be a structured UniverseRef")


def _validate_variable_bindings(
    bindings: tuple[VariableBinding, ...],
    *,
    available_variables: set[str] | None,
) -> None:
    binding_ids: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, VariableBinding):
            _fail("variable_bindings must contain VariableBinding values")
        _require_text(binding.binding_id, "binding.binding_id")
        _require_text(binding.variable_ref, "binding.variable_ref")
        if binding.binding_id in binding_ids:
            _fail(f"duplicate variable binding_id: {binding.binding_id}")
        binding_ids.add(binding.binding_id)
        if available_variables is not None:
            if binding.variable_ref not in available_variables:
                _fail(f"unknown variable_ref: {binding.variable_ref}")


def _validate_category_bindings(
    bindings: tuple[CategoryOptionBinding, ...],
    *,
    category_ids: set[str] | None,
) -> None:
    binding_ids: set[str] = set()
    raw_values: set[object] = set()
    for binding in bindings:
        if not isinstance(binding, CategoryOptionBinding):
            _fail(
                "category_bindings must contain CategoryOptionBinding values"
            )
        _require_text(binding.binding_id, "category_binding.binding_id")
        _require_text(binding.category_id, "category_binding.category_id")
        if binding.binding_id in binding_ids:
            _fail(
                f"duplicate category binding_id: {binding.binding_id}"
            )
        binding_ids.add(binding.binding_id)
        if category_ids is not None and binding.category_id not in category_ids:
            _fail(f"unknown category_id: {binding.category_id}")
        for raw_value in binding.raw_values:
            if raw_value in raw_values:
                _fail(f"duplicate raw category value: {raw_value}")
            raw_values.add(raw_value)


def _validate_applicability_refs(
    refs: dict[str, UniverseRef],
    *,
    universe_ids: set[str] | None,
) -> None:
    for scope, ref in refs.items():
        _require_text(scope, "applicability scope")
        base_scope = scope.split(":", 1)[0]
        if base_scope not in SUPPORTED_APPLICABILITY_SCOPES_V1:
            _fail(f"unsupported applicability scope: {scope}")
        if not isinstance(ref, UniverseRef):
            _fail("applicability_refs must use structured UniverseRef values")
        _require_text(ref.universe_id, "applicability_refs.universe_id")
        if universe_ids is not None and ref.universe_id not in universe_ids:
            _fail(f"unknown universe_ref: {ref.universe_id}")


def _validate_exclusive_options(spec: StructureSpec) -> None:
    option_ids = {
        member.member_id
        for axis in spec.axes
        if _enum_value(axis.role) in {"option", "column"}
        for member in axis.members
    }
    binding_option_ids = {
        binding.option_id
        for binding in spec.variable_bindings
        if binding.option_id is not None
    }
    known_options = option_ids | binding_option_ids
    for option_id in spec.exclusive_option_ids:
        _require_text(option_id, "exclusive_option_id")
        if known_options and option_id not in known_options:
            _fail(f"unknown exclusive option_id: {option_id}")


def _validate_structure_type_shape(spec: StructureSpec) -> None:
    structure_type = str(spec.structure_type)
    roles = {_enum_value(axis.role) for axis in spec.axes}
    if not spec.variable_bindings:
        _fail("M4 executable structures require variable_bindings")
    if structure_type in {"RU", "GRID_ESCALA", "LOOP_RU"}:
        if not spec.category_bindings:
            _fail(f"{structure_type} requires category_bindings")
    if structure_type == "RM":
        if "option" not in roles and not any(
            binding.option_id for binding in spec.variable_bindings
        ):
            _fail("RM requires explicit option members or option bindings")
    if structure_type == "GRID_RM":
        if "row" not in roles or "column" not in roles:
            _fail("GRID_RM requires row and column axes")
    if structure_type == "GRID_ESCALA":
        if "row" not in roles:
            _fail("GRID_ESCALA requires a row axis")
    if structure_type.startswith("LOOP_"):
        if not spec.loop_instance_binding and not all(
            binding.loop_instance_id for binding in spec.variable_bindings
        ):
            _fail("loop structures require explicit loop instance identity")


def validate_weight_spec(
    spec: WeightSpec,
    project_weight_specs: Iterable[WeightSpec] | None = None,
) -> WeightSpec:
    validate_ai_release_guard(spec)
    for field_name in (
        "spec_id",
        "version",
        "weight_id",
        "variable_ref",
        "provenance",
        "scope",
    ):
        _require_text(getattr(spec, field_name), field_name)
    expected = {
        "missing_policy": "EXCLUDE_AND_QA",
        "non_numeric_policy": "EXCLUDE_AND_QA",
        "non_finite_policy": "FAIL",
        "zero_policy": "VALID",
        "negative_policy": "UNSUPPORTED_V1",
        "normalization": "NONE",
        "trimming": "NONE",
    }
    for field_name, expected_value in expected.items():
        if getattr(spec, field_name) != expected_value:
            _fail(f"{field_name} must be {expected_value} in B1 V1")
    if spec.weighted_significance:
        _fail("weighted significance is UNSUPPORTED in B1 V1")
    required_bases = {
        CanonicalBaseMeasure.UNWEIGHTED_N,
        CanonicalBaseMeasure.WEIGHTED_N_RAW,
        CanonicalBaseMeasure.WEIGHTED_N,
        CanonicalBaseMeasure.EFFECTIVE_N,
    }
    if set(spec.canonical_base_measures) != required_bases:
        _fail("B1 V1 canonical base measures are incomplete")
    if project_weight_specs is not None:
        defaults = [
            item for item in project_weight_specs if item.is_project_default
        ]
        if len(defaults) > 1:
            _fail("only one project default weight is allowed")
    return spec


def validate_weight_override(
    override_weight_id: str | None,
    project_weight_specs: Iterable[WeightSpec],
) -> WeightSpec | None:
    weights = list(project_weight_specs)
    for weight in weights:
        validate_weight_spec(weight, weights)
    if override_weight_id is None:
        return None
    _require_text(override_weight_id, "override_weight_id")
    matches = [
        weight for weight in weights if weight.weight_id == override_weight_id
    ]
    if not matches:
        _fail(f"unknown weight override: {override_weight_id}")
    if len(matches) > 1:
        _fail(f"ambiguous weight override: {override_weight_id}")
    selected = matches[0]
    allowed = set(selected.permitted_analysis_overrides)
    if allowed and override_weight_id not in allowed:
        _fail(f"out-of-scope weight override: {override_weight_id}")
    return selected


_UNIVERSE_SIGNATURES = {
    "true": (),
    "false": (),
    "and": ("expression_list_2plus",),
    "or": ("expression_list_2plus",),
    "not": ("expression",),
    "eq": ("variable_ref", "scalar"),
    "neq": ("variable_ref", "scalar"),
    "in": ("variable_ref", "scalar_list"),
    "not_in": ("variable_ref", "scalar_list"),
    "gt": ("variable_ref", "scalar"),
    "gte": ("variable_ref", "scalar"),
    "lt": ("variable_ref", "scalar"),
    "lte": ("variable_ref", "scalar"),
    "is_missing": ("variable_ref",),
    "not_missing": ("variable_ref",),
    "selected": ("question_ref", "category_ref"),
    "not_selected": ("question_ref", "category_ref"),
    "answered": ("question_ref",),
    "not_answered": ("question_ref",),
    "universe_ref": ("universe_ref",),
}


def validate_universe_spec(
    spec: UniverseSpec,
    *,
    variables: set[str] | None = None,
    questions: set[str] | None = None,
    categories: set[str] | None = None,
    universes: Mapping[str, UniverseSpec] | None = None,
) -> UniverseSpec:
    validate_ai_release_guard(spec)
    _require_text(spec.spec_id, "spec_id")
    _require_text(spec.version, "version")
    validate_universe_expression(
        spec.expression,
        variables=variables,
        questions=questions,
        categories=categories,
        universes=universes,
        current_universe=spec.spec_id,
        stack=(),
    )
    return spec


def validate_universe_expression(
    expression: UniverseExpression,
    *,
    variables: set[str] | None = None,
    questions: set[str] | None = None,
    categories: set[str] | None = None,
    universes: Mapping[str, UniverseSpec] | None = None,
    current_universe: str | None = None,
    stack: tuple[str, ...] = (),
) -> UniverseExpression:
    operator = expression.operator
    if operator not in _UNIVERSE_SIGNATURES:
        _fail(f"unknown universe operator: {operator}")
    signature = _UNIVERSE_SIGNATURES[operator]
    args = expression.args
    if signature == ("expression_list_2plus",):
        if len(args) < 2 or not all(
            isinstance(arg, UniverseExpression) for arg in args
        ):
            _fail(f"{operator} requires at least two expressions")
        for arg in args:
            validate_universe_expression(
                arg,
                variables=variables,
                questions=questions,
                categories=categories,
                universes=universes,
                current_universe=current_universe,
                stack=stack,
            )
        return expression
    if len(args) != len(signature):
        _fail(f"{operator} requires {len(signature)} arguments")
    for arg, arg_type in zip(args, signature):
        _validate_universe_arg(
            arg,
            arg_type,
            variables=variables,
            questions=questions,
            categories=categories,
            universes=universes,
            current_universe=current_universe,
            stack=stack,
        )
    return expression


def _validate_universe_arg(
    arg: Any,
    arg_type: str,
    *,
    variables: set[str] | None,
    questions: set[str] | None,
    categories: set[str] | None,
    universes: Mapping[str, UniverseSpec] | None,
    current_universe: str | None,
    stack: tuple[str, ...],
) -> None:
    if arg_type == "expression":
        if not isinstance(arg, UniverseExpression):
            _fail("expression argument must be a UniverseExpression")
        validate_universe_expression(
            arg,
            variables=variables,
            questions=questions,
            categories=categories,
            universes=universes,
            current_universe=current_universe,
            stack=stack,
        )
        return
    if arg_type == "scalar":
        if isinstance(arg, UniverseExpression) or isinstance(
            arg, (list, tuple, dict, set)
        ):
            _fail("scalar argument has invalid type")
        return
    if arg_type == "scalar_list":
        if not isinstance(arg, (list, tuple)) or not arg:
            _fail("scalar list argument must be a non-empty list")
        for value in arg:
            _validate_universe_arg(
                value,
                "scalar",
                variables=variables,
                questions=questions,
                categories=categories,
                universes=universes,
                current_universe=current_universe,
                stack=stack,
            )
        return
    if arg_type == "universe_ref":
        if not isinstance(arg, UniverseRef):
            _fail("universe_ref must be a structured UniverseRef")
        ref_value = str(arg.universe_id or "").strip()
    else:
        ref_value = str(arg or "").strip()
    _require_text(ref_value, arg_type)
    if arg_type == "variable_ref" and variables is not None:
        if ref_value not in variables:
            _fail(f"unknown variable_ref: {ref_value}")
    if arg_type == "question_ref" and questions is not None:
        if ref_value not in questions:
            _fail(f"unknown question_ref: {ref_value}")
    if arg_type == "category_ref" and categories is not None:
        if ref_value not in categories:
            _fail(f"unknown category_ref: {ref_value}")
    if arg_type == "universe_ref":
        if current_universe and ref_value == current_universe:
            _fail("circular universe_ref detected")
        if universes is not None:
            if ref_value not in universes:
                _fail(f"unknown universe_ref: {ref_value}")
            if ref_value in stack:
                _fail("circular universe_ref detected")
            validate_universe_expression(
                universes[ref_value].expression,
                variables=variables,
                questions=questions,
                categories=categories,
                universes=universes,
                current_universe=current_universe,
                stack=stack + (ref_value,),
            )


def validate_metric_spec(spec: MetricSpec) -> MetricSpec:
    validate_ai_release_guard(spec)
    for field_name in (
        "spec_id",
        "version",
        "metric_id",
        "formula_id",
        "question_ref",
        "universe_ref",
        "denominator_policy",
        "missing_behavior",
        "weight_behavior",
        "significance_family",
    ):
        _require_text(getattr(spec, field_name), field_name)
    if (
        spec.denominator_policy == "NOT_APPLICABLE"
        and spec.significance_supported
    ):
        _fail("significance requires an explicit denominator policy")
    return spec


def validate_significance_spec(spec: SignificanceSpec) -> SignificanceSpec:
    validate_ai_release_guard(spec)
    if spec.confidence not in {0.90, 0.95, 0.99}:
        _fail("confidence must be one of 0.90, 0.95, 0.99")
    if not math.isclose(spec.alpha, 1 - spec.confidence):
        _fail("alpha must equal 1 - confidence")
    if spec.sidedness != "two_sided":
        _fail("sidedness must be two_sided in B2 V1")
    if spec.minimum_base_rule != "unweighted_n>=30":
        _fail("minimum base must be unweighted_n>=30 in B2 V1")
    if spec.proportion_test != "pooled_two_proportion_z":
        _fail("proportion test must be pooled_two_proportion_z")
    if spec.mean_test != "welch_independent_t":
        _fail("mean test must be welch_independent_t")
    if spec.adjustment != "HOLM":
        _fail("multiplicity adjustment must be HOLM in B2 V1")
    if not spec.total_excluded:
        _fail("Total must be excluded from B2 V1 comparisons")
    if not isinstance(spec.sample_relationship, SampleRelationship):
        _fail("sample_relationship is required")
    if spec.weighted_inference:
        _fail("weighted inference is UNSUPPORTED in B2 V1")
    return spec


def validate_canonical_result(result: CanonicalResult) -> CanonicalResult:
    for field_name in (
        "result_schema_version",
        "result_run_id",
        "project_id",
        "dataset_fingerprint",
        "project_spec_ref",
        "core_version",
    ):
        _require_text(getattr(result, field_name), field_name)
    if not isinstance(result.qa, QAEnvelope):
        _fail("qa envelope is required")
    if (
        result.qa.aggregate_state is AggregateReleaseState.FAIL
        and result.release is None
    ):
        _fail("canonical result has aggregate FAIL state")
    for record in result.base_records:
        _validate_finite_record(record)
    for record in result.value_records:
        _validate_finite_record(record)
    if result.result_fingerprint is not None:
        _require_text(result.result_fingerprint, "result_fingerprint")
    _validate_unique_ids(
        "slice_id",
        (item.slice_id for item in result.slices),
    )
    _validate_unique_ids(
        "base_id",
        (item.base_id for item in result.bases),
    )
    _validate_unique_ids(
        "value_id",
        (item.value_id for item in result.values),
    )
    _validate_unique_ids(
        "comparison_id",
        (item.comparison_id for item in result.comparisons),
    )
    _validate_unique_ids(
        "qa_id",
        (item.qa_id for item in result.qa_events),
    )
    for item in result.slices:
        _validate_slice(item)
    for item in result.bases:
        _validate_base(item)
    base_ids = {item.base_id for item in result.bases}
    qa_ids = {item.qa_id for item in result.qa_events}
    for item in result.values:
        _validate_value(item, base_ids=base_ids, qa_ids=qa_ids)
    for item in result.comparisons:
        _validate_significance_relation(item)
    for item in result.qa_events:
        _validate_qa_event(item)
    if result.release is not None:
        _validate_release_state(result.release, result.qa_events)
    return result


def _validate_finite_record(record: dict[str, Any]) -> None:
    for key, value in record.items():
        if isinstance(value, float) and not math.isfinite(value):
            _fail(f"{key} must be finite")


def _validate_unique_ids(name: str, values: Iterable[str]) -> None:
    seen: set[str] = set()
    for value in values:
        _require_text(value, name)
        if value in seen:
            _fail(f"duplicate {name}: {value}")
        seen.add(value)


def _validate_slice(item: CanonicalSlice) -> None:
    _require_text(item.slice_fingerprint, "slice_fingerprint")


def _validate_base(item: CanonicalBase) -> None:
    for field_name in (
        "question_id",
        "structure_id",
        "slice_id",
        "denominator_ref",
        "denominator_scope_id",
        "base_status",
    ):
        _require_text(getattr(item, field_name), field_name)
    if not isinstance(item.universe_ref, UniverseRef):
        _fail("universe_ref is required")
    if item.unweighted_n < 0:
        _fail("unweighted_n must be non-negative")
    _validate_finite_optional("weighted_n_raw", item.weighted_n_raw)
    _validate_finite_optional("weighted_n", item.weighted_n)
    _validate_finite_optional("effective_n", item.effective_n)


def _validate_value(
    item: CanonicalValue,
    *,
    base_ids: set[str],
    qa_ids: set[str],
) -> None:
    for field_name in (
        "question_id",
        "structure_id",
        "slice_id",
        "metric_id",
        "formula_id",
        "formula_version",
        "base_id",
    ):
        _require_text(getattr(item, field_name), field_name)
    if item.base_id not in base_ids:
        _fail(f"value references unknown base_id: {item.base_id}")
    status = ValueStatus(str(getattr(item.value_status, "value", item.value_status)))
    if status is not ValueStatus.OK and item.estimate is not None:
        _fail("estimate must be null unless value_status is OK")
    _validate_finite_optional("estimate", item.estimate)
    _validate_finite_optional("numerator", item.numerator)
    _validate_finite_optional("denominator", item.denominator)
    for qa_ref in item.qa_refs:
        if qa_ref not in qa_ids:
            _fail(f"value references unknown qa_id: {qa_ref}")


def _validate_significance_relation(item: Any) -> None:
    for field_name in (
        "comparison_id",
        "question_id",
        "metric_id",
        "analytical_scope",
        "family_id",
        "left_slice_id",
        "right_slice_id",
        "test_id",
        "test_version",
    ):
        _require_text(getattr(item, field_name), field_name)
    _validate_finite_optional("raw_p_value", item.raw_p_value)
    _validate_finite_optional("adjusted_p_value", item.adjusted_p_value)


def _validate_qa_event(item: QAEvent) -> None:
    for field_name in ("qa_id", "code", "message"):
        _require_text(getattr(item, field_name), field_name)


def _validate_release_state(release: Any, qa_events: tuple[QAEvent, ...]) -> None:
    ComputationStatus(
        str(getattr(release.computation_status, "value", release.computation_status))
    )
    qa_status = QAReleaseStatus(
        str(getattr(release.qa_release_status, "value", release.qa_release_status))
    )
    has_blocking = any(event.blocking for event in qa_events)
    if has_blocking and release.releasable:
        _fail("blocking QA events cannot be releasable")
    if qa_status is QAReleaseStatus.FAIL and release.releasable:
        _fail("FAIL release status cannot be releasable")


def _validate_finite_optional(name: str, value: float | int | None) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        _fail(f"{name} must be finite")
