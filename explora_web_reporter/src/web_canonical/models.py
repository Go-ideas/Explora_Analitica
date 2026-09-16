from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CanonicalWebQAItem:
    qa_id: str
    domain: str
    code: str
    state: str
    blocking: bool
    scope_type: str
    message: str
    related_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CanonicalWebCell:
    result_run_id: str
    value_id: str
    base_id: str
    question_id: str
    structure_id: str
    slice_id: str
    metric_id: str
    formula_id: str
    formula_version: str
    value_status: str
    value_unit: str
    estimate: float | int | None
    display_value: str
    denominator_unit: str
    denominator_ref: str
    denominator_scope_id: str
    unweighted_n: int
    weighted_n_raw: float | None = None
    weighted_n: float | None = None
    effective_n: float | None = None
    active_weight_ref: str | None = None
    slice_label: str | None = None
    banner_dimension_id: str | None = None
    member_id: str | None = None
    row_id: str | None = None
    entity_id: str | None = None
    column_id: str | None = None
    option_id: str | None = None
    category_id: str | None = None
    loop_instance_id: str | None = None
    significance_tokens: tuple[str, ...] = field(default_factory=tuple)
    qa_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CanonicalWebProjection:
    authority: str
    adapter_version: str
    result_schema_version: str
    result_run_id: str
    result_fingerprint: str
    request_fingerprint: str | None
    project_id: str
    table: pd.DataFrame
    bases: pd.DataFrame
    significance: pd.DataFrame
    significance_legend: pd.DataFrame
    qa: tuple[CanonicalWebQAItem, ...]
    release: dict[str, Any]
    cells: tuple[CanonicalWebCell, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    cache_key: str = ""
    presentation_identity: str = "default"
