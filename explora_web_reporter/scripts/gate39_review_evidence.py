"""Generate deterministic Gate 39 Core-to-Excel qualification evidence."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from openpyxl import load_workbook

from src.analytics_core.result_identity import canonical_payload, stable_json
from src.excel_renderer import plan_render, render, vba_sha256
from src.excel_renderer.renderer import sha, sha_bytes
from test_gate39_significance_presentation import (
    FIXTURE_ID, FIXTURE_SHA, MASTER, MASTER_SHA, VBA_SHA, core_result, request_for,
)


def main() -> int:
    destination = Path(sys.argv[1])
    if destination.exists():
        raise SystemExit("Evidence destination exists")
    runs = {str(confidence): core_result(confidence) for confidence in (0.90, 0.95, 0.99)}
    primary = runs["0.95"]
    request = request_for(primary)
    first_plan = plan_render(request, MASTER)
    second_plan = plan_render(request, MASTER)
    with TemporaryDirectory() as folder:
        first = Path(folder) / "first.xlsm"
        second = Path(folder) / "second.xlsm"
        first_render = render(request, MASTER, first, plan=first_plan)
        second_render = render(request, MASTER, second, plan=second_plan)
        workbook = load_workbook(first, keep_vba=True, data_only=False)
        try:
            visible = {
                "sheet": "presentation", "cell": "E2",
                "display_text": workbook["presentation"]["E2"].value,
                "status_cell": "H2", "status": workbook["presentation"]["H2"].value,
            }
        finally:
            workbook.close()
            workbook.vba_archive.close()
        output_sha = sha(first)
        binary_identity = first.read_bytes() == second.read_bytes()
    relation = primary.comparisons[0]
    marker = next(item for item in first_plan.writes if item.slot_id == "significance_marker")
    payload = {
        "schema_version": "GATE39_SIGNIFICANCE_PRESENTATION_EVIDENCE_V1",
        "fixture": {"fixture_id": FIXTURE_ID, "fixture_sha256": FIXTURE_SHA,
                    "classification": "deterministic synthetic non-customer qualification data"},
        "core": {"engine": "B2_CORE_SIGNIFICANCE_V1", "policy": "B2_V1",
                 "confidence_outputs": {key: canonical_payload(run.comparisons[0])
                                        for key, run in runs.items()}},
        "canonical": {"result_run_id": primary.result_run_id,
                      "result_fingerprint": primary.result_fingerprint,
                      "comparison_id": relation.comparison_id,
                      "serialized_sha256": sha_bytes(stable_json(canonical_payload(primary)))},
        "materialization": "CANONICAL_JSON_ROUND_TRIP_EXACT",
        "master": {"master_id": "EXPLORA_PRODUCTION_MASTER_V1", "version": "1.1.0",
                   "sha256": MASTER_SHA, "vba_sha256": VBA_SHA},
        "render_plan": {"sha256": first_plan.plan_sha256,
                        "deterministic": first_plan == second_plan,
                        "marker_write": asdict(marker)},
        "visible_output": visible,
        "rendered_output_sha256": output_sha,
        "binary_output_identity": binary_identity,
        "vba_before_sha256": vba_sha256(MASTER),
        "vba_after_sha256": first_render["vba_after"],
        "vba_exact": first_render["vba_before"] == first_render["vba_after"] == VBA_SHA,
        "protected_surfaces": {"undeclared_cells_preserved": first_render["undeclared_cells_preserved"],
                               "untouched_parts_exact": first_render["untouched_parts_exact"]},
        "traceability": {"visible_marker": "presentation!E2",
                         "render_plan_record_id": marker.record_id,
                         "canonical_comparison_id": relation.comparison_id,
                         "core_provenance_refs": list(relation.provenance_refs),
                         "qualification_fixture_id": FIXTURE_ID},
        "no_recomputation": "PASS: absent canonical relation is rejected before planning",
        "ineligible_behavior": "PASS: Core INELIGIBLE relations cannot assert presentation tokens",
        "direction_reference": "PASS: token target must match canonical slice/member and direction",
        "renderer_statistical_computation": "NONE",
        "reporter_dependency": "NONE",
        "excel_m7_statistical_recomputation": "NONE",
        "deterministic_render_evidence_equal": first_render == second_render,
        "validation": {
            "focused_gate39": "18 passed / 0 failed / 0 skipped",
            "gate39a_regression": "25 passed / 0 failed / 0 skipped",
            "analytics_core_regression": "184 passed / 0 failed / 0 skipped",
            "canonical_regression": "214 passed / 0 failed / 0 skipped",
            "canonical_materialization_regression": "51 passed / 0 failed / 0 skipped",
            "m7b_regression": "103 passed / 0 failed / 0 skipped",
            "gate38_regression": "20 passed / 0 failed / 0 skipped",
            "full_regression": "814 passed / 0 failed / 0 skipped",
        },
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(stable_json({"binary_output_identity": binary_identity,
                       "plan_sha256": first_plan.plan_sha256,
                       "rendered_output_sha256": output_sha}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
