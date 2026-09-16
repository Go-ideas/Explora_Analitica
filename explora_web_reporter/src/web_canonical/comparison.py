from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.contracts.models import CanonicalBase, CanonicalResult, CanonicalSlice, CanonicalValue
from src.contracts.vocabulary import LegacyCanonicalComparisonStatus


SEMANTIC_KEY_FIELDS = (
    "question_id",
    "metric_id",
    "formula_id",
    "formula_version",
    "slice_identity",
    "banner_identity",
    "filter_identity",
    "row_id",
    "entity_id",
    "column_id",
    "option_id",
    "category_id",
    "loop_instance_id",
    "denominator_unit",
    "denominator_scope_id",
    "weight_identity",
    "structure_type",
    "value_unit",
    "value_status",
)


@dataclass(frozen=True)
class ComparisonRecord:
    source: str
    semantic_key: tuple[tuple[str, str], ...]
    value: Any
    request_identity: str = ""
    source_ref: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DualRunComparisonItem:
    semantic_key: tuple[tuple[str, str], ...]
    classification: LegacyCanonicalComparisonStatus
    canonical_value: Any = None
    legacy_value: Any = None
    reason: str = ""
    blocking: bool = False


@dataclass(frozen=True)
class DualRunComparisonResult:
    items: tuple[DualRunComparisonItem, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def blocks_migration(self) -> bool:
        return any(item.blocking for item in self.items)


def canonical_semantic_key(
    value: CanonicalValue,
    base: CanonicalBase,
    slice_item: CanonicalSlice | None = None,
) -> tuple[tuple[str, str], ...]:
    slice_identity = value.slice_id
    banner_identity = ""
    filter_identity = ""
    if slice_item is not None:
        slice_identity = _slice_semantic_identity(slice_item)
        banner_identity = _slice_banner_identity(slice_item)
        filter_identity = _normalize(slice_item.filter_refs)
    payload = {
        "question_id": value.question_id,
        "metric_id": value.metric_id,
        "formula_id": value.formula_id,
        "formula_version": value.formula_version,
        "slice_identity": slice_identity,
        "banner_identity": banner_identity,
        "filter_identity": filter_identity,
        "row_id": value.row_id,
        "entity_id": value.entity_id,
        "column_id": value.column_id,
        "option_id": value.option_id,
        "category_id": value.category_id,
        "loop_instance_id": value.loop_instance_id,
        "denominator_unit": _enum_value(base.denominator_unit),
        "denominator_scope_id": base.denominator_scope_id,
        "weight_identity": base.active_weight_ref,
        "structure_type": value.structure_id,
        "value_unit": _enum_value(value.unit),
        "value_status": _enum_value(value.value_status),
    }
    return _semantic_key(payload)


def canonical_comparison_records_from_result(
    result: CanonicalResult,
    *,
    request_identity: str = "",
) -> dict[tuple[tuple[str, str], ...], ComparisonRecord]:
    bases = {base.base_id: base for base in result.bases}
    slices = {slice_item.slice_id: slice_item for slice_item in result.slices}
    records = {}
    for value in result.values:
        base = bases.get(value.base_id)
        slice_item = slices.get(value.slice_id)
        if base is None or slice_item is None:
            continue
        key = canonical_semantic_key(value, base, slice_item)
        records[key] = ComparisonRecord(
            source="CANONICAL",
            semantic_key=key,
            value=value.estimate,
            request_identity=request_identity,
            source_ref="|".join(
                item
                for item in (result.result_run_id, value.value_id, value.base_id)
                if item
            ),
            provenance={
                "value_id": value.value_id,
                "base_id": value.base_id,
                "slice_id": value.slice_id,
                "slice_fingerprint": slice_item.slice_fingerprint,
                "result_run_id": result.result_run_id,
                "result_fingerprint": result.result_fingerprint,
                "request_fingerprint": (
                    result.request.request_fingerprint
                    if result.request is not None
                    else None
                ),
            },
        )
    return records


def canonical_comparison_records(
    values: tuple[CanonicalValue, ...],
    bases: Mapping[str, CanonicalBase],
    *,
    request_identity: str = "",
    result_run_id: str = "",
) -> dict[tuple[tuple[str, str], ...], ComparisonRecord]:
    records = {}
    for value in values:
        base = bases.get(value.base_id)
        if base is None:
            continue
        key = canonical_semantic_key(value, base)
        records[key] = ComparisonRecord(
            source="CANONICAL",
            semantic_key=key,
            value=value.estimate,
            request_identity=request_identity,
            source_ref="|".join(
                item for item in (result_run_id, value.value_id, value.base_id) if item
            ),
            provenance={
                "value_id": value.value_id,
                "base_id": value.base_id,
                "result_run_id": result_run_id,
            },
        )
    return records


def legacy_comparison_records(
    legacy_result: Any,
    *,
    request_identity: str = "",
) -> tuple[dict[tuple[tuple[str, str], ...], ComparisonRecord], tuple[str, ...]]:
    explicit = getattr(legacy_result, "m6_comparison_records", None)
    if explicit is not None:
        return _explicit_legacy_records(
            explicit,
            request_identity=request_identity,
        ), ()
    if isinstance(legacy_result, Mapping) and "m6_comparison_records" in legacy_result:
        return _explicit_legacy_records(
            legacy_result["m6_comparison_records"],
            request_identity=request_identity,
        ), ()
    if all(hasattr(legacy_result, attr) for attr in ("question_id", "summary")):
        return {}, (
            "Legacy ReportResult lacks stable M6 semantic comparison projection.",
        )
    return {}, (
        "Legacy result lacks deterministic semantic comparison records.",
    )


def legacy_semantic_key(
    record: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    missing = [
        field
        for field in SEMANTIC_KEY_FIELDS
        if field not in record and field not in {"banner_identity", "filter_identity"}
    ]
    if missing:
        raise ValueError(
            "Legacy record lacks stable semantic identity fields: "
            + ", ".join(missing)
        )
    return _semantic_key(record)


def compare_dual_run_records(
    canonical_records: Mapping[tuple[tuple[str, str], ...], Any],
    legacy_records: Mapping[tuple[tuple[str, str], ...], Any],
    *,
    classifications: Mapping[
        tuple[tuple[str, str], ...], LegacyCanonicalComparisonStatus | str
    ]
    | None = None,
) -> DualRunComparisonResult:
    overrides = classifications or {}
    items = []
    for key in sorted(set(canonical_records) | set(legacy_records)):
        canonical_record = canonical_records.get(key)
        legacy_record = legacy_records.get(key)
        canonical_value = _record_value(canonical_record)
        legacy_value = _record_value(legacy_record)
        values_equal = bool(canonical_value == legacy_value)
        if values_equal:
            classification = LegacyCanonicalComparisonStatus.PARITY
            reason = "values are equivalent before presentation rounding"
        else:
            raw_classification = overrides.get(
                key,
                LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION,
            )
            classification = LegacyCanonicalComparisonStatus(
                str(getattr(raw_classification, "value", raw_classification))
            )
            if classification is LegacyCanonicalComparisonStatus.PARITY:
                classification = (
                    LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
                )
                reason = "PARITY classification rejected for actual delta"
            else:
                reason = (
                    "classified delta"
                    if key in overrides
                    else "unexplained delta"
                )
        items.append(
            DualRunComparisonItem(
                semantic_key=key,
                classification=classification,
                canonical_value=canonical_record,
                legacy_value=legacy_record,
                reason=reason,
                blocking=(
                    not values_equal
                    and classification
                    is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
                ),
            )
        )
    return DualRunComparisonResult(items=tuple(items))


def _explicit_legacy_records(
    records: Any,
    *,
    request_identity: str,
) -> dict[tuple[tuple[str, str], ...], ComparisonRecord]:
    result = {}
    if isinstance(records, Mapping):
        iterable = records.items()
    else:
        iterable = []
        for record in records:
            if isinstance(record, ComparisonRecord):
                result[record.semantic_key] = record
            elif isinstance(record, Mapping):
                key = legacy_semantic_key(record)
                result[key] = ComparisonRecord(
                    source="LEGACY",
                    semantic_key=key,
                    value=record.get("value"),
                    request_identity=request_identity,
                    source_ref=str(record.get("source_ref") or ""),
                    provenance=dict(record.get("provenance") or {}),
                )
        return result
    for key, value in iterable:
        semantic_key = tuple(key)
        record_value = _record_value(value)
        if isinstance(value, ComparisonRecord):
            result[semantic_key] = value
        else:
            result[semantic_key] = ComparisonRecord(
                source="LEGACY",
                semantic_key=semantic_key,
                value=record_value,
                request_identity=request_identity,
                source_ref="legacy_result",
            )
    return result


def _record_value(record: Any) -> Any:
    if isinstance(record, ComparisonRecord):
        return record.value
    return record


def _semantic_key(
    values: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (field, _normalize(values.get(field)))
        for field in SEMANTIC_KEY_FIELDS
    )


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (tuple, list, set)):
        return "|".join(sorted(str(item) for item in value))
    return str(getattr(value, "value", value))


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _slice_semantic_identity(slice_item: CanonicalSlice) -> str:
    if slice_item.is_total:
        return "total"
    parts = [
        "banner",
        str(slice_item.banner_dimension_id or ""),
        str(slice_item.member_id or ""),
    ]
    filters = _normalize(slice_item.filter_refs)
    if filters:
        parts.extend(["filters", filters])
    return ":".join(parts)


def _slice_banner_identity(slice_item: CanonicalSlice) -> str:
    if slice_item.is_total:
        return ""
    return ":".join(
        (
            str(slice_item.banner_dimension_id or ""),
            str(slice_item.member_id or ""),
        )
    )
