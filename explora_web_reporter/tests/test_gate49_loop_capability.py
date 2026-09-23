from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from src.canonical_materialization.orchestrator import run_canonical_project
from src.package_authoring.builder import build_released_package
from src.package_authoring.contract import PackageAuthoringError, validate_execution_release
from src.project_intake.contract import project_spec_fingerprint, validate_project
from src.project_intake.generic_productive import run_generic_productive


def _fixture(tmp_path: Path, *, kind: str = "LOOP_RU", count: int = 2, weighted: bool = False):
    data = {"respondent_id": [1, 2, 3], "eligible": [1, 1, 1], "weight": [1.0, 2.0, 1.0]}
    for index in range(1, count + 1):
        data[f"QUESTION.{index}"] = ([1, 2, 1] if kind == "LOOP_RU" else [index, index + 1, None])
    source = tmp_path / f"{kind.lower()}.sav"
    pyreadstat.write_sav(pd.DataFrame(data), source)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    variables = [
        {"variable_id": "respondent_id", "source_name": "respondent_id", "data_type": "INTEGER", "missing_values": []},
        {"variable_id": "eligible", "source_name": "eligible", "data_type": "INTEGER", "missing_values": []},
        {"variable_id": "weight", "source_name": "weight", "data_type": "NUMBER", "missing_values": []},
        *[{"variable_id": f"QUESTION.{i}", "source_name": f"QUESTION.{i}", "data_type": "NUMBER" if kind == "LOOP_NUMERICO" else "INTEGER", "missing_values": []} for i in range(1, count + 1)],
    ]
    categories = [] if kind == "LOOP_NUMERICO" else [
        {"category_id": "YES", "raw_value": 1, "canonical_value": "YES", "label": "Yes", "order": 1, "included": True, "special": False},
        {"category_id": "NO", "raw_value": 2, "canonical_value": "NO", "label": "No", "order": 2, "included": True, "special": False},
    ]
    project = {
        "schema_version": "EXPLORA_PROJECT_SPEC_V1",
        "project": {"project_id": "SYNTH_LOOP", "display_name": "Synthetic loop", "project_version": "1", "spec_version": "1"},
        "dataset": {"source_id": "SYNTH", "input_type": "SAV", "fingerprint": f"sha256:{source_sha}", "respondent_id_variable": "respondent_id", "duplicate_row_policy": "FAIL", "variables": variables},
        "source_metadata_fingerprints": ["sha256:" + "a" * 64],
        "questions": [{"question_id": "QUESTION", "question_type": kind, "source_variables": [f"QUESTION.{i}" for i in range(1, count + 1)], "display_label": "Repeated question", "universe_ref": "U", "structure_ref": "STR_LOOP", "categories": categories}],
        "universes": [{"universe_id": "U", "parent_universe_ref": None, "source_variables": ["eligible"], "expression": {"operator": "in", "args": ["eligible", [1]]}, "rule_state": "DETERMINISTIC", "execution_scope": "PROJECT"}],
        "weights": ([{"weight_id": "W", "variable_ref": "weight", "normalization": "NONE", "trimming": "NONE"}] if weighted else []),
        "default_weight_ref": "W" if weighted else None,
        "banners": [], "filters": [], "significance_requests": [], "derived_variables": [],
        "output_requests": [{"output_request_id": "OUT", "question_refs": ["QUESTION"], "banner_refs": [], "filter_refs": [], "web_included": True, "excel_included": False, "display_decimals": 2}],
        "ambiguities": [], "ai_interpretations": [],
        "provenance": {"created_at": "2026-09-22T00:00:00Z", "created_by": "gate49-test", "source_refs": ["SYNTH"], "b1_policy_ref": "B1_V1", "b2_policy_ref": "B2_V1", "b3_policy_ref": "B3_V1"},
    }
    iterations = [{"iteration_id": f"ITER_{i}", "order": i, "label": f"Iteration {i}", "variable_ref": f"QUESTION.{i}", "response_domain": [1, 2] if kind == "LOOP_RU" else []} for i in range(1, count + 1)]
    metric_id = "M_PROP" if kind == "LOOP_RU" else "M_MEAN"
    formula = "PROPORTION" if kind == "LOOP_RU" else "SCALE_MEAN"
    release = {
        "schema_version": "EXPLORA_PROJECT_EXECUTION_RELEASE_V1", "release_spec_id": "ER_LOOP", "release_spec_version": "1", "project_id": "SYNTH_LOOP", "project_spec_fingerprint": project_spec_fingerprint(project),
        "package": {"package_id": f"PKG_{kind}_{count}_{weighted}", "package_version": "1", "dataset_version": "1", "default_execution_mode": "LEGACY", "internal_project_name": "SYNTH_LOOP"},
        "source_authority": {"dataset_filename": source.name, "dataset_sha256": source_sha, "questionnaire_filename": "synthetic.txt", "questionnaire_sha256": "a" * 64, "datamap_ref": "SYNTH_LOOP_MAP", "mapping_authority": "SYNTHETIC_EXPLICIT_LOOP_METADATA"},
        "policy_refs": {"b1": "B1_V1", "b2": "B2_V1", "b3": "B3_V1", "formula_registry": "M5_FORMULA_REGISTRY_V1"},
        "release_decision": {"human_decision_id": "SYNTH_APPROVAL", "human_decision_basis": "Synthetic qualification", "release_mode": "MANUAL", "released_at": "2026-09-22T00:00:00Z", "approved": True},
        "questions": [{"question_id": "QUESTION", "analytical_role": "repeated_measure", "structure_ref": "STR_LOOP", "metric_refs": [metric_id], "weight_behavior": "weighted" if weighted else "unweighted"}],
        "structures": [{"structure_id": "STR_LOOP", "question_id": "QUESTION", "structure_type": kind, "variable_bindings": [{"binding_id": f"B_{i}", "variable_ref": f"QUESTION.{i}", "loop_instance_id": f"ITER_{i}"} for i in range(1, count + 1)], "loop_iterations": iterations, "category_bindings": [{"category_id": x["category_id"], "raw_value": x["raw_value"], "label": x["label"]} for x in categories], "applicability_refs": {"question": "U"}, "selected_values": [], "not_selected_values": [], "ordinary_missing_values": [], "completion_policy": "explicit_response", "duplicate_policy": "error", "exclusive_option_ids": [], "storage_encoding": "single_numeric_variable", "respondent_denominator_behavior": "VALID_RESPONSE", "response_state_version": "M4_STRUCTURE_V1"}],
        "metrics": [{"metric_id": metric_id, "metric_type": "PROPORTION" if kind == "LOOP_RU" else "MEAN", "formula_id": formula, "question_ref": "QUESTION", "universe_ref": "U", "denominator_policy": "VALID_RESPONSE", "missing_behavior": "EXCLUDE", "weight_behavior": "weighted" if weighted else "unweighted", "significance": {"status": "none", "supported": False}, "parameters": {}}],
        "weights": ([{"weight_id": "W", "variable_ref": "weight", "provenance": "SYNTH", "scope": "project", "permitted_analysis_overrides": [], "missing_policy": "EXCLUDE_AND_QA", "non_numeric_policy": "EXCLUDE_AND_QA", "non_finite_policy": "FAIL", "zero_policy": "VALID", "negative_policy": "UNSUPPORTED_V1", "normalization": "NONE", "trimming": "NONE", "weighted_significance": False}] if weighted else []),
        "banners": [], "filters": [], "significance": [],
        "requests": [{"request_id": "REQ", "output_request_ref": "OUT", "question_ref": "QUESTION", "metric_refs": [metric_id], "universe_ref": "U", "weight_ref": None, "weight_choice": "PROJECT_DEFAULT" if weighted else "EXPLICITLY_UNWEIGHTED", "filters": [], "banner": None, "significance_ref": None, "significance_status": "NOT_REQUESTED", "purpose": "Synthetic loop qualification"}],
    }
    return project, release, source


def _run(tmp_path: Path, **kwargs):
    project, release, source = _fixture(tmp_path, **kwargs)
    package = tmp_path / "package.zip"
    evidence = build_released_package(project, release, destination=package, source_path=source)
    result = run_canonical_project(source_path=source, package_path=package, request_ids=("REQ",)).results["REQ"]
    return project, release, evidence, result


def test_g49_01_loop_ru_two_iterations(tmp_path):
    *_, result = _run(tmp_path, count=2)
    assert {v.loop_instance_id for v in result.values} == {"ITER_1", "ITER_2"}


def test_g49_02_loop_ru_four_iterations(tmp_path):
    *_, result = _run(tmp_path, count=4)
    assert len(result.values) == 8


def test_g49_03_deterministic_iteration_order(tmp_path):
    project, release, source = _fixture(tmp_path, count=4)
    release["structures"][0]["variable_bindings"].reverse()
    package = tmp_path / "ordered.zip"
    build_released_package(project, release, destination=package, source_path=source)
    result = run_canonical_project(source_path=source, package_path=package, request_ids=("REQ",)).results["REQ"]
    assert [(v.loop_instance_id, v.category_id) for v in result.values] == [(f"ITER_{i}", c) for i in range(1, 5) for c in ("NO", "YES")]


def test_g49_04_value_label_compatibility(tmp_path):
    project, release, _ = _fixture(tmp_path)
    release["structures"][0]["loop_iterations"][1]["response_domain"] = [1, 3]
    with pytest.raises(PackageAuthoringError, match="incompatible response domains"):
        validate_execution_release(project, release)


def test_g49_05_missing_variable_fails(tmp_path):
    project, release, _ = _fixture(tmp_path)
    release["structures"][0]["loop_iterations"][0]["variable_ref"] = "MISSING"
    with pytest.raises(PackageAuthoringError, match="source variable is missing"):
        validate_execution_release(project, release)


def test_g49_06_duplicate_iteration_fails(tmp_path):
    project, release, _ = _fixture(tmp_path)
    release["structures"][0]["loop_iterations"][1]["iteration_id"] = "ITER_1"
    with pytest.raises(PackageAuthoringError, match="duplicate loop iteration"):
        validate_execution_release(project, release)


@pytest.mark.parametrize("weighted", [False, True], ids=["unweighted", "weighted"])
def test_g49_07_08_loop_ru_weight_modes(tmp_path, weighted):
    *_, result = _run(tmp_path, weighted=weighted)
    assert all((base.active_weight_ref == "W") is weighted for base in result.bases)


def test_g49_09_canonical_identity(tmp_path):
    *_, result = _run(tmp_path)
    assert len({v.value_id for v in result.values}) == len(result.values)


def test_g49_10_provenance(tmp_path):
    *_, result = _run(tmp_path)
    assert all(any(ref.startswith("loop_instance:") for ref in value.provenance_refs) for value in result.values)


def test_g49_11_deterministic_package(tmp_path):
    project, release, source = _fixture(tmp_path)
    one = build_released_package(project, release, destination=tmp_path / "one.zip", source_path=source)
    two = build_released_package(project, release, destination=tmp_path / "two.zip", source_path=source)
    assert one.package_sha256 == two.package_sha256


def test_g49_12_loop_significance_fails_closed(tmp_path):
    project, release, _ = _fixture(tmp_path)
    project["significance_requests"] = [{"significance_request_id": "SIG", "confidence": .95, "policy_ref": "B2_V1"}]
    release["project_spec_fingerprint"] = project_spec_fingerprint(project)
    release["significance"] = [{"significance_id": "SIG", "question_ref": "QUESTION", "metric_refs": ["M_PROP"], "banner_ref": "B", "family_id": "F", "family_members": ["X"], "sample_relationship": "INDEPENDENT", "confidence": .95, "weight_compatibility": "UNWEIGHTED", "test_family": "PROPORTION"}]
    with pytest.raises(PackageAuthoringError):
        validate_execution_release(project, release)


@pytest.mark.parametrize("weighted", [False, True], ids=["unweighted", "weighted"])
def test_g49_13_14_loop_numeric_execution(tmp_path, weighted):
    *_, result = _run(tmp_path, kind="LOOP_NUMERICO", weighted=weighted)
    assert len(result.values) == 2 and all(value.estimate is not None for value in result.values)


def test_g49_15_numeric_missing_excluded(tmp_path):
    *_, result = _run(tmp_path, kind="LOOP_NUMERICO")
    assert all(base.unweighted_n == 2 for base in result.bases)


def test_g49_16_loop_rm_remains_unsupported(tmp_path):
    project, release, _ = _fixture(tmp_path)
    project["questions"][0]["question_type"] = "LOOP_RM"
    release["structures"][0]["structure_type"] = "LOOP_RM"
    release["project_spec_fingerprint"] = project_spec_fingerprint(project)
    with pytest.raises(PackageAuthoringError, match="unsupported"):
        validate_execution_release(project, release)


def test_g49_17_project_spec_accepts_loop_vocabulary(tmp_path):
    project, _, _ = _fixture(tmp_path)
    assert validate_project(project).ready_for_execution


def test_g49_18_parent_identity_preserved(tmp_path):
    *_, result = _run(tmp_path)
    assert {value.question_id for value in result.values} == {"QUESTION"}


def test_g49_19_builder_roundtrip(tmp_path):
    *_, evidence, _ = _run(tmp_path)
    assert evidence.loader_roundtrip and evidence.file_count == 10


def test_g49_20_no_customer_specific_tokens():
    targets = [
        "src/package_authoring/contract.py",
        "src/canonical_materialization/orchestrator.py",
        "src/canonical_materialization/materializer.py",
        "src/analytics_core/execution_adapter.py",
    ]
    text = "\n".join(Path(path).read_text(encoding="utf-8").lower() for path in targets)
    assert all(token not in text for token in ("yin", "p11", "p12", "atlas", "client"))


def test_g49_21_generic_productive_runtime(tmp_path):
    project, release, source = _fixture(tmp_path)
    package = tmp_path / "package.zip"
    build_released_package(project, release, destination=package, source_path=source)
    summary = run_generic_productive(
        project,
        source_path=source,
        package_path=package,
        output_root=tmp_path / "release",
    )
    assert summary["qa_status"] == "PASS"
