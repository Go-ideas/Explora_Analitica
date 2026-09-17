import json
from pathlib import Path

import pytest

from scripts.validate_canonical_default_switch import execute_switch


@pytest.fixture(scope="module")
def switch_evidence():
    inputs = Path(__file__).resolve().parents[3] / "_gate19_inputs" / "benchmark_a"
    source = inputs / "FUNSMX_297140_20260914.sav"
    package = inputs / "BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip"
    return execute_switch(source, package), execute_switch(source, package)


@pytest.mark.parametrize("request_id", ["BA-01", "BA-02", "BA-03", "BA-04", "BA-05"])
def test_benchmark_four_runtime_paths(switch_evidence, request_id):
    evidence = switch_evidence[0]
    assert evidence["default_resolved_runtime"] == "CANONICAL_V1"
    report = evidence["runtime_switch_results"][request_id]
    assert report["status"] == "PASS"
    assert report["default_matches_explicit"]
    assert report["legacy_matches_dual_run"]
    assert report["implicit_resolved_runtime"] == report["explicit_resolved_runtime"] == "CANONICAL_V1"
    assert report["legacy_resolved_runtime"] == "LEGACY"


def test_accepted_parity_set_unchanged(switch_evidence):
    reports = switch_evidence[0]["gate19_comparison"]["requests"]
    assert [reports[key]["comparable_records"] for key in reports] == [40, 4, 4, 40, 6]
    items = [item for report in reports.values() for item in report["comparisons"]]
    assert len(items) == 94
    assert all(item["classification"] == "PARITY" for item in items)


def test_ba03_mention_scope_unchanged(switch_evidence):
    result = switch_evidence[0]["gate19_comparison"]["requests"]["BA-03"]["canonical_result"]
    for base in result["bases"]:
        assert base["denominator_unit"] == "mention"
        assert "m4_resolved_scope_type:PARENT_RM" in base["provenance_refs"]
        assert "m4_resolved_scope_ref:STR_Q_DELIVERY_APPS_RM_V1" in base["provenance_refs"]


def test_default_switch_deterministic(switch_evidence):
    assert json.dumps(switch_evidence[0], sort_keys=True, default=str) == json.dumps(switch_evidence[1], sort_keys=True, default=str)


def test_default_switch_provenance(switch_evidence):
    for report in switch_evidence[0]["runtime_switch_results"].values():
        for field in ("implicit_resolved_runtime", "explicit_resolved_runtime", "result_run_id", "result_fingerprint", "request_fingerprint", "project_id", "dataset_fingerprint"):
            assert report[field]
