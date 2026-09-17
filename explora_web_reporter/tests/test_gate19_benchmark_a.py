import json
from pathlib import Path

import pytest

from scripts.validate_gate19_corrective import execute


@pytest.fixture(scope="module")
def productive_evidence():
    inputs = Path(__file__).resolve().parents[3] / "_gate19_inputs" / "benchmark_a"
    source = inputs / "FUNSMX_297140_20260914.sav"
    package = inputs / "BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip"
    return execute(source, package), execute(source, package)


@pytest.mark.parametrize("request_id", ["BA-01", "BA-02", "BA-03", "BA-04", "BA-05"])
def test_productive_benchmark_comparison(productive_evidence, request_id):
    report = productive_evidence[0]["requests"][request_id]
    assert report["status"] == "PASS", report.get("limitations", report.get("error"))
    assert report["comparable_records"] > 0
    assert report["comparable_records"] == len(report["canonical_result"]["values"])
    assert all(item["classification"] == "PARITY" for item in report["comparisons"])


def test_ba03_parent_mention_identity(productive_evidence):
    result = productive_evidence[0]["requests"]["BA-03"]["canonical_result"]
    for base in result["bases"]:
        assert base["denominator_unit"] == "mention"
        assert "m4_resolved_scope_type:PARENT_RM" in base["provenance_refs"]
        assert "m4_resolved_scope_ref:STR_Q_DELIVERY_APPS_RM_V1" in base["provenance_refs"]


def test_productive_comparison_determinism(productive_evidence):
    assert json.dumps(productive_evidence[0], sort_keys=True, default=str) == json.dumps(productive_evidence[1], sort_keys=True, default=str)


def test_comparison_provenance_reconstructable(productive_evidence):
    evidence = productive_evidence[0]
    assert evidence["dataset_sha256"]
    assert evidence["runtime_fingerprint"]
    assert evidence["materialized_configuration"]
    for report in evidence["requests"].values():
        assert report["request"]["universe_ref"]
        assert report["identity_bridge"]["provenance_refs"]
        for item in report["comparisons"]:
            assert item["semantic_key"]
            assert item["canonical_value"]["source_ref"]
            assert item["legacy_value"]["source_ref"]
            assert item["legacy_value"]["provenance"]["identity_bridge"]
