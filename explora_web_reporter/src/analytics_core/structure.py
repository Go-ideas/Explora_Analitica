from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
import os
from typing import Any, Mapping

from src.analytics_core.universe import (
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    QAEnvelope,
    QAIssue,
    ProjectSpec,
    QuestionSpec,
    StructureSpec,
    UniverseRef,
    VariableBinding,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_ai_release_guard,
    validate_structure_spec,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    CompletionPolicy,
    DenominatorUnit,
    DuplicatePolicy,
    LegacyStructureComparisonStatus,
    QAIssueLifecycle,
    QAIssueState,
    ReleaseLifecycle,
    ResponseStateValue,
    StructureAuthorityMode,
    StructureExecutionStatus,
)


STRUCTURE_RUNTIME_RULES_VERSION = "M4_STRUCTURE_V1"
STRUCTURE_AUTHORITY_ENV = "EXPLORA_STRUCTURE_AUTHORITY"


@dataclass(frozen=True)
class StructureEvaluationContext:
    respondent_ids: tuple[str, ...]
    values_by_variable: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    universe_results: Mapping[str, UniverseEvaluationResult] = field(
        default_factory=dict
    )
    available_variables: set[str] | None = None
    category_ids: set[str] | None = None
    universe_ids: set[str] | None = None
    detector_evidence: Mapping[str, Any] = field(default_factory=dict)
    weight_values: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    traceability: Mapping[str, str] = field(default_factory=dict)

    def value(self, respondent_id: str, binding: VariableBinding) -> Any:
        if binding.variable_ref not in self.values_by_variable:
            raise StructureExecutionError(
                f"missing physical variable: {binding.variable_ref}",
                status=StructureExecutionStatus.FAIL,
            )
        return self.values_by_variable[binding.variable_ref].get(
            respondent_id
        )


@dataclass(frozen=True)
class AnalyticalRecord:
    respondent_id: str
    structure_id: str
    question_id: str
    binding_id: str
    variable_ref: str
    response_state: ResponseStateValue
    row_id: str | None = None
    column_id: str | None = None
    option_id: str | None = None
    category_id: str | None = None
    loop_instance_id: str | None = None
    entity_id: str | None = None
    raw_value: Any = None
    applicable: bool = True
    selected: bool = False
    not_selected: bool = False
    structural_zero: bool = False
    structural_missing: bool = False
    ordinary_missing: bool = False
    invalid: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DenominatorLedger:
    scope_id: str
    metric_id: str
    denominator_unit: DenominatorUnit
    denominator_n: int
    valid_n: int
    selected_n: int
    not_selected_n: int
    ordinary_missing_n: int
    structural_missing_n: int
    invalid_n: int
    zero_base_status: str
    repeated_dependency: bool = False
    traceability: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructureExecutionResult:
    structure_id: str
    structure_version: str
    structure_type: str
    authority_mode: StructureAuthorityMode
    runtime_rules_version: str
    status: StructureExecutionStatus
    records: tuple[AnalyticalRecord, ...] = field(default_factory=tuple)
    denominator_ledgers: tuple[DenominatorLedger, ...] = (
        field(default_factory=tuple)
    )
    warnings: tuple[str, ...] = field(default_factory=tuple)
    failures: tuple[str, ...] = field(default_factory=tuple)
    qa: QAEnvelope | None = None
    traceability: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LegacyStructureComparison:
    status: LegacyStructureComparisonStatus
    differences: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class StructureExecutionError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        status: StructureExecutionStatus = StructureExecutionStatus.FAIL,
    ) -> None:
        super().__init__(message)
        self.status = status


class StructureAuthorityModeError(ValueError):
    pass


def resolve_structure_authority_mode(
    value: str | StructureAuthorityMode | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> StructureAuthorityMode:
    if isinstance(value, StructureAuthorityMode):
        return value
    env = os.environ if environ is None else environ
    candidate = value or env.get(STRUCTURE_AUTHORITY_ENV)
    if candidate is None or candidate == "":
        return StructureAuthorityMode.LEGACY_INFERENCE
    normalized = str(candidate).strip().lower()
    for mode in StructureAuthorityMode:
        if normalized == mode.value:
            return mode
    raise StructureAuthorityModeError(
        f"unsupported structure authority mode: {candidate}"
    )


def evaluate_structure(
    *,
    project_spec: ProjectSpec,
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    context: StructureEvaluationContext,
    authority_mode: str | StructureAuthorityMode | None = None,
) -> StructureExecutionResult:
    mode = resolve_structure_authority_mode(authority_mode)
    if mode is StructureAuthorityMode.LEGACY_INFERENCE:
        return _result(
            project_spec,
            question_spec,
            structure_spec,
            mode,
            StructureExecutionStatus.REVIEW_REQUIRED,
            warnings=(
                "legacy_inference mode does not perform canonical "
                "M4 execution",
            ),
            context=context,
        )
    try:
        _require_released(project_spec, "project")
        _require_released(question_spec, "question")
        _require_released(structure_spec, "structure")
        _validate_released_reference_chain(question_spec, structure_spec)
        validate_structure_spec(
            structure_spec,
            available_variables=context.available_variables,
            category_ids=context.category_ids,
            universe_ids=context.universe_ids,
            enforce_m4=True,
        )
        warnings = list(_detector_warnings(structure_spec, context))
        records = _build_records(question_spec, structure_spec, context)
        failures = _record_failures(records)
        failures.extend(_exclusive_failures(structure_spec, records))
        failures.extend(_duplicate_failures(structure_spec, records))
        ledgers = _build_ledgers(structure_spec, records)
        status = (
            StructureExecutionStatus.FAIL
            if failures
            else (
                StructureExecutionStatus.PASS_WITH_WARNINGS
                if warnings
                else StructureExecutionStatus.PASS
            )
        )
        return _result(
            project_spec,
            question_spec,
            structure_spec,
            mode,
            status,
            records=tuple(records),
            ledgers=tuple(ledgers),
            warnings=tuple(warnings),
            failures=tuple(dict.fromkeys(failures)),
            context=context,
        )
    except (ContractValidationError, StructureExecutionError) as exc:
        status = (
            exc.status
            if isinstance(exc, StructureExecutionError)
            else StructureExecutionStatus.FAIL
        )
        return _result(
            project_spec,
            question_spec,
            structure_spec,
            mode,
            status,
            failures=(str(exc),),
            context=context,
        )


def compare_legacy_structure(
    canonical: StructureExecutionResult,
    legacy: Mapping[str, Any],
    *,
    declared_difference: LegacyStructureComparisonStatus | None = None,
    reason: str = "",
) -> LegacyStructureComparison:
    canonical_summary = {
        ledger.scope_id: {
            "denominator_n": ledger.denominator_n,
            "valid_n": ledger.valid_n,
            "selected_n": ledger.selected_n,
            "not_selected_n": ledger.not_selected_n,
            "invalid_n": ledger.invalid_n,
        }
        for ledger in canonical.denominator_ledgers
    }
    if (
        "structure" not in canonical_summary
        and canonical.denominator_ledgers
    ):
        first = canonical.denominator_ledgers[0]
        canonical_summary["structure"] = {
            "denominator_n": first.denominator_n,
            "valid_n": first.valid_n,
            "selected_n": first.selected_n,
            "not_selected_n": first.not_selected_n,
            "invalid_n": first.invalid_n,
        }
    comparison_keys = set(legacy) if legacy else set(canonical_summary)
    differences = {
        key: (canonical_summary.get(key), legacy.get(key))
        for key in comparison_keys
        if canonical_summary.get(key) != legacy.get(key)
    }
    if not differences:
        return LegacyStructureComparison(
            status=LegacyStructureComparisonStatus.PARITY,
            reason=reason,
        )
    if declared_difference in {
        LegacyStructureComparisonStatus.INTENDED_CORRECTION,
        LegacyStructureComparisonStatus.POTENTIAL_REGRESSION,
        LegacyStructureComparisonStatus.UNSUPPORTED,
        LegacyStructureComparisonStatus.REVIEW_REQUIRED,
    }:
        return LegacyStructureComparison(
            status=declared_difference,
            differences=differences,
            reason=reason,
        )
    return LegacyStructureComparison(
        status=LegacyStructureComparisonStatus.REVIEW_REQUIRED,
        differences=differences,
        reason=reason,
    )


def _build_records(
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    context: StructureEvaluationContext,
) -> list[AnalyticalRecord]:
    records: list[AnalyticalRecord] = []
    for respondent_id in context.respondent_ids:
        for binding in structure_spec.variable_bindings:
            applicable = _is_applicable(
                respondent_id,
                binding,
                structure_spec,
                context,
            )
            if not applicable:
                records.append(
                    _record(
                        respondent_id,
                        question_spec,
                        structure_spec,
                        binding,
                        None,
                        ResponseStateValue.STRUCTURAL_MISSING,
                        applicable=False,
                        structural_missing=True,
                    )
                )
                continue
            raw_value = context.value(respondent_id, binding)
            records.append(
                _classify_value(
                    respondent_id,
                    question_spec,
                    structure_spec,
                    binding,
                    raw_value,
                )
            )
    return records


def _is_applicable(
    respondent_id: str,
    binding: VariableBinding,
    structure_spec: StructureSpec,
    context: StructureEvaluationContext,
) -> bool:
    for scope, ref in _applicability_refs_for_binding(
        binding,
        structure_spec,
    ):
        result = context.universe_results.get(ref.universe_id)
        if result is None:
            raise StructureExecutionError(
                f"missing M2 universe result: {ref.universe_id}"
            )
        if result.status is UniverseEvaluationStatus.FAIL:
            raise StructureExecutionError(
                f"M2 universe failed: {ref.universe_id}"
            )
        if result.status is UniverseEvaluationStatus.UNSUPPORTED:
            raise StructureExecutionError(
                f"M2 universe unsupported: {ref.universe_id}",
                status=StructureExecutionStatus.REVIEW_REQUIRED,
            )
        if not result.respondent_mask.get(respondent_id, False):
            return False
    return True


def _applicability_refs_for_binding(
    binding: VariableBinding,
    structure_spec: StructureSpec,
) -> tuple[tuple[str, UniverseRef], ...]:
    question_ref = structure_spec.applicability_refs.get("question")
    if question_ref is None:
        raise StructureExecutionError(
            "question applicability requires explicit M2 UniverseRef"
        )
    refs: list[tuple[str, UniverseRef]] = [("question", question_ref)]
    optional_refs = (
        ("row", _row_universe_ref(binding, structure_spec)),
        ("column", _column_universe_ref(binding, structure_spec)),
        ("cell", _cell_universe_ref(binding, structure_spec)),
        ("loop_instance", _loop_universe_ref(binding, structure_spec)),
    )
    refs.extend((scope, ref) for scope, ref in optional_refs if ref)
    return tuple(refs)


def _row_universe_ref(
    binding: VariableBinding,
    structure_spec: StructureSpec,
) -> UniverseRef | None:
    if binding.row_id is None:
        return None
    return (
        _member_universe_ref(structure_spec, "row", binding.row_id)
        or structure_spec.applicability_refs.get(f"row:{binding.row_id}")
        or structure_spec.applicability_refs.get("row")
    )


def _column_universe_ref(
    binding: VariableBinding,
    structure_spec: StructureSpec,
) -> UniverseRef | None:
    member_id = binding.column_id or binding.option_id
    if member_id is None:
        return None
    return (
        _member_universe_ref(structure_spec, "column", member_id)
        or _member_universe_ref(structure_spec, "option", member_id)
        or structure_spec.applicability_refs.get(f"column:{member_id}")
        or structure_spec.applicability_refs.get("column")
    )


def _cell_universe_ref(
    binding: VariableBinding,
    structure_spec: StructureSpec,
) -> UniverseRef | None:
    column_id = binding.column_id or binding.option_id
    if binding.row_id is None or column_id is None:
        return None
    return (
        structure_spec.applicability_refs.get(
            f"cell:{binding.row_id}:{column_id}"
        )
        or structure_spec.applicability_refs.get("cell")
    )


def _loop_universe_ref(
    binding: VariableBinding,
    structure_spec: StructureSpec,
) -> UniverseRef | None:
    if binding.loop_instance_id is None:
        return None
    return (
        structure_spec.applicability_refs.get(
            f"loop_instance:{binding.loop_instance_id}"
        )
        or structure_spec.applicability_refs.get("loop_instance")
    )


def _member_universe_ref(
    structure_spec: StructureSpec,
    role: str,
    member_id: str,
) -> UniverseRef | None:
    for axis in structure_spec.axes:
        axis_role = str(getattr(axis.role, "value", axis.role))
        if axis_role != role:
            continue
        for member in axis.members:
            if member.member_id == member_id:
                return member.universe_ref
    return None


def _classify_value(
    respondent_id: str,
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    binding: VariableBinding,
    raw_value: Any,
) -> AnalyticalRecord:
    if _is_raw_missing(raw_value):
        state = (
            ResponseStateValue.NOT_ANSWERED
            if _completion_policy(structure_spec)
            is CompletionPolicy.MISSING_SET_UNANSWERED
            else ResponseStateValue.ORDINARY_MISSING
        )
        return _record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
            state,
            ordinary_missing=True,
        )
    if raw_value in set(structure_spec.ordinary_missing_values):
        return _record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
            ResponseStateValue.ORDINARY_MISSING,
            ordinary_missing=True,
        )
    if str(structure_spec.structure_type) in {
        "RM",
        "GRID_RM",
        "LOOP_RM",
    }:
        if raw_value in set(structure_spec.selected_values):
            return _record(
                respondent_id,
                question_spec,
                structure_spec,
                binding,
                raw_value,
                ResponseStateValue.SELECTED,
                selected=True,
            )
        if raw_value in set(structure_spec.not_selected_values):
            return _record(
                respondent_id,
                question_spec,
                structure_spec,
                binding,
                raw_value,
                ResponseStateValue.NOT_SELECTED,
                not_selected=True,
                structural_zero=True,
            )
        return _invalid_record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
        )
    if str(structure_spec.structure_type) == "LOOP_NUMERICO":
        if isinstance(raw_value, bool):
            return _invalid_record(
                respondent_id,
                question_spec,
                structure_spec,
                binding,
                raw_value,
            )
        if isinstance(raw_value, (int, float)) and math.isfinite(raw_value):
            return _record(
                respondent_id,
                question_spec,
                structure_spec,
                binding,
                raw_value,
                ResponseStateValue.ANSWERED,
            )
        return _invalid_record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
        )
    category_id = _category_for_raw_value(structure_spec, raw_value)
    if category_id is None:
        return _invalid_record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
        )
    return replace(
        _record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
            ResponseStateValue.VALID_CATEGORY,
        ),
        category_id=category_id,
    )


def _record(
    respondent_id: str,
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    binding: VariableBinding,
    raw_value: Any,
    state: ResponseStateValue,
    *,
    applicable: bool = True,
    selected: bool = False,
    not_selected: bool = False,
    structural_zero: bool = False,
    structural_missing: bool = False,
    ordinary_missing: bool = False,
) -> AnalyticalRecord:
    return AnalyticalRecord(
        respondent_id=respondent_id,
        structure_id=structure_spec.structure_id,
        question_id=question_spec.question_id,
        binding_id=binding.binding_id,
        variable_ref=binding.variable_ref,
        response_state=state,
        row_id=binding.row_id,
        column_id=binding.column_id,
        option_id=binding.option_id,
        category_id=binding.category_id,
        loop_instance_id=binding.loop_instance_id,
        entity_id=binding.entity_id,
        raw_value=raw_value,
        applicable=applicable,
        selected=selected,
        not_selected=not_selected,
        structural_zero=structural_zero,
        structural_missing=structural_missing,
        ordinary_missing=ordinary_missing,
        provenance={
            "runtime_rules_version": STRUCTURE_RUNTIME_RULES_VERSION,
            "response_state_version": structure_spec.response_state_version,
            "structural_zero_provenance": (
                structure_spec.structural_zero_provenance
            ),
            "storage_encoding": str(
                getattr(
                    structure_spec.storage_encoding,
                    "value",
                    structure_spec.storage_encoding,
                )
            ),
        },
    )


def _invalid_record(
    respondent_id: str,
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    binding: VariableBinding,
    raw_value: Any,
) -> AnalyticalRecord:
    return replace(
        _record(
            respondent_id,
            question_spec,
            structure_spec,
            binding,
            raw_value,
            ResponseStateValue.INVALID_OUT_OF_DOMAIN,
        ),
        invalid=True,
    )


def _record_failures(records: list[AnalyticalRecord]) -> list[str]:
    return [
        f"invalid out-of-domain value for {record.binding_id}"
        for record in records
        if record.invalid
    ]


def _exclusive_failures(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
) -> list[str]:
    failures: list[str] = []
    selected_by_scope: dict[tuple[str, ...], set[str]] = {}
    for record in records:
        if record.selected and record.option_id is not None:
            selected_by_scope.setdefault(_exclusive_scope_key(record), set()).add(
                record.option_id
            )
    for scope, selected in selected_by_scope.items():
        exclusive_selected = selected & set(structure_spec.exclusive_option_ids)
        if exclusive_selected and len(selected) > len(exclusive_selected):
            failures.append(
                f"exclusive option conflict for scope {'/'.join(scope)}"
            )
    return failures


def _duplicate_failures(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
) -> list[str]:
    if _duplicate_policy(structure_spec) is not DuplicatePolicy.ERROR:
        return []
    seen: set[tuple[str, ...]] = set()
    failures: list[str] = []
    for record in records:
        if not record.selected:
            continue
        key = _analytical_option_key(record)
        if key in seen:
            failures.append(
                "duplicate selected mention violates duplicate_policy=error: "
                f"{'/'.join(key)}"
            )
        seen.add(key)
    return failures


def _build_ledgers(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
) -> list[DenominatorLedger]:
    structure_type = str(structure_spec.structure_type)
    if structure_type in {"RM", "GRID_RM", "LOOP_RM"}:
        ledgers = [
            _respondent_option_ledger(
                records,
                duplicate_policy=_duplicate_policy(structure_spec),
            )
        ]
        if structure_spec.mention_denominator_scope:
            ledgers.extend(
                _mention_ledgers(
                    structure_spec,
                    records,
                    duplicate_policy=_duplicate_policy(structure_spec),
                )
            )
        return ledgers
    if structure_type in {"RU", "GRID_ESCALA", "LOOP_RU"}:
        unit = DenominatorUnit.RESPONDENT
    elif structure_type == "LOOP_NUMERICO":
        unit = DenominatorUnit.INSTANCE
    else:
        unit = DenominatorUnit.RESPONDENT_OPTION
    return [
        _ledger(
            "structure",
            "structure_validity",
            unit,
            records,
            duplicate_policy=_duplicate_policy(structure_spec),
        )
    ]


def _respondent_option_ledger(
    records: list[AnalyticalRecord],
    *,
    duplicate_policy: DuplicatePolicy,
) -> DenominatorLedger:
    included = [record for record in records if record.applicable]
    valid_records = [
        record
        for record in included
        if record.selected or record.not_selected
    ]
    denominator_keys = {_analytical_option_key(record) for record in valid_records}
    selected_keys = {
        _analytical_option_key(record)
        for record in valid_records
        if record.selected
    }
    not_selected_keys = {
        _analytical_option_key(record)
        for record in valid_records
        if record.not_selected
    }
    denominator_n = len(denominator_keys)
    return DenominatorLedger(
        scope_id="respondent",
        metric_id="rm_respondent",
        denominator_unit=DenominatorUnit.RESPONDENT_OPTION,
        denominator_n=denominator_n,
        valid_n=denominator_n,
        selected_n=len(selected_keys),
        not_selected_n=len(not_selected_keys),
        ordinary_missing_n=sum(1 for record in included if record.ordinary_missing),
        structural_missing_n=sum(1 for record in records if record.structural_missing),
        invalid_n=sum(1 for record in included if record.invalid),
        zero_base_status="VALID_ZERO_BASE"
        if denominator_n == 0
        else "NONZERO_BASE",
        repeated_dependency=_has_repeated_dependency(records),
        traceability={
            "duplicate_policy": duplicate_policy.value,
            "denominator_by_option": _counts_by_option(denominator_keys),
            "selected_by_option": _counts_by_option(selected_keys),
            "runtime_rules_version": STRUCTURE_RUNTIME_RULES_VERSION,
        },
    )


def _mention_ledgers(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
    *,
    duplicate_policy: DuplicatePolicy,
) -> list[DenominatorLedger]:
    scope = str(structure_spec.mention_denominator_scope or "").strip()
    if not scope:
        return []
    memberships = _mention_scope_memberships(scope, structure_spec, records)
    return [
        _mention_ledger(
            scoped_records,
            duplicate_policy=duplicate_policy,
            scope=scope_id,
        )
        for scope_id, scoped_records in memberships
    ]


def _mention_scope_memberships(
    scope: str,
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
) -> tuple[tuple[str, list[AnalyticalRecord]], ...]:
    if scope in {"structure", "parent_structure", "all_options"}:
        return ((scope, records),)
    if scope == "row":
        return tuple(
            (f"row:{row_id}", _records_for_scope(records, "row", row_id))
            for row_id in _declared_ids(structure_spec, records, "row")
        )
    if scope.startswith("row:"):
        row_id = _scope_id(scope, "row")
        _require_declared_scope_id(structure_spec, records, "row", row_id)
        return ((scope, _records_for_scope(records, "row", row_id)),)
    if scope in {"entity", "row/entity"}:
        return tuple(
            (f"entity:{entity_id}", _records_for_scope(records, "entity", entity_id))
            for entity_id in _declared_ids(structure_spec, records, "entity")
        )
    if scope.startswith("entity:"):
        entity_id = _scope_id(scope, "entity")
        _require_declared_scope_id(
            structure_spec,
            records,
            "entity",
            entity_id,
        )
        return ((scope, _records_for_scope(records, "entity", entity_id)),)
    if scope == "loop_instance":
        return tuple(
            (
                f"loop_instance:{loop_id}",
                _records_for_scope(records, "loop_instance", loop_id),
            )
            for loop_id in _declared_ids(
                structure_spec,
                records,
                "loop_instance",
            )
        )
    if scope.startswith("loop_instance:"):
        loop_id = _scope_id(scope, "loop_instance")
        _require_declared_scope_id(
            structure_spec,
            records,
            "loop_instance",
            loop_id,
        )
        return (
            (
                scope,
                _records_for_scope(records, "loop_instance", loop_id),
            ),
        )
    raise StructureExecutionError(
        f"unsupported mention_denominator_scope: {scope}",
        status=StructureExecutionStatus.REVIEW_REQUIRED,
    )


def _mention_ledger(
    records: list[AnalyticalRecord],
    *,
    duplicate_policy: DuplicatePolicy,
    scope: str,
) -> DenominatorLedger:
    selected_records = [
        record for record in records if record.applicable and record.selected
    ]
    if duplicate_policy is DuplicatePolicy.KEEP:
        selected_n = len(selected_records)
        mention_keys = [_analytical_option_key(record) for record in selected_records]
    else:
        unique_keys = {_analytical_option_key(record) for record in selected_records}
        selected_n = len(unique_keys)
        mention_keys = list(unique_keys)
    return DenominatorLedger(
        scope_id=f"mention:{scope}",
        metric_id="rm_mention",
        denominator_unit=DenominatorUnit.MENTION,
        denominator_n=selected_n,
        valid_n=selected_n,
        selected_n=selected_n,
        not_selected_n=0,
        ordinary_missing_n=0,
        structural_missing_n=sum(1 for record in records if record.structural_missing),
        invalid_n=sum(1 for record in records if record.applicable and record.invalid),
        zero_base_status="VALID_ZERO_BASE"
        if selected_n == 0
        else "NONZERO_BASE",
        repeated_dependency=_has_repeated_dependency(records),
        traceability={
            "duplicate_policy": duplicate_policy.value,
            "mention_denominator_scope": scope,
            "mention_by_option": _counts_by_option(mention_keys),
            "runtime_rules_version": STRUCTURE_RUNTIME_RULES_VERSION,
        },
    )


def _scope_id(scope: str, prefix: str) -> str:
    value = scope.removeprefix(f"{prefix}:").strip()
    if not value:
        raise StructureExecutionError(
            f"empty mention_denominator_scope id: {scope}"
        )
    return value


def _declared_ids(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
    kind: str,
) -> tuple[str, ...]:
    axis_role = "row" if kind == "row" else kind
    axis_ids = tuple(
        member.member_id
        for axis in structure_spec.axes
        if str(getattr(axis.role, "value", axis.role)) == axis_role
        for member in axis.members
    )
    if axis_ids:
        return axis_ids
    record_ids = {
        _record_scope_value(record, kind)
        for record in records
        if _record_scope_value(record, kind) is not None
    }
    return tuple(sorted(record_ids))


def _require_declared_scope_id(
    structure_spec: StructureSpec,
    records: list[AnalyticalRecord],
    kind: str,
    scope_id: str,
) -> None:
    if scope_id not in _declared_ids(structure_spec, records, kind):
        raise StructureExecutionError(
            f"unknown mention_denominator_scope {kind} id: {scope_id}"
        )


def _records_for_scope(
    records: list[AnalyticalRecord],
    kind: str,
    scope_id: str,
) -> list[AnalyticalRecord]:
    return [
        record
        for record in records
        if _record_scope_value(record, kind) == scope_id
    ]


def _record_scope_value(
    record: AnalyticalRecord,
    kind: str,
) -> str | None:
    if kind == "row":
        return record.row_id
    if kind == "entity":
        return record.entity_id
    if kind == "loop_instance":
        return record.loop_instance_id
    return None


def _ledger(
    scope_id: str,
    metric_id: str,
    unit: DenominatorUnit,
    records: list[AnalyticalRecord],
    *,
    duplicate_policy: DuplicatePolicy,
) -> DenominatorLedger:
    included = [record for record in records if record.applicable]
    structural_missing_n = sum(1 for record in records if record.structural_missing)
    invalid_n = sum(1 for record in included if record.invalid)
    ordinary_missing_n = sum(1 for record in included if record.ordinary_missing)
    selected_records = [record for record in included if record.selected]
    not_selected_n = sum(1 for record in included if record.not_selected)
    selected_n = _selected_count(selected_records, duplicate_policy)
    denominator_n = _denominator_count(included, unit)
    valid_n = denominator_n - ordinary_missing_n - invalid_n
    loop_instances = {
        record.respondent_id: set()
        for record in records
        if record.loop_instance_id is not None
    }
    for record in records:
        if record.loop_instance_id is not None and record.applicable:
            loop_instances.setdefault(record.respondent_id, set()).add(
                record.loop_instance_id
            )
    repeated_dependency = any(
        len(instances) > 1 for instances in loop_instances.values()
    )
    return DenominatorLedger(
        scope_id=scope_id,
        metric_id=metric_id,
        denominator_unit=unit,
        denominator_n=denominator_n,
        valid_n=max(valid_n, 0),
        selected_n=selected_n,
        not_selected_n=not_selected_n,
        ordinary_missing_n=ordinary_missing_n,
        structural_missing_n=structural_missing_n,
        invalid_n=invalid_n,
        zero_base_status="VALID_ZERO_BASE"
        if denominator_n == 0
        else "NONZERO_BASE",
        repeated_dependency=repeated_dependency,
        traceability={
            "duplicate_policy": duplicate_policy.value,
            "runtime_rules_version": STRUCTURE_RUNTIME_RULES_VERSION,
        },
    )


def _denominator_count(
    records: list[AnalyticalRecord],
    unit: DenominatorUnit,
) -> int:
    if unit is DenominatorUnit.RESPONDENT:
        return len({record.respondent_id for record in records})
    if unit is DenominatorUnit.RESPONDENT_OPTION:
        return len(
            {
                (record.respondent_id, record.option_id or record.binding_id)
                for record in records
            }
        )
    if unit is DenominatorUnit.INSTANCE:
        return len(
            {
                (
                    record.respondent_id,
                    record.loop_instance_id or record.binding_id,
                )
                for record in records
            }
        )
    return len(records)


def _selected_count(
    records: list[AnalyticalRecord],
    duplicate_policy: DuplicatePolicy,
) -> int:
    if duplicate_policy is DuplicatePolicy.KEEP:
        return len(records)
    keys = {_analytical_option_key(record) for record in records}
    return len(keys)


def _analytical_option_key(record: AnalyticalRecord) -> tuple[str, ...]:
    option_id = (
        record.option_id
        or record.column_id
        or record.category_id
        or record.binding_id
    )
    parts = [record.respondent_id]
    if record.row_id is not None:
        parts.append(f"row:{record.row_id}")
    if record.entity_id is not None:
        parts.append(f"entity:{record.entity_id}")
    if record.loop_instance_id is not None:
        parts.append(f"loop:{record.loop_instance_id}")
    parts.append(f"option:{option_id}")
    return tuple(parts)


def _exclusive_scope_key(record: AnalyticalRecord) -> tuple[str, ...]:
    parts = [record.respondent_id]
    if record.row_id is not None:
        parts.append(f"row:{record.row_id}")
    if record.entity_id is not None:
        parts.append(f"entity:{record.entity_id}")
    if record.loop_instance_id is not None:
        parts.append(f"loop:{record.loop_instance_id}")
    return tuple(parts)


def _counts_by_option(keys: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in keys:
        option = str(key[-1]).removeprefix("option:")
        counts[option] = counts.get(option, 0) + 1
    return counts


def _has_repeated_dependency(records: list[AnalyticalRecord]) -> bool:
    loop_instances: dict[str, set[str]] = {}
    for record in records:
        if record.loop_instance_id is not None and record.applicable:
            loop_instances.setdefault(record.respondent_id, set()).add(
                record.loop_instance_id
            )
    return any(len(instances) > 1 for instances in loop_instances.values())


def _category_for_raw_value(
    structure_spec: StructureSpec,
    raw_value: Any,
) -> str | None:
    for binding in structure_spec.category_bindings:
        if raw_value in binding.raw_values:
            return binding.category_id
    return None


def _completion_policy(spec: StructureSpec) -> CompletionPolicy:
    value = getattr(spec.completion_policy, "value", spec.completion_policy)
    return CompletionPolicy(value)


def _duplicate_policy(spec: StructureSpec) -> DuplicatePolicy:
    value = getattr(spec.duplicate_policy, "value", spec.duplicate_policy)
    return DuplicatePolicy(value)


def _is_raw_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _detector_warnings(
    structure_spec: StructureSpec,
    context: StructureEvaluationContext,
) -> tuple[str, ...]:
    detector_type = context.detector_evidence.get("structure_type")
    if detector_type and detector_type != structure_spec.structure_type:
        return (
            "detector evidence differs from RELEASED StructureSpec; "
            "RELEASED authority used",
        )
    return ()


def _validate_released_reference_chain(
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
) -> None:
    if question_spec.structure_ref is not None and question_spec.structure_ref not in {
        structure_spec.structure_id,
        structure_spec.spec_id,
    }:
        raise StructureExecutionError(
            "QuestionSpec.structure_ref does not match executed StructureSpec"
        )
    if structure_spec.parent_question_ref != question_spec.question_id:
        raise StructureExecutionError(
            "StructureSpec.parent_question_ref does not match QuestionSpec"
        )
    question_universe_ref = structure_spec.applicability_refs.get("question")
    if (
        question_spec.universe_ref
        and question_universe_ref is not None
        and question_universe_ref.universe_id != question_spec.universe_ref
    ):
        raise StructureExecutionError(
            "QuestionSpec.universe_ref conflicts with StructureSpec question "
            "applicability UniverseRef"
        )


def _require_released(spec: object, label: str) -> None:
    release = getattr(spec, "release", None)
    state = getattr(release, "state", None)
    if state is not ReleaseLifecycle.RELEASED:
        raise StructureExecutionError(
            f"{label} spec is not RELEASED: {state}"
        )
    try:
        validate_ai_release_guard(spec)
    except ContractValidationError as exc:
        raise StructureExecutionError(str(exc)) from exc


def _result(
    project_spec: ProjectSpec,
    question_spec: QuestionSpec,
    structure_spec: StructureSpec,
    mode: StructureAuthorityMode,
    status: StructureExecutionStatus,
    *,
    records: tuple[AnalyticalRecord, ...] = (),
    ledgers: tuple[DenominatorLedger, ...] = (),
    warnings: tuple[str, ...] = (),
    failures: tuple[str, ...] = (),
    context: StructureEvaluationContext,
) -> StructureExecutionResult:
    return StructureExecutionResult(
        structure_id=structure_spec.structure_id,
        structure_version=structure_spec.version,
        structure_type=structure_spec.structure_type,
        authority_mode=mode,
        runtime_rules_version=STRUCTURE_RUNTIME_RULES_VERSION,
        status=status,
        records=records,
        denominator_ledgers=ledgers,
        warnings=warnings,
        failures=failures,
        qa=_qa(status, warnings, failures),
        traceability={
            "project_id": project_spec.project_id,
            "question_id": question_spec.question_id,
            "project_spec_ref": project_spec.spec_id,
            "question_spec_ref": question_spec.spec_id,
            "structure_spec_ref": structure_spec.spec_id,
            **dict(context.traceability),
        },
    )


def _qa(
    status: StructureExecutionStatus,
    warnings: tuple[str, ...],
    failures: tuple[str, ...],
) -> QAEnvelope:
    if status is StructureExecutionStatus.PASS:
        return QAEnvelope(aggregate_state=AggregateReleaseState.PASS)
    aggregate = (
        AggregateReleaseState.FAIL
        if status is StructureExecutionStatus.FAIL
        else AggregateReleaseState.REVIEW_REQUIRED
        if status
        in {
            StructureExecutionStatus.REVIEW_REQUIRED,
            StructureExecutionStatus.UNSUPPORTED,
        }
        else AggregateReleaseState.PASS_WITH_WARNINGS
    )
    issues: list[QAIssue] = []
    for index, warning in enumerate(warnings):
        issues.append(
            QAIssue(
                issue_id=f"structure-warning-{index + 1}",
                state=QAIssueState.WARN,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="structure",
                message=warning,
                scope="structure",
            )
        )
    for index, failure in enumerate(failures):
        issues.append(
            QAIssue(
                issue_id=f"structure-failure-{index + 1}",
                state=QAIssueState.FAIL,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="structure",
                message=failure,
                scope="structure",
            )
        )
    return QAEnvelope(aggregate_state=aggregate, issues=tuple(issues))
