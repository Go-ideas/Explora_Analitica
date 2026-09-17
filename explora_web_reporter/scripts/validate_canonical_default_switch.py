"""Validate the default switch against accepted external Benchmark A inputs."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_gate19_corrective import (
    PACKAGE_SHA, SOURCE_SHA, RUNTIME_FP, REQUEST_IDS, execute,
)
from src.analytics_core.mode import ANALYTICS_ENGINE_ENV_VAR, resolve_execution_mode
from src.analytics_core.runner import generate_report
from src.builder.analytic_db_builder import build_analytic_database
from src.canonical_materialization.orchestrator import run_canonical_project
from src.readers.spss_reader import read_spss


BASELINE_SHA = "6c0bf08895603b2b80b6a3c5fb5e1fea744b9d30"


def execute_switch(source: Path, package: Path) -> dict:
    dual = execute(source, package)
    canonical = run_canonical_project(
        source_path=source, package_path=package, request_ids=REQUEST_IDS,
        expected_source_sha256=SOURCE_SHA, expected_package_sha256=PACKAGE_SHA,
        expected_runtime_fingerprint=RUNTIME_FP,
    )
    frame, metadata, _ = read_spss(source)
    reports = {}
    with tempfile.TemporaryDirectory(prefix="gate32-") as directory:
        db = Path(directory) / "legacy.db"
        build_analytic_database(
            frame, metadata, pd.DataFrame(dual["legacy_datamap"]), {},
            db_path=db, export_revision=False,
        )
        for request_id in REQUEST_IDS:
            candidate = canonical.results[request_id]
            snapshot = candidate.request
            options = {
                "canonical_result": candidate,
                "canonical_metric_refs": snapshot.metric_refs,
                "canonical_filters": snapshot.filters,
                "canonical_banner_config": snapshot.banner_config,
                "canonical_execution_options": snapshot.execution_options,
                "request_fingerprint": snapshot.request_fingerprint,
                "weight_override": snapshot.weight_override,
            }
            question = snapshot.question_ids[0]
            before = asdict(candidate)
            implicit = generate_report(db, question, **options)
            explicit = generate_report(db, question, mode="CANONICAL", **options)
            # Use the actual Legacy settings retained by productive DUAL_RUN.
            first_record = dual["requests"][request_id]["comparisons"][0]["legacy_value"]
            provenance = first_record["provenance"]
            legacy = generate_report(
                db, question, mode="LEGACY", filters=provenance["legacy_filters"],
                banner=provenance["legacy_banner"],
            )
            matches = implicit is explicit is candidate and asdict(candidate) == before
            legacy_matches = legacy.summary.equals(pd.DataFrame(dual["requests"][request_id]["legacy_summary"]))
            reports[request_id] = {
                "status": "PASS" if matches and legacy_matches and dual["requests"][request_id]["status"] == "PASS" else "FAIL",
                "implicit_requested_runtime": None,
                "implicit_resolved_runtime": resolve_execution_mode().value,
                "explicit_requested_runtime": "CANONICAL",
                "explicit_resolved_runtime": resolve_execution_mode("CANONICAL").value,
                "default_matches_explicit": matches,
                "legacy_requested_runtime": "LEGACY",
                "legacy_resolved_runtime": resolve_execution_mode("LEGACY").value,
                "legacy_matches_dual_run": legacy_matches,
                "result_run_id": candidate.result_run_id,
                "result_fingerprint": candidate.result_fingerprint,
                "request_fingerprint": snapshot.request_fingerprint,
                "project_id": candidate.project_id,
                "dataset_fingerprint": candidate.dataset_fingerprint,
                "legacy_summary": legacy.summary.to_dict(orient="records"),
            }
    return {"default_resolved_runtime": resolve_execution_mode().value, "runtime_switch_results": reports, "gate19_comparison": dual}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    if args.evidence.exists():
        raise SystemExit("Evidence already exists; preserve previous executions")
    first = execute_switch(args.source, args.package)
    second = execute_switch(args.source, args.package)
    deterministic = json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)
    passed = deterministic and first["default_resolved_runtime"] == "CANONICAL_V1" and all(r["status"] == "PASS" for r in first["runtime_switch_results"].values())
    evidence = {
        "baseline_sha": BASELINE_SHA,
        "head_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "status": "PASS" if passed else "FAIL",
        "determinism": "PASS" if deterministic else "FAIL",
        "environment_selector_name": ANALYTICS_ENGINE_ENV_VAR,
        "package_sha256": PACKAGE_SHA,
        "source_sha256": SOURCE_SHA,
        "runtime_fingerprint": RUNTIME_FP,
        "worktree_status": subprocess.check_output(["git", "status", "--short"], text=True).splitlines(),
        **first,
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"status": evidence["status"], "default": first["default_resolved_runtime"], "determinism": evidence["determinism"], "requests": {key: report["status"] for key, report in first["runtime_switch_results"].items()}}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
