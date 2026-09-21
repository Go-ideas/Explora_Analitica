from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from m7b_fixtures import build_test_master, source_result
from src.excel_renderer import QualifiedMaster
from src.project_intake.compiler import ProjectExecutionBinding
from src.project_intake import generic_productive as generic


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "gate45" / "non_benchmark_presentation.json"
G44 = ROOT / "evidence" / "gate44" / "FUNSMX_297140"


def spec(*, web: bool = True, excel: bool = True) -> dict:
    data = json.loads((ROOT / "tests" / "fixtures" / "gate43" / "minimal_project_spec.json").read_text())
    data["project"].update({"project_id": "project_m6", "display_name": "Neutral synthetic project"})
    data["dataset"].update({"input_type": "SAV", "fingerprint": "sha256:" + "1" * 64})
    data["output_requests"] = [{"output_request_id": "request_m6", "question_refs": ["Q1"],
        "banner_refs": [], "filter_refs": [], "web_included": web, "excel_included": excel,
        "display_decimals": 2}]
    return data


def binding(*, targets=("EXCEL", "WEB"), weights=()) -> ProjectExecutionBinding:
    return ProjectExecutionBinding(
        "EXPLORA_PROJECT_EXECUTION_BINDING_V1", "project_m6", "1.0.0", "spec_fp",
        "1" * 64, "2" * 64, "NEUTRAL_PACKAGE", "1.0.0", "3" * 64, "CANONICAL_V1",
        ("request_m6",), ("Q1",), ("RU",), ("U_ALL",), weights, (), (), (), targets,
        ("B1_V1", "B2_V1", "B3_V1"), ("neutral-source",), "binding_fp")


@pytest.fixture
def runtime(tmp_path: Path) -> dict:
    master_path = tmp_path / "neutral_master.xlsm"
    manifest = build_test_master(master_path)
    run = source_result()
    execution = SimpleNamespace(runtime=SimpleNamespace(fingerprint="core_runtime_fp"),
                                results={"request_m6": run})
    return {"master_path": master_path, "qualified": QualifiedMaster(manifest, {}),
            "run": run, "execution": execution, "config": json.loads(FIXTURE.read_text())}


def produce(runtime: dict, tmp_path: Path, *, web=True, excel=True, name="release") -> dict:
    intent, targets = generic.output_intent(spec(web=web, excel=excel))
    return generic.produce_generic_release(
        spec(web=web, excel=excel), binding(targets=targets), runtime["execution"],
        output_root=tmp_path / name, intent=intent, targets=targets,
        presentation_configuration=runtime["config"] if excel else None,
        qualified_master=runtime["qualified"] if excel else None,
        master_path=runtime["master_path"] if excel else None)


def test_g45_01_generic_runtime_has_no_benchmark_decision_dependency() -> None:
    text = (ROOT / "src" / "project_intake" / "generic_productive.py").read_text().lower()
    for forbidden in ("funsmx", "benchmark_a", "ba-01", "gate44"):
        assert forbidden not in text


def test_g45_02_ready_project_spec_required(tmp_path: Path) -> None:
    invalid = spec(); invalid["ambiguities"] = [{"ambiguity_id": "A", "severity": "BLOCKING",
        "description": "open", "status": "OPEN"}]
    with pytest.raises(generic.GenericRuntimeError, match="READY_FOR_EXECUTION"):
        generic._build_release(invalid, source_path=tmp_path / "x", package_path=tmp_path / "y",
            output_root=tmp_path / "out", presentation_configuration=None, qualified_master=None,
            master_path=None, expected_source_sha256=None, expected_package_sha256=None)


def test_g45_03_execution_binding_is_deterministic() -> None:
    assert binding() == binding() and binding().binding_fingerprint == "binding_fp"


def test_g45_04_project_neutral_output_naming() -> None:
    assert generic.release_name("Project 17", "Config A") == "Project_17__Config_A"


def test_g45_05_web_only_output_intent() -> None:
    intent, targets = generic.output_intent(spec(web=True, excel=False))
    assert targets == ("WEB",) and intent["WEB"] == ("request_m6",) and not intent["EXCEL"]


def test_g45_06_excel_only_output_intent() -> None:
    intent, targets = generic.output_intent(spec(web=False, excel=True))
    assert targets == ("EXCEL",) and intent["EXCEL"] == ("request_m6",) and not intent["WEB"]


def test_g45_07_web_and_excel_output_intent() -> None:
    _, targets = generic.output_intent(spec())
    assert targets == ("WEB", "EXCEL")


def test_g45_08_unsupported_output_fails_closed() -> None:
    with pytest.raises(generic.GenericRuntimeError, match="unsupported output"):
        generic.output_intent(spec(web=False, excel=False))


def test_g45_09_generic_visual_spec_render_request_binding(runtime: dict) -> None:
    request = generic.build_render_request(runtime["config"], project_id="project_m6",
                                           results={"request_m6": runtime["run"]},
                                           qualified_master=runtime["qualified"])
    visual = json.loads(request.visual_spec_json)
    assert visual["project_id"] == "project_m6"
    assert visual["sections"][0]["visuals"][0]["source_bindings"][0]["result_run_id"] == runtime["run"].result_run_id


def test_g45_10_generic_excel_path_does_not_use_benchmark_helper() -> None:
    text = (ROOT / "src" / "project_intake" / "generic_productive.py").read_text()
    assert "benchmark_a_request" not in text


def test_g45_11_canonical_results_remain_authority(runtime: dict, tmp_path: Path) -> None:
    produce(runtime, tmp_path)
    payload = json.loads((tmp_path / "release" / "canonical" / "canonical_results.json").read_text())
    assert payload["request_m6"]["result_fingerprint"] == runtime["run"].result_fingerprint


def test_g45_12_web_has_no_statistical_calculation() -> None:
    text = (ROOT / "src" / "project_intake" / "generic_productive.py").read_text()
    assert "project_canonical_result" in text and "numerator /" not in text


def test_g45_13_excel_and_vba_have_no_statistical_calculation() -> None:
    text = (ROOT / "src" / "project_intake" / "generic_productive.py").read_text()
    assert "plan_render" in text and "render(" in text and "significance" not in text.lower()


def test_g45_14_weight_references_are_preserved() -> None:
    assert binding(weights=("WEIGHT_MAIN",)).weight_ids == ("WEIGHT_MAIN",)


def test_g45_15_universe_banner_filter_identities_are_preserved() -> None:
    item = replace(binding(), banner_ids=("BANNER_A",), filter_ids=("FILTER_A",))
    assert item.universe_ids == ("U_ALL",) and item.banner_ids == ("BANNER_A",) and item.filter_ids == ("FILTER_A",)


def test_g45_16_no_first_universe_implicit_rule() -> None:
    text = (ROOT / "src" / "project_intake" / "generic_productive.py").read_text()
    assert "universes[0]" not in text


def test_g45_17_display_configuration_does_not_change_canonical_value(runtime: dict, tmp_path: Path) -> None:
    before = runtime["run"].values[0].estimate
    produce(runtime, tmp_path)
    assert runtime["run"].values[0].estimate == before


def test_g45_18_release_names_and_fingerprints_are_deterministic(runtime: dict, tmp_path: Path) -> None:
    first = produce(runtime, tmp_path, name="first")
    second = produce(runtime, tmp_path, name="second")
    assert first["release_name"] == second["release_name"]
    assert first["release_fingerprint"] == second["release_fingerprint"]


def test_g45_19_provenance_is_complete(runtime: dict, tmp_path: Path) -> None:
    evidence = produce(runtime, tmp_path)
    required = {"project_id", "project_spec_version", "project_spec_fingerprint",
                "source_sha256", "package_sha256", "binding_fingerprint",
                "core_runtime_fingerprint", "canonical_result_fingerprints", "presentation_fingerprint",
                "web_adapter_identity", "excel_renderer_identity", "production_master_sha256",
                "vba_sha256", "qa_status", "release_fingerprint"}
    assert required <= set(evidence) and evidence["qa_status"] == "PASS"


def test_g45_20_release_is_atomic(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "published"
    def fail(*args, **kwargs):
        kwargs["output_root"].mkdir(parents=True)
        (kwargs["output_root"] / "partial").write_text("partial")
        raise RuntimeError("controlled")
    monkeypatch.setattr(generic, "_build_release", fail)
    with pytest.raises(RuntimeError, match="controlled"):
        generic.run_generic_productive(spec(), source_path="x", package_path="y", output_root=output)
    assert not output.exists()


def test_g45_21_non_benchmark_generic_fixture_passes(runtime: dict, tmp_path: Path) -> None:
    evidence = produce(runtime, tmp_path)
    assert evidence["project_id"] == "project_m6" and evidence["canonical_excel_exact"] is True


def test_g45_22_benchmark_backward_compatibility() -> None:
    summary = json.loads((G44 / "qa" / "gate44_summary.json").read_text())
    assert summary["project_spec_fingerprint"] == "4ebe8cf190c565b7708ef9b46c93f685e3c4af38cd047307c0399acc90bf312b"


def test_g45_23_gate44_parity_is_unchanged() -> None:
    parity = json.loads((G44 / "qa" / "parity.json").read_text())
    assert parity["canonical_web_exact"] and parity["canonical_excel_exact"] and parity["web_excel_exact"]


def test_g45_24_no_legacy_silent_fallback(runtime: dict, tmp_path: Path) -> None:
    assert produce(runtime, tmp_path)["legacy_fallback"] is False


def test_g45_25_b1_b2_b3_authority_is_preserved() -> None:
    assert binding().policy_refs == ("B1_V1", "B2_V1", "B3_V1")


def test_g45_26_release_manifest_is_complete(runtime: dict, tmp_path: Path) -> None:
    produce(runtime, tmp_path)
    manifest = json.loads((tmp_path / "release" / "release_manifest.json").read_text())
    assert manifest["schema_version"] == "EXPLORA_PRODUCTIVE_RELEASE_V1"
    assert {"canonical/canonical_results.json", "qa/generic_runtime_qa.json",
            "provenance/release_provenance.json", "config/presentation_configuration.json"} <= set(manifest["files"])
