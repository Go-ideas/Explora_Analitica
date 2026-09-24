from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.project_intake.contract import validate_project
from src.project_spec_authoring import authoring
from src.project_spec_authoring.authoring import (
    PROJECT_SPEC_DRAFT_AUTHORING_VERSION,
    author_project_spec_draft,
    canonical_draft_json,
)


def _variable(name, *, labels=None, data_type="INTEGER", label=None):
    values = deepcopy(labels or [])
    return {
        "variable": name,
        "label": label or f"Label {name}",
        "data_type": data_type,
        "value_label_count": len(values),
        "value_labels": values,
        "missing_user_values": [99] if name == "choice" else [],
        "missing_ranges": [],
        "questionnaire_evidence": [],
    }


def _inputs():
    labels = [
        {"raw_value": 2, "label": "Second"},
        {"raw_value": 1, "label": "First"},
    ]
    analysis = {
        "schema_version": "EXPLORA_SOURCE_ANALYSIS_V1",
        "authority": "SOURCE_EVIDENCE_ONLY",
        "dataset": {"filename": "source.sav", "sha256": "A" * 64, "n_cases": 3, "n_variables": 12},
        "questionnaire": {"filename": "source.docx", "sha256": "B" * 64},
        "datamap": {"filename": "map.csv", "sha256": "C" * 64},
        "variables": [
            _variable("respondent_id", labels=[], data_type="STRING"),
            _variable("choice", labels=labels),
            _variable("multi_1", labels=labels),
            _variable("multi_2", labels=labels),
            _variable("repeat.2", labels=labels),
            _variable("repeat.10", labels=labels),
            _variable("measure.2", labels=[], data_type="NUMBER"),
            _variable("measure.10", labels=[], data_type="NUMBER"),
            _variable("control", labels=[]),
            _variable("grid_r1", labels=labels),
            _variable("age", labels=[], data_type="NUMBER"),
        ],
    }
    items = [
        ("VAR::respondent_id", "RESPONDENT_ID", ["respondent_id"], "APPROVED"),
        ("VAR::choice", "RU", ["choice"], "APPROVED"),
        ("RM::multi", "RM", ["multi_1", "multi_2"], "APPROVED"),
        ("LOOP::repeat", "LOOP_RU", ["repeat.10", "repeat.2"], "APPROVED"),
        ("LOOP::measure", "LOOP_NUMERICO", ["measure.10", "measure.2"], "APPROVED"),
        ("VAR::control", "META_CONTROL", ["control"], "APPROVED"),
        ("GRID::grid", "GRID_ESCALA", ["grid_r1"], "EXCLUDED"),
        ("VAR::age", "NUMERIC", ["age"], "EXCLUDED"),
    ]
    review_items = [{
        "item_id": item_id,
        "source_kind": "GROUP" if "::" in item_id and not item_id.startswith("VAR::") else "VARIABLE",
        "variables": variables,
        "proposed_type": final_type,
        "final_type": final_type,
        "review_state": state,
        "capability_status": "QUALIFIED" if final_type in {"RU", "RM", "LOOP_RU", "LOOP_NUMERICO"} else "CONFIG_ROLE",
        "authority": "HUMAN_APPROVED" if state == "APPROVED" else "HUMAN_EXCLUDED",
    } for item_id, final_type, variables, state in items]
    review = {
        "schema_version": "EXPLORA_STRUCTURE_REVIEW_V1",
        "authority": "HUMAN_REVIEWED",
        "status": "READY_FOR_PROJECT_SPEC_DRAFT",
        "items": review_items,
        "summary": {"pending_items": 0, "capability_gaps": []},
    }
    metadata = {
        "project_id": "SYNTHETIC_PROJECT",
        "display_name": "Synthetic Project",
        "project_version": "1.0.0",
        "spec_version": "1.0.0",
    }
    return analysis, review, metadata


def _draft():
    result = author_project_spec_draft(*_inputs())
    assert result.project_spec is not None
    return result, result.project_spec


def _question(spec, question_id):
    return next(item for item in spec["questions"] if item["question_id"] == question_id)


def test_g50_01_ready_review_creates_valid_draft():
    result, spec = _draft()
    assert result.status == "DRAFT_VALID"
    assert validate_project(spec).ready_for_execution


def test_g50_02_pending_review_fails_closed():
    analysis, review, metadata = _inputs()
    review["status"] = "NEEDS_HUMAN_DECISION"
    assert author_project_spec_draft(analysis, review, metadata).status == "DRAFT_REQUIRES_HUMAN_DECISION"


def test_g50_03_capability_gap_review_fails_closed():
    analysis, review, metadata = _inputs()
    review["status"] = "CAPABILITY_GAP"
    assert author_project_spec_draft(analysis, review, metadata).project_spec is None


def test_g50_04_ru_authoring():
    _, spec = _draft()
    assert _question(spec, "CHOICE")["question_type"] == "RU"


def test_g50_05_rm_authoring():
    _, spec = _draft()
    assert _question(spec, "MULTI")["source_variables"] == ["multi_1", "multi_2"]


def test_g50_06_loop_ru_authoring_preserves_parent():
    _, spec = _draft()
    question = _question(spec, "REPEAT")
    assert question["question_type"] == "LOOP_RU"
    assert question["structure_ref"] == "STRUCTURE_REPEAT"


def test_g50_07_loop_numeric_authoring():
    _, spec = _draft()
    assert _question(spec, "MEASURE")["question_type"] == "LOOP_NUMERICO"


def test_g50_08_excluded_grid_is_not_executable():
    result, spec = _draft()
    assert all(item["question_type"] != "GRID_ESCALA" for item in spec["questions"])
    assert any(item["final_type"] == "GRID_ESCALA" for item in result.authoring_evidence["excluded_items"])


def test_g50_09_excluded_numeric_is_not_executable():
    result, spec = _draft()
    assert all(item["question_type"] != "NUMERIC" for item in spec["questions"])
    assert any(item["final_type"] == "NUMERIC" for item in result.authoring_evidence["excluded_items"])


def test_g50_10_meta_control_is_configuration_only():
    result, spec = _draft()
    assert "control" in result.authoring_evidence["available_configuration_variables"]
    assert all("control" not in item["source_variables"] for item in spec["questions"])


def test_g50_11_one_approved_respondent_id_is_accepted():
    _, spec = _draft()
    assert spec["dataset"]["respondent_id_variable"] == "respondent_id"


def test_g50_12_zero_respondent_id_fails_closed():
    analysis, review, metadata = _inputs()
    review["items"] = [item for item in review["items"] if item["final_type"] != "RESPONDENT_ID"]
    result = author_project_spec_draft(analysis, review, metadata)
    assert any(item["code"] == "HUMAN_RESPONDENT_ID_REQUIRED" for item in result.errors)


def test_g50_13_multiple_respondent_ids_fail_closed():
    analysis, review, metadata = _inputs()
    review["items"].append(deepcopy(review["items"][0]))
    result = author_project_spec_draft(analysis, review, metadata)
    assert result.status == "DRAFT_REQUIRES_HUMAN_DECISION"


def test_g50_14_category_order_is_deterministic():
    _, spec = _draft()
    assert [item["raw_value"] for item in _question(spec, "CHOICE")["categories"]] == [1, 2]


def test_g50_15_loop_iteration_order_is_natural_and_deterministic():
    _, spec = _draft()
    assert [item["variable_ref"] for item in _question(spec, "REPEAT")["loop_iterations"]] == ["repeat.2", "repeat.10"]


def test_g50_16_dataset_fingerprint_is_preserved():
    _, spec = _draft()
    assert spec["dataset"]["fingerprint"] == "sha256:" + "a" * 64


def test_g50_17_questionnaire_fingerprint_is_preserved():
    _, spec = _draft()
    assert "sha256:" + "b" * 64 in spec["source_metadata_fingerprints"]


def test_g50_18_structure_review_provenance_is_preserved():
    result, spec = _draft()
    ref = "structure_review_sha256:" + result.authoring_evidence["structure_review_fingerprint"].upper()
    assert ref in spec["provenance"]["source_refs"]


def test_g50_19_project_spec_fingerprint_matches_canonical_bytes():
    result, spec = _draft()
    import hashlib
    assert result.project_spec_fingerprint == hashlib.sha256(canonical_draft_json(spec).encode()).hexdigest()


def test_g50_20_identical_input_produces_identical_draft():
    one = author_project_spec_draft(*_inputs())
    two = author_project_spec_draft(*_inputs())
    assert canonical_draft_json(one.project_spec) == canonical_draft_json(two.project_spec)


def test_g50_21_significance_is_never_auto_authored():
    _, spec = _draft()
    assert spec["significance_requests"] == []


def test_g50_22_weight_is_not_inferred():
    _, spec = _draft()
    assert spec["weights"] == [] and spec["default_weight_ref"] is None


def test_g50_23_banners_and_filters_are_empty_until_configured():
    _, spec = _draft()
    assert spec["banners"] == [] and spec["filters"] == []


def test_g50_24_output_is_web_only():
    _, spec = _draft()
    assert spec["output_requests"][0]["web_included"] is True
    assert spec["output_requests"][0]["excel_included"] is False


def test_g50_25_existing_validate_project_is_called(monkeypatch):
    calls = []
    original = authoring.validate_project
    monkeypatch.setattr(authoring, "validate_project", lambda spec: calls.append(spec) or original(spec))
    result = author_project_spec_draft(*_inputs())
    assert result.status == "DRAFT_VALID" and len(calls) == 1


def test_g50_26_validator_rejection_is_draft_invalid():
    analysis, review, metadata = _inputs()
    next(item for item in analysis["variables"] if item["variable"] == "choice")["data_type"] = "UNSUPPORTED"
    result = author_project_spec_draft(analysis, review, metadata)
    assert result.status == "DRAFT_INVALID"
    assert any(item["code"] == "VARIABLE_TYPE" for item in result.errors)


def test_g50_27_no_customer_specific_hardcoding():
    source = Path("src/project_spec_authoring/authoring.py").read_text(encoding="utf-8").lower()
    forbidden = ["y" + "in", "p" + "11", "p" + "41", "c" + "1"]
    assert all(token not in source for token in forbidden)


def test_g50_28_authoring_has_no_statistical_execution_path():
    source = Path("src/project_spec_authoring/authoring.py").read_text(encoding="utf-8")
    assert "analytics_core" not in source
    assert "run_generic_productive" not in source
    assert PROJECT_SPEC_DRAFT_AUTHORING_VERSION in source


def test_g50_29_explicitly_approved_weight_maps_without_transformation():
    analysis, review, metadata = _inputs()
    analysis["variables"].append(_variable("weight", labels=[], data_type="NUMBER"))
    review["items"].append({
        "item_id": "VAR::weight", "variables": ["weight"], "proposed_type": "WEIGHT",
        "final_type": "WEIGHT", "review_state": "APPROVED", "authority": "HUMAN_APPROVED",
    })
    result = author_project_spec_draft(analysis, review, metadata)
    assert result.project_spec["weights"] == [{
        "weight_id": "WEIGHT_1", "variable_ref": "weight",
        "validation_state": "HUMAN_APPROVED_SOURCE_VARIABLE",
        "normalization": "NONE", "trimming": "NONE", "policy_ref": "B1_V1",
    }]


def test_g50_30_required_operator_metadata_is_not_inferred():
    analysis, review, metadata = _inputs()
    metadata["project_id"] = ""
    result = author_project_spec_draft(analysis, review, metadata)
    assert result.project_spec is None
    assert any(item["code"] == "HUMAN_PROJECT_METADATA_REQUIRED" for item in result.errors)


def test_g50_31_missing_approved_source_variable_fails_closed():
    analysis, review, metadata = _inputs()
    analysis["variables"] = [item for item in analysis["variables"] if item["variable"] != "choice"]
    result = author_project_spec_draft(analysis, review, metadata)
    assert any(item["code"] == "SOURCE_VARIABLE_MISSING" for item in result.errors)


def test_g50_32_incompatible_category_metadata_requires_human_decision():
    analysis, review, metadata = _inputs()
    next(item for item in analysis["variables"] if item["variable"] == "multi_2")["value_labels"][0]["label"] = "Different"
    result = author_project_spec_draft(analysis, review, metadata)
    assert result.status == "DRAFT_REQUIRES_HUMAN_DECISION"
    assert any(item["code"] == "CATEGORY_METADATA_INCOMPATIBLE" for item in result.ambiguities)


def test_g50_33_incomplete_loop_mapping_fails_closed():
    analysis, review, metadata = _inputs()
    next(item for item in review["items"] if item["item_id"] == "LOOP::repeat")["variables"] = ["repeat.2"]
    result = author_project_spec_draft(analysis, review, metadata)
    assert any(item["code"] == "LOOP_ITERATION_MAPPING_INCOMPLETE" for item in result.errors)


def test_g50_34_duplicate_logical_question_identity_fails_closed():
    analysis, review, metadata = _inputs()
    duplicate = deepcopy(next(item for item in review["items"] if item["item_id"] == "VAR::choice"))
    duplicate["item_id"] = "GROUP::choice"
    review["items"].append(duplicate)
    result = author_project_spec_draft(analysis, review, metadata)
    assert any(item["code"] == "DUPLICATE_LOGICAL_QUESTION" for item in result.errors)


def test_g50_35_approved_unqualified_type_fails_closed():
    analysis, review, metadata = _inputs()
    grid = next(item for item in review["items"] if item["final_type"] == "GRID_ESCALA")
    grid["review_state"] = "APPROVED"
    result = author_project_spec_draft(analysis, review, metadata)
    assert any(item["code"] == "HUMAN_UNSUPPORTED_ANALYTICAL_TYPE" for item in result.errors)


def test_g50_36_operator_console_confirms_saved_project_spec_transition():
    source = Path("operator_console.py").read_text(encoding="utf-8")
    assert "Generando Project Spec Draft..." in source
    assert "Project Spec generado y guardado: READY_FOR_EXECUTION" in source
    assert "Continúa en la pestaña 4. Decisiones." in source
