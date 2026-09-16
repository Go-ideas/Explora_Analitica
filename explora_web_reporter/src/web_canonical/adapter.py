from __future__ import annotations

from typing import Callable

import pandas as pd

from src.contracts.models import (
    CanonicalBase,
    CanonicalResult,
    CanonicalValue,
    QAEvent,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_canonical_result,
)
from src.contracts.vocabulary import (
    ExecutionMode,
    ValueStatus,
    ValueUnit,
)
from src.web_canonical.cache import canonical_cache_key
from src.web_canonical.models import (
    CanonicalWebCell,
    CanonicalWebProjection,
    CanonicalWebQAItem,
)
from src.web_canonical.significance import significance_presentation


CANONICAL_WEB_ADAPTER_VERSION = "M6_CANONICAL_WEB_ADAPTER_V1"
SUPPORTED_SCHEMA_VERSIONS = {"M5_CANONICAL_RESULT_V1"}


class CanonicalWebAdapterError(ValueError):
    pass


LabelResolver = Callable[[CanonicalValue, CanonicalBase], str | None]


def project_canonical_result(
    result: CanonicalResult,
    *,
    selected_slice_ids: tuple[str, ...] = (),
    presentation_identity: str = "default",
    label_resolver: LabelResolver | None = None,
) -> CanonicalWebProjection:
    _validate_result_for_web(result)
    slice_by_id = {item.slice_id: item for item in result.slices}
    base_by_id = {item.base_id: item for item in result.bases}
    missing_slices = set(selected_slice_ids) - set(slice_by_id)
    if missing_slices:
        raise CanonicalWebAdapterError(
            "selected slice_id is not present in CanonicalResult: "
            + ", ".join(sorted(missing_slices))
        )
    selected = set(selected_slice_ids)
    values = tuple(
        item
        for item in result.values
        if not selected or item.slice_id in selected
    )
    missing_bases = sorted(
        {item.base_id for item in values if item.base_id not in base_by_id}
    )
    if missing_bases:
        raise CanonicalWebAdapterError(
            "CanonicalValue references missing base_id: "
            + ", ".join(missing_bases)
        )
    significance = significance_presentation(
        result.comparisons, result.slices
    )
    cells = tuple(
        _cell_from_value(
            result,
            value,
            base_by_id[value.base_id],
            slice_by_id.get(value.slice_id),
            significance.tokens_for_value(value),
            label_resolver=label_resolver,
        )
        for value in values
    )
    table = _table_from_cells(cells)
    bases = _bases_table(result.bases, slice_by_id)
    warnings = tuple(
        item.message
        for item in result.qa_events
        if str(getattr(item.state, "value", item.state))
        in {"WARN", "PASS_WITH_WARNINGS", "REVIEW_REQUIRED", "FAIL"}
    )
    cache_key = canonical_cache_key(
        result,
        execution_mode=ExecutionMode.CANONICAL_V1,
        presentation_identity=presentation_identity,
        slice_ids=selected_slice_ids,
    )
    return CanonicalWebProjection(
        authority=ExecutionMode.CANONICAL_V1.value,
        adapter_version=CANONICAL_WEB_ADAPTER_VERSION,
        result_schema_version=result.result_schema_version,
        result_run_id=result.result_run_id,
        result_fingerprint=result.result_fingerprint or "",
        request_fingerprint=(
            result.request.request_fingerprint
            if result.request is not None
            else None
        ),
        project_id=result.project_id,
        table=table,
        bases=bases,
        significance=significance.table,
        significance_legend=significance.legend,
        qa=tuple(_qa_item(event) for event in result.qa_events),
        release=_release_payload(result),
        cells=cells,
        warnings=warnings,
        cache_key=cache_key,
        presentation_identity=presentation_identity,
    )


def _validate_result_for_web(result: CanonicalResult) -> None:
    if result.result_schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise CanonicalWebAdapterError(
            "unsupported CanonicalResult schema version: "
            f"{result.result_schema_version}"
        )
    try:
        validate_canonical_result(result)
    except ContractValidationError as exc:
        raise CanonicalWebAdapterError(str(exc)) from exc
    if (
        result.manifest is not None
        and result.result_fingerprint is not None
        and result.manifest.result_fingerprint != result.result_fingerprint
    ):
        raise CanonicalWebAdapterError(
            "manifest result_fingerprint does not match CanonicalResult"
        )


def _cell_from_value(
    result: CanonicalResult,
    value: CanonicalValue,
    base: CanonicalBase,
    slice_item,
    significance_tokens: tuple[str, ...],
    *,
    label_resolver: LabelResolver | None,
) -> CanonicalWebCell:
    label = label_resolver(value, base) if label_resolver else None
    status = _enum_value(value.value_status)
    unit = _enum_value(value.unit)
    return CanonicalWebCell(
        result_run_id=result.result_run_id,
        value_id=value.value_id,
        base_id=value.base_id,
        question_id=value.question_id,
        structure_id=value.structure_id,
        slice_id=value.slice_id,
        metric_id=value.metric_id,
        formula_id=value.formula_id,
        formula_version=value.formula_version,
        value_status=status,
        value_unit=unit,
        estimate=value.estimate,
        display_value=_display_value(value),
        denominator_unit=_enum_value(base.denominator_unit),
        denominator_ref=base.denominator_ref,
        denominator_scope_id=base.denominator_scope_id,
        unweighted_n=base.unweighted_n,
        weighted_n_raw=base.weighted_n_raw,
        weighted_n=base.weighted_n,
        effective_n=base.effective_n,
        active_weight_ref=base.active_weight_ref,
        slice_label=(
            slice_item.label
            or slice_item.member_id
            or slice_item.slice_id
            if slice_item is not None
            else value.slice_id
        ),
        banner_dimension_id=(
            slice_item.banner_dimension_id if slice_item is not None else None
        ),
        member_id=slice_item.member_id if slice_item is not None else None,
        row_id=value.row_id,
        entity_id=value.entity_id,
        column_id=value.column_id,
        option_id=value.option_id,
        category_id=value.category_id,
        loop_instance_id=value.loop_instance_id,
        significance_tokens=tuple(significance_tokens),
        qa_refs=value.qa_refs,
        provenance_refs=value.provenance_refs,
    )


def _table_from_cells(cells: tuple[CanonicalWebCell, ...]) -> pd.DataFrame:
    rows = []
    for cell in sorted(
        cells,
        key=lambda item: (
            item.question_id,
            item.structure_id,
            item.row_id or "",
            item.entity_id or "",
            item.loop_instance_id or "",
            item.option_id or item.category_id or item.column_id or "",
            item.metric_id,
            item.slice_label or item.slice_id,
        ),
    ):
        rows.append(
            {
                "Pregunta": cell.question_id,
                "Estructura": cell.structure_id,
                "Slice": cell.slice_label or cell.slice_id,
                "Fila/Entidad": cell.row_id or cell.entity_id or "",
                "Columna/Opcion": (
                    cell.column_id or cell.option_id or cell.category_id or ""
                ),
                "Loop": cell.loop_instance_id or "",
                "Metrica": cell.metric_id,
                "Estado": cell.value_status,
                "Valor": cell.display_value,
                "Base": cell.unweighted_n,
                "Base ponderada": cell.weighted_n,
                "N efectivo": cell.effective_n,
                "Significancia": " ".join(cell.significance_tokens),
                "value_id": cell.value_id,
                "base_id": cell.base_id,
                "result_run_id": cell.result_run_id,
            }
        )
    return pd.DataFrame(rows)


def _bases_table(
    bases: tuple[CanonicalBase, ...],
    slice_by_id: dict[str, object],
) -> pd.DataFrame:
    rows = []
    for base in bases:
        slice_item = slice_by_id.get(base.slice_id)
        rows.append(
            {
                "base_id": base.base_id,
                "Pregunta": base.question_id,
                "Estructura": base.structure_id,
                "Slice": (
                    getattr(slice_item, "label", None)
                    or getattr(slice_item, "member_id", None)
                    or base.slice_id
                ),
                "denominator_unit": _enum_value(base.denominator_unit),
                "denominator_ref": base.denominator_ref,
                "denominator_scope_id": base.denominator_scope_id,
                "unweighted_n": base.unweighted_n,
                "weighted_n_raw": base.weighted_n_raw,
                "weighted_n": base.weighted_n,
                "effective_n": base.effective_n,
                "active_weight_ref": base.active_weight_ref,
                "base_status": base.base_status,
            }
        )
    return pd.DataFrame(rows)


def _display_value(value: CanonicalValue) -> str:
    status = ValueStatus(_enum_value(value.value_status))
    if status is not ValueStatus.OK:
        return status.value
    if value.estimate is None:
        return ""
    unit = _enum_value(value.unit)
    if unit == ValueUnit.PROPORTION.value:
        return f"{float(value.estimate) * 100:.1f}%"
    if unit == ValueUnit.COUNT.value:
        return f"{float(value.estimate):,.0f}"
    if unit in {
        ValueUnit.MEAN.value,
        ValueUnit.STANDARD_DEVIATION.value,
        ValueUnit.SCORE.value,
    }:
        return f"{float(value.estimate):.2f}"
    return str(value.estimate)


def _qa_item(event: QAEvent) -> CanonicalWebQAItem:
    return CanonicalWebQAItem(
        qa_id=event.qa_id,
        domain=_enum_value(event.qa_domain),
        code=event.code,
        state=_enum_value(event.state),
        blocking=event.blocking,
        scope_type=_enum_value(event.scope_type),
        message=event.message,
        related_ids=event.related_ids,
    )


def _release_payload(result: CanonicalResult) -> dict[str, object]:
    release = result.release
    if release is None:
        return {
            "computation_status": "UNKNOWN",
            "qa_release_status": "UNKNOWN",
            "releasable": False,
            "reasons": ("missing release state",),
        }
    return {
        "computation_status": _enum_value(release.computation_status),
        "qa_release_status": _enum_value(release.qa_release_status),
        "releasable": release.releasable,
        "policy_ref": release.policy_ref,
        "reasons": release.reasons,
    }


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))
