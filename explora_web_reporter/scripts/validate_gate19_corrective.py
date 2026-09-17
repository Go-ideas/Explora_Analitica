"""Reproduce productive comparisons from a released package and external source."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics_core.runner import generate_report
from src.canonical_materialization.legacy_bridge import legacy_identity_bridge
from src.canonical_materialization.orchestrator import run_canonical_project
from src.readers.spss_reader import read_spss
from src.builder.analytic_db_builder import build_analytic_database


BASELINE = "e465457d7e6e23d13bea8d43955c1a84790f5d65"
PACKAGE_SHA = "78AFA38484DC4B27FDD0AB5C3F8F2B80B2B49CABC67A57361B94BEB591685A41"
SOURCE_SHA = "71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F"
RUNTIME_FP = "eece0a4dec84266136033907b99b64b04d49428ff8c2d73846e4e36e910f5360"
REQUEST_IDS = ("BA-01", "BA-02", "BA-03", "BA-04", "BA-05")


def datamap_from_package(runtime):
    rows = []
    for structure in runtime.package.structures:
        bindings = structure.get("option_bindings", structure.get("variable_bindings", ()))
        for binding in bindings:
            rows.append({"variable": binding["variable_ref"], "pregunta_id": structure["question_id"], "texto_pregunta": structure["question_id"], "label": binding.get("label", binding["variable_ref"]), "tipo_pregunta": structure["structure_type"], "clasificacion_analitica": "Pregunta analizable", "tipo_calculo": "% respondentes" if structure["structure_type"] == "RM" else "Frecuencia", "usar_en_dashboard": True, "es_banner": False, "es_filtro": False, "es_ponderador": False})
    for kind, flag in (("filters", "es_filtro"), ("banners", "es_banner")):
        for spec in runtime.package.banner_filters[kind]:
            variable = spec["physical_variable_ref"]
            rows.append({"variable": variable, "pregunta_id": variable, "texto_pregunta": variable, "label": variable, "tipo_pregunta": "RU", "clasificacion_analitica": "Pregunta analizable", "tipo_calculo": "Frecuencia", "usar_en_dashboard": False, "es_banner": flag == "es_banner", "es_filtro": flag == "es_filtro", "es_ponderador": False})
    return pd.DataFrame(rows)


def execute(source, package):
    execution = run_canonical_project(source_path=source, package_path=package, request_ids=REQUEST_IDS, expected_source_sha256=SOURCE_SHA, expected_package_sha256=PACKAGE_SHA, expected_runtime_fingerprint=RUNTIME_FP)
    frame, metadata, _ = read_spss(source)
    runtime = execution.runtime
    reports = {}
    with tempfile.TemporaryDirectory(prefix="gate19-") as directory:
        db_path = Path(directory) / "legacy.db"
        datamap = datamap_from_package(runtime)
        build_analytic_database(frame, metadata, datamap, {}, db_path=db_path, export_revision=False)
        for request_id in REQUEST_IDS:
            result = execution.results[request_id]
            released = next(r for r in runtime.package.requests["requests"] if r["request_id"] == request_id)
            filters = {}
            for item in released.get("filters", ()):
                spec = next(s for s in runtime.package.banner_filters["filters"] if s["filter_id"] == item["filter_ref"])
                filters[spec["physical_variable_ref"]] = [m["raw_value"] for m in spec["members"] if m["member_id"] in item["member_ids"]]
            banner = None
            if released.get("banner"):
                spec = next(s for s in runtime.package.banner_filters["banners"] if s["banner_id"] == released["banner"]["banner_ref"])
                banner = spec["physical_variable_ref"]
            snapshot = result.request
            bridge = legacy_identity_bridge(runtime, request_id)
            try:
                output = generate_report(db_path, released["question_ref"], mode="DUAL_RUN", canonical_result=result, legacy_identity_bridge=bridge, canonical_metric_refs=snapshot.metric_refs, canonical_filters=snapshot.filters, canonical_banner_config=snapshot.banner_config, canonical_execution_options=snapshot.execution_options, request_fingerprint=snapshot.request_fingerprint, filters=filters, banner=banner)
                items = [asdict(item) for item in output.comparison.items]
                reports[request_id] = {"status": "PASS" if output.aggregate_comparison_status == "PASS" and items else "FAIL", "aggregate_status": output.aggregate_comparison_status, "comparable_records": sum(i.legacy_value is not None and i.canonical_value is not None for i in output.comparison.items), "limitations": output.limitations, "request": asdict(execution.requests[request_id]), "identity_bridge": asdict(bridge), "canonical_result": asdict(result), "legacy_summary": output.legacy_result.summary.to_dict(orient="records"), "legacy_identity_rows": output.legacy_result.identity_rows.to_dict(orient="records"), "comparisons": items}
            except Exception as exc:
                reports[request_id] = {"status": "FAIL", "error": str(exc), "exception": type(exc).__name__}
    return {"runtime_fingerprint": runtime.fingerprint, "project_id": runtime.project_id, "dataset_sha256": runtime.source_fingerprint, "materialized_configuration": asdict(runtime.package), "legacy_datamap": datamap.to_dict(orient="records"), "requests": reports}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--regression-report", type=Path)
    args = parser.parse_args()
    if args.evidence.exists():
        raise SystemExit("Evidence destination already exists; preserve historical runs")
    first = execute(args.source, args.package)
    second = execute(args.source, args.package)
    deterministic = json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    counts = Counter(item["classification"] for report in first["requests"].values() for item in report.get("comparisons", ()))
    evidence = {"baseline_sha": BASELINE, "corrective_head_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "package_sha256": PACKAGE_SHA, "determinism": "PASS" if deterministic else "FAIL", "provenance": "COMPLETE" if all(r["status"] == "PASS" for r in first["requests"].values()) else "INCOMPLETE", "comparison_classifications": counts, "comparable_record_count": sum(r.get("comparable_records", 0) for r in first["requests"].values()), "ba03_resolved_identity": "MENTION / PARENT_RM / STR_Q_DELIVERY_APPS_RM_V1", "regression_counts": {}, "modified_files": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(), **first}
    evidence["blocker_resolution_status"] = {"B-G19-01": "RESOLVED" if all(first["requests"][key]["status"] == "PASS" for key in REQUEST_IDS) else "NOT RESOLVED", "B-G19-02": "RESOLVED" if first["requests"]["BA-04"]["status"] == "PASS" else "NOT RESOLVED", "B-G19-03": "RESOLVED" if first["requests"]["BA-05"]["status"] == "PASS" else "NOT RESOLVED"}
    evidence["difference_classifications"] = {"NONE": counts.get("PARITY", 0), "EXPECTED REPRESENTATIONAL DIFFERENCE": counts.get("PRESENTATION_ONLY", 0), "EXPECTED CONTRACTUAL DIFFERENCE": sum(counts.get(key, 0) for key in ("INTENDED_CORRECTION", "M2_BASE_DIFFERENCE", "M3_WEIGHT_DIFFERENCE", "M4_STRUCTURE_DIFFERENCE")), "UNEXPECTED NUMERICAL DELTA": counts.get("POTENTIAL_REGRESSION", 0), "UNEXPECTED STRUCTURAL DELTA": sum(bool(r.get("limitations") or r.get("error")) for r in first["requests"].values())}
    evidence["changed_files_from_baseline"] = subprocess.check_output(["git", "diff", "--name-status", BASELINE, "HEAD"], text=True).splitlines()
    evidence["worktree_status"] = evidence.pop("modified_files")
    evidence["modified_files"] = [line.split("\t")[-1] for line in evidence["changed_files_from_baseline"] if line.startswith("M\t")]
    evidence["added_files"] = [line.split("\t")[-1] for line in evidence["changed_files_from_baseline"] if line.startswith("A\t")]
    regression_ok = True
    if args.regression_report:
        modules = {}
        totals = Counter()
        for case in ET.parse(args.regression_report).iter("testcase"):
            module = case.attrib["classname"]
            outcome = "failed" if case.find("failure") is not None or case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
            modules.setdefault(module, Counter())[outcome] += 1
            totals[outcome] += 1
        evidence["regression_counts"] = {"full": {k: totals[k] for k in ("passed", "failed", "skipped")}, "modules": {m: {k: c[k] for k in ("passed", "failed", "skipped")} for m, c in modules.items()}}
        regression_ok = totals["passed"] > 0 and totals["failed"] == 0 and totals["skipped"] == 0
    ba03 = first["requests"]["BA-03"].get("canonical_result", {})
    resolved = set()
    for base in ba03.get("bases", ()):
        refs = base["provenance_refs"]
        scope = [r.split(":", 1)[1] for r in refs if r.startswith("m4_resolved_scope_type:")]
        scope_ref = [r.split(":", 1)[1] for r in refs if r.startswith("m4_resolved_scope_ref:")]
        if len(scope) == len(scope_ref) == 1:
            resolved.add(f"{str(base['denominator_unit']).upper()} / {scope[0]} / {scope_ref[0]}")
    evidence["ba03_resolved_identity"] = next(iter(resolved)) if len(resolved) == 1 else "UNRESOLVED / AMBIGUOUS"
    successful = regression_ok and deterministic and all(r["status"] == "PASS" for r in first["requests"].values()) and evidence["ba03_resolved_identity"] == "MENTION / PARENT_RM / STR_Q_DELIVERY_APPS_RM_V1"
    evidence["status"] = "PASS" if successful else "FAIL"
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"requests": {key: {k: v for k, v in report.items() if k in {"status", "aggregate_status", "comparable_records", "limitations", "error"}} for key, report in first["requests"].items()}, "determinism": evidence["determinism"], "comparable_record_count": evidence["comparable_record_count"], "classifications": counts}, indent=2))
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
