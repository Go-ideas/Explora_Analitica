from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.execution_release_authoring import authoring
from src.execution_release_authoring.authoring import author_execution_release_draft, canonical_release_json
from src.operator_console.service import approve_execution_release
from src.package_authoring.contract import validate_execution_release
from src.project_intake.contract import project_spec_fingerprint


def _category(qid, raw, label, order):
    return {"category_id": f"{qid}_{raw}", "raw_value": raw, "canonical_value": str(raw), "label": label, "order": order, "included": True, "special": False}


def _inputs(weighted=False):
    variables = [{"variable_id": "respondent_id", "source_name": "respondent_id", "data_type": "STRING", "missing_values": []}]
    for name in ("ru", "rm_1", "rm_2", "loop.1", "loop.2", "number.1", "number.2"):
        variables.append({"variable_id": name, "source_name": name, "data_type": "NUMBER", "missing_values": [99] if name.startswith("rm") else []})
    if weighted:
        variables.append({"variable_id": "weight", "source_name": "weight", "data_type": "NUMBER", "missing_values": []})
    binary = [_category("B", 0, "No", 1), _category("B", 1, "Yes", 2)]
    questions = [
        {"question_id": "RU", "question_type": "RU", "source_variables": ["ru"], "display_label": "Choice", "universe_ref": "U", "structure_ref": "STRUCTURE_RU", "categories": deepcopy(binary)},
        {"question_id": "RM", "question_type": "RM", "source_variables": ["rm_1", "rm_2"], "display_label": "Multiple", "universe_ref": "U", "structure_ref": "STRUCTURE_RM", "categories": deepcopy(binary)},
        {"question_id": "LOOP_RU", "question_type": "LOOP_RU", "source_variables": ["loop.1", "loop.2"], "display_label": "Repeated", "universe_ref": "U", "structure_ref": "STRUCTURE_LOOP_RU", "categories": deepcopy(binary), "loop_iterations": [{"iteration_id": "ITER_1", "order": 1, "variable_ref": "loop.1", "source_label": "First"}, {"iteration_id": "ITER_2", "order": 2, "variable_ref": "loop.2", "source_label": "Second"}]},
        {"question_id": "LOOP_NUM", "question_type": "LOOP_NUMERICO", "source_variables": ["number.1", "number.2"], "display_label": "Measures", "universe_ref": "U", "structure_ref": "STRUCTURE_LOOP_NUM", "categories": [], "loop_iterations": [{"iteration_id": "NUM_1", "order": 1, "variable_ref": "number.1", "source_label": "First"}, {"iteration_id": "NUM_2", "order": 2, "variable_ref": "number.2", "source_label": "Second"}]},
    ]
    project = {
        "schema_version": "EXPLORA_PROJECT_SPEC_V1", "project": {"project_id": "SYNTH", "display_name": "Synthetic", "project_version": "1", "spec_version": "1"},
        "dataset": {"source_id": "DATA", "input_type": "SAV", "fingerprint": "sha256:" + "a" * 64, "respondent_id_variable": "respondent_id", "duplicate_row_policy": "FAIL", "variables": variables},
        "source_metadata_fingerprints": ["sha256:" + "b" * 64], "questions": questions,
        "universes": [{"universe_id": "U", "parent_universe_ref": None, "source_variables": [], "expression": {"operator": "true", "args": []}, "rule_state": "DETERMINISTIC", "execution_scope": "PROJECT"}],
        "weights": ([{"weight_id": "W", "variable_ref": "weight", "normalization": "NONE", "trimming": "NONE"}] if weighted else []), "default_weight_ref": "W" if weighted else None,
        "banners": [], "filters": [], "significance_requests": [], "derived_variables": [],
        "output_requests": [{"output_request_id": "OUT", "question_refs": [q["question_id"] for q in questions], "banner_refs": [], "filter_refs": [], "web_included": True, "excel_included": False, "display_decimals": 2}],
        "ambiguities": [], "ai_interpretations": [], "provenance": {"created_at": "deterministic", "created_by": "human", "source_refs": ["DATA"], "b1_policy_ref": "B1_V1", "b2_policy_ref": "B2_V1", "b3_policy_ref": "B3_V1"},
    }
    authority = {"dataset_filename": "source.sav", "dataset_sha256": "A" * 64, "questionnaire_filename": "questionnaire.docx", "questionnaire_sha256": "B" * 64, "datamap_ref": "sha256:" + "C" * 64}
    metadata = {"release_spec_id": "ER", "release_spec_version": "1", "package_id": "PKG", "package_version": "1", "dataset_version": "1", "internal_project_name": "SYNTH_INTERNAL"}
    return project, authority, metadata


def _draft(weighted=False):
    result = author_execution_release_draft(*_inputs(weighted))
    assert result.execution_release is not None
    return result, result.execution_release


def _structure(release, qid): return next(x for x in release["structures"] if x["question_id"] == qid)
def _metric(release, qid): return next(x for x in release["metrics"] if x["question_ref"] == qid)


def test_g51_01_ready_project_creates_valid_pending_draft():
    result, release = _draft()
    assert result.status == "ER_DRAFT_VALID"
    validate_execution_release(_inputs()[0], release, require_approved=False)


def test_g51_02_non_ready_project_fails_closed():
    p, a, m = _inputs(); p["ambiguities"] = [{"ambiguity_id": "A", "classification": "HUMAN_DECISION_REQUIRED", "state": "OPEN"}]
    assert author_execution_release_draft(p, a, m).status == "ER_DRAFT_REQUIRES_HUMAN_DECISION"


def test_g51_03_project_fingerprint_preserved():
    _, release = _draft(); assert release["project_spec_fingerprint"] == project_spec_fingerprint(_inputs()[0])


@pytest.mark.parametrize("qid,qtype,formula", [("RU", "RU", "PROPORTION"), ("RM", "RM", "RM_RESPONDENT_PROPORTION"), ("LOOP_RU", "LOOP_RU", "PROPORTION"), ("LOOP_NUM", "LOOP_NUMERICO", "MEAN")])
def test_g51_04_07_question_structure_metric_mapping(qid, qtype, formula):
    _, release = _draft(); assert _structure(release, qid)["structure_type"] == qtype; assert _metric(release, qid)["formula_id"] == formula


def test_g51_08_deterministic_structure_ids():
    _, r = _draft(); assert [x["structure_id"] for x in r["structures"]] == [f"STRUCTURE_{x}" for x in ("LOOP_NUM", "LOOP_RU", "RM", "RU")]


def test_g51_09_deterministic_metric_ids():
    _, r = _draft(); assert all(x["metric_id"] == f"METRIC_{x['question_ref']}" for x in r["metrics"])


def test_g51_10_deterministic_request_ids():
    _, r = _draft(); assert all(x["request_id"] == f"REQUEST_OUT_{x['question_ref']}" for x in r["requests"])


def test_g51_11_loop_order_preserved():
    _, r = _draft(); assert [x["iteration_id"] for x in _structure(r, "LOOP_RU")["loop_iterations"]] == ["ITER_1", "ITER_2"]


def test_g51_12_category_domain_preserved():
    _, r = _draft(); assert [x["raw_value"] for x in _structure(r, "RU")["category_bindings"]] == [0, 1]


def test_g51_13_unweighted_is_explicit():
    _, r = _draft(); assert r["weights"] == [] and {x["weight_choice"] for x in r["requests"]} == {"EXPLICITLY_UNWEIGHTED"}


def test_g51_14_weighted_mapping():
    _, r = _draft(True); assert r["weights"][0]["weight_id"] == "W" and {x["weight_choice"] for x in r["requests"]} == {"PROJECT_DEFAULT"}


@pytest.mark.parametrize("field", ["banners", "filters", "significance"])
def test_g51_15_17_empty_collections_preserved(field):
    _, r = _draft(); assert r[field] == []


def test_g51_18_web_only_intent_preserved():
    p, _, _ = _inputs(); _, r = _draft(); assert p["output_requests"][0]["web_included"] and all(x["output_request_ref"] == "OUT" for x in r["requests"])


def test_g51_19_excel_intent_fails_closed():
    p, a, m = _inputs(); p["output_requests"][0]["excel_included"] = True
    assert author_execution_release_draft(p, a, m).status == "ER_DRAFT_REQUIRES_HUMAN_DECISION"


def test_g51_20_b3_starts_pending_without_identity_or_time():
    result, r = _draft(); assert result.b3_status == "PENDING_HUMAN_RELEASE"; assert r["release_decision"] == {"human_decision_id": None, "human_decision_basis": None, "release_mode": "MANUAL", "released_at": None, "approved": False}


def test_g51_21_source_authority_preserved():
    _, r = _draft(); assert r["source_authority"]["dataset_filename"] == "source.sav" and r["source_authority"]["questionnaire_sha256"] == "B" * 64


def test_g51_22_internal_name_is_explicit_not_display_name():
    _, r = _draft(); assert r["package"]["internal_project_name"] == "SYNTH_INTERNAL" and r["package"]["internal_project_name"] != "Synthetic"


def test_g51_23_validator_is_delegated(monkeypatch):
    calls=[]; original=authoring.validate_execution_release
    monkeypatch.setattr(authoring, "validate_execution_release", lambda *args, **kwargs: calls.append(kwargs) or original(*args, **kwargs))
    assert author_execution_release_draft(*_inputs()).status == "ER_DRAFT_VALID" and calls == [{"require_approved": False}]


def test_g51_24_invalid_generated_release_fails_closed(monkeypatch):
    monkeypatch.setattr(authoring, "validate_execution_release", lambda *a, **k: (_ for _ in ()).throw(ValueError("invalid")))
    assert author_execution_release_draft(*_inputs()).status == "ER_DRAFT_INVALID"


def test_g51_25_identical_input_is_byte_identical():
    one=author_execution_release_draft(*_inputs()); two=author_execution_release_draft(*_inputs()); assert canonical_release_json(one.execution_release) == canonical_release_json(two.execution_release)


@pytest.mark.parametrize("missing", ["release_spec_id", "package_id", "internal_project_name"])
def test_g51_26_28_missing_package_metadata_fails(missing):
    p,a,m=_inputs(); m[missing]=""; assert author_execution_release_draft(p,a,m).execution_release is None


def test_g51_29_missing_source_authority_fails():
    p,a,m=_inputs(); a["questionnaire_sha256"]=""; assert author_execution_release_draft(p,a,m).status == "ER_DRAFT_REQUIRES_HUMAN_DECISION"


def test_g51_30_incomplete_loop_fails():
    p,a,m=_inputs(); p["questions"][2]["loop_iterations"].pop(); assert author_execution_release_draft(p,a,m).execution_release is None


def test_g51_31_unqualified_type_fails():
    p,a,m=_inputs(); p["questions"][0]["question_type"]="SCALE"; assert author_execution_release_draft(p,a,m).status == "ER_DRAFT_REQUIRES_HUMAN_DECISION"


def test_g51_32_human_approval_makes_default_validator_valid():
    p,_,_=_inputs(); _,r=_draft(); approved=approve_execution_release(r, decision_id="HUMAN", decision_basis="Reviewed", released_at="2026-01-01T00:00:00Z"); validate_execution_release(p, approved)


def test_g51_33_no_customer_or_statistics_path():
    source=Path("src/execution_release_authoring/authoring.py").read_text().lower(); assert "analytics_core.execution" not in source and "customer_id" not in source


def test_g51_34_project_structure_identity_is_preserved():
    project, authority, metadata = _inputs()
    project["questions"][0]["structure_ref"] = "EXPLICIT_RU_STRUCTURE"
    result = author_execution_release_draft(project, authority, metadata)
    assert _structure(result.execution_release, "RU")["structure_id"] == "EXPLICIT_RU_STRUCTURE"


def test_g51_35_missing_structure_identity_fails_closed():
    project, authority, metadata = _inputs()
    project["questions"][0].pop("structure_ref")
    result = author_execution_release_draft(project, authority, metadata)
    assert any(item["code"] == "STRUCTURE_IDENTITY_REQUIRED" for item in result.errors)
