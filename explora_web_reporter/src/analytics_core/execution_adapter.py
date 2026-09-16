from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Mapping, Sequence

from src.analytics_core.results import (
    assemble_canonical_result,
    base_from_ledger,
    qa_event,
    value_from_formula,
)
from src.analytics_core.result_identity import new_result_run_id
from src.analytics_core.structure import (
    AnalyticalRecord,
    DenominatorLedger,
    StructureExecutionResult,
)
from src.analytics_core.universe import (
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.analytics_core.weights import WeightEvaluationResult
from src.contracts.models import (
    CanonicalResult,
    CanonicalSlice,
    CanonicalValue,
    MetricSpec,
    QAEvent,
    RequestSnapshot,
    SignificanceRelation,
    UniverseRef,
)
from src.contracts.validators import ContractValidationError, validate_metric_spec
from src.contracts.vocabulary import (
    AggregateReleaseState,
    DenominatorUnit,
    QADomain,
    QAReleaseStatus,
    QAScopeType,
    ReleaseLifecycle,
    StructureExecutionStatus,
)


EXECUTION_ADAPTER_VERSION = "M5_CANONICAL_EXECUTION_ADAPTER_V1"


FORMULA_ID_ALIASES = {
    "count/v1": "COUNT",
    "proportion/v1": "PROPORTION",
    "rm_respondent_proportion/v1": "RM_RESPONDENT_PROPORTION",
    "rm_mention_proportion/v1": "RM_MENTION_PROPORTION",
    "mean/v1": "MEAN",
    "scale_mean/v1": "SCALE_MEAN",
    "standard_deviation/v1": "STANDARD_DEVIATION",
    "top_box/v1": "TOP_BOX",
    "bottom_box/v1": "BOTTOM_BOX",
    "nps_descriptive/v1": "NPS_DESCRIPTIVE",
}


class ExecutionAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class SliceExecutionAuthority:
    slice: CanonicalSlice
    universe_result: UniverseEvaluationResult


@dataclass(frozen=True)
class CanonicalExecutionContext:
    project_id: str
    dataset_fingerprint: str
    project_spec_ref: str
    request: RequestSnapshot
    question_id: str
    structure_ref: str
    structure_result: StructureExecutionResult
    universe_result: UniverseEvaluationResult
    metric_specs: tuple[MetricSpec, ...]
    runtime_fingerprint: str
    slices: tuple[SliceExecutionAuthority, ...] = field(default_factory=tuple)
    weight_result: WeightEvaluationResult | None = None
    comparisons: tuple[SignificanceRelation, ...] = field(default_factory=tuple)
    qa_events: tuple[QAEvent, ...] = field(default_factory=tuple)
    core_version: str = EXECUTION_ADAPTER_VERSION
    result_run_id: str | None = None
    b3_release_evidence: bool = False
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)


def execute_canonical_request(
    context: CanonicalExecutionContext | None = None,
    **kwargs: Any,
) -> CanonicalResult:
    ctx = context if context is not None else CanonicalExecutionContext(**kwargs)
    _validate_context(ctx)
    run_id = ctx.result_run_id or new_result_run_id()
    slices = _validated_slices(ctx)
    bases: list[Any] = []
    values: list[CanonicalValue] = []
    qa_events = list(ctx.qa_events)
    for slice_authority in slices:
        _require_universe(slice_authority.universe_result, "slice")
        records = _records_for_slice(
            ctx.structure_result.records,
            slice_authority.universe_result,
        )
        for metric in ctx.metric_specs:
            runtime_metric = _runtime_metric(metric)
            metric_bases, metric_values = _execute_metric(
                runtime_metric,
                released_metric=metric,
                ctx=ctx,
                slice_authority=slice_authority,
                records=records,
                result_run_id=run_id,
            )
            bases.extend(metric_bases)
            values.extend(metric_values)
    qa_events.extend(_upstream_qa_events(ctx))
    return assemble_canonical_result(
        project_id=ctx.project_id,
        dataset_fingerprint=ctx.dataset_fingerprint,
        project_spec_ref=ctx.project_spec_ref,
        core_version=ctx.core_version,
        request=ctx.request,
        slices=tuple(authority.slice for authority in slices),
        bases=tuple(bases),
        values=tuple(values),
        comparisons=ctx.comparisons,
        qa_events=tuple(_unique_qa_events(qa_events)),
        result_run_id=run_id,
        b3_release_evidence=ctx.b3_release_evidence,
    )


def _execute_metric(
    metric: MetricSpec,
    *,
    released_metric: MetricSpec,
    ctx: CanonicalExecutionContext,
    slice_authority: SliceExecutionAuthority,
    records: tuple[AnalyticalRecord, ...],
    result_run_id: str,
) -> tuple[tuple[Any, ...], tuple[CanonicalValue, ...]]:
    formula_id = metric.formula_id
    if formula_id in {"COUNT", "PROPORTION", "TOP_BOX", "BOTTOM_BOX"}:
        _require_structure_type(ctx, {"RU", "GRID_ESCALA", "LOOP_RU"})
        return _execute_ru_metric(
            metric,
            released_metric=released_metric,
            ctx=ctx,
            slice_authority=slice_authority,
            records=records,
            source_ledger=_require_ledger(
                ctx.structure_result,
                DenominatorUnit.RESPONDENT,
            ),
            result_run_id=result_run_id,
        )
    if formula_id == "RM_RESPONDENT_PROPORTION":
        _require_structure_type(ctx, {"RM", "GRID_RM", "LOOP_RM"})
        return _execute_rm_respondent_metric(
            metric,
            released_metric=released_metric,
            ctx=ctx,
            slice_authority=slice_authority,
            records=records,
            source_ledger=_require_ledger(
                ctx.structure_result,
                DenominatorUnit.RESPONDENT_OPTION,
            ),
            result_run_id=result_run_id,
        )
    if formula_id == "RM_MENTION_PROPORTION":
        _require_structure_type(ctx, {"RM", "GRID_RM", "LOOP_RM"})
        return _execute_rm_mention_metric(
            metric,
            released_metric=released_metric,
            ctx=ctx,
            slice_authority=slice_authority,
            records=records,
            source_ledger=_compatible_mention_ledger(
                ctx,
                metric,
            ),
            result_run_id=result_run_id,
        )
    raise ExecutionAdapterError(f"unsupported adapter formula: {formula_id}")


def _execute_ru_metric(
    metric: MetricSpec,
    *,
    released_metric: MetricSpec,
    ctx: CanonicalExecutionContext,
    slice_authority: SliceExecutionAuthority,
    records: tuple[AnalyticalRecord, ...],
    source_ledger: DenominatorLedger,
    result_run_id: str,
) -> tuple[tuple[Any, ...], tuple[CanonicalValue, ...]]:
    _require_structure_type(ctx, {"RU", "GRID_ESCALA", "LOOP_RU"})
    categories = _requested_categories(metric, records)
    if not categories:
        raise ExecutionAdapterError("RU metric requires category identity")
    valid_records = tuple(record for record in records if _valid_category(record))
    denominator = len({record.respondent_id for record in valid_records})
    bases = []
    values = []
    for order, category_id in enumerate(categories):
        numerator = sum(1 for record in valid_records if record.category_id == category_id)
        ledger = _ledger(
            scope_id=f"structure:category:{category_id}",
            metric_id=metric.metric_id,
            denominator_unit=DenominatorUnit.RESPONDENT,
            denominator_n=denominator,
            valid_n=denominator,
            selected_n=numerator,
        )
        base = base_from_ledger(
            ledger,
            result_run_id=result_run_id,
            question_id=ctx.question_id,
            structure_id=ctx.structure_result.structure_id,
            slice_id=slice_authority.slice.slice_id,
            universe_ref=metric_universe(metric),
            weight_result=ctx.weight_result,
            option_id=category_id,
        )
        provenance = _provenance_refs(
            ctx,
            released_metric,
            slice_authority,
            ledger,
            source_ledger,
        )
        base = replace(base, provenance_refs=provenance)
        value = value_from_formula(
            metric,
            base,
            structure_type=str(ctx.structure_result.structure_type),
            result_run_id=result_run_id,
            numerator=numerator,
            denominator=denominator,
            qa_refs=tuple(event.qa_id for event in ctx.qa_events),
        )
        bases.append(base)
        values.append(
            replace(
                value,
                category_id=category_id,
                semantic_order=order,
                provenance_refs=provenance,
            )
        )
        _validate_value_provenance(values[-1], ctx, metric)
    return tuple(bases), tuple(values)


def _execute_rm_respondent_metric(
    metric: MetricSpec,
    *,
    released_metric: MetricSpec,
    ctx: CanonicalExecutionContext,
    slice_authority: SliceExecutionAuthority,
    records: tuple[AnalyticalRecord, ...],
    source_ledger: DenominatorLedger,
    result_run_id: str,
) -> tuple[tuple[Any, ...], tuple[CanonicalValue, ...]]:
    _require_structure_type(ctx, {"RM", "GRID_RM", "LOOP_RM"})
    options = _requested_options(metric, records)
    if not options:
        raise ExecutionAdapterError("RM respondent metric requires option identity")
    _require_ledger(ctx.structure_result, DenominatorUnit.RESPONDENT_OPTION)
    bases = []
    values = []
    for order, option_id in enumerate(options):
        valid = tuple(
            record
            for record in records
            if record.option_id == option_id
            and record.applicable
            and (record.selected or record.not_selected)
        )
        denominator = len({record.respondent_id for record in valid})
        numerator = len({record.respondent_id for record in valid if record.selected})
        ledger = _ledger(
            scope_id=f"respondent:option:{option_id}",
            metric_id=metric.metric_id,
            denominator_unit=DenominatorUnit.RESPONDENT,
            denominator_n=denominator,
            valid_n=denominator,
            selected_n=numerator,
            not_selected_n=denominator - numerator,
        )
        base = base_from_ledger(
            ledger,
            result_run_id=result_run_id,
            question_id=ctx.question_id,
            structure_id=ctx.structure_result.structure_id,
            slice_id=slice_authority.slice.slice_id,
            universe_ref=metric_universe(metric),
            weight_result=ctx.weight_result,
            option_id=option_id,
        )
        provenance = _provenance_refs(
            ctx,
            released_metric,
            slice_authority,
            ledger,
            source_ledger,
        )
        base = replace(base, provenance_refs=provenance)
        value = value_from_formula(
            metric,
            base,
            structure_type=str(ctx.structure_result.structure_type),
            result_run_id=result_run_id,
            numerator=numerator,
            denominator=denominator,
            qa_refs=tuple(event.qa_id for event in ctx.qa_events),
        )
        bases.append(base)
        values.append(
            replace(
                value,
                semantic_order=order,
                provenance_refs=provenance,
            )
        )
        _validate_value_provenance(values[-1], ctx, metric)
    return tuple(bases), tuple(values)


def _execute_rm_mention_metric(
    metric: MetricSpec,
    *,
    released_metric: MetricSpec,
    ctx: CanonicalExecutionContext,
    slice_authority: SliceExecutionAuthority,
    records: tuple[AnalyticalRecord, ...],
    source_ledger: DenominatorLedger,
    result_run_id: str,
) -> tuple[tuple[Any, ...], tuple[CanonicalValue, ...]]:
    _require_structure_type(ctx, {"RM", "GRID_RM", "LOOP_RM"})
    options = _requested_options(metric, records)
    if not options:
        raise ExecutionAdapterError("RM mention metric requires option identity")
    selected = tuple(record for record in records if record.applicable and record.selected)
    denominator = len(_mention_keys(selected, source_ledger))
    bases = []
    values = []
    for order, option_id in enumerate(options):
        option_selected = tuple(record for record in selected if record.option_id == option_id)
        numerator = len(_mention_keys(option_selected, source_ledger))
        ledger = _ledger(
            scope_id=source_ledger.scope_id,
            metric_id=metric.metric_id,
            denominator_unit=DenominatorUnit.MENTION,
            denominator_n=denominator,
            valid_n=denominator,
            selected_n=numerator,
        )
        base = base_from_ledger(
            ledger,
            result_run_id=result_run_id,
            question_id=ctx.question_id,
            structure_id=ctx.structure_result.structure_id,
            slice_id=slice_authority.slice.slice_id,
            universe_ref=metric_universe(metric),
            weight_result=ctx.weight_result,
            option_id=option_id,
        )
        provenance = _provenance_refs(
            ctx,
            released_metric,
            slice_authority,
            ledger,
            source_ledger,
        )
        base = replace(base, provenance_refs=provenance)
        value = value_from_formula(
            metric,
            base,
            structure_type=str(ctx.structure_result.structure_type),
            result_run_id=result_run_id,
            numerator=numerator,
            denominator=denominator,
            qa_refs=tuple(event.qa_id for event in ctx.qa_events),
        )
        bases.append(base)
        values.append(
            replace(
                value,
                semantic_order=order,
                provenance_refs=provenance,
            )
        )
        _validate_value_provenance(values[-1], ctx, metric)
    return tuple(bases), tuple(values)


def _validate_context(ctx: CanonicalExecutionContext) -> None:
    _require_text(ctx.project_id, "project_id")
    _require_text(ctx.dataset_fingerprint, "dataset_fingerprint")
    _require_text(ctx.project_spec_ref, "project_spec_ref")
    _require_text(ctx.runtime_fingerprint, "runtime_fingerprint")
    _require_text(ctx.question_id, "question_id")
    _require_text(ctx.structure_ref, "structure_ref")
    if ctx.request is None:
        raise ExecutionAdapterError("missing request snapshot")
    _require_text(ctx.request.request_id, "request_id")
    _require_text(ctx.request.request_fingerprint, "request_fingerprint")
    _require_universe(ctx.universe_result, "request")
    if ctx.structure_result is None:
        raise ExecutionAdapterError("missing M4 structure result")
    if ctx.structure_result.status not in {
        StructureExecutionStatus.PASS,
        StructureExecutionStatus.PASS_WITH_WARNINGS,
    }:
        raise ExecutionAdapterError(
            f"M4 structure status is not executable: {ctx.structure_result.status}"
        )
    if not ctx.metric_specs:
        raise ExecutionAdapterError("missing released metric specs")
    for metric in ctx.metric_specs:
        _require_text(metric.metric_id, "metric_ref")
        _require_text(metric.formula_id, "formula_ref")
        _require_text(metric.universe_ref, "universe_ref")
        try:
            validate_metric_spec(metric)
        except ContractValidationError as exc:
            raise ExecutionAdapterError(str(exc)) from exc
        if metric.metric_id not in set(ctx.request.metric_refs):
            raise ExecutionAdapterError(
                f"metric_ref is not in request snapshot: {metric.metric_id}"
            )
        if metric.release.state is not ReleaseLifecycle.RELEASED:
            raise ExecutionAdapterError(f"metric is not RELEASED: {metric.metric_id}")
        if metric.weight_behavior != "unweighted":
            if ctx.weight_result is None:
                raise ExecutionAdapterError("weighted request requires M3 result")
            if ctx.weight_result.status is AggregateReleaseState.FAIL:
                raise ExecutionAdapterError("blocking M3 weight status")
            if not ctx.weight_result.qa_envelope:
                raise ExecutionAdapterError("weighted request requires M3 QA reference")
            if not ctx.weight_result.active_weight_id:
                raise ExecutionAdapterError("weighted request requires active M3 weight")


def _validated_slices(
    ctx: CanonicalExecutionContext,
) -> tuple[SliceExecutionAuthority, ...]:
    if not ctx.slices:
        raise ExecutionAdapterError("missing authoritative slice")
    for authority in ctx.slices:
        _require_text(authority.slice.slice_id, "slice identity")
        _require_text(authority.slice.slice_fingerprint, "slice fingerprint")
        _require_universe(authority.universe_result, "slice")
        if authority.slice.is_total:
            if ctx.request.filters or ctx.request.banner_config:
                raise ExecutionAdapterError(
                    "filtered or banner request requires non-total slice authority"
                )
            if ctx.request.execution_options.get("slice_authority") != "explicit_total":
                raise ExecutionAdapterError(
                    "explicit Total slice requires request slice_authority=explicit_total"
                )
        if ctx.request.filters and not authority.slice.filter_refs:
            raise ExecutionAdapterError(
                "filtered request requires authoritative filtered slice"
            )
        if ctx.request.banner_config and (
            not authority.slice.banner_dimension_id or not authority.slice.member_id
        ):
            raise ExecutionAdapterError(
                "banner request requires authoritative banner slice"
            )
    return ctx.slices


def _runtime_metric(metric: MetricSpec) -> MetricSpec:
    mapped = FORMULA_ID_ALIASES.get(metric.formula_id, metric.formula_id)
    if mapped != metric.formula_id:
        return replace(
            metric,
            formula_id=mapped,
            parameters={
                **metric.parameters,
                "released_formula_id": metric.formula_id,
            },
        )
    return metric


def _records_for_slice(
    records: Sequence[AnalyticalRecord],
    universe_result: UniverseEvaluationResult,
) -> tuple[AnalyticalRecord, ...]:
    allowed = universe_result.respondent_mask
    return tuple(record for record in records if allowed.get(record.respondent_id, False))


def _requested_categories(
    metric: MetricSpec,
    records: tuple[AnalyticalRecord, ...],
) -> tuple[str, ...]:
    if metric.parameters.get("category_id"):
        return (str(metric.parameters["category_id"]),)
    return tuple(
        sorted(
            {
                str(record.category_id)
                for record in records
                if record.category_id is not None
            }
        )
    )


def _requested_options(
    metric: MetricSpec,
    records: tuple[AnalyticalRecord, ...],
) -> tuple[str, ...]:
    option = metric.parameters.get("option_id") or metric.parameters.get("category_id")
    if option:
        return (str(option),)
    return tuple(
        sorted(
            {
                str(record.option_id)
                for record in records
                if record.option_id is not None
            }
        )
    )


def _valid_category(record: AnalyticalRecord) -> bool:
    return (
        record.applicable
        and record.category_id is not None
        and not record.ordinary_missing
        and not record.structural_missing
        and not record.invalid
    )


def _require_structure_type(
    ctx: CanonicalExecutionContext,
    allowed: set[str],
) -> None:
    actual = str(ctx.structure_result.structure_type)
    if actual not in allowed:
        raise ExecutionAdapterError(
            f"metric/structure incompatibility: {actual}"
        )


def _require_ledger(
    result: StructureExecutionResult,
    unit: DenominatorUnit,
) -> DenominatorLedger:
    matches = tuple(
        ledger
        for ledger in result.denominator_ledgers
        if DenominatorUnit(str(ledger.denominator_unit)) is unit
    )
    if not matches:
        raise ExecutionAdapterError(f"missing required denominator ledger: {unit.value}")
    if len(matches) > 1 and unit is DenominatorUnit.MENTION:
        raise ExecutionAdapterError("ambiguous mention denominator ledger")
    return matches[0]


def _compatible_mention_ledger(
    ctx: CanonicalExecutionContext,
    metric: MetricSpec,
) -> DenominatorLedger:
    ledger = _require_ledger(ctx.structure_result, DenominatorUnit.MENTION)
    expected = metric.parameters.get("mention_denominator_scope")
    if expected and str(expected) not in ledger.scope_id:
        raise ExecutionAdapterError(
            "mention denominator scope is incompatible with request"
        )
    if not ledger.scope_id.startswith("mention:"):
        raise ExecutionAdapterError("mention ledger scope must start with mention:")
    return ledger


def _mention_keys(
    records: tuple[AnalyticalRecord, ...],
    ledger: DenominatorLedger,
) -> set[tuple[str, ...]]:
    duplicate_policy = str(ledger.traceability.get("duplicate_policy", "error"))
    keys = []
    for record in records:
        parts = [record.respondent_id]
        if record.row_id is not None:
            parts.append(f"row:{record.row_id}")
        if record.entity_id is not None:
            parts.append(f"entity:{record.entity_id}")
        if record.loop_instance_id is not None:
            parts.append(f"loop:{record.loop_instance_id}")
        parts.append(f"option:{record.option_id or record.binding_id}")
        keys.append(tuple(parts))
    return set(keys) if duplicate_policy != "keep" else set((str(i), *key) for i, key in enumerate(keys))


def _ledger(
    *,
    scope_id: str,
    metric_id: str,
    denominator_unit: DenominatorUnit,
    denominator_n: int,
    valid_n: int,
    selected_n: int = 0,
    not_selected_n: int = 0,
) -> DenominatorLedger:
    _require_finite(denominator_n, "denominator_n")
    _require_finite(selected_n, "selected_n")
    return DenominatorLedger(
        scope_id=scope_id,
        metric_id=metric_id,
        denominator_unit=denominator_unit,
        denominator_n=int(denominator_n),
        valid_n=int(valid_n),
        selected_n=int(selected_n),
        not_selected_n=int(not_selected_n),
        ordinary_missing_n=0,
        structural_missing_n=0,
        invalid_n=0,
        zero_base_status="VALID_ZERO_BASE" if denominator_n == 0 else "NONZERO_BASE",
        traceability={
            "runtime_rules_version": EXECUTION_ADAPTER_VERSION,
            "source_authority": "M4",
        },
    )


def metric_universe(metric: MetricSpec) -> UniverseRef:
    _require_text(metric.universe_ref, "metric.universe_ref")
    return UniverseRef(metric.universe_ref)


def _require_universe(
    result: UniverseEvaluationResult | None,
    scope: str,
) -> None:
    if result is None:
        raise ExecutionAdapterError(f"missing M2 universe result for {scope}")
    if result.status is not UniverseEvaluationStatus.PASS:
        raise ExecutionAdapterError(
            f"M2 universe status is not executable for {scope}: {result.status}"
        )


def _upstream_qa_events(ctx: CanonicalExecutionContext) -> tuple[QAEvent, ...]:
    events = []
    if ctx.structure_result.status is StructureExecutionStatus.PASS_WITH_WARNINGS:
        for warning in ctx.structure_result.warnings:
            events.append(
                qa_event(
                    qa_domain=QADomain.STRUCTURE,
                    code="M4_PASS_WITH_WARNINGS",
                    state=QAReleaseStatus.PASS_WITH_WARNINGS,
                    blocking=False,
                    scope_type=QAScopeType.REQUEST,
                    message=warning,
                    related_ids=(ctx.structure_result.structure_id,),
                    source_component="analytics_core.execution_adapter",
                    policy_version=EXECUTION_ADAPTER_VERSION,
                )
            )
    return tuple(events)


def _provenance_refs(
    ctx: CanonicalExecutionContext,
    released_metric: MetricSpec,
    slice_authority: SliceExecutionAuthority,
    ledger: DenominatorLedger,
    source_ledger: DenominatorLedger,
) -> tuple[str, ...]:
    refs = (
        EXECUTION_ADAPTER_VERSION,
        f"request:{ctx.request.request_id}",
        f"request_fp:{ctx.request.request_fingerprint}",
        f"runtime_fp:{ctx.runtime_fingerprint}",
        f"question:{ctx.question_id}",
        f"structure_ref:{ctx.structure_ref}",
        f"metric:{released_metric.metric_id}",
        f"formula:{released_metric.formula_id}",
        f"slice:{slice_authority.slice.slice_id}",
        f"universe_ref:{released_metric.universe_ref}",
        f"m2:{slice_authority.universe_result.universe_ref.universe_id}",
        f"structure:{ctx.structure_result.structure_id}",
        f"m4_source_ledger:{source_ledger.scope_id}",
        f"m4_source_ledger_unit:{_enum_value(source_ledger.denominator_unit)}",
        f"derived_ledger:{ledger.scope_id}",
        f"denominator_unit:{_enum_value(ledger.denominator_unit)}",
        f"denominator_scope:{ledger.scope_id}",
        f"weight_ref:{_weight_ref(ctx)}",
        *(f"qa_ref:{event.qa_id}" for event in ctx.qa_events),
        *ctx.provenance_refs,
    )
    if ctx.weight_result is not None:
        refs = (
            *refs,
            f"m3_resolution:{ctx.weight_result.resolution_source}",
            f"m3_qa:{_enum_value(ctx.weight_result.qa_envelope.aggregate_state)}",
        )
    return tuple(dict.fromkeys(refs))


def _weight_ref(ctx: CanonicalExecutionContext) -> str:
    if ctx.weight_result is not None and ctx.weight_result.active_weight_id:
        return ctx.weight_result.active_weight_id
    return "UNWEIGHTED"


def _validate_value_provenance(
    value: CanonicalValue,
    ctx: CanonicalExecutionContext,
    metric: MetricSpec,
) -> None:
    refs = tuple(value.provenance_refs)
    required_prefixes = (
        "request:",
        "request_fp:",
        "runtime_fp:",
        "question:",
        "structure_ref:",
        "metric:",
        "formula:",
        "slice:",
        "universe_ref:",
        "m2:",
        "m4_source_ledger:",
        "denominator_unit:",
        "denominator_scope:",
        "weight_ref:",
    )
    for prefix in required_prefixes:
        if not any(ref.startswith(prefix) for ref in refs):
            raise ExecutionAdapterError(
                f"incomplete provenance: missing {prefix.removesuffix(':')}"
            )
    if metric.weight_behavior != "unweighted" and not any(
        ref.startswith("m3_qa:") for ref in refs
    ):
        raise ExecutionAdapterError("incomplete provenance: missing M3 QA reference")
    for event in ctx.qa_events:
        if f"qa_ref:{event.qa_id}" not in refs:
            raise ExecutionAdapterError(
                f"incomplete provenance: missing QA ref {event.qa_id}"
            )


def _unique_qa_events(events: list[QAEvent]) -> tuple[QAEvent, ...]:
    unique = {}
    for event in events:
        unique[event.qa_id] = event
    return tuple(unique.values())


def _require_text(value: object, name: str) -> None:
    if not str(value or "").strip():
        raise ExecutionAdapterError(f"{name} is required")


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _require_finite(value: object, name: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ExecutionAdapterError(f"non-finite analytical input: {name}")
