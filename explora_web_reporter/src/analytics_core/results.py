from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from src.analytics_core.formula_registry import (
    FORMULA_REGISTRY_VERSION,
    FormulaRegistryError,
    evaluate_formula,
    get_formula,
)
from src.analytics_core.result_identity import (
    make_id,
    new_result_run_id,
    request_identity,
    result_fingerprint,
    slice_identity,
)
from src.analytics_core.structure import DenominatorLedger, StructureExecutionResult
from src.analytics_core.universe import UniverseEvaluationResult
from src.analytics_core.weights import WeightEvaluationResult
from src.contracts.models import (
    CanonicalBase,
    CanonicalReleaseState,
    CanonicalResult,
    CanonicalResultManifest,
    CanonicalSlice,
    CanonicalValue,
    LegacyCanonicalComparison,
    MetricSpec,
    QAEnvelope,
    QAEvent,
    QAIssue,
    RequestSnapshot,
    SignificanceComparison,
    SignificanceRelation,
    UniverseRef,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    ComputationStatus,
    DenominatorUnit,
    LegacyCanonicalComparisonStatus,
    QADomain,
    QAIssueLifecycle,
    QAIssueState,
    QAReleaseStatus,
    QAScopeType,
    StatisticalState,
    ValueStatus,
)
from src.contracts.validators import validate_canonical_result


CANONICAL_RESULTS_RULES_VERSION = "M5_CANONICAL_RESULTS_V1"
CANONICAL_RESULT_SCHEMA_VERSION = "M5_CANONICAL_RESULT_V1"


def make_request_snapshot(**payload: Any) -> RequestSnapshot:
    request_id, request_fingerprint = request_identity(payload)
    return RequestSnapshot(
        request_id=request_id,
        request_fingerprint=request_fingerprint,
        question_ids=tuple(payload.get("question_ids", ())),
        metric_refs=tuple(payload.get("metric_refs", ())),
        banner_config=dict(payload.get("banner_config", {})),
        filters=dict(payload.get("filters", {})),
        weight_override=payload.get("weight_override"),
        compatibility_profile=payload.get("compatibility_profile"),
        execution_options=dict(payload.get("execution_options", {})),
    )


def make_slice(**payload: Any) -> CanonicalSlice:
    slice_id, slice_fingerprint = slice_identity(payload)
    return CanonicalSlice(
        slice_id=slice_id,
        slice_fingerprint=slice_fingerprint,
        is_total=bool(payload.get("is_total", False)),
        banner_dimension_id=payload.get("banner_dimension_id"),
        member_id=payload.get("member_id"),
        filter_refs=tuple(payload.get("filter_refs", ())),
        configuration=dict(payload.get("configuration", {})),
        label=payload.get("label"),
    )


def base_from_ledger(
    ledger: DenominatorLedger,
    *,
    result_run_id: str,
    question_id: str,
    structure_id: str,
    slice_id: str,
    universe_ref: UniverseRef,
    weight_result: WeightEvaluationResult | None = None,
    row_id: str | None = None,
    entity_id: str | None = None,
    column_id: str | None = None,
    option_id: str | None = None,
    loop_instance_id: str | None = None,
) -> CanonicalBase:
    weight_id = weight_result.active_weight_id if weight_result else None
    identity = {
        "result_run_id": result_run_id,
        "question_id": question_id,
        "structure_id": structure_id,
        "slice_id": slice_id,
        "universe_ref": universe_ref.universe_id,
        "denominator_unit": str(ledger.denominator_unit),
        "denominator_ref": ledger.metric_id,
        "denominator_scope_id": ledger.scope_id,
        "row_id": row_id,
        "entity_id": entity_id,
        "column_id": column_id,
        "option_id": option_id,
        "loop_instance_id": loop_instance_id,
        "active_weight_ref": weight_id,
    }
    return CanonicalBase(
        base_id=make_id("base", identity),
        question_id=question_id,
        structure_id=structure_id,
        slice_id=slice_id,
        universe_ref=universe_ref,
        denominator_unit=ledger.denominator_unit,
        denominator_ref=ledger.metric_id,
        denominator_scope_id=ledger.scope_id,
        unweighted_n=(
            weight_result.unweighted_n
            if weight_result is not None
            else ledger.denominator_n
        ),
        weighted_n_raw=weight_result.weighted_n_raw if weight_result else None,
        weighted_n=weight_result.weighted_n if weight_result else None,
        effective_n=weight_result.effective_n if weight_result else None,
        active_weight_ref=weight_id,
        base_status=ledger.zero_base_status,
        row_id=row_id,
        entity_id=entity_id,
        column_id=column_id,
        option_id=option_id,
        loop_instance_id=loop_instance_id,
        provenance_refs=(ledger.traceability.get("runtime_rules_version", ""),),
    )


def value_from_formula(
    metric_spec: MetricSpec,
    base: CanonicalBase,
    *,
    structure_type: str,
    result_run_id: str,
    numerator: float | int | None = None,
    denominator: float | int | None = None,
    observations: tuple[float, ...] = (),
    promoters: int | None = None,
    detractors: int | None = None,
    qa_refs: tuple[str, ...] = (),
) -> CanonicalValue:
    value, _qa_events = value_and_qa_from_formula(
        metric_spec,
        base,
        structure_type=structure_type,
        result_run_id=result_run_id,
        numerator=numerator,
        denominator=denominator,
        observations=observations,
        promoters=promoters,
        detractors=detractors,
        qa_refs=qa_refs,
    )
    return value


def value_and_qa_from_formula(
    metric_spec: MetricSpec,
    base: CanonicalBase,
    *,
    structure_type: str,
    result_run_id: str,
    numerator: float | int | None = None,
    denominator: float | int | None = None,
    observations: tuple[float, ...] = (),
    promoters: int | None = None,
    detractors: int | None = None,
    qa_refs: tuple[str, ...] = (),
) -> tuple[CanonicalValue, tuple[QAEvent, ...]]:
    weight_mode = "weighted" if base.active_weight_ref else "unweighted"
    qa: list[QAEvent] = []
    try:
        formula = get_formula(metric_spec.formula_id)
        formula_result = evaluate_formula(
            metric_spec.formula_id,
            structure_type=structure_type,
            weight_mode=weight_mode,
            denominator=denominator,
            numerator=numerator,
            observations=observations,
            promoters=promoters,
            detractors=detractors,
        )
        formula_version = formula.entry.formula_version
    except FormulaRegistryError as exc:
        formula_version = "UNKNOWN"
        formula_result = type(
            "_UnknownFormulaResult",
            (),
            {
                "value_status": ValueStatus.ERROR,
                "unit": "UNKNOWN",
                "estimate": None,
                "numerator": None,
                "denominator": None,
                "reason": str(exc),
            },
        )()
        qa.append(
            qa_event(
                qa_domain=QADomain.METRIC,
                code="UNKNOWN_FORMULA_ID",
                state=QAReleaseStatus.FAIL,
                blocking=True,
                scope_type=QAScopeType.VALUE,
                message=str(exc),
                related_ids=(metric_spec.metric_id,),
                details={"formula_id": metric_spec.formula_id},
            )
        )
    value_identity = {
        "result_run_id": result_run_id,
        "question_id": base.question_id,
        "structure_id": base.structure_id,
        "row_id": base.row_id,
        "entity_id": base.entity_id,
        "column_id": base.column_id,
        "option_id": base.option_id,
        "slice_id": base.slice_id,
        "metric_id": metric_spec.metric_id,
        "formula_id": metric_spec.formula_id,
        "formula_version": formula_version,
        "base_id": base.base_id,
    }
    if (
        formula_result.value_status is not ValueStatus.OK
        and not any(event.code == "UNKNOWN_FORMULA_ID" for event in qa)
    ):
        blocking = formula_result.value_status is ValueStatus.ERROR
        qa.append(
            qa_event(
                qa_domain=QADomain.METRIC,
                code=(
                    "FORMULA_EXECUTION_ERROR"
                    if blocking
                    else "FORMULA_UNSUPPORTED_COMBINATION"
                ),
                state=(
                    QAReleaseStatus.FAIL
                    if blocking
                    else QAReleaseStatus.REVIEW_REQUIRED
                ),
                blocking=blocking,
                scope_type=QAScopeType.VALUE,
                message=formula_result.reason
                or f"{metric_spec.formula_id} returned {formula_result.value_status.value}",
                related_ids=(metric_spec.metric_id, base.base_id),
                details={
                    "formula_id": metric_spec.formula_id,
                    "formula_version": formula_version,
                    "value_status": formula_result.value_status.value,
                    "structure_type": structure_type,
                    "weight_mode": weight_mode,
                },
            )
        )
    all_qa_refs = tuple(dict.fromkeys((*qa_refs, *(event.qa_id for event in qa))))
    value = CanonicalValue(
        value_id=make_id("value", value_identity),
        question_id=base.question_id,
        structure_id=base.structure_id,
        slice_id=base.slice_id,
        metric_id=metric_spec.metric_id,
        formula_id=metric_spec.formula_id,
        formula_version=formula_version,
        base_id=base.base_id,
        value_status=formula_result.value_status,
        unit=formula_result.unit,
        estimate=formula_result.estimate,
        numerator=formula_result.numerator,
        denominator=formula_result.denominator,
        row_id=base.row_id,
        entity_id=base.entity_id,
        column_id=base.column_id,
        option_id=base.option_id,
        loop_instance_id=base.loop_instance_id,
        qa_refs=all_qa_refs,
        provenance_refs=(FORMULA_REGISTRY_VERSION,),
    )
    return value, tuple(qa)


def qa_event(
    *,
    qa_domain: QADomain,
    code: str,
    state: QAReleaseStatus | QAIssueState,
    blocking: bool,
    scope_type: QAScopeType,
    message: str,
    related_ids: tuple[str, ...] = (),
    details: Mapping[str, Any] | None = None,
    source_component: str = "analytics_core.results",
    policy_version: str = CANONICAL_RESULTS_RULES_VERSION,
) -> QAEvent:
    payload = {
        "qa_domain": qa_domain.value,
        "code": code,
        "scope_type": scope_type.value,
        "message": message,
        "related_ids": related_ids,
        "details": details or {},
        "source_component": source_component,
        "policy_version": policy_version,
    }
    return QAEvent(
        qa_id=make_id("qa", payload),
        qa_domain=qa_domain,
        code=code,
        state=state,
        blocking=blocking,
        scope_type=scope_type,
        message=message,
        related_ids=related_ids,
        details=dict(details or {}),
        source_component=source_component,
        policy_version=policy_version,
    )


def qa_events_from_envelope(
    envelope: QAEnvelope,
    *,
    domain: QADomain,
    source_component: str,
) -> tuple[QAEvent, ...]:
    events = []
    for issue in envelope.issues:
        events.append(
            qa_event(
                qa_domain=domain,
                code=issue.layer or "UPSTREAM_QA",
                state=issue.state,
                blocking=issue.state is QAIssueState.FAIL,
                scope_type=QAScopeType.UPSTREAM,
                message=issue.message,
                related_ids=(issue.issue_id,),
                details={"lifecycle": issue.lifecycle.value, "scope": issue.scope},
                source_component=source_component,
            )
        )
    return tuple(events)


def derive_release_state(
    qa_events: tuple[QAEvent, ...],
    *,
    computation_status: ComputationStatus = ComputationStatus.COMPLETE,
    b3_release_evidence: bool = False,
) -> CanonicalReleaseState:
    if computation_status is ComputationStatus.FAILED:
        return CanonicalReleaseState(
            computation_status,
            QAReleaseStatus.FAIL,
            False,
            reasons=("computation failed",),
        )
    blocking = tuple(event for event in qa_events if event.blocking)
    if blocking:
        return CanonicalReleaseState(
            computation_status,
            QAReleaseStatus.FAIL,
            False,
            reasons=tuple(event.qa_id for event in blocking),
        )
    review_required = tuple(
        event
        for event in qa_events
        if event.state is QAReleaseStatus.REVIEW_REQUIRED
    )
    if review_required:
        return CanonicalReleaseState(
            computation_status,
            QAReleaseStatus.REVIEW_REQUIRED,
            False,
            reasons=tuple(event.qa_id for event in review_required),
        )
    if qa_events:
        return CanonicalReleaseState(
            computation_status,
            QAReleaseStatus.PASS_WITH_WARNINGS,
            b3_release_evidence,
        )
    if not b3_release_evidence:
        return CanonicalReleaseState(
            computation_status,
            QAReleaseStatus.REVIEW_REQUIRED,
            False,
            reasons=("B3 release evidence not established",),
        )
    return CanonicalReleaseState(computation_status, QAReleaseStatus.PASS, True)


def transport_significance(
    comparison: SignificanceComparison,
    *,
    result_run_id: str,
    question_id: str,
    metric_id: str,
    analytical_scope: str,
    left_slice_id: str,
    right_slice_id: str,
) -> SignificanceRelation:
    left = left_slice_id
    right = right_slice_id
    left_member = comparison.left_member_id
    right_member = comparison.right_member_id
    if (right, left) < (left, right):
        left, right = right, left
        left_member, right_member = right_member, left_member
    identity = {
        "result_run_id": result_run_id,
        "question_id": question_id,
        "metric_id": metric_id,
        "analytical_scope": analytical_scope,
        "family_id": comparison.family_id,
        "left_slice_id": left,
        "right_slice_id": right,
        "test_id": comparison.test_id,
        "test_version": comparison.test_version,
        "confidence": comparison.confidence,
    }
    return SignificanceRelation(
        comparison_id=make_id("comparison", identity),
        question_id=question_id,
        metric_id=metric_id,
        analytical_scope=analytical_scope,
        family_id=comparison.family_id,
        left_slice_id=left,
        right_slice_id=right,
        left_member_id=left_member,
        right_member_id=right_member,
        test_id=comparison.test_id,
        test_version=comparison.test_version,
        confidence=comparison.confidence,
        raw_p_value=comparison.raw_p_value,
        adjusted_p_value=comparison.adjusted_p_value,
        status=comparison.status,
        direction=comparison.direction,
    )


def assemble_canonical_result(
    *,
    project_id: str,
    dataset_fingerprint: str,
    project_spec_ref: str,
    core_version: str,
    request: RequestSnapshot,
    slices: tuple[CanonicalSlice, ...],
    bases: tuple[CanonicalBase, ...],
    values: tuple[CanonicalValue, ...],
    comparisons: tuple[SignificanceRelation, ...] = (),
    qa_events: tuple[QAEvent, ...] = (),
    result_run_id: str | None = None,
    supersedes_result_run_id: str | None = None,
    b3_release_evidence: bool = False,
) -> CanonicalResult:
    run_id = result_run_id or new_result_run_id()
    release = derive_release_state(
        qa_events,
        b3_release_evidence=b3_release_evidence,
    )
    qa = QAEnvelope(
        aggregate_state=_aggregate_state(release),
        issues=tuple(_issue_from_event(event) for event in qa_events),
    )
    draft = CanonicalResult(
        result_schema_version=CANONICAL_RESULT_SCHEMA_VERSION,
        result_run_id=run_id,
        project_id=project_id,
        dataset_fingerprint=dataset_fingerprint,
        project_spec_ref=project_spec_ref,
        core_version=core_version,
        qa=qa,
        request=request,
        slices=slices,
        bases=bases,
        values=values,
        comparisons=comparisons,
        qa_events=qa_events,
        release=release,
        supersedes_result_run_id=supersedes_result_run_id,
    )
    fp = result_fingerprint(draft)
    manifest = CanonicalResultManifest(
        schema_version=CANONICAL_RESULT_SCHEMA_VERSION,
        core_version=core_version,
        result_fingerprint=fp,
        ruleset=CANONICAL_RESULTS_RULES_VERSION,
        b1_policy_ref="B1",
        b2_policy_ref="B2",
        b3_policy_ref="B3",
        source_spec_refs=(project_spec_ref,),
    )
    result = replace(draft, result_fingerprint=fp, manifest=manifest)
    return validate_canonical_result(result)


def compare_legacy_canonical_result(
    canonical_values: Mapping[str, Any],
    legacy_values: Mapping[str, Any],
    *,
    classification: LegacyCanonicalComparisonStatus,
    reason: str = "",
) -> LegacyCanonicalComparison:
    allowed = set(LegacyCanonicalComparisonStatus)
    if classification not in allowed:
        raise ValueError(f"unknown legacy/canonical classification: {classification}")
    keys = sorted(set(canonical_values) | set(legacy_values))
    deltas = {
        key: (canonical_values.get(key), legacy_values.get(key))
        for key in keys
        if canonical_values.get(key) != legacy_values.get(key)
    }
    blocking = bool(deltas) and (
        classification is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
    )
    return LegacyCanonicalComparison(
        classification=classification,
        deltas=deltas,
        reason=reason,
        blocking=blocking,
    )


def significance_state_for_request(
    *,
    requested: bool,
    weighted: bool = False,
    rm_mention: bool = False,
    nps: bool = False,
) -> StatisticalState:
    if not requested:
        return StatisticalState.NOT_TESTED
    if weighted or rm_mention or nps:
        return StatisticalState.UNSUPPORTED
    return StatisticalState.NOT_TESTED


def _aggregate_state(release: CanonicalReleaseState) -> AggregateReleaseState:
    status = release.qa_release_status
    if status is QAReleaseStatus.FAIL:
        return AggregateReleaseState.FAIL
    if status is QAReleaseStatus.REVIEW_REQUIRED:
        return AggregateReleaseState.REVIEW_REQUIRED
    if status is QAReleaseStatus.PASS_WITH_WARNINGS:
        return AggregateReleaseState.PASS_WITH_WARNINGS
    return AggregateReleaseState.PASS


def _issue_from_event(event: QAEvent) -> QAIssue:
    state = event.state
    if isinstance(state, QAReleaseStatus):
        issue_state = (
            QAIssueState.FAIL
            if state is QAReleaseStatus.FAIL
            else QAIssueState.WARN
            if state
            in {
                QAReleaseStatus.PASS_WITH_WARNINGS,
                QAReleaseStatus.REVIEW_REQUIRED,
            }
            else QAIssueState.PASS
        )
    else:
        issue_state = QAIssueState(str(getattr(state, "value", state)))
    return QAIssue(
        issue_id=event.qa_id,
        state=issue_state,
        lifecycle=QAIssueLifecycle.OPEN,
        layer=event.qa_domain.value if isinstance(event.qa_domain, QADomain) else str(event.qa_domain),
        message=event.message,
        scope=str(getattr(event.scope_type, "value", event.scope_type)),
    )
