from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.canonical_materialization.materializer import load_released_package
from src.project_intake.contract import project_spec_fingerprint, validate_project


EXECUTION_BINDING_SCHEMA = "EXPLORA_PROJECT_EXECUTION_BINDING_V1"


class ProjectCompilationError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectExecutionBinding:
    schema_version: str
    project_id: str
    project_spec_version: str
    project_spec_fingerprint: str
    source_sha256: str
    package_sha256: str
    package_id: str
    package_version: str
    package_spec_hash: str
    execution_mode: str
    request_ids: tuple[str, ...]
    question_ids: tuple[str, ...]
    structure_ids: tuple[str, ...]
    universe_ids: tuple[str, ...]
    weight_ids: tuple[str, ...]
    banner_ids: tuple[str, ...]
    filter_ids: tuple[str, ...]
    significance_ids: tuple[str, ...]
    output_targets: tuple[str, ...]
    policy_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    binding_fingerprint: str


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def _load(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return json.loads(json.dumps(value))
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _fingerprint(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compile_project_spec(
    project_spec: Mapping[str, Any] | str | Path,
    *,
    source_path: str | Path,
    package_path: str | Path,
    expected_source_sha256: str | None = None,
    expected_package_sha256: str | None = None,
) -> ProjectExecutionBinding:
    spec = _load(project_spec)
    intake = validate_project(spec)
    if not intake.ready_for_execution:
        codes = ", ".join(issue.code for issue in intake.errors)
        raise ProjectCompilationError(f"Project Spec is not READY_FOR_EXECUTION: {codes}")
    source_sha = _sha(source_path)
    package_sha = _sha(package_path)
    if expected_source_sha256 and source_sha != expected_source_sha256.upper():
        raise ProjectCompilationError("source fingerprint mismatch")
    if expected_package_sha256 and package_sha != expected_package_sha256.upper():
        raise ProjectCompilationError("release package fingerprint mismatch")
    declared_source = str(spec["dataset"]["fingerprint"]).removeprefix("sha256:").upper()
    if declared_source != source_sha:
        raise ProjectCompilationError("Project Spec source fingerprint mismatch")
    package = load_released_package(package_path)
    if package.manifest.get("status") != "RELEASED":
        raise ProjectCompilationError("downstream package is not RELEASED")
    if package.project.get("project_id") != spec["project"]["project_id"]:
        raise ProjectCompilationError("project identity mismatch")
    if package.manifest.get("dataset_fingerprint_sha256") != source_sha:
        raise ProjectCompilationError("package dataset fingerprint mismatch")
    declared_metadata = {str(item).removeprefix("sha256:").upper()
                         for item in spec["source_metadata_fingerprints"]}
    required_metadata = {package_sha, str(package.manifest["questionnaire_sha256"]).upper()}
    if not required_metadata.issubset(declared_metadata):
        raise ProjectCompilationError("Project Spec metadata fingerprints do not match released package")

    question_ids = tuple(sorted(item["question_id"] for item in package.questions))
    spec_question_ids = tuple(sorted(item["question_id"] for item in spec["questions"]))
    if spec_question_ids != question_ids:
        raise ProjectCompilationError("Project Spec questions do not match released package")
    released_questions = {item["question_id"]: item for item in package.questions}
    for item in spec["questions"]:
        released = released_questions[item["question_id"]]
        if (item["structure_ref"], item["universe_ref"]) != (
                released["structure_ref"], released["universe_ref"]):
            raise ProjectCompilationError("Project Spec question binding mismatch")
    structure_ids = tuple(sorted(item["structure_id"] for item in package.structures))
    universe_ids = tuple(sorted(item["universe_id"] for item in package.universes))
    if tuple(sorted(item["universe_id"] for item in spec["universes"])) != universe_ids:
        raise ProjectCompilationError("Project Spec universes do not match released package")
    weights = tuple(sorted(item["weight_id"] for item in package.weights.get("weights", ())))
    if tuple(sorted(item["weight_id"] for item in spec["weights"])) != weights:
        raise ProjectCompilationError("Project Spec weights do not match B1 registry")
    banners = tuple(sorted(item["banner_id"] for item in package.banner_filters.get("banners", ())))
    filters = tuple(sorted(item["filter_id"] for item in package.banner_filters.get("filters", ())))
    significance = tuple(sorted(item["significance_id"] for item in package.significance))
    if tuple(sorted(item["banner_id"] for item in spec["banners"])) != banners:
        raise ProjectCompilationError("Project Spec banners do not match released package")
    if tuple(sorted(item["filter_id"] for item in spec["filters"])) != filters:
        raise ProjectCompilationError("Project Spec filters do not match released package")
    if tuple(sorted(item["significance_request_id"] for item in spec["significance_requests"])) != significance:
        raise ProjectCompilationError("Project Spec significance requests do not match B2 release")
    requests = tuple(sorted(item["request_id"] for item in package.requests.get("requests", ())))
    requested = tuple(sorted(item["output_request_id"] for item in spec["output_requests"]))
    if requested != requests:
        raise ProjectCompilationError("Project Spec outputs do not match released requests")
    targets = tuple(sorted({target for item in spec["output_requests"] for target in (
        "WEB" if item.get("web_included") else None,
        "EXCEL" if item.get("excel_included") else None) if target}))
    if not targets or not set(targets).issubset({"WEB", "EXCEL"}):
        raise ProjectCompilationError("unqualified presentation target")
    provenance = spec["provenance"]
    policies = (provenance["b1_policy_ref"], provenance["b2_policy_ref"], provenance["b3_policy_ref"])
    if policies != ("B1_V1", "B2_V1", "B3_V1"):
        raise ProjectCompilationError("B1/B2/B3 authority mismatch")
    payload = {
        "schema_version": EXECUTION_BINDING_SCHEMA,
        "project_id": intake.project_id,
        "project_spec_version": intake.spec_version,
        "project_spec_fingerprint": project_spec_fingerprint(spec),
        "source_sha256": source_sha,
        "package_sha256": package_sha,
        "package_id": package.package_id,
        "package_version": package.package_version,
        "package_spec_hash": package.spec_hash,
        "execution_mode": "CANONICAL_V1",
        "request_ids": requests,
        "question_ids": question_ids,
        "structure_ids": structure_ids,
        "universe_ids": universe_ids,
        "weight_ids": weights,
        "banner_ids": banners,
        "filter_ids": filters,
        "significance_ids": significance,
        "output_targets": targets,
        "policy_refs": policies,
        "provenance_refs": tuple(sorted(str(item) for item in provenance["source_refs"])),
    }
    return ProjectExecutionBinding(**payload, binding_fingerprint=_fingerprint(payload))


def binding_payload(binding: ProjectExecutionBinding) -> dict[str, Any]:
    return {key: value for key, value in binding.__dict__.items()}
