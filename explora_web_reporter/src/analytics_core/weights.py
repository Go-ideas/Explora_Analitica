from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Real
from typing import Any, Iterable, Mapping

from src.analytics_core.universe import (
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.contracts.models import (
    ProjectSpec,
    QAEnvelope,
    QAIssue,
    UniverseRef,
    WeightSpec,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_weight_override,
    validate_weight_spec,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    QAIssueLifecycle,
    QAIssueState,
    StatisticalState,
)


WEIGHT_RUNTIME_RULES_VERSION = "M3_WEIGHT_B1_V1"

RESOLUTION_ANALYSIS_OVERRIDE = "analysis_override"
RESOLUTION_PROJECT_DEFAULT = "project_default"
RESOLUTION_NONE = "none"

LEGACY_CANONICAL_PARITY = "PARITY"
LEGACY_CANONICAL_INTENDED_B1_CHANGE = "INTENDED_B1_CHANGE"
LEGACY_CANONICAL_M2_BASE_DIFFERENCE = "M2_BASE_DIFFERENCE"
LEGACY_CANONICAL_LEGACY_DEFECT_REPRODUCED = "LEGACY_DEFECT_REPRODUCED"
LEGACY_CANONICAL_UNSUPPORTED_V1 = "UNSUPPORTED_V1"
LEGACY_CANONICAL_POTENTIAL_REGRESSION = "POTENTIAL_REGRESSION"
LEGACY_CANONICAL_PRESENTATION_ONLY = "PRESENTATION_ONLY"


@dataclass(frozen=True)
class WeightEvaluationContext:
    respondent_ids: tuple[str, ...]
    weight_values: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    weight_specs: tuple[WeightSpec, ...] = field(default_factory=tuple)
    project_spec: ProjectSpec | None = None
    project_id: str | None = None
    dataset_fingerprint: str | None = None
    analysis_config_version: str | None = None
    analytical_scope: str = "project"
    traceability: Mapping[str, str] = field(default_factory=dict)
    candidate_weight_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WeightResolution:
    source: str
    weight_spec: WeightSpec | None = None
    status: AggregateReleaseState = AggregateReleaseState.PASS
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WeightDistributionDiagnostics:
    minimum: float | None = None
    p1: float | None = None
    p5: float | None = None
    median: float | None = None
    mean: float | None = None
    p95: float | None = None
    p99: float | None = None
    maximum: float | None = None
    cv: float | None = None
    max_min_positive_ratio: float | None = None


@dataclass(frozen=True)
class WeightQA:
    active_weight_id: str | None
    source_variable: str | None
    resolution_source: str
    weight_type_provenance: str | None
    universe_ref: UniverseRef
    universe_spec_version: str
    analytical_scope: str
    unweighted_n: int
    valid_weight_count: int
    missing_count: int
    missing_rate: float
    non_numeric_count: int
    non_numeric_rate: float
    non_finite_count: int
    non_finite_rate: float
    negative_count: int
    negative_rate: float
    zero_count: int
    zero_rate: float
    weighted_n_raw: float | None
    weighted_n: float | None
    effective_n: float | None
    distribution: WeightDistributionDiagnostics
    warnings: tuple[str, ...]
    blocking_failures: tuple[str, ...]
    status: AggregateReleaseState


@dataclass(frozen=True)
class WeightProvenance:
    project_id: str | None
    project_spec_id: str | None
    project_spec_version: str | None
    dataset_fingerprint: str | None
    analysis_config_version: str | None
    universe_ref: UniverseRef
    universe_spec_version: str
    analytical_scope: str
    weight_id: str | None
    weight_spec_id: str | None
    weight_spec_version: str | None
    source_variable: str | None
    resolution_source: str
    weight_type: str | None
    upstream_provenance: str | None
    external_normalization_provenance: str | None = None
    external_trimming_provenance: str | None = None
    b1_policy_id: str | None = None
    b1_policy_version: str | None = None
    b1_policy_hash: str | None = None
    core_rules_version: str = WEIGHT_RUNTIME_RULES_VERSION


@dataclass(frozen=True)
class WeightEvaluationResult:
    active_weight_id: str | None
    resolution_source: str
    unweighted_n: int
    weighted_n_raw: float | None
    weighted_n: float | None
    effective_n: float | None
    status: AggregateReleaseState
    qa: WeightQA
    qa_envelope: QAEnvelope
    warnings: tuple[str, ...] = field(default_factory=tuple)
    failures: tuple[str, ...] = field(default_factory=tuple)
    provenance: WeightProvenance | None = None
    traceability: dict[str, str] = field(default_factory=dict)
    significance_status: StatisticalState = StatisticalState.NOT_TESTED
    significance_reason: str | None = None
    m2_universe_result: UniverseEvaluationResult | None = None
    source_values_by_respondent: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LegacyCanonicalWeightComparison:
    classification: str
    deltas: dict[str, tuple[Any, Any]]
    reason: str = ""


def evaluate_weighted_base(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    *,
    analysis_weight_override: str | None = None,
    metric_valid_mask: Mapping[str, bool] | None = None,
    significance_requested: bool = False,
    external_normalization_provenance: str | None = None,
    external_trimming_provenance: str | None = None,
) -> WeightEvaluationResult:
    denominator_ids = _analytical_denominator_ids(
        universe_result,
        context,
        metric_valid_mask,
    )
    if universe_result.status is not UniverseEvaluationStatus.PASS:
        status = (
            AggregateReleaseState.FAIL
            if universe_result.status is UniverseEvaluationStatus.FAIL
            else AggregateReleaseState.REVIEW_REQUIRED
        )
        reason = (
            "M2 Universe dependency is not executable: "
            f"{universe_result.status.value}"
        )
        return _blocked_result(
            universe_result,
            context,
            status=status,
            reason=reason,
            resolution_source=RESOLUTION_NONE,
            unweighted_n=len(denominator_ids),
            significance_requested=significance_requested,
        )

    resolution = resolve_active_weight(
        context,
        analysis_weight_override=analysis_weight_override,
    )
    if resolution.status is AggregateReleaseState.FAIL:
        return _blocked_result(
            universe_result,
            context,
            status=AggregateReleaseState.FAIL,
            reason="; ".join(resolution.reasons),
            resolution_source=resolution.source,
            unweighted_n=len(denominator_ids),
            significance_requested=significance_requested,
        )

    if resolution.weight_spec is None:
        return _unweighted_result(
            universe_result,
            context,
            unweighted_n=len(denominator_ids),
            significance_requested=significance_requested,
        )

    spec = resolution.weight_spec
    source_values = context.weight_values.get(spec.variable_ref)
    if source_values is None:
        return _blocked_result(
            universe_result,
            context,
            status=AggregateReleaseState.FAIL,
            reason=f"missing source weight variable: {spec.variable_ref}",
            resolution_source=resolution.source,
            unweighted_n=len(denominator_ids),
            weight_spec=spec,
            significance_requested=significance_requested,
            external_normalization_provenance=external_normalization_provenance,
            external_trimming_provenance=external_trimming_provenance,
        )

    validation = _validate_applied_weights(
        denominator_ids,
        source_values,
    )
    warnings = list(validation["warnings"])
    failures = list(validation["failures"])
    valid_weights = validation["valid_weights"]
    weighted_n_raw = None if failures else float(sum(valid_weights))
    weighted_n = weighted_n_raw
    effective_n = None
    if not failures and weighted_n_raw is not None:
        effective_n = _kish_effective_n(valid_weights)
        if effective_n is None:
            warnings.append("effective_n unavailable: no positive usable weight mass")
        if denominator_ids and weighted_n_raw <= 0:
            failures.append("no positive total applied weight")
            weighted_n_raw = None
            weighted_n = None

    significance_status, significance_reason, significance_warnings = (
        _significance_guard(bool(spec), significance_requested)
    )
    warnings.extend(significance_warnings)
    status = _status_from_messages(warnings, failures)
    qa = _weight_qa(
        universe_result,
        context,
        spec,
        resolution.source,
        len(denominator_ids),
        validation,
        weighted_n_raw,
        weighted_n,
        effective_n,
        warnings,
        failures,
        status,
    )
    provenance = _provenance(
        universe_result,
        context,
        spec,
        resolution.source,
        external_normalization_provenance,
        external_trimming_provenance,
    )
    return WeightEvaluationResult(
        active_weight_id=spec.weight_id,
        resolution_source=resolution.source,
        unweighted_n=len(denominator_ids),
        weighted_n_raw=weighted_n_raw,
        weighted_n=weighted_n,
        effective_n=effective_n,
        status=status,
        qa=qa,
        qa_envelope=_qa_envelope(status, warnings, failures),
        warnings=tuple(dict.fromkeys(warnings)),
        failures=tuple(dict.fromkeys(failures)),
        provenance=provenance,
        traceability=_traceability(context),
        significance_status=significance_status,
        significance_reason=significance_reason,
        m2_universe_result=universe_result,
        source_values_by_respondent={
            respondent_id: source_values.get(respondent_id)
            for respondent_id in denominator_ids
        },
    )


def resolve_active_weight(
    context: WeightEvaluationContext,
    *,
    analysis_weight_override: str | None = None,
) -> WeightResolution:
    specs = tuple(context.weight_specs)
    try:
        for spec in specs:
            validate_weight_spec(spec, specs)
    except ContractValidationError as exc:
        return WeightResolution(
            source=(
                RESOLUTION_ANALYSIS_OVERRIDE
                if analysis_weight_override
                else RESOLUTION_PROJECT_DEFAULT
            ),
            status=AggregateReleaseState.FAIL,
            reasons=(str(exc),),
        )

    if analysis_weight_override is not None:
        try:
            selected = validate_weight_override(
                analysis_weight_override,
                specs,
            )
        except ContractValidationError as exc:
            return WeightResolution(
                source=RESOLUTION_ANALYSIS_OVERRIDE,
                status=AggregateReleaseState.FAIL,
                reasons=(str(exc),),
            )
        return WeightResolution(
            source=RESOLUTION_ANALYSIS_OVERRIDE,
            weight_spec=selected,
        )

    default_result = _resolve_project_default(context, specs)
    if default_result.status is AggregateReleaseState.FAIL:
        return default_result
    if default_result.weight_spec is not None:
        return default_result
    return WeightResolution(source=RESOLUTION_NONE)


def compare_legacy_canonical_weight_result(
    canonical: WeightEvaluationResult,
    legacy_values: Mapping[str, Any],
    *,
    classification: str,
    reason: str = "",
) -> LegacyCanonicalWeightComparison:
    allowed = {
        LEGACY_CANONICAL_PARITY,
        LEGACY_CANONICAL_INTENDED_B1_CHANGE,
        LEGACY_CANONICAL_M2_BASE_DIFFERENCE,
        LEGACY_CANONICAL_LEGACY_DEFECT_REPRODUCED,
        LEGACY_CANONICAL_UNSUPPORTED_V1,
        LEGACY_CANONICAL_POTENTIAL_REGRESSION,
        LEGACY_CANONICAL_PRESENTATION_ONLY,
    }
    if classification not in allowed:
        raise ValueError(f"unknown legacy/canonical classification: {classification}")
    canonical_values = {
        "unweighted_n": canonical.unweighted_n,
        "weighted_n_raw": canonical.weighted_n_raw,
        "weighted_n": canonical.weighted_n,
        "effective_n": canonical.effective_n,
        "status": canonical.status,
    }
    deltas = {
        key: (canonical_values.get(key), legacy_values.get(key))
        for key in sorted(set(canonical_values) | set(legacy_values))
        if canonical_values.get(key) != legacy_values.get(key)
    }
    return LegacyCanonicalWeightComparison(
        classification=classification,
        deltas=deltas,
        reason=reason,
    )


def _resolve_project_default(
    context: WeightEvaluationContext,
    specs: tuple[WeightSpec, ...],
) -> WeightResolution:
    flagged = tuple(spec for spec in specs if spec.is_project_default)
    selector = (
        context.project_spec.default_weight_ref
        if context.project_spec is not None
        else None
    )
    if selector and flagged:
        matching_flagged = tuple(
            spec for spec in flagged if spec.weight_id == selector
        )
        if len(matching_flagged) != len(flagged):
            return WeightResolution(
                source=RESOLUTION_PROJECT_DEFAULT,
                status=AggregateReleaseState.FAIL,
                reasons=(
                    "conflicting project default weight authorities: "
                    "ProjectSpec.default_weight_ref and "
                    "WeightSpec.is_project_default disagree",
                ),
            )
    if selector:
        matches = _matching_specs(specs, selector)
        if not matches:
            return WeightResolution(
                source=RESOLUTION_PROJECT_DEFAULT,
                status=AggregateReleaseState.FAIL,
                reasons=(f"unknown project default weight: {selector}",),
            )
        if len(matches) > 1:
            return WeightResolution(
                source=RESOLUTION_PROJECT_DEFAULT,
                status=AggregateReleaseState.FAIL,
                reasons=(f"ambiguous project default weight: {selector}",),
            )
        return WeightResolution(
            source=RESOLUTION_PROJECT_DEFAULT,
            weight_spec=matches[0],
        )
    if len(flagged) > 1:
        return WeightResolution(
            source=RESOLUTION_PROJECT_DEFAULT,
            status=AggregateReleaseState.FAIL,
            reasons=("only one project default weight is allowed",),
        )
    if flagged:
        return WeightResolution(
            source=RESOLUTION_PROJECT_DEFAULT,
            weight_spec=flagged[0],
        )
    return WeightResolution(source=RESOLUTION_NONE)


def _matching_specs(
    specs: Iterable[WeightSpec],
    weight_id: str,
) -> tuple[WeightSpec, ...]:
    return tuple(spec for spec in specs if spec.weight_id == weight_id)


def _analytical_denominator_ids(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    metric_valid_mask: Mapping[str, bool] | None,
) -> tuple[str, ...]:
    ids = []
    seen = set()
    for respondent_id in context.respondent_ids:
        if respondent_id in seen:
            continue
        seen.add(respondent_id)
        if not universe_result.respondent_mask.get(respondent_id, False):
            continue
        if metric_valid_mask is not None and not metric_valid_mask.get(
            respondent_id, False
        ):
            continue
        ids.append(respondent_id)
    return tuple(ids)


def _validate_applied_weights(
    denominator_ids: tuple[str, ...],
    source_values: Mapping[str, Any],
) -> dict[str, Any]:
    counts = {
        "valid_weight_count": 0,
        "missing_count": 0,
        "non_numeric_count": 0,
        "non_finite_count": 0,
        "negative_count": 0,
        "zero_count": 0,
    }
    valid_weights: list[float] = []
    warnings: list[str] = []
    failures: list[str] = []
    for respondent_id in denominator_ids:
        raw = source_values.get(respondent_id)
        if _is_missing(raw):
            counts["missing_count"] += 1
            continue
        if not _is_numeric_weight(raw):
            counts["non_numeric_count"] += 1
            continue
        value = float(raw)
        if not math.isfinite(value):
            counts["non_finite_count"] += 1
            failures.append(f"non-finite weight for respondent: {respondent_id}")
            continue
        if value < 0:
            counts["negative_count"] += 1
            failures.append(
                f"negative weight is UNSUPPORTED V1 for respondent: {respondent_id}"
            )
            continue
        if value == 0:
            counts["zero_count"] += 1
        counts["valid_weight_count"] += 1
        valid_weights.append(value)
    if counts["missing_count"]:
        warnings.append("missing weight values excluded from weighted contribution")
    if counts["non_numeric_count"]:
        warnings.append("non-numeric weight values excluded from weighted contribution")
    return {
        **counts,
        "valid_weights": tuple(valid_weights),
        "warnings": tuple(dict.fromkeys(warnings)),
        "failures": tuple(dict.fromkeys(failures)),
    }


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if _is_numeric_weight(value):
        try:
            return math.isnan(float(value))
        except (OverflowError, TypeError, ValueError):
            return False
    return False


def _is_numeric_weight(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _kish_effective_n(weights: tuple[float, ...]) -> float | None:
    total = sum(weights)
    square_total = sum(weight * weight for weight in weights)
    if total <= 0 or square_total <= 0:
        return None
    return (total * total) / square_total


def _status_from_messages(
    warnings: list[str],
    failures: list[str],
) -> AggregateReleaseState:
    if failures:
        return AggregateReleaseState.FAIL
    if warnings:
        return AggregateReleaseState.PASS_WITH_WARNINGS
    return AggregateReleaseState.PASS


def _rate(count: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else count / denominator


def _weight_qa(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    spec: WeightSpec,
    resolution_source: str,
    unweighted_n: int,
    validation: Mapping[str, Any],
    weighted_n_raw: float | None,
    weighted_n: float | None,
    effective_n: float | None,
    warnings: list[str],
    failures: list[str],
    status: AggregateReleaseState,
) -> WeightQA:
    return WeightQA(
        active_weight_id=spec.weight_id,
        source_variable=spec.variable_ref,
        resolution_source=resolution_source,
        weight_type_provenance=spec.provenance,
        universe_ref=universe_result.universe_ref,
        universe_spec_version=universe_result.universe_spec_version,
        analytical_scope=context.analytical_scope,
        unweighted_n=unweighted_n,
        valid_weight_count=int(validation["valid_weight_count"]),
        missing_count=int(validation["missing_count"]),
        missing_rate=_rate(int(validation["missing_count"]), unweighted_n),
        non_numeric_count=int(validation["non_numeric_count"]),
        non_numeric_rate=_rate(int(validation["non_numeric_count"]), unweighted_n),
        non_finite_count=int(validation["non_finite_count"]),
        non_finite_rate=_rate(int(validation["non_finite_count"]), unweighted_n),
        negative_count=int(validation["negative_count"]),
        negative_rate=_rate(int(validation["negative_count"]), unweighted_n),
        zero_count=int(validation["zero_count"]),
        zero_rate=_rate(int(validation["zero_count"]), unweighted_n),
        weighted_n_raw=weighted_n_raw,
        weighted_n=weighted_n,
        effective_n=effective_n,
        distribution=_distribution(validation["valid_weights"]),
        warnings=tuple(dict.fromkeys(warnings)),
        blocking_failures=tuple(dict.fromkeys(failures)),
        status=status,
    )


def _empty_weight_qa(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    *,
    status: AggregateReleaseState,
    resolution_source: str,
    unweighted_n: int,
    warnings: tuple[str, ...] = (),
    failures: tuple[str, ...] = (),
    weight_spec: WeightSpec | None = None,
) -> WeightQA:
    return WeightQA(
        active_weight_id=weight_spec.weight_id if weight_spec else None,
        source_variable=weight_spec.variable_ref if weight_spec else None,
        resolution_source=resolution_source,
        weight_type_provenance=weight_spec.provenance if weight_spec else None,
        universe_ref=universe_result.universe_ref,
        universe_spec_version=universe_result.universe_spec_version,
        analytical_scope=context.analytical_scope,
        unweighted_n=unweighted_n,
        valid_weight_count=0,
        missing_count=0,
        missing_rate=0.0,
        non_numeric_count=0,
        non_numeric_rate=0.0,
        non_finite_count=0,
        non_finite_rate=0.0,
        negative_count=0,
        negative_rate=0.0,
        zero_count=0,
        zero_rate=0.0,
        weighted_n_raw=None,
        weighted_n=None,
        effective_n=None,
        distribution=WeightDistributionDiagnostics(),
        warnings=warnings,
        blocking_failures=failures,
        status=status,
    )


def _distribution(
    weights: tuple[float, ...],
) -> WeightDistributionDiagnostics:
    if not weights:
        return WeightDistributionDiagnostics()
    ordered = tuple(sorted(weights))
    mean = sum(ordered) / len(ordered)
    variance = sum((value - mean) ** 2 for value in ordered) / len(ordered)
    sd = math.sqrt(variance)
    positives = tuple(value for value in ordered if value > 0)
    return WeightDistributionDiagnostics(
        minimum=ordered[0],
        p1=_percentile(ordered, 0.01),
        p5=_percentile(ordered, 0.05),
        median=_percentile(ordered, 0.50),
        mean=mean,
        p95=_percentile(ordered, 0.95),
        p99=_percentile(ordered, 0.99),
        maximum=ordered[-1],
        cv=None if mean == 0 else sd / mean,
        max_min_positive_ratio=(
            None if not positives else max(positives) / min(positives)
        ),
    )


def _percentile(values: tuple[float, ...], quantile: float) -> float:
    if len(values) == 1:
        return values[0]
    position = quantile * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


def _significance_guard(
    has_active_weight: bool,
    significance_requested: bool,
) -> tuple[StatisticalState, str | None, tuple[str, ...]]:
    if not significance_requested:
        return StatisticalState.NOT_TESTED, None, ()
    if has_active_weight:
        reason = "weighted significance is UNSUPPORTED V1"
        return StatisticalState.UNSUPPORTED, reason, (reason,)
    return StatisticalState.NOT_TESTED, None, ()


def _unweighted_result(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    *,
    unweighted_n: int,
    significance_requested: bool,
) -> WeightEvaluationResult:
    significance_status, significance_reason, warnings = _significance_guard(
        False,
        significance_requested,
    )
    status = AggregateReleaseState.PASS
    qa = _empty_weight_qa(
        universe_result,
        context,
        status=status,
        resolution_source=RESOLUTION_NONE,
        unweighted_n=unweighted_n,
        warnings=warnings,
    )
    return WeightEvaluationResult(
        active_weight_id=None,
        resolution_source=RESOLUTION_NONE,
        unweighted_n=unweighted_n,
        weighted_n_raw=None,
        weighted_n=None,
        effective_n=None,
        status=status,
        qa=qa,
        qa_envelope=_qa_envelope(status, list(warnings), []),
        warnings=warnings,
        provenance=_provenance(universe_result, context, None, RESOLUTION_NONE),
        traceability=_traceability(context),
        significance_status=significance_status,
        significance_reason=significance_reason,
        m2_universe_result=universe_result,
    )


def _blocked_result(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    *,
    status: AggregateReleaseState,
    reason: str,
    resolution_source: str,
    unweighted_n: int,
    significance_requested: bool,
    weight_spec: WeightSpec | None = None,
    external_normalization_provenance: str | None = None,
    external_trimming_provenance: str | None = None,
) -> WeightEvaluationResult:
    failures = (reason,)
    significance_status, significance_reason, warnings = _significance_guard(
        weight_spec is not None,
        significance_requested,
    )
    qa = _empty_weight_qa(
        universe_result,
        context,
        status=status,
        resolution_source=resolution_source,
        unweighted_n=unweighted_n,
        warnings=warnings,
        failures=failures,
        weight_spec=weight_spec,
    )
    return WeightEvaluationResult(
        active_weight_id=weight_spec.weight_id if weight_spec else None,
        resolution_source=resolution_source,
        unweighted_n=unweighted_n,
        weighted_n_raw=None,
        weighted_n=None,
        effective_n=None,
        status=status,
        qa=qa,
        qa_envelope=_qa_envelope(status, list(warnings), list(failures)),
        warnings=warnings,
        failures=failures,
        provenance=_provenance(
            universe_result,
            context,
            weight_spec,
            resolution_source,
            external_normalization_provenance,
            external_trimming_provenance,
        ),
        traceability=_traceability(context),
        significance_status=significance_status,
        significance_reason=significance_reason,
        m2_universe_result=universe_result,
    )


def _provenance(
    universe_result: UniverseEvaluationResult,
    context: WeightEvaluationContext,
    spec: WeightSpec | None,
    resolution_source: str,
    external_normalization_provenance: str | None = None,
    external_trimming_provenance: str | None = None,
) -> WeightProvenance:
    project = context.project_spec
    return WeightProvenance(
        project_id=(
            project.project_id
            if project is not None
            else context.project_id
        ),
        project_spec_id=project.spec_id if project is not None else None,
        project_spec_version=project.version if project is not None else None,
        dataset_fingerprint=(
            project.dataset_fingerprint
            if project is not None
            else context.dataset_fingerprint
        ),
        analysis_config_version=context.analysis_config_version,
        universe_ref=universe_result.universe_ref,
        universe_spec_version=universe_result.universe_spec_version,
        analytical_scope=context.analytical_scope,
        weight_id=spec.weight_id if spec else None,
        weight_spec_id=spec.spec_id if spec else None,
        weight_spec_version=spec.version if spec else None,
        source_variable=spec.variable_ref if spec else None,
        resolution_source=resolution_source,
        weight_type=spec.provenance if spec else None,
        upstream_provenance=spec.provenance if spec else None,
        external_normalization_provenance=external_normalization_provenance,
        external_trimming_provenance=external_trimming_provenance,
        b1_policy_id=spec.release.policy_id if spec else None,
        b1_policy_version=spec.release.policy_version if spec else None,
        b1_policy_hash=spec.release.source_hash if spec else None,
    )


def _qa_envelope(
    status: AggregateReleaseState,
    warnings: list[str],
    failures: list[str],
) -> QAEnvelope:
    issues = []
    for index, message in enumerate(failures):
        issues.append(
            QAIssue(
                issue_id=f"weight-fail-{index + 1}",
                state=QAIssueState.FAIL,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="analytical",
                message=message,
                scope="weight",
            )
        )
    for index, message in enumerate(warnings):
        issues.append(
            QAIssue(
                issue_id=f"weight-warn-{index + 1}",
                state=QAIssueState.WARN,
                lifecycle=QAIssueLifecycle.OPEN,
                layer="analytical",
                message=message,
                scope="weight",
            )
        )
    return QAEnvelope(aggregate_state=status, issues=tuple(issues))


def _traceability(context: WeightEvaluationContext) -> dict[str, str]:
    return dict(context.traceability)
