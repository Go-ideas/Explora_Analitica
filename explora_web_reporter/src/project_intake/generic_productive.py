from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping

from openpyxl import load_workbook

from src.analytics_core.result_identity import stable_json
from src.analytics_core.serialization import to_canonical_data
from src.canonical_materialization.orchestrator import run_canonical_project
from src.canonical_materialization.materializer import load_released_package
from src.contracts.models import ReleaseMetadata
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode
from src.excel_renderer import QualifiedMaster, RenderRequest, plan_render, render, vba_sha256
from src.excel_renderer.renderer import (
    BUILD, MASTER, NUMERIC, VISUAL, configuration_fingerprint,
)
from src.project_intake.compiler import (
    ProjectExecutionBinding, binding_payload, compile_project_spec,
)
from src.project_intake.contract import validate_project
from src.web_canonical.adapter import project_canonical_result


PRESENTATION_SCHEMA = "EXPLORA_PRODUCTIVE_PRESENTATION_V1"
GENERIC_RUNTIME_VERSION = "EXPLORA_GENERIC_PRODUCTIVE_RUNTIME_V1"
SUPPORTED_INPUT_TYPES = frozenset({"SAV"})
SUPPORTED_OUTPUT_TARGETS = frozenset({"WEB", "EXCEL"})


class GenericRuntimeError(ValueError):
    pass


@dataclass(frozen=True)
class GenericReleaseEvidence:
    project_id: str
    runtime_version: str
    project_spec_version: str
    project_spec_fingerprint: str
    source_sha256: str
    package_sha256: str
    binding_fingerprint: str
    core_runtime_fingerprint: str
    canonical_result_fingerprints: tuple[tuple[str, str], ...]
    output_targets: tuple[str, ...]
    release_name: str
    presentation_configuration_id: str | None
    presentation_fingerprint: str | None
    web_adapter_identity: str | None
    web_logical_fingerprint: str | None
    excel_renderer_identity: str | None
    render_plan_fingerprint: str | None
    excel_readback_fingerprint: str | None
    production_master_sha256: str | None
    vba_sha256: str | None
    canonical_web_exact: bool | None
    canonical_excel_exact: bool | None
    web_excel_exact: bool | None
    legacy_fallback: bool
    qa_status: str
    release_fingerprint: str


def _load(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return json.loads(json.dumps(value))
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _execute_binding(binding: ProjectExecutionBinding, *, source_path: str | Path,
                     package_path: str | Path) -> Any:
    if binding.execution_mode != "CANONICAL_V1":
        raise GenericRuntimeError("generic runtime requires CANONICAL_V1")
    if _sha256_file(source_path).upper() != binding.source_sha256:
        raise GenericRuntimeError("source fingerprint changed after compilation")
    if _sha256_file(package_path).upper() != binding.package_sha256:
        raise GenericRuntimeError("package fingerprint changed after compilation")
    return run_canonical_project(
        source_path=source_path, package_path=package_path,
        request_ids=binding.request_ids,
        expected_source_sha256=binding.source_sha256,
        expected_package_sha256=binding.package_sha256,
    )


def _identity(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    if not normalized:
        raise GenericRuntimeError("identity cannot produce a release name")
    return normalized


def release_name(project_id: str, configuration_id: str | None) -> str:
    parts = [_identity(project_id)]
    if configuration_id:
        parts.append(_identity(configuration_id))
    return "__".join(parts)


def output_intent(project_spec: Mapping[str, Any]) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    by_target: dict[str, list[str]] = {"WEB": [], "EXCEL": []}
    for request in project_spec["output_requests"]:
        request_id = request["output_request_id"]
        if request.get("web_included"):
            by_target["WEB"].append(request_id)
        if request.get("excel_included"):
            by_target["EXCEL"].append(request_id)
    targets = tuple(key for key in ("WEB", "EXCEL") if by_target[key])
    if not targets or not set(targets).issubset(SUPPORTED_OUTPUT_TARGETS):
        raise GenericRuntimeError("unsupported output intent")
    return {key: tuple(values) for key, values in by_target.items()}, targets


def _analytical_output_intent(project_spec: Mapping[str, Any], package_path: str | Path) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    package = load_released_package(package_path)
    outputs = {item["output_request_id"]: item for item in project_spec["output_requests"]}
    by_target: dict[str, list[str]] = {"WEB": [], "EXCEL": []}
    for request in package.requests.get("requests", ()):
        output_ref = request.get("output_request_ref", request["request_id"])
        output = outputs.get(output_ref)
        if output is None:
            raise GenericRuntimeError("released request references unknown output intent")
        if output.get("web_included"):
            by_target["WEB"].append(request["request_id"])
        if output.get("excel_included"):
            by_target["EXCEL"].append(request["request_id"])
    targets = tuple(key for key in ("WEB", "EXCEL") if by_target[key])
    return {key: tuple(values) for key, values in by_target.items()}, targets


def _release(authority: str, version: str, checksum: str) -> ReleaseMetadata:
    return ReleaseMetadata(ReleaseLifecycle.RELEASED, ReleaseMode.MANUAL, authority,
                           "2026-09-21", "GATE45_REVIEW", version, checksum)


def build_render_request(
    configuration: Mapping[str, Any] | str | Path,
    *,
    project_id: str,
    results: Mapping[str, Any],
    qualified_master: QualifiedMaster,
) -> RenderRequest:
    config = _load(configuration)
    required = {"schema_version", "configuration_id", "configuration_version", "project_id",
                "visual_spec_id", "revision", "slot_ids", "sections", "provenance_refs"}
    if set(config) != required or config["schema_version"] != PRESENTATION_SCHEMA:
        raise GenericRuntimeError("unsupported presentation configuration")
    if config["project_id"] != project_id:
        raise GenericRuntimeError("presentation project identity mismatch")
    if not isinstance(config["sections"], list) or not config["sections"]:
        raise GenericRuntimeError("missing presentation binding")
    selected_ids = tuple(config["slot_ids"])
    slots_by_id = {slot.slot_id: slot for slot in qualified_master.manifest.writable_slots}
    if not selected_ids or len(set(selected_ids)) != len(selected_ids) or any(i not in slots_by_id for i in selected_ids):
        raise GenericRuntimeError("unknown Master slot")
    selected_slots = tuple(slots_by_id[item] for item in selected_ids)

    bound_request_ids: set[str] = set()
    sections = json.loads(json.dumps(config["sections"]))
    for section in sections:
        for visual in section.get("visuals", ()):
            for binding in visual.get("source_bindings", ()):
                request_id = binding.pop("request_id", None)
                if request_id not in results:
                    raise GenericRuntimeError("missing presentation result binding")
                binding["result_run_id"] = results[request_id].result_run_id
                bound_request_ids.add(request_id)
                if binding.get("slot_id") not in selected_ids:
                    raise GenericRuntimeError("binding references undeclared Master slot")
    if not bound_request_ids:
        raise GenericRuntimeError("missing presentation binding")
    runs = tuple(results[key] for key in sorted(bound_request_ids))
    spec = {
        "schema_version": VISUAL,
        "visual_spec_id": config["visual_spec_id"],
        "revision": config["revision"],
        "project_id": project_id,
        "result_refs": [{"result_run_id": run.result_run_id,
                         "result_fingerprint": run.result_fingerprint,
                         "request_fingerprint": run.request.request_fingerprint} for run in runs],
        "master_interface_version": MASTER,
        "numeric_profile_version": NUMERIC,
        "provenance_refs": list(config["provenance_refs"]),
        "sections": sections,
    }
    visual_json = stable_json(spec)
    master = qualified_master.manifest
    request = RenderRequest(
        runs, visual_json, master, selected_slots,
        config["configuration_id"], config["configuration_version"],
        _release("PRESENTATION_CONFIGURATION", config["configuration_version"], "PENDING"),
        _release("QUALIFIED_MASTER", master.version, master.artifact_sha256),
        renderer_build=BUILD,
    )
    return replace(request, configuration_release=_release(
        "PRESENTATION_CONFIGURATION", config["configuration_version"],
        configuration_fingerprint(request)))


def run_generic_productive(
    project_spec: Mapping[str, Any] | str | Path,
    *,
    source_path: str | Path,
    package_path: str | Path,
    output_root: str | Path,
    presentation_configuration: Mapping[str, Any] | str | Path | None = None,
    qualified_master: QualifiedMaster | None = None,
    master_path: str | Path | None = None,
    expected_source_sha256: str | None = None,
    expected_package_sha256: str | None = None,
) -> dict[str, Any]:
    destination = Path(output_root)
    if destination.exists():
        raise FileExistsError(f"refusing to replace existing release: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}.", dir=destination.parent) as temporary:
        staging = Path(temporary) / "release"
        summary = _build_release(
            project_spec, source_path=source_path, package_path=package_path, output_root=staging,
            presentation_configuration=presentation_configuration, qualified_master=qualified_master,
            master_path=master_path, expected_source_sha256=expected_source_sha256,
            expected_package_sha256=expected_package_sha256,
        )
        staging.replace(destination)
        return summary


def _build_release(
    project_spec: Mapping[str, Any] | str | Path,
    *, source_path: str | Path, package_path: str | Path, output_root: Path,
    presentation_configuration: Mapping[str, Any] | str | Path | None,
    qualified_master: QualifiedMaster | None, master_path: str | Path | None,
    expected_source_sha256: str | None, expected_package_sha256: str | None,
) -> dict[str, Any]:
    spec = _load(project_spec)
    intake = validate_project(spec)
    if not intake.ready_for_execution:
        raise GenericRuntimeError("Project Spec is not READY_FOR_EXECUTION")
    input_type = spec["dataset"]["input_type"]
    if input_type not in SUPPORTED_INPUT_TYPES:
        raise GenericRuntimeError(f"unsupported physical input type: {input_type}")
    intent, targets = output_intent(spec)
    if "EXCEL" in targets and (presentation_configuration is None or qualified_master is None or master_path is None):
        raise GenericRuntimeError("Excel output requires presentation configuration and qualified Master")
    binding = compile_project_spec(
        spec, source_path=source_path, package_path=package_path,
        expected_source_sha256=expected_source_sha256,
        expected_package_sha256=expected_package_sha256,
    )
    intent, targets = _analytical_output_intent(spec, package_path)
    if binding.execution_mode != "CANONICAL_V1":
        raise GenericRuntimeError("generic runtime requires CANONICAL_V1")
    first = _execute_binding(binding, source_path=source_path, package_path=package_path)
    second = _execute_binding(binding, source_path=source_path, package_path=package_path)
    first_ids = tuple((key, first.results[key].result_fingerprint) for key in binding.request_ids)
    second_ids = tuple((key, second.results[key].result_fingerprint) for key in binding.request_ids)
    if first.runtime.fingerprint != second.runtime.fingerprint or first_ids != second_ids:
        raise GenericRuntimeError("productive rerun is not deterministic")
    return produce_generic_release(
        spec, binding, first, output_root=output_root, intent=intent, targets=targets,
        presentation_configuration=presentation_configuration, qualified_master=qualified_master,
        master_path=master_path,
    )


def produce_generic_release(
    project_spec: Mapping[str, Any],
    binding: ProjectExecutionBinding,
    execution: Any,
    *, output_root: str | Path,
    intent: Mapping[str, tuple[str, ...]] | None = None,
    targets: tuple[str, ...] | None = None,
    presentation_configuration: Mapping[str, Any] | str | Path | None = None,
    qualified_master: QualifiedMaster | None = None,
    master_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(output_root)
    if intent is None:
        intent, derived_targets = output_intent(project_spec)
    else:
        intent = dict(intent)
        derived_targets = tuple(key for key in ("WEB", "EXCEL") if intent.get(key))
    targets = targets or derived_targets
    for name in ("config", "canonical", "qa", "provenance", *[item.lower() for item in targets]):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "config" / "project_spec.json").write_text(
        json.dumps(project_spec, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    config_data = _load(presentation_configuration) if presentation_configuration is not None else None
    if config_data is not None:
        (root / "config" / "presentation_configuration.json").write_text(
            json.dumps(config_data, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (root / "canonical" / "execution_binding.json").write_text(
        json.dumps(binding_payload(binding), indent=2) + "\n", encoding="utf-8")
    canonical = {key: to_canonical_data(execution.results[key]) for key in binding.request_ids}
    if any(not execution.results[key].release.releasable for key in binding.request_ids):
        raise GenericRuntimeError("Canonical result is not releasable")
    (root / "canonical" / "canonical_results.json").write_text(
        json.dumps(canonical, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    web_payload: dict[str, Any] = {}
    web_estimates: dict[tuple[str, str], Any] = {}
    web_adapter = None
    if "WEB" in targets:
        for request_id in intent["WEB"]:
            projection = project_canonical_result(
                execution.results[request_id], presentation_identity=binding.project_id)
            cells = [asdict(cell) for cell in projection.cells]
            web_payload[request_id] = {
                "authority": projection.authority, "adapter_version": projection.adapter_version,
                "result_run_id": projection.result_run_id,
                "result_fingerprint": projection.result_fingerprint, "cells": cells,
            }
            web_adapter = projection.adapter_version
            web_estimates.update({(request_id, cell.value_id): cell.estimate for cell in projection.cells})
        (root / "web" / "canonical_web_output.json").write_text(
            json.dumps(web_payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    config_id = config_data["configuration_id"] if config_data else None
    name = release_name(binding.project_id, config_id)
    plan_fingerprint = readback_fingerprint = master_sha = output_vba = None
    excel_exact: bool | None = None
    excel_values: dict[tuple[str, str], Any] = {}
    if "EXCEL" in targets:
        if config_data is None or qualified_master is None or master_path is None:
            raise GenericRuntimeError("Excel output requires presentation configuration and qualified Master")
        excel_results = {key: execution.results[key] for key in intent["EXCEL"]}
        request = build_render_request(config_data, project_id=binding.project_id,
                                       results=excel_results, qualified_master=qualified_master)
        plan = plan_render(request, Path(master_path))
        output_path = root / "excel" / f"{name}.xlsm"
        render(request, Path(master_path), output_path, plan=plan)
        for write in plan.writes:
            if write.record_role == "value" and write.field_name == "estimate":
                request_id, expected = _find_value(excel_results, write.record_id)
                actual = _cell(output_path, write.sheet, write.cell)
                excel_values[(request_id, write.record_id)] = actual
                if actual != expected:
                    raise GenericRuntimeError("Canonical to Excel parity failure")
        if not excel_values:
            raise GenericRuntimeError("Excel presentation has no canonical numeric read-back")
        excel_exact = True
        plan_fingerprint = plan.plan_sha256
        readback_fingerprint = _fingerprint(sorted((list(key), value) for key, value in excel_values.items()))
        master_sha = _sha256_file(master_path)
        output_vba = vba_sha256(output_path)
        if output_vba != vba_sha256(Path(master_path)):
            raise GenericRuntimeError("VBA preservation failure")

    web_exact = None if "WEB" not in targets else all(
        web_estimates[(request_id, item.value_id)] == item.estimate
        for request_id in intent["WEB"] for item in execution.results[request_id].values)
    common = set(web_estimates) & set(excel_values)
    web_excel_exact = None if not common else all(web_estimates[key] == excel_values[key] for key in common)
    if web_exact is False or excel_exact is False or web_excel_exact is False:
        raise GenericRuntimeError("presentation parity failure")

    evidence_payload = {
        "project_id": binding.project_id,
        "runtime_version": GENERIC_RUNTIME_VERSION,
        "project_spec_version": binding.project_spec_version,
        "project_spec_fingerprint": binding.project_spec_fingerprint,
        "source_sha256": binding.source_sha256,
        "package_sha256": binding.package_sha256,
        "binding_fingerprint": binding.binding_fingerprint,
        "core_runtime_fingerprint": execution.runtime.fingerprint,
        "canonical_result_fingerprints": tuple(
            (key, execution.results[key].result_fingerprint or "") for key in binding.request_ids),
        "output_targets": targets,
        "release_name": name,
        "presentation_configuration_id": config_id,
        "presentation_fingerprint": None if config_data is None else _fingerprint(config_data),
        "web_adapter_identity": web_adapter,
        "web_logical_fingerprint": None if not web_payload else _fingerprint(web_payload),
        "excel_renderer_identity": BUILD if "EXCEL" in targets else None,
        "render_plan_fingerprint": plan_fingerprint,
        "excel_readback_fingerprint": readback_fingerprint,
        "production_master_sha256": master_sha,
        "vba_sha256": output_vba,
        "canonical_web_exact": web_exact,
        "canonical_excel_exact": excel_exact,
        "web_excel_exact": web_excel_exact,
        "legacy_fallback": False,
        "qa_status": "PASS",
    }
    evidence = GenericReleaseEvidence(
        **evidence_payload, release_fingerprint=_fingerprint(evidence_payload))
    (root / "qa" / "generic_runtime_qa.json").write_text(
        json.dumps(asdict(evidence), indent=2) + "\n", encoding="utf-8")
    (root / "provenance" / "release_provenance.json").write_text(
        json.dumps(asdict(evidence), indent=2) + "\n", encoding="utf-8")
    manifest = {"schema_version": "EXPLORA_PRODUCTIVE_RELEASE_V1", **asdict(evidence),
                "files": sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())}
    (root / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return asdict(evidence)


def _find_value(results: Mapping[str, Any], value_id: str) -> tuple[str, Any]:
    found = [(request_id, item.estimate) for request_id, result in results.items()
             for item in result.values if item.value_id == value_id]
    if len(found) != 1:
        raise GenericRuntimeError("ambiguous canonical read-back identity")
    return found[0]


def _cell(path: Path, sheet: str, cell: str) -> Any:
    workbook = load_workbook(path, keep_vba=True, data_only=False)
    try:
        return workbook[sheet][cell].value
    finally:
        workbook.close()
        if workbook.vba_archive:
            workbook.vba_archive.close()
