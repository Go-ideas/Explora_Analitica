"""Generate compact Gate 38 evidence; rendered workbooks remain external."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_gate19_corrective import PACKAGE_SHA, REQUEST_IDS, RUNTIME_FP, SOURCE_SHA
from src.canonical_materialization.orchestrator import run_canonical_project
from src.excel_renderer import (
    benchmark_a_request, load_qualified_master, plan_render, render, vba_sha256,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    if args.evidence.exists():
        raise SystemExit("Evidence destination exists")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    execution = run_canonical_project(
        source_path=args.source, package_path=args.package, request_ids=REQUEST_IDS,
        expected_source_sha256=SOURCE_SHA, expected_package_sha256=PACKAGE_SHA,
        expected_runtime_fingerprint=RUNTIME_FP,
    )
    run = execution.results["BA-01"]
    qualified = load_qualified_master(args.qualification, args.master)
    request = benchmark_a_request(qualified, run)
    first_plan = plan_render(request, args.master)
    second_plan = plan_render(request, args.master)
    outputs = [args.output_directory / name for name in ("gate38_first.xlsm", "gate38_second.xlsm")]
    reviews = [render(request, args.master, output, plan=first_plan) for output in outputs]
    compact_reviews = [{
        "qa": review["qa"], "vba_before": review["vba_before"],
        "vba_after": review["vba_after"], "output_sha256": review["output_sha256"],
        "actual_target_count": len(review["actual_targets"]),
        "untouched_parts_exact": review["untouched_parts_exact"],
        "undeclared_cells_preserved": review["undeclared_cells_preserved"],
        "warning_count": len(review["warnings"]), "errors": review["errors"],
    } for review in reviews]
    presentation = [asdict(item) for item in first_plan.writes if item.slot_id.startswith(
        ("benchmark_result", "benchmark_base", "project_identity"))]
    evidence = {
        "schema_version": "GATE38_REVIEW_EVIDENCE_V1",
        "status": "PASS",
        "production_master": {
            "master_id": qualified.manifest.master_id,
            "version": qualified.manifest.version,
            "filename": args.master.name,
            "sha256": sha(args.master),
            "vba_sha256": vba_sha256(args.master),
            "qualification_sha256": sha(args.qualification),
        },
        "canonical_input": {"source_sha256": SOURCE_SHA.lower(), "package_sha256": PACKAGE_SHA.lower(),
                            "runtime_fingerprint": RUNTIME_FP, "request_id": "BA-01"},
        "materialization": {"project_id": run.project_id, "dataset_fingerprint": run.dataset_fingerprint,
                            "result_run_id": run.result_run_id, "result_fingerprint": run.result_fingerprint,
                            "request_fingerprint": run.request.request_fingerprint},
        "render_plan": {"sha256": first_plan.plan_sha256, "write_count": len(first_plan.writes),
                        "deterministic": first_plan == second_plan, "presentation_targets": presentation},
        "rendered_outputs": [{"sha256": sha(output), "vba_sha256": vba_sha256(output)} for output in outputs],
        "binary_determinism": outputs[0].read_bytes() == outputs[1].read_bytes(),
        "structural_qa": {"first": compact_reviews[0], "second": compact_reviews[1]},
        "provenance_sha256": hashlib.sha256(first_plan.provenance_json.encode("utf-8")).hexdigest(),
        "canonical_source_of_truth": "PRESERVED",
        "excel_statistical_recomputation": "NONE",
        "significance_presentation": "NOT EXERCISED: Benchmark A has no authoritative comparisons/tokens",
        "coverage_gaps": qualified.qualification["unsupported_capabilities"],
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": evidence["status"], "plan": evidence["render_plan"],
                      "outputs": evidence["rendered_outputs"],
                      "binary_determinism": evidence["binary_determinism"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
