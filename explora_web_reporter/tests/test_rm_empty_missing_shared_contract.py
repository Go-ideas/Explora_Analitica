import hashlib
import json

import pandas as pd
import pyreadstat
import pytest

from test_gate51_execution_release_draft_authoring import _inputs, _structure
from src.execution_release_authoring.authoring import author_execution_release_draft, canonical_release_json
from src.operator_console.service import approve_execution_release
from src.package_authoring import build_released_package, validate_execution_release, PackageAuthoringError
from src.canonical_materialization.materializer import load_released_package, materialize_project
from src.canonical_materialization.orchestrator import run_canonical_project
from src.canonical_materialization.models import MaterializationError


def states(missing=()):
    return {"RM": {"selected_values": [1], "not_selected_values": [0], "ordinary_missing_values": list(missing)}}


@pytest.mark.parametrize("missing", [[], [99]])
def test_explicit_missing_authority_draft_and_approved_contract(missing):
    inputs = _inputs()
    result = author_execution_release_draft(*inputs, states(missing))
    assert result.status == "ER_DRAFT_VALID"
    assert _structure(result.execution_release, "RM")["ordinary_missing_values"] == missing
    assert result.execution_release["package"]["default_execution_mode"] == "LEGACY"
    validate_execution_release(inputs[0], result.execution_release, require_approved=False)
    approved = approve_execution_release(result.execution_release, decision_id="SYNTHETIC", decision_basis="Explicit review", released_at="2026-10-06T00:00:00Z")
    validate_execution_release(inputs[0], approved)


INVALID = [
    ("selected_values", [], "RM_RESPONSE_STATE_REQUIRED"),
    ("not_selected_values", [], "RM_RESPONSE_STATE_REQUIRED"),
    ("ordinary_missing_values", None, "RM_RESPONSE_STATE_REQUIRED"),
    ("ordinary_missing_values", "[]", "RM_RESPONSE_STATE_REQUIRED"),
    ("selected_values", [1, 1], "RM_RESPONSE_STATE_DUPLICATE"),
    ("not_selected_values", [0, 0], "RM_RESPONSE_STATE_DUPLICATE"),
    ("ordinary_missing_values", [99, 99], "RM_RESPONSE_STATE_DUPLICATE"),
    ("not_selected_values", [1], "RM_RESPONSE_STATES_OVERLAP"),
    ("ordinary_missing_values", [1], "RM_RESPONSE_STATES_OVERLAP"),
    ("ordinary_missing_values", [0], "RM_RESPONSE_STATES_OVERLAP"),
    ("ordinary_missing_values", [float("nan")], "RM_RESPONSE_STATE_INVALID"),
]


@pytest.mark.parametrize("field,value,code", INVALID)
def test_invalid_authority_fails_closed(field, value, code):
    authority = states(); authority["RM"][field] = value
    result = author_execution_release_draft(*_inputs(), authority)
    assert result.execution_release is None
    assert any(error["code"] == code for error in result.errors)


@pytest.mark.parametrize("field", ["selected_values", "not_selected_values", "ordinary_missing_values"])
def test_missing_authority_field_fails(field):
    authority = states(); del authority["RM"][field]
    result = author_execution_release_draft(*_inputs(), authority)
    assert result.execution_release is None
    assert any(error["code"] == "RM_RESPONSE_STATE_AUTHORITY_INVALID" for error in result.errors)


def test_empty_missing_serialization_and_fingerprint_are_deterministic():
    authority = states(); authority["RM"]["selected_values"] = [3, 1, 2]
    one = author_execution_release_draft(*_inputs(), authority)
    authority["RM"]["selected_values"] = (2, 3, 1)
    two = author_execution_release_draft(*_inputs(), authority)
    assert one.status == two.status == "ER_DRAFT_VALID"
    assert canonical_release_json(one.execution_release) == canonical_release_json(two.execution_release)
    assert one.execution_release_fingerprint == two.execution_release_fingerprint
    serialized = json.loads(canonical_release_json(one.execution_release))
    assert _structure(serialized, "RM")["ordinary_missing_values"] == []
    assert _structure(serialized, "RM")["selected_values"] == [1, 2, 3]


@pytest.mark.parametrize("field,value", [
    ("selected_values", []), ("not_selected_values", []),
    ("ordinary_missing_values", None), ("ordinary_missing_values", "[]"),
    ("ordinary_missing_values", {}), ("selected_values", "1"),
    ("not_selected_values", 0), ("ordinary_missing_values", [1]),
    ("ordinary_missing_values", [0]), ("not_selected_values", [1]),
    ("ordinary_missing_values", [float("nan")]),
])
def test_shared_contract_rejects_invalid_states(field, value):
    inputs = _inputs(); release = author_execution_release_draft(*inputs, states()).execution_release
    _structure(release, "RM")[field] = value
    with pytest.raises(PackageAuthoringError):
        validate_execution_release(inputs[0], release, require_approved=False)


@pytest.mark.parametrize("field", ["selected_values", "not_selected_values", "ordinary_missing_values"])
def test_shared_contract_requires_each_field(field):
    inputs = _inputs(); release = author_execution_release_draft(*inputs, states()).execution_release
    del _structure(release, "RM")[field]
    with pytest.raises(PackageAuthoringError):
        validate_execution_release(inputs[0], release, require_approved=False)


def synthetic_package(tmp_path, missing, third_state=False):
    project, authority, metadata = _inputs()
    project["questions"] = [q for q in project["questions"] if q["question_type"] == "RM"]
    project["output_requests"][0]["question_refs"] = ["RM"]
    project["dataset"]["variables"] = [v for v in project["dataset"]["variables"] if v["variable_id"] in {"respondent_id", "eligible", "rm_1", "rm_2", "rm_3"}]
    for variable in project["dataset"]["variables"]:
        variable["missing_values"] = []
    source = tmp_path / "synthetic.sav"
    pyreadstat.write_sav(pd.DataFrame({"respondent_id": ["R1", "R2", "R3"], "eligible": [1, 1, 1], "rm_1": [1, 0, 99 if third_state else 1], "rm_2": [0, 1, 1], "rm_3": [1, 1, 0]}), source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    project["dataset"]["fingerprint"] = "sha256:" + digest
    authority.update(dataset_filename=source.name, dataset_sha256=digest)
    result = author_execution_release_draft(project, authority, metadata, states(missing))
    assert result.status == "ER_DRAFT_VALID"
    approved = approve_execution_release(result.execution_release, decision_id="SYNTHETIC", decision_basis="Explicit review", released_at="2026-10-06T00:00:00Z")
    target = tmp_path / "package.zip"
    evidence = build_released_package(project, approved, destination=target, source_path=source)
    assert evidence.loader_roundtrip
    return source, target


@pytest.mark.parametrize("missing", [[], [99]])
def test_package_loader_materialization_and_canonical_result(tmp_path, missing):
    source, target = synthetic_package(tmp_path, missing)
    package = load_released_package(target)
    assert package.default_execution_mode == "LEGACY"
    assert package.structures[0]["ordinary_missing_values"] == missing
    runtime = materialize_project(source_path=source, package_path=target)
    assert runtime.manifest.materialization_state == "PASS"
    execution = run_canonical_project(source_path=source, package_path=target, request_ids=("REQUEST_OUT_RM",))
    result = execution.results["REQUEST_OUT_RM"]
    assert len(result.values) == 3
    for value in result.values:
        assert value.estimate == pytest.approx(2 / 3)


@pytest.mark.parametrize("missing,expected", [([], "FAIL"), ([99], "PASS")])
def test_undeclared_third_state_requires_explicit_missing(tmp_path, missing, expected):
    source, target = synthetic_package(tmp_path, missing, third_state=True)
    if expected == "FAIL":
        with pytest.raises(MaterializationError, match="undeclared observed analytical category for rm_1"):
            materialize_project(source_path=source, package_path=target)
    else:
        runtime = materialize_project(source_path=source, package_path=target)
        assert runtime.manifest.materialization_state == "PASS"
