from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping
import zipfile

from src.canonical_materialization.materializer import PACKAGE_FILES, load_released_package
from src.contracts.models import ReleaseMetadata, SignificanceSpec
from src.contracts.validators import validate_significance_spec
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode, SampleRelationship
from src.package_authoring.contract import PackageAuthoringError, validate_execution_release


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
BUILDER_VERSION = "EXPLORA_GENERIC_PACKAGE_BUILDER_V1"


@dataclass(frozen=True)
class BuildEvidence:
    package_path: Path
    package_sha256: str
    package_spec_hash: str
    project_spec_fingerprint: str
    file_count: int
    loader_roundtrip: bool
    deterministic_zip: bool


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _with_hash(value: dict[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    payload.pop("spec_hash", None)
    payload["spec_hash"] = _hash(_canonical(payload))
    return payload


def _release_envelope(release: dict[str, Any]) -> dict[str, Any]:
    decision = release["release_decision"]
    return {
        "release_state": "RELEASED",
        "provenance": {
            "human_decision_id": decision["human_decision_id"],
            "human_decision_basis": decision["human_decision_basis"],
            "release_mode": decision["release_mode"],
            "released_at": decision["released_at"],
            "mapping_authority": release["source_authority"]["mapping_authority"],
            "methodology_authorities": ["B1_V1", "B2_V1", "B3_V1", release["policy_refs"]["formula_registry"]],
            "authoritative_datamap": release["source_authority"]["datamap_ref"],
            "execution_release_spec_id": release["release_spec_id"],
            "execution_release_spec_version": release["release_spec_version"],
            "execution_release_spec_fingerprint": _hash(_canonical(release)),
            "builder_version": BUILDER_VERSION,
        },
    }


def _records(items: list[dict[str, Any]], release: dict[str, Any], spec_type: str) -> list[dict[str, Any]]:
    envelope = _release_envelope(release)
    return [_with_hash({**item, "spec_type": spec_type, "spec_version": release["release_spec_version"], **envelope}) for item in items]


def _physicalize(items: list[dict[str, Any]], variable_map: dict[str, str]) -> list[dict[str, Any]]:
    data = json.loads(json.dumps(items))
    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if "variable_ref" in value:
                logical = value["variable_ref"]
                if logical not in variable_map:
                    raise PackageAuthoringError(f"unknown logical variable binding: {logical}")
                value["variable_ref"] = variable_map[logical]
            if "physical_variable_ref" in value:
                logical = value["physical_variable_ref"]
                if logical not in variable_map:
                    raise PackageAuthoringError(f"unknown physical variable binding: {logical}")
                value["physical_variable_ref"] = variable_map[logical]
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(data)
    return data


def _b2_significance_records(items: list[dict[str, Any]], release: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    decision = release["release_decision"]
    for item in items:
        metadata = ReleaseMetadata(
            ReleaseLifecycle.RELEASED, ReleaseMode.MANUAL,
            decision["human_decision_id"], decision["released_at"],
            "B2", "B2_V1", release["source_authority"]["questionnaire_sha256"],
        )
        proportion_test = SignificanceSpec.__dataclass_fields__["proportion_test"].default
        spec = validate_significance_spec(SignificanceSpec(
            spec_id=item["significance_id"], version=release["release_spec_version"],
            release=metadata, test_id=proportion_test,
            confidence=item["confidence"], alpha=1 - item["confidence"],
            sample_relationship=SampleRelationship(item["sample_relationship"]),
        ))
        policy = asdict(spec)
        for key in ("spec_id", "version", "release"):
            policy.pop(key)
        policy["sample_relationship"] = spec.sample_relationship.value.upper()
        records.append({**item, **policy})
    return _records(records, release, "SIGNIFICANCE_SPEC_RELEASED")


def _artifact_payloads(project: dict[str, Any], release: dict[str, Any]) -> dict[str, bytes]:
    variables = {item["variable_id"]: item["source_name"] for item in project["dataset"]["variables"]}
    envelope = _release_envelope(release)
    authority = release["source_authority"]
    questions_by_id = {item["question_id"]: item for item in project["questions"]}
    questions = []
    for item in release["questions"]:
        source = questions_by_id[item["question_id"]]
        questions.append({**item, "question_spec_id": item.get("question_spec_id", f"QSP_{item['question_id']}"),
            "physical_variable_bindings": [{"variable_ref": variables[ref], "spss_short_name": variables[ref]} for ref in source["source_variables"]],
            "category_refs": [category["category_id"] for category in source.get("categories", [])], "universe_ref": source["universe_ref"], "label_metadata_only": True})
    structures = _physicalize(release["structures"], variables)
    universes = []
    for source in project["universes"]:
        expression = source["expression"]
        operator = expression.get("operator")
        args = expression.get("args", [])
        if operator not in {"in", "not_in", "eq", "neq"} or len(args) != 2 or args[0] not in variables:
            raise PackageAuthoringError("unsupported universe expression for current loader")
        values = args[1] if isinstance(args[1], list) else [args[1]]
        universes.append({"universe_id": source["universe_id"], "expression": {"op": operator, "variable_ref": variables[args[0]], "values": values},
            "level": source["execution_scope"], "missing_policy": "EXCLUDE", "on_unresolved": "FAIL"})
    weights = _physicalize(release["weights"], variables)
    banners = _physicalize(release["banners"], variables)
    filters = _physicalize(release["filters"], variables)
    requests = [{**item, "output_request_ref": item.get("output_request_ref", item["request_id"])}
                for item in release["requests"]]
    common_project = {
        "project_id": project["project"]["project_id"], "spec_version": project["project"]["spec_version"],
        "internal_project_name": release["package"]["internal_project_name"], "spec_type": "PROJECT_SPEC_RELEASED",
        "canonical_structure_authority": "M4_STRUCTURE_V1", "release_state": "RELEASED", "productive_project": True,
        "default_execution_mode": "LEGACY", "default_weight_ref": project.get("default_weight_ref"),
        "dataset": {"dataset_fingerprint_sha256": authority["dataset_sha256"].upper(), "dataset_version": release["package"]["dataset_version"], "source_filename": authority["dataset_filename"]},
        "respondent_key": {"candidate_physical_variable": variables[project["dataset"]["respondent_id_variable"]], "status": "APPROVED"},
        "question_spec_refs": sorted(item["question_id"] for item in questions), "structure_spec_refs": sorted(item["structure_id"] for item in structures),
        "universe_spec_refs": sorted(item["universe_id"] for item in universes), "metric_spec_refs": sorted(item["metric_id"] for item in release["metrics"]),
        "significance_spec_refs": sorted(item["significance_id"] for item in release["significance"]), "banner_spec_refs": sorted(item["banner_id"] for item in banners),
        "filter_spec_refs": sorted(item["filter_id"] for item in filters), "request_refs": sorted(item["request_id"] for item in release["requests"]),
        "provenance": envelope["provenance"],
    }
    objects: dict[str, Any] = {
        "01_PROJECT_SPEC_RELEASED.json": _with_hash(common_project),
        "02_QUESTION_SPECS_RELEASED.json": _records(questions, release, "QUESTION_SPEC_RELEASED"),
        "03_STRUCTURE_SPECS_RELEASED.json": _records(structures, release, "STRUCTURE_SPEC_RELEASED"),
        "04_UNIVERSE_SPECS_RELEASED.json": _records(universes, release, "UNIVERSE_SPEC_RELEASED"),
        "05_WEIGHT_REGISTRY_RELEASED.json": _with_hash({"weights": _records([{**item, "is_project_default": item["weight_id"] == project.get("default_weight_ref")} for item in weights], release, "WEIGHT_SPEC_RELEASED"), "registered_weights": [item["weight_id"] for item in weights], "project_default_weight_ref": project.get("default_weight_ref"), "analysis_specific_overrides": [{"request_id": item["request_id"], "weight_ref": item["weight_ref"]} for item in release["requests"] if item.get("weight_choice") == "REQUEST_OVERRIDE"], "explicitly_unweighted_requests": [item["request_id"] for item in release["requests"] if item.get("weight_choice") == "EXPLICITLY_UNWEIGHTED"], "resolution": "EXPLICIT_B1"}),
        "06_METRIC_SPECS_RELEASED.json": _records(release["metrics"], release, "METRIC_SPEC_RELEASED"),
        "07_SIGNIFICANCE_SPECS_RELEASED.json": _b2_significance_records(release["significance"], release),
        "08_BANNER_FILTER_SPECS_RELEASED.json": _with_hash({"banners": _records(banners, release, "BANNER_SPEC_RELEASED"), "filters": _records(filters, release, "FILTER_SPEC_RELEASED")}),
        "09_REQUEST_MATRIX_RELEASED.json": _with_hash({"matrix_id": f"MATRIX_{release['release_spec_id']}", "requests": _records(requests, release, "REQUEST_SPEC_RELEASED")}),
    }
    serialized = {name: _canonical(value) for name, value in objects.items()}
    package_spec_hash = _hash(_canonical({name: _hash(data) for name, data in sorted(serialized.items())}))
    manifest = {
        "package_id": release["package"]["package_id"], "package_version": release["package"]["package_version"],
        "project_id": release["project_id"], "project_spec_fingerprint": release["project_spec_fingerprint"],
        "execution_release_spec_id": release["release_spec_id"], "execution_release_spec_version": release["release_spec_version"],
        "execution_release_spec_fingerprint": _hash(_canonical(release)), "builder_version": BUILDER_VERSION,
        "dataset_fingerprint_sha256": authority["dataset_sha256"].upper(), "questionnaire_sha256": authority["questionnaire_sha256"].upper(),
        "status": "RELEASED", "released_at": release["release_decision"]["released_at"], "human_decision_id": release["release_decision"]["human_decision_id"],
        "default_execution_mode": "LEGACY", "dual_run_executed": False, "canonical_result_generated": False, "m7_started": False,
        "files": [{"filename": name, "sha256": _hash(data), "size_bytes": len(data)} for name, data in sorted(serialized.items())],
        "spec_hash": package_spec_hash,
    }
    serialized["MANIFEST.json"] = _canonical(manifest)
    if set(serialized) != set(PACKAGE_FILES):
        raise AssertionError("builder output differs from loader contract")
    return serialized


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in PACKAGE_FILES:
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def build_released_package(
    project_spec: Mapping[str, Any] | str | Path,
    execution_release: Mapping[str, Any] | str | Path,
    *, destination: str | Path,
    source_path: str | Path | None = None,
) -> BuildEvidence:
    validated = validate_execution_release(project_spec, execution_release)
    release = validated.execution_release
    if source_path is not None and _hash(Path(source_path).read_bytes()) != release["source_authority"]["dataset_sha256"].upper():
        raise PackageAuthoringError("source artifact hash mismatch")
    files = _artifact_payloads(validated.project_spec, release)
    first = _zip_bytes(files)
    if first != _zip_bytes(files):
        raise PackageAuthoringError("ZIP production is not deterministic")
    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"refusing to replace existing package: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(first)
            stream.flush()
            os.fsync(stream.fileno())
        loaded = load_released_package(temporary)
        if loaded.package_id != release["package"]["package_id"] or len(files) != 10:
            raise PackageAuthoringError("loader round-trip validation failed")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return BuildEvidence(target, _hash(first), loaded.spec_hash, validated.project_spec_fingerprint, 10, True, True)
