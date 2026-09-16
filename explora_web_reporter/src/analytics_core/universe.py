from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from numbers import Real
from typing import Any, Mapping

from src.contracts.models import (
    QAEnvelope,
    QAIssue,
    ReleaseMetadata,
    UniverseExpression,
    UniverseRef,
    UniverseSpec,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_ai_release_guard,
    validate_universe_spec,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    QAIssueLifecycle,
    QAIssueState,
    ReleaseLifecycle,
)


UNIVERSE_EVALUATOR_RULES_VERSION = "M2_UNIVERSE_V1"
SUPPORTED_SCOPE_IDS_V1 = frozenset(
    ("project", "question", "row/entity", "column", "cell")
)


class UniverseEvaluationStatus(str, Enum):
    PASS = "PASS"
    UNSUPPORTED = "UNSUPPORTED"
    FAIL = "FAIL"


class LegacyUniverseComparisonStatus(str, Enum):
    MATCH = "MATCH"
    EXPECTED_METHODOLOGICAL_CHANGE = "EXPECTED_METHODOLOGICAL_CHANGE"
    LEGACY_DEFECT = "LEGACY_DEFECT"
    UNKNOWN_REQUIRES_REVIEW = "UNKNOWN_REQUIRES_REVIEW"


@dataclass(frozen=True)
class ResponseState:
    applicable: bool | None
    answered: bool | None = None
    selected_categories: frozenset[str] = field(default_factory=frozenset)
    explicitly_not_selected_categories: frozenset[str] = field(
        default_factory=frozenset
    )


@dataclass(frozen=True)
class UniverseEvaluationContext:
    respondent_ids: tuple[str, ...]
    field_values: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    response_states: Mapping[str, Mapping[str, ResponseState]] = field(
        default_factory=dict
    )
    universe_registry: Mapping[str, UniverseSpec] = field(
        default_factory=dict
    )
    scope_universe_refs: Mapping[str, UniverseRef] = field(
        default_factory=dict
    )
    traceability: Mapping[str, str] = field(default_factory=dict)
    weights: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def field_value(self, respondent_id: str, variable_ref: str) -> Any:
        if variable_ref not in self.field_values:
            raise UniverseEvaluationError(
                f"unknown variable_ref: {variable_ref}",
                status=UniverseEvaluationStatus.FAIL,
            )
        return self.field_values[variable_ref].get(respondent_id)

    def response_state(
        self, respondent_id: str, question_ref: str
    ) -> ResponseState:
        question_states = self.response_states.get(question_ref)
        if question_states is None:
            raise UniverseEvaluationError(
                f"missing response state for question_ref: {question_ref}",
                status=UniverseEvaluationStatus.UNSUPPORTED,
            )
        state = question_states.get(respondent_id)
        if state is None:
            raise UniverseEvaluationError(
                "missing response state for respondent/question: "
                f"{respondent_id}/{question_ref}",
                status=UniverseEvaluationStatus.UNSUPPORTED,
            )
        return state

    def scope_ref(self, scope: str) -> UniverseRef:
        if scope not in SUPPORTED_SCOPE_IDS_V1:
            raise UniverseEvaluationError(
                f"unsupported universe scope: {scope}",
                status=UniverseEvaluationStatus.UNSUPPORTED,
            )
        try:
            return self.scope_universe_refs[scope]
        except KeyError as exc:
            raise UniverseEvaluationError(
                f"scope has no explicit universe composition: {scope}",
                status=UniverseEvaluationStatus.UNSUPPORTED,
            ) from exc


@dataclass(frozen=True)
class UniverseEvaluationResult:
    universe_ref: UniverseRef
    universe_spec_version: str
    evaluator_rules_version: str
    respondent_mask: dict[str, bool]
    input_n: int
    eligible_n: int
    excluded_n: int
    status: UniverseEvaluationStatus
    reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    qa: QAEnvelope | None = None
    traceability: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LegacyUniverseComparison:
    status: LegacyUniverseComparisonStatus
    differences: dict[str, tuple[bool, bool]]
    reason: str = ""


class UniverseEvaluationError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        status: UniverseEvaluationStatus = UniverseEvaluationStatus.FAIL,
    ) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class _Evaluation:
    mask: dict[str, bool]
    status: UniverseEvaluationStatus = UniverseEvaluationStatus.PASS
    reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


class UniverseEvaluator:
    rules_version = UNIVERSE_EVALUATOR_RULES_VERSION

    def evaluate(
        self,
        universe: UniverseSpec | UniverseRef,
        context: UniverseEvaluationContext,
    ) -> UniverseEvaluationResult:
        try:
            spec = self._resolve_universe(universe, context)
            evaluation = self._evaluate_spec(spec, context, stack=())
        except UniverseEvaluationError as exc:
            ref = (
                universe
                if isinstance(universe, UniverseRef)
                else UniverseRef(universe.spec_id)
            )
            return self._result(
                ref,
                "",
                context,
                _Evaluation(
                    self._empty_mask(context),
                    exc.status,
                    reasons=(str(exc),),
                ),
            )
        ref = UniverseRef(spec.spec_id)
        return self._result(ref, spec.version, context, evaluation)

    def evaluate_scope(
        self,
        scope: str,
        context: UniverseEvaluationContext,
    ) -> UniverseEvaluationResult:
        try:
            return self.evaluate(context.scope_ref(scope), context)
        except UniverseEvaluationError as exc:
            return self._result(
                UniverseRef(f"scope:{scope}"),
                "",
                context,
                _Evaluation(
                    self._empty_mask(context),
                    exc.status,
                    reasons=(str(exc),),
                ),
            )

    def _resolve_universe(
        self,
        universe: UniverseSpec | UniverseRef,
        context: UniverseEvaluationContext,
    ) -> UniverseSpec:
        if isinstance(universe, UniverseSpec):
            return universe
        if not isinstance(universe, UniverseRef):
            raise UniverseEvaluationError("universe must be a UniverseSpec or UniverseRef")
        universe_id = _require_ref_text(
            universe.universe_id, "universe_ref.universe_id"
        )
        spec = context.universe_registry.get(universe_id)
        if spec is None:
            raise UniverseEvaluationError(
                f"unknown universe_ref: {universe_id}"
            )
        return spec

    def _evaluate_spec(
        self,
        spec: UniverseSpec,
        context: UniverseEvaluationContext,
        *,
        stack: tuple[str, ...],
    ) -> _Evaluation:
        if spec.spec_id in stack:
            raise UniverseEvaluationError(
                f"circular universe_ref detected: {' -> '.join(stack + (spec.spec_id,))}"
            )
        _require_released(spec.release, spec.spec_id)
        try:
            validate_universe_spec(
                spec,
                universes=context.universe_registry,
            )
        except ContractValidationError as exc:
            raise UniverseEvaluationError(str(exc)) from exc
        return self._evaluate_expression(
            spec.expression,
            context,
            stack=stack + (spec.spec_id,),
        )

    def _evaluate_expression(
        self,
        expression: UniverseExpression,
        context: UniverseEvaluationContext,
        *,
        stack: tuple[str, ...],
    ) -> _Evaluation:
        operator = expression.operator
        args = expression.args
        try:
            if operator == "true":
                return _Evaluation(self._full_mask(context))
            if operator == "false":
                return _Evaluation(self._empty_mask(context))
            if operator == "and":
                parts = [
                    self._evaluate_expression(arg, context, stack=stack)
                    for arg in args
                ]
                return self._combine(parts, context, all)
            if operator == "or":
                parts = [
                    self._evaluate_expression(arg, context, stack=stack)
                    for arg in args
                ]
                return self._combine(parts, context, any)
            if operator == "not":
                part = self._evaluate_expression(args[0], context, stack=stack)
                return _Evaluation(
                    {
                        respondent_id: not eligible
                        for respondent_id, eligible in part.mask.items()
                    },
                    part.status,
                    part.reasons,
                    part.warnings,
                )
            if operator == "universe_ref":
                return self._evaluate_universe_ref(args[0], context, stack)
            if operator in {
                "eq",
                "neq",
                "in",
                "not_in",
                "gt",
                "gte",
                "lt",
                "lte",
                "is_missing",
                "not_missing",
            }:
                return self._evaluate_field_operator(operator, args, context)
            if operator in {
                "selected",
                "not_selected",
                "answered",
                "not_answered",
            }:
                return self._evaluate_response_operator(
                    operator, args, context
                )
            raise UniverseEvaluationError(f"unknown universe operator: {operator}")
        except IndexError as exc:
            raise UniverseEvaluationError(
                f"malformed arguments for operator: {operator}"
            ) from exc

    def _evaluate_universe_ref(
        self,
        ref: object,
        context: UniverseEvaluationContext,
        stack: tuple[str, ...],
    ) -> _Evaluation:
        if not isinstance(ref, UniverseRef):
            raise UniverseEvaluationError(
                "universe_ref must be a structured UniverseRef"
            )
        universe_id = _require_ref_text(
            ref.universe_id, "universe_ref.universe_id"
        )
        spec = context.universe_registry.get(universe_id)
        if spec is None:
            raise UniverseEvaluationError(
                f"unknown universe_ref: {universe_id}"
            )
        return self._evaluate_spec(spec, context, stack=stack)

    def _evaluate_field_operator(
        self,
        operator: str,
        args: tuple[Any, ...],
        context: UniverseEvaluationContext,
    ) -> _Evaluation:
        variable_ref = _require_ref_text(args[0], "variable_ref")
        mask: dict[str, bool] = {}
        issues: list[str] = []
        status = UniverseEvaluationStatus.PASS
        for respondent_id in context.respondent_ids:
            try:
                value = context.field_value(respondent_id, variable_ref)
                mask[respondent_id] = _field_result(
                    operator, value, args[1:], variable_ref
                )
            except UniverseEvaluationError as exc:
                mask[respondent_id] = False
                status = _max_status(status, exc.status)
                issues.append(str(exc))
        return _Evaluation(mask, status, tuple(dict.fromkeys(issues)))

    def _evaluate_response_operator(
        self,
        operator: str,
        args: tuple[Any, ...],
        context: UniverseEvaluationContext,
    ) -> _Evaluation:
        question_ref = _require_ref_text(args[0], "question_ref")
        category_ref = (
            _require_ref_text(args[1], "category_ref")
            if len(args) > 1
            else None
        )
        mask: dict[str, bool] = {}
        issues: list[str] = []
        status = UniverseEvaluationStatus.PASS
        for respondent_id in context.respondent_ids:
            try:
                state = context.response_state(respondent_id, question_ref)
                mask[respondent_id] = _response_result(
                    operator,
                    state,
                    category_ref,
                    respondent_id,
                    question_ref,
                )
            except UniverseEvaluationError as exc:
                mask[respondent_id] = False
                status = _max_status(status, exc.status)
                issues.append(str(exc))
        return _Evaluation(mask, status, tuple(dict.fromkeys(issues)))

    def _combine(
        self,
        parts: list[_Evaluation],
        context: UniverseEvaluationContext,
        reducer: Any,
    ) -> _Evaluation:
        mask = {
            respondent_id: bool(
                reducer(part.mask[respondent_id] for part in parts)
            )
            for respondent_id in context.respondent_ids
        }
        status = UniverseEvaluationStatus.PASS
        reasons: list[str] = []
        warnings: list[str] = []
        for part in parts:
            status = _max_status(status, part.status)
            reasons.extend(part.reasons)
            warnings.extend(part.warnings)
        return _Evaluation(
            mask,
            status,
            tuple(dict.fromkeys(reasons)),
            tuple(dict.fromkeys(warnings)),
        )

    def _result(
        self,
        ref: UniverseRef,
        version: str,
        context: UniverseEvaluationContext,
        evaluation: _Evaluation,
    ) -> UniverseEvaluationResult:
        eligible_n = sum(1 for value in evaluation.mask.values() if value)
        input_n = len(context.respondent_ids)
        return UniverseEvaluationResult(
            universe_ref=ref,
            universe_spec_version=version,
            evaluator_rules_version=self.rules_version,
            respondent_mask=dict(evaluation.mask),
            input_n=input_n,
            eligible_n=eligible_n,
            excluded_n=input_n - eligible_n,
            status=evaluation.status,
            reasons=evaluation.reasons,
            warnings=evaluation.warnings,
            qa=_qa(evaluation.status, evaluation.reasons),
            traceability=dict(context.traceability),
        )

    def _full_mask(
        self,
        context: UniverseEvaluationContext,
    ) -> dict[str, bool]:
        return {respondent_id: True for respondent_id in context.respondent_ids}

    def _empty_mask(
        self,
        context: UniverseEvaluationContext,
    ) -> dict[str, bool]:
        return {respondent_id: False for respondent_id in context.respondent_ids}


def _require_released(release: ReleaseMetadata, spec_id: str) -> None:
    try:
        validate_ai_release_guard(type("_Spec", (), {"release": release})())
    except ContractValidationError as exc:
        state = (
            release.state.value
            if isinstance(release.state, ReleaseLifecycle)
            else str(release.state)
        )
        raise UniverseEvaluationError(
            f"universe {spec_id} is not RELEASED: {state}"
        ) from exc


def _field_result(
    operator: str,
    value: Any,
    extra_args: tuple[Any, ...],
    variable_ref: str,
) -> bool:
    if operator == "is_missing":
        return _is_missing(value)
    if operator == "not_missing":
        return not _is_missing(value)
    if _is_missing(value):
        return False
    if operator == "eq":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return value == target
    if operator == "neq":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return value != target
    if operator == "in":
        candidates = _require_membership_candidates(
            value, extra_args[0], operator, variable_ref
        )
        return value in candidates
    if operator == "not_in":
        candidates = _require_membership_candidates(
            value, extra_args[0], operator, variable_ref
        )
        return value not in candidates
    if operator == "gt":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return _checked_compare(lambda: value > target, operator, variable_ref)
    if operator == "gte":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return _checked_compare(lambda: value >= target, operator, variable_ref)
    if operator == "lt":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return _checked_compare(lambda: value < target, operator, variable_ref)
    if operator == "lte":
        target = _require_comparable(value, extra_args[0], operator, variable_ref)
        return _checked_compare(lambda: value <= target, operator, variable_ref)
    raise UniverseEvaluationError(f"unknown field operator: {operator}")


def _response_result(
    operator: str,
    state: ResponseState,
    category_ref: str | None,
    respondent_id: str,
    question_ref: str,
) -> bool:
    if state.applicable is None:
        raise UniverseEvaluationError(
            "unknown applicability for respondent/question: "
            f"{respondent_id}/{question_ref}",
            status=UniverseEvaluationStatus.UNSUPPORTED,
        )
    if state.applicable is False:
        return False
    if operator in {"answered", "not_answered"}:
        if state.answered is None:
            raise UniverseEvaluationError(
                "unknown answer state for respondent/question: "
                f"{respondent_id}/{question_ref}",
                status=UniverseEvaluationStatus.UNSUPPORTED,
            )
        return bool(state.answered) if operator == "answered" else not state.answered
    if category_ref is None:
        raise UniverseEvaluationError(
            f"{operator} requires a category_ref",
            status=UniverseEvaluationStatus.FAIL,
        )
    selected = category_ref in state.selected_categories
    explicitly_not_selected = (
        category_ref in state.explicitly_not_selected_categories
    )
    if selected and explicitly_not_selected:
        raise UniverseEvaluationError(
            "contradictory selection state for respondent/question/category: "
            f"{respondent_id}/{question_ref}/{category_ref}",
            status=UniverseEvaluationStatus.FAIL,
        )
    if not selected and not explicitly_not_selected:
        raise UniverseEvaluationError(
            "unknown selection state for respondent/question/category: "
            f"{respondent_id}/{question_ref}/{category_ref}",
            status=UniverseEvaluationStatus.UNSUPPORTED,
        )
    if operator == "selected":
        return selected
    if operator == "not_selected":
        return state.applicable is True and explicitly_not_selected
    raise UniverseEvaluationError(f"unknown response operator: {operator}")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _require_ref_text(ref: object, name: str) -> str:
    if not isinstance(ref, str) or not ref.strip():
        raise UniverseEvaluationError(
            f"{name} must be a non-empty string reference",
            status=UniverseEvaluationStatus.FAIL,
        )
    return ref


def _require_comparable(
    value: Any,
    target: Any,
    operator: str,
    variable_ref: str,
) -> Any:
    if _is_missing(target) or not _same_comparison_domain(value, target):
        raise UniverseEvaluationError(
            "incompatible comparison operand types for "
            f"{operator} on variable_ref {variable_ref}: "
            f"{type(value).__name__} vs {type(target).__name__}",
            status=UniverseEvaluationStatus.FAIL,
        )
    return target


def _require_membership_candidates(
    value: Any,
    candidates: Any,
    operator: str,
    variable_ref: str,
) -> tuple[Any, ...]:
    if not isinstance(candidates, (list, tuple)) or not candidates:
        raise UniverseEvaluationError(
            f"{operator} requires a non-empty scalar list for {variable_ref}",
            status=UniverseEvaluationStatus.FAIL,
        )
    candidate_tuple = tuple(candidates)
    for candidate in candidate_tuple:
        _require_comparable(value, candidate, operator, variable_ref)
    return candidate_tuple


def _same_comparison_domain(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool)
    if isinstance(left, Real) and isinstance(right, Real):
        return True
    return type(left) is type(right)


def _checked_compare(
    compare: Any,
    operator: str,
    variable_ref: str,
) -> bool:
    try:
        return bool(compare())
    except (TypeError, ValueError) as exc:
        raise UniverseEvaluationError(
            f"invalid comparison for {operator} on variable_ref {variable_ref}",
            status=UniverseEvaluationStatus.FAIL,
        ) from exc


def _max_status(
    left: UniverseEvaluationStatus,
    right: UniverseEvaluationStatus,
) -> UniverseEvaluationStatus:
    order = {
        UniverseEvaluationStatus.PASS: 0,
        UniverseEvaluationStatus.UNSUPPORTED: 1,
        UniverseEvaluationStatus.FAIL: 2,
    }
    return left if order[left] >= order[right] else right


def _qa(
    status: UniverseEvaluationStatus,
    reasons: tuple[str, ...],
) -> QAEnvelope:
    if status is UniverseEvaluationStatus.PASS:
        return QAEnvelope(aggregate_state=AggregateReleaseState.PASS)
    aggregate = (
        AggregateReleaseState.REVIEW_REQUIRED
        if status is UniverseEvaluationStatus.UNSUPPORTED
        else AggregateReleaseState.FAIL
    )
    issue_state = (
        QAIssueState.WARN
        if status is UniverseEvaluationStatus.UNSUPPORTED
        else QAIssueState.FAIL
    )
    issues = tuple(
        QAIssue(
            issue_id=f"universe-{index + 1}",
            state=issue_state,
            lifecycle=QAIssueLifecycle.OPEN,
            layer="analytical",
            message=reason,
            scope="universe",
        )
        for index, reason in enumerate(reasons)
    )
    return QAEnvelope(aggregate_state=aggregate, issues=issues)


def compare_legacy_universe(
    canonical: UniverseEvaluationResult,
    legacy_mask: Mapping[str, bool],
    *,
    declared_difference: LegacyUniverseComparisonStatus | None = None,
    reason: str = "",
) -> LegacyUniverseComparison:
    differences = {
        respondent_id: (canonical_value, bool(legacy_mask.get(respondent_id)))
        for respondent_id, canonical_value in canonical.respondent_mask.items()
        if canonical_value != bool(legacy_mask.get(respondent_id))
    }
    if not differences:
        return LegacyUniverseComparison(
            status=LegacyUniverseComparisonStatus.MATCH,
            differences={},
            reason=reason,
        )
    if declared_difference in {
        LegacyUniverseComparisonStatus.EXPECTED_METHODOLOGICAL_CHANGE,
        LegacyUniverseComparisonStatus.LEGACY_DEFECT,
    }:
        return LegacyUniverseComparison(
            status=declared_difference,
            differences=differences,
            reason=reason,
        )
    return LegacyUniverseComparison(
        status=LegacyUniverseComparisonStatus.UNKNOWN_REQUIRES_REVIEW,
        differences=differences,
        reason=reason,
    )
