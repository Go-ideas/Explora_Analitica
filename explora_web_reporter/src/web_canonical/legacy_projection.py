from __future__ import annotations

from typing import Any

from src.contracts.models import CanonicalBase, CanonicalResult, CanonicalSlice, CanonicalValue
from src.contracts.vocabulary import DenominatorUnit, ValueUnit
from src.web_canonical.comparison import ComparisonRecord, canonical_semantic_key


def legacy_comparison_records_from_report(
    legacy_result: Any,
    canonical_result: CanonicalResult,
    *,
    request_identity: str = "",
) -> tuple[dict[tuple[tuple[str, str], ...], ComparisonRecord], tuple[str, ...]]:
    if not all(hasattr(legacy_result, attr) for attr in ("question_id", "summary")):
        return {}, ("Legacy result lacks actual ReportResult comparison source.",)
    summary = getattr(legacy_result, "summary")
    if summary is None or getattr(summary, "empty", True):
        return {}, ("Legacy ReportResult summary is empty.",)

    bases = {base.base_id: base for base in canonical_result.bases}
    slices = {slice_item.slice_id: slice_item for slice_item in canonical_result.slices}
    records: dict[tuple[tuple[str, str], ...], ComparisonRecord] = {}
    limitations: list[str] = []
    for value in canonical_result.values:
        base = bases.get(value.base_id)
        slice_item = slices.get(value.slice_id)
        if base is None or slice_item is None:
            limitations.append(
                f"Canonical value {value.value_id} lacks base/slice for comparison."
            )
            continue
        extracted = _extract_legacy_value(
            legacy_result,
            value,
            base,
            slice_item,
        )
        if extracted.reason:
            limitations.append(extracted.reason)
            continue
        key = canonical_semantic_key(value, base, slice_item)
        records[key] = ComparisonRecord(
            source="LEGACY",
            semantic_key=key,
            value=extracted.value,
            request_identity=request_identity,
            source_ref=extracted.source_ref,
            provenance={
                "legacy_question_id": str(getattr(legacy_result, "question_id", "")),
                "legacy_calculations": tuple(
                    str(item) for item in getattr(legacy_result, "calculations", ())
                ),
                "legacy_banner": getattr(legacy_result, "banner", None),
                "legacy_banners": tuple(
                    str(item) for item in getattr(legacy_result, "banners", ())
                ),
                "legacy_banner_mode": getattr(legacy_result, "banner_mode", ""),
                "legacy_filters": dict(getattr(legacy_result, "filters", {}) or {}),
                "legacy_filter_summary": getattr(legacy_result, "filter_summary", ""),
                "legacy_base": getattr(legacy_result, "base", None),
                "summary_row_index": extracted.row_index,
                "summary_column": extracted.column,
            },
        )
    if not records and not limitations:
        limitations.append("No deterministic Legacy comparison records were projected.")
    return records, tuple(limitations)


class _Extraction:
    def __init__(
        self,
        value: Any = None,
        *,
        source_ref: str = "",
        row_index: str = "",
        column: str = "",
        reason: str = "",
    ) -> None:
        self.value = value
        self.source_ref = source_ref
        self.row_index = row_index
        self.column = column
        self.reason = reason


def _extract_legacy_value(
    legacy_result: Any,
    value: CanonicalValue,
    base: CanonicalBase,
    slice_item: CanonicalSlice,
) -> _Extraction:
    summary = getattr(legacy_result, "summary")
    work = summary.copy()
    if "banner" in work.columns:
        banner_key = _legacy_banner_key(slice_item)
        banner_mask = work["banner"].map(_stable_text).eq(banner_key)
        if not banner_mask.any() and not slice_item.is_total:
            alternate = _legacy_separate_banner_key(slice_item)
            banner_mask = work["banner"].map(_stable_text).eq(alternate)
        work = work[banner_mask].copy()
        if work.empty:
            return _Extraction(
                reason=f"Legacy summary lacks stable banner slice {banner_key}."
            )
    row_identity = _value_row_identity(value)
    if row_identity:
        matched = _filter_by_row_identity(work, row_identity)
        if matched is None:
            return _Extraction(
                reason=(
                    "Legacy summary lacks stable row/category identity "
                    f"{row_identity} for value {value.value_id}."
                )
            )
        work = matched
    metric_column = _metric_column(work, value, base)
    if metric_column is None:
        return _Extraction(
            reason=(
                "Legacy summary lacks comparable metric column for "
                f"value {value.value_id}."
            )
        )
    if len(work) != 1:
        return _Extraction(
            reason=(
                "Legacy summary comparison grain is ambiguous for "
                f"value {value.value_id}."
            )
        )
    row = work.iloc[0]
    return _Extraction(
        row[metric_column],
        source_ref=f"ReportResult.summary[{row.name}].{metric_column}",
        row_index=str(row.name),
        column=str(metric_column),
    )


def _legacy_banner_key(slice_item: CanonicalSlice) -> str:
    if slice_item.is_total:
        return "Total"
    return _stable_text(slice_item.member_id)


def _legacy_separate_banner_key(slice_item: CanonicalSlice) -> str:
    return f"{_stable_text(slice_item.banner_dimension_id)}: {_stable_text(slice_item.member_id)}"


def _value_row_identity(value: CanonicalValue) -> str:
    for candidate in (
        value.option_id,
        value.category_id,
        value.row_id,
        value.entity_id,
        value.column_id,
        value.loop_instance_id,
    ):
        text = _stable_text(candidate)
        if text:
            return text
    return ""


def _filter_by_row_identity(work: Any, row_identity: str) -> Any | None:
    for column in (
        "codigo_respuesta",
        "codigo",
        "option_id",
        "category_id",
        "row_id",
        "entity_id",
        "column_id",
        "loop_instance_id",
        "respuesta",
    ):
        if column in work.columns:
            matched = work[work[column].map(_stable_text).eq(row_identity)].copy()
            if not matched.empty:
                return matched
    return None


def _metric_column(
    work: Any,
    value: CanonicalValue,
    base: CanonicalBase,
) -> str | None:
    direct = (value.metric_id, value.formula_id)
    for column in direct:
        if column and column in work.columns:
            return str(column)
    weighted = bool(base.active_weight_ref)
    denominator_unit = str(getattr(base.denominator_unit, "value", base.denominator_unit))
    value_unit = str(getattr(value.unit, "value", value.unit))
    structure_id = str(value.structure_id)
    candidates: tuple[str, ...]
    if value_unit == ValueUnit.COUNT.value:
        candidates = (
            ("menciones", "n")
            if denominator_unit == DenominatorUnit.MENTION.value
            else ("respondentes", "n")
        )
    elif value_unit == ValueUnit.PROPORTION.value:
        if weighted and denominator_unit == DenominatorUnit.MENTION.value:
            candidates = ("pct_menciones_ponderado", "porcentaje_ponderado")
        elif weighted:
            candidates = ("pct_respondentes_ponderado", "porcentaje_ponderado")
        elif denominator_unit == DenominatorUnit.MENTION.value:
            candidates = ("pct_menciones", "porcentaje")
        elif structure_id in {"RM", "GRID_RM", "LOOP_RM"}:
            candidates = ("pct_respondentes", "porcentaje")
        else:
            candidates = ("porcentaje", "pct_respondentes")
    elif value_unit == ValueUnit.MEAN.value:
        candidates = ("media_ponderada", "media") if weighted else ("media",)
    elif value_unit == ValueUnit.STANDARD_DEVIATION.value:
        candidates = ("desviacion_estandar",)
    elif value_unit == ValueUnit.SCORE.value:
        candidates = ("nps",)
    else:
        candidates = ()
    for column in candidates:
        if column in work.columns:
            return column
    return None


def _stable_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except TypeError:
        pass
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value).strip()
