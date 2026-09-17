from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CANONICAL_RUNTIME_SCHEMA_VERSION = "canonical-runtime/1"
CANONICAL_REQUEST_SCHEMA_VERSION = "canonical-request/1"
SOURCE_ROW_ORDINAL_V1 = "SOURCE_ROW_ORDINAL_V1"
RELEASED_SOURCE_ID = "RELEASED_SOURCE_ID"


class MaterializationError(ValueError):
    pass


@dataclass(frozen=True)
class MaterializationQAEvent:
    code: str
    state: str
    message: str
    blocking: bool = False
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeManifest:
    project_id: str
    runtime_schema: str
    package_id: str
    package_version: str
    package_spec_hash: str
    source_fingerprint: str
    package_fingerprint: str
    source_n: int
    runtime_n: int
    respondent_identity_mode: str
    materialization_state: str
    default_execution_mode: str
    dual_run_executed: bool
    canonical_result_generated: bool


@dataclass(frozen=True)
class BoundVariable:
    variable_ref: str
    source_name: str
    values_by_respondent: dict[str, Any]
    missing_count: int
    observed_values: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReleasedPackage:
    package_id: str
    package_version: str
    spec_hash: str
    default_execution_mode: str
    dual_run_executed: bool
    canonical_result_generated: bool
    manifest: dict[str, Any]
    project: dict[str, Any]
    questions: tuple[dict[str, Any], ...]
    structures: tuple[dict[str, Any], ...]
    universes: tuple[dict[str, Any], ...]
    weights: dict[str, Any]
    metrics: tuple[dict[str, Any], ...]
    significance: tuple[dict[str, Any], ...]
    banner_filters: dict[str, Any]
    requests: dict[str, Any]


@dataclass(frozen=True)
class CanonicalRuntimeInput:
    schema_version: str
    project_id: str
    source_fingerprint: str
    package_fingerprint: str
    source_n: int
    runtime_n: int
    respondent_identity_mode: str
    respondent_ids: tuple[str, ...]
    variables: tuple[BoundVariable, ...]
    package: ReleasedPackage
    manifest: RuntimeManifest
    qa_events: tuple[MaterializationQAEvent, ...]
    fingerprint: str

    @property
    def values_by_variable(self) -> dict[str, dict[str, Any]]:
        return {variable.variable_ref: variable.values_by_respondent for variable in self.variables}

    @property
    def blocking_failures(self) -> tuple[MaterializationQAEvent, ...]:
        return tuple(event for event in self.qa_events if event.blocking)


@dataclass(frozen=True)
class CanonicalRequestSnapshot:
    schema_version: str
    project_id: str
    request_id: str
    question_id: str
    structure_ref: str
    universe_ref: str
    weight_ref: str | None
    metric_refs: tuple[str, ...]
    formula_refs: tuple[str, ...]
    filters: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    banner: dict[str, Any] | None = None
    significance_ref: str | None = None
    runtime_schema_version: str = CANONICAL_RUNTIME_SCHEMA_VERSION
    runtime_fingerprint: str = ""
    package_fingerprint: str = ""
    spec_refs: dict[str, str] = field(default_factory=dict)
    request_fingerprint: str = ""


@dataclass(frozen=True)
class CanonicalExecutionEvidence:
    runtime: CanonicalRuntimeInput
    requests: dict[str, CanonicalRequestSnapshot]
    results: dict[str, Any]
    qa_events: tuple[MaterializationQAEvent, ...]
