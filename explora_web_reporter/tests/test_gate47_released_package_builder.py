from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import zipfile

import pandas as pd
import pyreadstat
import pytest

from src.canonical_materialization.materializer import PACKAGE_FILES, load_released_package, materialize_project
from src.package_authoring import PackageAuthoringError, build_released_package, validate_execution_release
from src.project_intake import compile_project_spec, run_generic_productive


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


@pytest.fixture
def authoring_input(tmp_path: Path) -> tuple[dict, dict, Path]:
    source = tmp_path / "synthetic.sav"
    pyreadstat.write_sav(pd.DataFrame({"respondent_id": ["R1", "R2", "R3"], "eligible": [1, 1, 1], "choice": [1, 2, 1]}), source)
    source_sha = sha(source.read_bytes())
    questionnaire_sha = "A" * 64
    project = {
        "schema_version": "EXPLORA_PROJECT_SPEC_V1",
        "project": {"project_id": "SYNTH_G47", "display_name": "Synthetic Gate 47", "project_version": "1.0.0", "spec_version": "1.0.0"},
        "dataset": {"source_id": "SYNTH_DATA", "input_type": "SAV", "fingerprint": f"sha256:{source_sha}", "respondent_id_variable": "respondent_id", "duplicate_row_policy": "FAIL", "variables": [
            {"variable_id": "respondent_id", "source_name": "respondent_id", "data_type": "STRING", "missing_values": []},
            {"variable_id": "eligible", "source_name": "eligible", "data_type": "INTEGER", "missing_values": []},
            {"variable_id": "choice", "source_name": "choice", "data_type": "INTEGER", "missing_values": [99]},
        ]},
        "source_metadata_fingerprints": [f"sha256:{questionnaire_sha}"],
        "questions": [{"question_id": "Q_CHOICE", "question_type": "RU", "source_variables": ["choice"], "display_label": "Choice", "universe_ref": "U_ELIGIBLE", "structure_ref": "STR_Q_CHOICE", "categories": [
            {"category_id": "YES", "raw_value": 1, "canonical_value": "YES", "label": "Yes", "order": 1, "included": True, "special": False},
            {"category_id": "NO", "raw_value": 2, "canonical_value": "NO", "label": "No", "order": 2, "included": True, "special": False},
        ]}],
        "universes": [{"universe_id": "U_ELIGIBLE", "parent_universe_ref": None, "source_variables": ["eligible"], "expression": {"operator": "in", "args": ["eligible", [1]]}, "rule_state": "DETERMINISTIC", "execution_scope": "PROJECT"}],
        "weights": [], "default_weight_ref": None, "banners": [], "filters": [], "significance_requests": [], "derived_variables": [],
        "output_requests": [{"output_request_id": "OUT_CHOICE", "question_refs": ["Q_CHOICE"], "banner_refs": [], "filter_refs": [], "web_included": True, "excel_included": False, "display_decimals": 1}],
        "ambiguities": [], "ai_interpretations": [],
        "provenance": {"created_at": "2026-09-22T00:00:00Z", "created_by": "gate47-test", "source_refs": ["SYNTH_DATA"], "b1_policy_ref": "B1_V1", "b2_policy_ref": "B2_V1", "b3_policy_ref": "B3_V1"},
    }
    from src.project_intake.contract import project_spec_fingerprint
    release = {
        "schema_version": "EXPLORA_PROJECT_EXECUTION_RELEASE_V1", "release_spec_id": "ER_SYNTH_G47", "release_spec_version": "1.0.0",
        "project_id": "SYNTH_G47", "project_spec_fingerprint": project_spec_fingerprint(project),
        "package": {"package_id": "PKG_SYNTH_G47", "package_version": "1.0.0", "dataset_version": "1.0.0", "default_execution_mode": "LEGACY"},
        "source_authority": {"dataset_filename": source.name, "dataset_sha256": source_sha, "questionnaire_filename": "synthetic-questionnaire.pdf", "questionnaire_sha256": questionnaire_sha, "datamap_ref": "SYNTH_DATAMAP_V1", "mapping_authority": "EXPLORA_MAPPING_V1"},
        "policy_refs": {"b1": "B1_V1", "b2": "B2_V1", "b3": "B3_V1", "formula_registry": "M5_FORMULA_REGISTRY_V1"},
        "release_decision": {"human_decision_id": "G47_SYNTH_APPROVAL", "human_decision_basis": "Approved synthetic contract fixture", "release_mode": "MANUAL", "released_at": "2026-09-22T00:00:00Z", "approved": True},
        "questions": [{"question_id": "Q_CHOICE", "analytical_role": "single_response", "structure_ref": "STR_Q_CHOICE", "metric_refs": ["METRIC_CHOICE"], "weight_behavior": "unweighted"}],
        "structures": [{"structure_id": "STR_Q_CHOICE", "question_id": "Q_CHOICE", "structure_type": "RU", "variable_bindings": [{"variable_ref": "choice"}], "category_bindings": [{"category_id": "YES", "raw_value": 1, "label": "Yes"}, {"category_id": "NO", "raw_value": 2, "label": "No"}], "applicability_refs": {"question": "U_ELIGIBLE"}, "selected_values": [], "not_selected_values": [], "ordinary_missing_values": [99], "completion_policy": "explicit_response", "duplicate_policy": "error", "exclusive_option_ids": [], "storage_encoding": "single_numeric_variable", "respondent_denominator_behavior": "VALID_RESPONSE", "response_state_version": "M4_STRUCTURE_V1"}],
        "metrics": [{"metric_id": "METRIC_CHOICE", "metric_type": "PROPORTION", "formula_id": "PROPORTION", "question_ref": "Q_CHOICE", "universe_ref": "U_ELIGIBLE", "denominator_policy": "VALID_RESPONSE", "missing_behavior": "EXCLUDE", "weight_behavior": "unweighted", "significance": {"status": "none", "supported": False}, "parameters": {}}],
        "weights": [], "banners": [], "filters": [], "significance": [],
        "requests": [{"request_id": "OUT_CHOICE", "question_ref": "Q_CHOICE", "metric_refs": ["METRIC_CHOICE"], "universe_ref": "U_ELIGIBLE", "weight_ref": None, "filters": [], "banner": None, "significance_ref": None, "significance_status": "NOT_REQUESTED", "purpose": "Synthetic E2E"}],
    }
    return project, release, source


def test_g47_01_contract_accepts_complete_release(authoring_input) -> None:
    project, release, _ = authoring_input
    assert validate_execution_release(project, release).execution_release == release


def test_g47_02_builds_exact_loader_files(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"
    evidence = build_released_package(project, release, destination=target, source_path=source)
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == set(PACKAGE_FILES)
    assert evidence.file_count == 10 and evidence.loader_roundtrip


def test_g47_03_deterministic_zip_bytes(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    one, two = tmp_path / "one.zip", tmp_path / "two.zip"
    build_released_package(project, release, destination=one, source_path=source)
    build_released_package(project, release, destination=two, source_path=source)
    assert one.read_bytes() == two.read_bytes()


def test_g47_04_zip_metadata_is_frozen(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"; build_released_package(project, release, destination=target, source_path=source)
    with zipfile.ZipFile(target) as archive:
        assert all(item.date_time == (1980, 1, 1, 0, 0, 0) and item.compress_type == zipfile.ZIP_DEFLATED for item in archive.infolist())


def test_g47_05_loader_roundtrip(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"; build_released_package(project, release, destination=target, source_path=source)
    assert load_released_package(target).package_id == "PKG_SYNTH_G47"


def test_g47_06_materialization_roundtrip(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"; build_released_package(project, release, destination=target, source_path=source)
    assert materialize_project(source_path=source, package_path=target).manifest.materialization_state == "PASS"


def test_g47_07_gate45_runtime_roundtrip(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    package = tmp_path / "package.zip"; output = tmp_path / "release"
    build_released_package(project, release, destination=package, source_path=source)
    summary = run_generic_productive(project, source_path=source, package_path=package, output_root=output)
    assert summary["qa_status"] == "PASS" and (output / "web" / "canonical_web_output.json").exists()


def test_g47_08_compiler_uses_non_circular_project_identity(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    package = tmp_path / "package.zip"; build_released_package(project, release, destination=package, source_path=source)
    assert compile_project_spec(project, source_path=source, package_path=package).package_id == "PKG_SYNTH_G47"


def test_g47_09_refuses_destination_replacement(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"; target.write_bytes(b"owned")
    with pytest.raises(FileExistsError):
        build_released_package(project, release, destination=target, source_path=source)
    assert target.read_bytes() == b"owned"


def test_g47_10_source_mismatch_publishes_nothing(authoring_input, tmp_path: Path) -> None:
    project, release, source = authoring_input; source.write_bytes(b"changed")
    target = tmp_path / "package.zip"
    with pytest.raises(PackageAuthoringError, match="source artifact hash mismatch"):
        build_released_package(project, release, destination=target, source_path=source)
    assert not target.exists()


MUTATIONS = [
    ("schema", lambda p, r: r.update(schema_version="OLD"), "schema"),
    ("fingerprint", lambda p, r: r.update(project_spec_fingerprint="bad"), "fingerprint"),
    ("project", lambda p, r: r.update(project_id="OTHER"), "identity"),
    ("b1", lambda p, r: r["policy_refs"].update(b1="OLD"), "policy"),
    ("b2", lambda p, r: r["policy_refs"].update(b2="OLD"), "policy"),
    ("b3", lambda p, r: r["policy_refs"].update(b3="OLD"), "policy"),
    ("formula_registry", lambda p, r: r["policy_refs"].update(formula_registry="OLD"), "policy"),
    ("approval", lambda p, r: r["release_decision"].update(approved=False), "decision"),
    ("release_mode", lambda p, r: r["release_decision"].update(release_mode="AI"), "decision"),
    ("source", lambda p, r: r["source_authority"].update(dataset_sha256="0" * 64), "source"),
    ("question", lambda p, r: r["questions"].clear(), "questions"),
    ("structure", lambda p, r: r["questions"][0].update(structure_ref="MISSING"), "dangling"),
    ("formula", lambda p, r: r["metrics"][0].update(formula_id="GUESS"), "formula"),
    ("weight", lambda p, r: r["requests"][0].update(weight_ref="UNKNOWN"), "weight"),
    ("statistical", lambda p, r: r.update(observed_count=3), "fields mismatch"),
]


@pytest.mark.parametrize("_name,mutate,message", MUTATIONS, ids=[item[0] for item in MUTATIONS])
def test_g47_11_fail_closed_contract(authoring_input, _name, mutate, message) -> None:
    project, release, _ = authoring_input; release = deepcopy(release); mutate(project, release)
    with pytest.raises(PackageAuthoringError, match=message):
        validate_execution_release(project, release)


ARTIFACT_ASSERTIONS = [
    ("01_PROJECT_SPEC_RELEASED.json", "project_id"), ("01_PROJECT_SPEC_RELEASED.json", "spec_hash"),
    ("02_QUESTION_SPECS_RELEASED.json", "question_id"), ("02_QUESTION_SPECS_RELEASED.json", "physical_variable_bindings"),
    ("03_STRUCTURE_SPECS_RELEASED.json", "structure_id"), ("03_STRUCTURE_SPECS_RELEASED.json", "category_bindings"),
    ("04_UNIVERSE_SPECS_RELEASED.json", "universe_id"), ("04_UNIVERSE_SPECS_RELEASED.json", "expression"),
    ("05_WEIGHT_REGISTRY_RELEASED.json", "resolution"), ("05_WEIGHT_REGISTRY_RELEASED.json", "explicitly_unweighted_requests"),
    ("06_METRIC_SPECS_RELEASED.json", "formula_id"), ("06_METRIC_SPECS_RELEASED.json", "weight_behavior"),
    ("07_SIGNIFICANCE_SPECS_RELEASED.json", None), ("08_BANNER_FILTER_SPECS_RELEASED.json", "banners"),
    ("08_BANNER_FILTER_SPECS_RELEASED.json", "filters"), ("09_REQUEST_MATRIX_RELEASED.json", "matrix_id"),
    ("09_REQUEST_MATRIX_RELEASED.json", "requests"), ("MANIFEST.json", "project_spec_fingerprint"),
    ("MANIFEST.json", "files"), ("MANIFEST.json", "spec_hash"),
]


@pytest.mark.parametrize("filename,key", ARTIFACT_ASSERTIONS, ids=[f"{i:02d}-{name}" for i, (name, _) in enumerate(ARTIFACT_ASSERTIONS, 1)])
def test_g47_12_released_artifact_contract(authoring_input, tmp_path: Path, filename, key) -> None:
    project, release, source = authoring_input
    target = tmp_path / "package.zip"; build_released_package(project, release, destination=target, source_path=source)
    with zipfile.ZipFile(target) as archive:
        value = json.loads(archive.read(filename))
    if key is None:
        assert value == []
    elif isinstance(value, list):
        assert value and key in value[0]
    else:
        assert key in value
