from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import tempfile
from typing import Any, Iterable
import zipfile

import pandas as pd

from src.canonical_materialization.fingerprints import file_sha256, runtime_fingerprint
from src.canonical_materialization.models import (
    CANONICAL_RUNTIME_SCHEMA_VERSION,
    RELEASED_SOURCE_ID,
    SOURCE_ROW_ORDINAL_V1,
    BoundVariable,
    CanonicalRuntimeInput,
    MaterializationError,
    MaterializationQAEvent,
    ReleasedPackage,
    RuntimeManifest,
)
from src.readers.spss_reader import read_spss


PACKAGE_FILES = {
    "01_PROJECT_SPEC_RELEASED.json": "project",
    "02_QUESTION_SPECS_RELEASED.json": "questions",
    "03_STRUCTURE_SPECS_RELEASED.json": "structures",
    "04_UNIVERSE_SPECS_RELEASED.json": "universes",
    "05_WEIGHT_REGISTRY_RELEASED.json": "weights",
    "06_METRIC_SPECS_RELEASED.json": "metrics",
    "07_SIGNIFICANCE_SPECS_RELEASED.json": "significance",
    "08_BANNER_FILTER_SPECS_RELEASED.json": "banner_filters",
    "09_REQUEST_MATRIX_RELEASED.json": "requests",
    "MANIFEST.json": "manifest",
}


def materialize_project(
    *,
    source_path: str | Path,
    package_path: str | Path,
    expected_source_sha256: str | None = None,
    expected_package_sha256: str | None = None,
    expected_runtime_fingerprint: str | None = None,
) -> CanonicalRuntimeInput:
    source_sha = file_sha256(source_path)
    package_sha = file_sha256(package_path)
    if expected_source_sha256 and source_sha != expected_source_sha256.upper():
        raise MaterializationError("source SHA mismatch")
    if expected_package_sha256 and package_sha != expected_package_sha256.upper():
        raise MaterializationError("RELEASED package SHA mismatch")
    package = load_released_package(package_path)
    _validate_package_manifest(package)
    project = package.project
    expected_dataset = project.get("dataset", {}).get("dataset_fingerprint_sha256") or package.manifest.get("dataset_fingerprint_sha256")
    if expected_dataset and expected_dataset != source_sha:
        raise MaterializationError("source dataset fingerprint mismatch")
    df, _meta, _summary = read_spss(Path(source_path))
    respondent_ids, identity_mode = _respondent_ids(df, project)
    variables = _bind_variables(df, respondent_ids, package)
    qa_events = tuple(_qa_events(df, respondent_ids, variables, package))
    failures = tuple(event for event in qa_events if event.blocking)
    manifest = RuntimeManifest(
        project_id=str(project["project_id"]),
        runtime_schema=CANONICAL_RUNTIME_SCHEMA_VERSION,
        package_id=package.package_id,
        package_version=package.package_version,
        package_spec_hash=package.spec_hash,
        source_fingerprint=source_sha,
        package_fingerprint=package_sha,
        source_n=len(df),
        runtime_n=len(respondent_ids),
        respondent_identity_mode=identity_mode,
        materialization_state="FAIL" if failures else "PASS",
        default_execution_mode=package.default_execution_mode,
        dual_run_executed=package.dual_run_executed,
        canonical_result_generated=package.canonical_result_generated,
    )
    draft = CanonicalRuntimeInput(
        schema_version=CANONICAL_RUNTIME_SCHEMA_VERSION,
        project_id=str(project["project_id"]),
        source_fingerprint=source_sha,
        package_fingerprint=package_sha,
        source_n=len(df),
        runtime_n=len(respondent_ids),
        respondent_identity_mode=identity_mode,
        respondent_ids=respondent_ids,
        variables=variables,
        package=package,
        manifest=manifest,
        qa_events=qa_events,
        fingerprint="",
    )
    runtime = replace(draft, fingerprint=runtime_fingerprint(draft))
    if expected_runtime_fingerprint and runtime.fingerprint != expected_runtime_fingerprint:
        raise MaterializationError("Canonical Runtime Input fingerprint mismatch")
    if failures:
        raise MaterializationError("; ".join(event.message for event in failures))
    return runtime


def load_released_package(path: str | Path) -> ReleasedPackage:
    import json

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        payload: dict[str, Any] = {}
        for filename, key in PACKAGE_FILES.items():
            file_path = root / filename
            if not file_path.exists():
                raise MaterializationError(f"required package file missing: {filename}")
            payload[key] = json.loads(file_path.read_text(encoding="utf-8"))
    manifest = payload["manifest"]
    return ReleasedPackage(
        package_id=str(manifest["package_id"]),
        package_version=str(manifest["package_version"]),
        spec_hash=str(manifest["spec_hash"]),
        default_execution_mode=str(manifest.get("default_execution_mode", "")),
        dual_run_executed=bool(manifest.get("dual_run_executed", False)),
        canonical_result_generated=bool(manifest.get("canonical_result_generated", False)),
        manifest=manifest,
        project=payload["project"],
        questions=tuple(payload["questions"]),
        structures=tuple(payload["structures"]),
        universes=tuple(payload["universes"]),
        weights=payload["weights"],
        metrics=tuple(payload["metrics"]),
        significance=tuple(payload["significance"]),
        banner_filters=payload["banner_filters"],
        requests=payload["requests"],
    )


def _validate_package_manifest(package: ReleasedPackage) -> None:
    if package.manifest.get("status") != "RELEASED":
        raise MaterializationError("package manifest is not RELEASED")
    if package.default_execution_mode != "LEGACY":
        raise MaterializationError("default execution mode changed from LEGACY")
    if package.dual_run_executed:
        raise MaterializationError("productive DUAL_RUN is not authorized")


def _respondent_ids(df: pd.DataFrame, project: dict[str, Any]) -> tuple[tuple[str, ...], str]:
    candidate = project.get("respondent_key", {}).get("candidate_physical_variable")
    if candidate:
        if candidate not in df.columns:
            raise MaterializationError("authoritative respondent id binding missing")
        ids = tuple(str(value) for value in df[candidate].tolist())
        if any(not value.strip() for value in ids):
            raise MaterializationError("authoritative respondent id contains blanks")
        if len(set(ids)) != len(ids):
            raise MaterializationError("authoritative respondent id is duplicated")
        return ids, RELEASED_SOURCE_ID
    return tuple(str(index) for index in range(1, len(df) + 1)), SOURCE_ROW_ORDINAL_V1


def _bind_variables(df: pd.DataFrame, respondent_ids: tuple[str, ...], package: ReleasedPackage) -> tuple[BoundVariable, ...]:
    refs = sorted(_required_variable_refs(package))
    if len(set(df.columns)) != len(tuple(df.columns)):
        raise MaterializationError("ambiguous physical binding")
    missing = [ref for ref in refs if ref not in set(df.columns)]
    if missing:
        raise MaterializationError(f"physical binding missing: {', '.join(missing)}")
    return tuple(_bound_variable(ref, df[ref].tolist(), respondent_ids) for ref in refs)


def _required_variable_refs(package: ReleasedPackage) -> set[str]:
    refs: set[str] = set()
    for universe in package.universes:
        expression = universe.get("expression", {})
        if expression.get("variable_ref"):
            refs.add(str(expression["variable_ref"]))
    for structure in package.structures:
        refs.update(str(binding["variable_ref"]) for binding in structure.get("variable_bindings", ()))
        refs.update(str(binding["variable_ref"]) for binding in structure.get("option_bindings", ()))
    refs.update(str(item["physical_variable_ref"]) for item in package.banner_filters.get("filters", ()))
    refs.update(str(item["physical_variable_ref"]) for item in package.banner_filters.get("banners", ()))
    for weight in package.weights.get("weights", ()):
        if weight.get("variable_ref"):
            refs.add(str(weight["variable_ref"]))
    return refs


def _bound_variable(variable_ref: str, values: list[Any], respondent_ids: tuple[str, ...]) -> BoundVariable:
    observed = tuple(sorted({_stable_observed(value) for value in values}, key=lambda item: str(item)))
    return BoundVariable(
        variable_ref=variable_ref,
        source_name=variable_ref,
        values_by_respondent=dict(zip(respondent_ids, values)),
        missing_count=sum(1 for value in values if _is_missing(value)),
        observed_values=observed,
    )


def _qa_events(df: pd.DataFrame, respondent_ids: tuple[str, ...], variables: tuple[BoundVariable, ...], package: ReleasedPackage) -> Iterable[MaterializationQAEvent]:
    yield MaterializationQAEvent("QA-SOURCE-N", "PASS", f"source_n={len(df)}", details={"source_n": len(df)})
    yield MaterializationQAEvent("QA-RUNTIME-N", "PASS" if len(df) == len(respondent_ids) else "FAIL", f"runtime_n={len(respondent_ids)}", blocking=len(df) != len(respondent_ids))
    yield MaterializationQAEvent("QA-BINDINGS", "PASS", "all bindings resolved")
    yield MaterializationQAEvent("QA-VALUE-RECONCILIATION", "PASS", "runtime preserves source raw values")
    for variable in variables:
        yield MaterializationQAEvent("QA-MISSING", "PASS", f"{variable.variable_ref} missing_count={variable.missing_count}")
    domain_failure = _category_domain_failure(variables, package)
    yield MaterializationQAEvent("QA-CATEGORY-DOMAIN", "FAIL" if domain_failure else "PASS", domain_failure or "observed domains compatible with released specs", blocking=bool(domain_failure))
    yield MaterializationQAEvent("QA-RESPONDENT-IDENTITY", "PASS", "respondent identity stable and unique")
    yield MaterializationQAEvent("QA-PACKAGE-INTEGRITY", "PASS", "package manifest and project spec are RELEASED")
    ref_failure = _reference_integrity_failure(package)
    yield MaterializationQAEvent("QA-REFERENCE-INTEGRITY", "FAIL" if ref_failure else "PASS", ref_failure or "released references resolved", blocking=bool(ref_failure))


def _category_domain_failure(variables: tuple[BoundVariable, ...], package: ReleasedPackage) -> str:
    by_ref = {variable.variable_ref: set(variable.observed_values) for variable in variables}
    for structure in package.structures:
        if structure.get("structure_type") == "LOOP_NUMERICO":
            continue
        allowed = set(structure.get("ordinary_missing_values", ()))
        if structure.get("structure_type") == "RM":
            allowed |= set(structure.get("selected_values", ())) | set(structure.get("not_selected_values", ()))
            refs = [binding["variable_ref"] for binding in structure.get("option_bindings", ())]
        else:
            allowed |= {category["raw_value"] for category in structure.get("category_bindings", ())}
            refs = [binding["variable_ref"] for binding in structure.get("variable_bindings", ())]
        for ref in refs:
            observed = {value for value in by_ref.get(ref, set()) if value != "__MISSING__"}
            if not observed.issubset(allowed):
                return f"undeclared observed analytical category for {ref}"
    return ""


def _reference_integrity_failure(package: ReleasedPackage) -> str:
    structure_ids = {item["structure_id"] for item in package.structures}
    universe_ids = {item["universe_id"] for item in package.universes}
    metric_ids = {item["metric_id"] for item in package.metrics}
    question_ids = {item["question_id"] for item in package.questions}
    filter_ids = {item["filter_id"] for item in package.banner_filters.get("filters", ())}
    banner_ids = {item["banner_id"] for item in package.banner_filters.get("banners", ())}
    for question in package.questions:
        if question.get("structure_ref") and question["structure_ref"] not in structure_ids:
            return f"dangling structure ref: {question['structure_ref']}"
        for metric in question.get("metric_refs", ()):
            if metric not in metric_ids:
                return f"dangling metric ref: {metric}"
    for structure in package.structures:
        if structure["question_id"] not in question_ids:
            return f"dangling question ref: {structure['question_id']}"
        for ref in structure.get("applicability_refs", {}).values():
            if ref not in universe_ids:
                return f"dangling universe ref: {ref}"
    for request in package.requests.get("requests", ()):
        if request["question_ref"] not in question_ids:
            return f"dangling request question ref: {request['question_ref']}"
        if request["universe_ref"] not in universe_ids:
            return f"dangling request universe ref: {request['universe_ref']}"
        for metric in request.get("metric_refs", ()):
            if metric not in metric_ids:
                return f"dangling request metric ref: {metric}"
        for item in request.get("filters", ()):
            if item["filter_ref"] not in filter_ids:
                return f"dangling filter ref: {item['filter_ref']}"
        banner = request.get("banner")
        if banner and banner["banner_ref"] not in banner_ids:
            return f"dangling banner ref: {banner['banner_ref']}"
    return ""


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _stable_observed(value: Any) -> Any:
    if _is_missing(value):
        return "__MISSING__"
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value
