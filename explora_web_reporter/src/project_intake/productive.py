from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from src.analytics_core.serialization import to_canonical_data
from src.canonical_materialization.materializer import load_released_package
from src.canonical_materialization.orchestrator import run_canonical_project
from src.excel_renderer import benchmark_a_request, load_qualified_master, plan_render, render, vba_sha256
from src.project_intake.compiler import ProjectExecutionBinding
from src.web_canonical.adapter import project_canonical_result


GATE44_RUNNER_VERSION = "GATE44_PRODUCTIVE_E2E_V1"


@dataclass(frozen=True)
class ProductiveReleaseEvidence:
    project_id: str
    runner_version: str
    binding_fingerprint: str
    runtime_fingerprint: str
    canonical_result_fingerprints: tuple[tuple[str, str], ...]
    web_logical_fingerprint: str
    fixed_plan_fingerprint: str
    dynamic_plan_fingerprint: str
    fixed_readback_fingerprint: str
    dynamic_readback_fingerprint: str
    production_master_sha256: str
    vba_sha256: str
    canonical_web_exact: bool
    canonical_excel_exact: bool
    web_excel_exact: bool


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def logical_fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def execute_binding(binding: ProjectExecutionBinding, *, source_path: str | Path,
                    package_path: str | Path):
    if binding.execution_mode != "CANONICAL_V1":
        raise ValueError("Gate 44 requires CANONICAL_V1 with no fallback")
    if sha256_file(source_path).upper() != binding.source_sha256:
        raise ValueError("source fingerprint changed after compilation")
    if sha256_file(package_path).upper() != binding.package_sha256:
        raise ValueError("package fingerprint changed after compilation")
    return run_canonical_project(
        source_path=source_path,
        package_path=package_path,
        request_ids=binding.request_ids,
        expected_source_sha256=binding.source_sha256,
        expected_package_sha256=binding.package_sha256,
    )


def build_project_spec(*, source_path: str | Path, package_path: str | Path) -> dict[str, Any]:
    package = load_released_package(package_path)
    source_sha = sha256_file(source_path).upper()
    structures = {item["structure_id"]: item for item in package.structures}
    required_variables = {"key"}
    for structure in package.structures:
        required_variables.update(item["variable_ref"] for item in structure.get("variable_bindings", ()))
        required_variables.update(item["variable_ref"] for item in structure.get("option_bindings", ()))
    required_variables.update(item["expression"]["variable_ref"] for item in package.universes)
    required_variables.update(item["physical_variable_ref"] for item in package.banner_filters.get("banners", ()))
    required_variables.update(item["physical_variable_ref"] for item in package.banner_filters.get("filters", ()))
    questions = []
    for question in package.questions:
        structure = structures[question["structure_ref"]]
        variables = [item["variable_ref"] for item in structure.get("variable_bindings", ())]
        variables += [item["variable_ref"] for item in structure.get("option_bindings", ())]
        categories = [{"category_id": item["category_id"], "raw_value": item["raw_value"],
                       "label": item.get("label", item["category_id"]), "order": index,
                       "included": True, "special": False}
                      for index, item in enumerate(structure.get("category_bindings", ()), 1)]
        questions.append({"question_id": question["question_id"],
            "question_type": "PARENT_RM" if structure["structure_type"] == "RM" else structure["structure_type"],
            "source_variables": variables, "display_label": question["question_id"],
            "universe_ref": question["universe_ref"], "structure_ref": question["structure_ref"],
            "categories": categories})
    universes = [{"universe_id": item["universe_id"], "parent_universe_ref": None,
        "source_variables": [item["expression"]["variable_ref"]],
        "expression": {"operator": item["expression"]["op"],
                       "args": [item["expression"]["variable_ref"], item["expression"].get("values", [])]},
        "rule_state": "DETERMINISTIC", "execution_scope": item.get("level", "question").upper()}
        for item in package.universes]
    banners = [{"banner_id": item["banner_id"], "variable_ref": item["physical_variable_ref"],
        "rule": {"operator": "categories", "values": [m["raw_value"] for m in item["members"]]},
        "category_order": [m["member_id"] for m in item["members"]],
        "universe_ref": universes[0]["universe_id"], "display_eligible": True}
        for item in package.banner_filters.get("banners", ())]
    filters = [{"filter_id": item["filter_id"], "variable_ref": item["physical_variable_ref"],
        "rule": {"operator": "in", "values": [m["raw_value"] for m in item["members"]]},
        "combination": "AND", "universe_ref": universes[0]["universe_id"]}
        for item in package.banner_filters.get("filters", ())]
    significance = [{"significance_request_id": item["significance_id"], "enabled": True,
        "confidence": item["confidence"], "comparison_scope": "BANNER_MEMBERS", "policy_ref": "B2_V1"}
        for item in package.significance]
    outputs = []
    for request in package.requests.get("requests", ()):
        outputs.append({"output_request_id": request["request_id"], "question_refs": [request["question_ref"]],
            "banner_refs": [] if not request.get("banner") else [request["banner"]["banner_ref"]],
            "filter_refs": [item["filter_ref"] for item in request.get("filters", ())],
            "web_included": True, "excel_included": True, "display_decimals": 6})
    manifest = package.manifest
    project = package.project
    return {"schema_version": "EXPLORA_PROJECT_SPEC_V1",
        "project": {"project_id": package.project["project_id"],
                    "display_name": project.get("internal_project_name", package.project["project_id"]),
                    "project_version": package.package_version, "spec_version": "1.0.0"},
        "dataset": {"source_id": Path(source_path).name, "input_type": "SAV",
                    "fingerprint": f"sha256:{source_sha}", "respondent_id_variable": "key",
                    "duplicate_row_policy": "FAIL",
                    "variables": [{"variable_id": name, "source_name": name,
                                   "data_type": "STRING" if name == "key" else "NUMBER", "missing_values": []}
                                  for name in sorted(required_variables)]},
        "source_metadata_fingerprints": [f"sha256:{manifest['questionnaire_sha256']}",
                                         f"sha256:{sha256_file(package_path).upper()}"],
        "questions": questions, "universes": universes, "weights": [], "default_weight_ref": None,
        "banners": banners, "filters": filters, "significance_requests": significance,
        "derived_variables": [], "output_requests": outputs, "ambiguities": [],
        "ai_interpretations": [{"decision_id": manifest["human_decision_id"],
            "source_evidence": "released Benchmark A package and questionnaire fingerprint",
            "proposed_interpretation": "released project configuration", "confidence": 1.0,
            "human_approval_required": True, "release_state": "HUMAN_APPROVED",
            "final_accepted_value": manifest["spec_hash"], "provenance": "B3_V1"}],
        "provenance": {"created_at": manifest["released_at"], "created_by": manifest["human_decision_id"],
            "source_refs": [Path(source_path).name, package.package_id, manifest["human_decision_id"]],
            "b1_policy_ref": "B1_V1", "b2_policy_ref": "B2_V1", "b3_policy_ref": "B3_V1"}}


def produce_release(binding: ProjectExecutionBinding, execution: Any, *, master_path: str | Path,
                    qualification_path: str | Path, dynamic_qualification_path: str | Path,
                    output_root: str | Path) -> ProductiveReleaseEvidence:
    root = Path(output_root)
    for name in ("canonical", "web", "excel", "qa", "provenance"):
        (root / name).mkdir(parents=True, exist_ok=True)
    canonical = {request_id: to_canonical_data(execution.results[request_id]) for request_id in binding.request_ids}
    (root / "canonical" / "canonical_results.json").write_text(
        json.dumps(canonical, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    web_payload: dict[str, Any] = {}
    web_estimates: dict[tuple[str, str], Any] = {}
    for request_id in binding.request_ids:
        projection = project_canonical_result(execution.results[request_id], presentation_identity="GATE44")
        cells = [{key: value for key, value in asdict(cell).items()} for cell in projection.cells]
        web_payload[request_id] = {"authority": projection.authority, "adapter_version": projection.adapter_version,
                                  "result_run_id": projection.result_run_id,
                                  "result_fingerprint": projection.result_fingerprint, "cells": cells}
        web_estimates.update({(request_id, cell.value_id): cell.estimate for cell in projection.cells})
    (root / "web" / "canonical_web_output.json").write_text(
        json.dumps(web_payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    master = Path(master_path)
    qualified = load_qualified_master(qualification_path, master)
    fixed_result = execution.results["BA-01"]
    fixed_request = benchmark_a_request(qualified, fixed_result)
    fixed_plan = plan_render(fixed_request, master)
    fixed_output = root / "excel" / "FUNSMX_297140_FIXED.xlsm"
    render(fixed_request, master, fixed_output, plan=fixed_plan)
    fixed_write = next(item for item in fixed_plan.writes if item.slot_id == "benchmark_result" and item.field_name == "estimate")
    fixed_readback = _cell(fixed_output, fixed_write.sheet, fixed_write.cell)
    expected_fixed = next(item.estimate for item in fixed_result.values if item.value_id == fixed_write.record_id)

    # Productive proportions contain more than 15 safe decimal digits. The
    # qualified Dynamic Result region requires PROPORTION, so Gate 44 records it
    # as NOT_EXERCISED rather than round or weaken the accepted fail-closed rule.
    del dynamic_qualification_path
    canonical_excel_exact = fixed_readback == expected_fixed
    canonical_web_exact = all(web_estimates[(request_id, item.value_id)] == item.estimate
                              for request_id, result in execution.results.items() for item in result.values)
    web_excel_exact = web_estimates[("BA-01", fixed_write.record_id)] == fixed_readback
    if not (canonical_web_exact and canonical_excel_exact and web_excel_exact):
        raise ValueError("productive parity failure")
    evidence = ProductiveReleaseEvidence(binding.project_id, GATE44_RUNNER_VERSION,
        binding.binding_fingerprint, execution.runtime.fingerprint,
        tuple((key, execution.results[key].result_fingerprint or "") for key in binding.request_ids),
        logical_fingerprint(web_payload), fixed_plan.plan_sha256, "NOT_EXERCISED",
        logical_fingerprint({"record_id": fixed_write.record_id, "value": fixed_readback}),
        "NOT_EXERCISED", sha256_file(master), vba_sha256(fixed_output),
        canonical_web_exact, canonical_excel_exact, web_excel_exact)
    if evidence.vba_sha256 != vba_sha256(master):
        raise ValueError("VBA preservation failure")
    (root / "qa" / "parity.json").write_text(json.dumps(asdict(evidence), indent=2) + "\n", encoding="utf-8")
    (root / "provenance" / "release_provenance.json").write_text(
        json.dumps({**asdict(evidence), "fixed_output_sha256": sha256_file(fixed_output),
                    "dynamic_output_sha256": "NOT_EXERCISED"}, indent=2) + "\n", encoding="utf-8")
    return evidence


def _cell(path: Path, sheet: str, cell: str) -> Any:
    workbook = load_workbook(path, keep_vba=True, data_only=False)
    try:
        return workbook[sheet][cell].value
    finally:
        workbook.close()
        if workbook.vba_archive:
            workbook.vba_archive.close()
