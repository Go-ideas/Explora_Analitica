from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import run_gate44_productive_e2e
from src.project_intake import ProjectCompilationError, compile_project_spec, validate_project
from src.project_intake.productive import GATE44_RUNNER_VERSION


ROOT = Path(__file__).parents[1]
RELEASE = ROOT / "evidence" / "gate44" / "FUNSMX_297140"
SOURCE_SHA = "71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F"
PACKAGE_SHA = "78AFA38484DC4B27FDD0AB5C3F8F2B80B2B49CABC67A57361B94BEB591685A41"
MASTER_SHA = "f3a11f291b6c661f0c937e9c95d7f227c351d7261b2e01aa44dfd4167d5c869c"
VBA_SHA = "0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758"


def load(relative: str) -> dict:
    return json.loads((RELEASE / relative).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def artifacts() -> dict:
    return {
        "spec": load("config/project_spec.json"),
        "binding": load("canonical/execution_binding.json"),
        "canonical": load("canonical/canonical_results.json"),
        "web": load("web/canonical_web_output.json"),
        "parity": load("qa/parity.json"),
        "summary": load("qa/gate44_summary.json"),
        "provenance": load("provenance/release_provenance.json"),
    }


def test_g44_01_authoritative_source_identity(artifacts: dict) -> None:
    assert artifacts["binding"]["source_sha256"] == SOURCE_SHA
    assert artifacts["binding"]["package_sha256"] == PACKAGE_SHA


def test_g44_02_project_spec_validation(artifacts: dict) -> None:
    result = validate_project(artifacts["spec"])
    assert result.validation_status == "READY_FOR_EXECUTION"
    assert result.project_spec_fingerprint == artifacts["summary"]["project_spec_fingerprint"]


def test_g44_03_ready_for_execution_is_enforced(artifacts: dict, tmp_path: Path) -> None:
    spec = deepcopy(artifacts["spec"])
    spec["ambiguities"] = [{"ambiguity_id": "A", "severity": "BLOCKING", "description": "unresolved", "status": "OPEN"}]
    with pytest.raises(ProjectCompilationError, match="not READY_FOR_EXECUTION"):
        compile_project_spec(spec, source_path=tmp_path / "missing.sav", package_path=tmp_path / "missing.zip")


def test_g44_04_compilation_is_deterministic(artifacts: dict) -> None:
    binding = artifacts["binding"]
    assert binding["binding_fingerprint"] == artifacts["summary"]["binding"]["binding_fingerprint"]


def test_g44_05_unsupported_compilation_fails_closed(artifacts: dict, tmp_path: Path) -> None:
    spec = deepcopy(artifacts["spec"])
    spec["questions"][0]["question_type"] = "FREE_TEXT_AI"
    with pytest.raises(ProjectCompilationError, match="not READY_FOR_EXECUTION"):
        compile_project_spec(spec, source_path=tmp_path / "missing.sav", package_path=tmp_path / "missing.zip")


def test_g44_06_core_used_canonical_v1(artifacts: dict) -> None:
    assert artifacts["binding"]["execution_mode"] == "CANONICAL_V1"


def test_g44_07_no_legacy_fallback(artifacts: dict) -> None:
    assert artifacts["summary"]["legacy_fallback"] is False


def test_g44_08_canonical_materialization_identity(artifacts: dict) -> None:
    assert artifacts["parity"]["runtime_fingerprint"] == "eece0a4dec84266136033907b99b64b04d49428ff8c2d73846e4e36e910f5360"


def test_g44_09_canonical_results_are_authority(artifacts: dict) -> None:
    expected = dict(artifacts["parity"]["canonical_result_fingerprints"])
    assert set(expected) == set(artifacts["canonical"]) == {"BA-01", "BA-02", "BA-03", "BA-04", "BA-05"}
    assert all(result["result_fingerprint"] == expected[key] for key, result in artifacts["canonical"].items())


def test_g44_10_web_consumes_canonical_results(artifacts: dict) -> None:
    expected = dict(artifacts["parity"]["canonical_result_fingerprints"])
    assert all(output["authority"] == "CANONICAL_V1" for output in artifacts["web"].values())
    assert all(output["result_fingerprint"] == expected[key] for key, output in artifacts["web"].items())


def test_g44_11_excel_consumes_canonical_result(artifacts: dict) -> None:
    assert artifacts["parity"]["fixed_plan_fingerprint"] != "NOT_EXERCISED"
    assert (RELEASE / "excel" / "FUNSMX_297140_FIXED.xlsm").is_file()


def test_g44_12_production_master_identity(artifacts: dict) -> None:
    assert artifacts["parity"]["production_master_sha256"] == MASTER_SHA


def test_g44_13_vba_is_preserved_exactly(artifacts: dict) -> None:
    assert artifacts["parity"]["vba_sha256"] == VBA_SHA


def test_g44_14_dynamic_region_is_truthfully_not_exercised(artifacts: dict) -> None:
    assert artifacts["parity"]["dynamic_plan_fingerprint"] == "NOT_EXERCISED"
    assert artifacts["parity"]["dynamic_readback_fingerprint"] == "NOT_EXERCISED"


def test_g44_15_significance_is_truthfully_not_exercised(artifacts: dict) -> None:
    assert artifacts["binding"]["significance_ids"] == ["SIG_Q_UE_CON_POST_VERY_PROB_BY_SEGMENT_V1"]
    assert all(not result["comparisons"] and not result["significance_records"] for result in artifacts["canonical"].values())


def test_g44_16_canonical_web_parity(artifacts: dict) -> None:
    assert artifacts["parity"]["canonical_web_exact"] is True


def test_g44_17_canonical_excel_parity(artifacts: dict) -> None:
    assert artifacts["parity"]["canonical_excel_exact"] is True


def test_g44_18_web_excel_parity(artifacts: dict) -> None:
    assert artifacts["parity"]["web_excel_exact"] is True


def test_g44_19_provenance_is_complete(artifacts: dict) -> None:
    required = {"binding_fingerprint", "runtime_fingerprint", "canonical_result_fingerprints",
                "web_logical_fingerprint", "fixed_plan_fingerprint", "production_master_sha256", "vba_sha256"}
    assert required <= set(artifacts["provenance"])


def test_g44_20_rerun_is_deterministic(artifacts: dict) -> None:
    assert artifacts["summary"]["deterministic_rerun"] is True


def test_g44_21_failed_execution_creates_no_release(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "release"

    def fail_after_partial_write(_input: Path, staging: Path) -> dict:
        staging.mkdir(parents=True)
        (staging / "partial.json").write_text("{}", encoding="utf-8")
        raise RuntimeError("controlled failure")

    monkeypatch.setattr(run_gate44_productive_e2e, "_build_release", fail_after_partial_write)
    with pytest.raises(RuntimeError, match="controlled failure"):
        run_gate44_productive_e2e.run(tmp_path, output)
    assert not output.exists()


def test_g44_22_b1_b2_b3_authority_is_preserved(artifacts: dict) -> None:
    assert artifacts["binding"]["policy_refs"] == ["B1_V1", "B2_V1", "B3_V1"]


def test_g44_23_protected_semantics_are_unchanged() -> None:
    assert GATE44_RUNNER_VERSION == "GATE44_PRODUCTIVE_E2E_V1"
    compiler = (ROOT / "src" / "project_intake" / "compiler.py").read_text(encoding="utf-8")
    assert "analytics_core" not in compiler and "percentage" not in compiler


def test_g44_24_release_package_is_complete(artifacts: dict) -> None:
    required = {
        "config/project_spec.json", "canonical/execution_binding.json", "canonical/canonical_results.json",
        "web/canonical_web_output.json", "excel/FUNSMX_297140_FIXED.xlsm", "qa/parity.json",
        "qa/gate44_summary.json", "provenance/release_provenance.json",
    }
    assert required <= {path.relative_to(RELEASE).as_posix() for path in RELEASE.rglob("*") if path.is_file()}
    assert artifacts["summary"]["customer_raw_data_added_to_git"] is False
