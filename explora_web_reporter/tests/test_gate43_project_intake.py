from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.project_intake import (
    PROJECT_SPEC_SCHEMA_VERSION,
    canonical_project_spec_json,
    project_spec_fingerprint,
    validate_project,
)


FIXTURES = Path(__file__).parent / "fixtures" / "gate43"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_machine_readable_schema_is_versioned_and_declares_required_domains() -> None:
    schema_path = Path(__file__).parents[1] / "src" / "project_intake" / "explora_project_spec_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["title"] == PROJECT_SPEC_SCHEMA_VERSION
    assert schema["properties"]["schema_version"]["const"] == PROJECT_SPEC_SCHEMA_VERSION
    assert {"project", "dataset", "questions", "universes", "provenance"} <= set(schema["required"])


@pytest.mark.parametrize("fixture", ["minimal_project_spec.json", "representative_project_spec.json"])
def test_valid_fixtures_are_ready_for_execution(fixture: str) -> None:
    result = validate_project(FIXTURES / fixture)
    assert result.validation_status == "READY_FOR_EXECUTION"
    assert result.ready_for_execution
    assert result.errors == ()


def test_representative_fixture_covers_supported_intake_domains() -> None:
    spec = load("representative_project_spec.json")
    assert {item["question_type"] for item in spec["questions"]} >= {"RU", "PARENT_RM", "MENTION", "SCALE"}
    assert spec["weights"] and spec["banners"] and spec["filters"]
    assert spec["significance_requests"][0]["policy_ref"] == "B2_V1"
    assert spec["output_requests"][0]["web_included"]
    assert spec["output_requests"][0]["excel_included"]


def test_serialization_round_trip_and_fingerprint_are_deterministic() -> None:
    spec = load("representative_project_spec.json")
    reordered = dict(reversed(list(spec.items())))
    canonical = canonical_project_spec_json(spec)
    assert json.loads(canonical) == spec
    assert canonical == canonical_project_spec_json(reordered)
    assert project_spec_fingerprint(spec) == project_spec_fingerprint(reordered)
    assert validate_project(spec).project_spec_fingerprint == project_spec_fingerprint(spec)


def test_source_fingerprints_are_normalized_deterministically() -> None:
    result = validate_project(FIXTURES / "representative_project_spec.json")
    assert result.source_fingerprints == tuple(sorted(result.source_fingerprints))
    assert "sha256:representative-dataset" in result.source_fingerprints


def mutate(spec: dict, mutation: str) -> None:
    if mutation == "unknown_question_variable":
        spec["questions"][0]["source_variables"] = ["absent"]
    elif mutation == "unknown_weight_variable":
        spec["weights"] = [{"weight_id": "W", "variable_ref": "absent", "negative_values_observed": False, "normalization": "NONE", "trimming": "NONE"}]
    elif mutation == "negative_weight":
        spec["weights"] = [{"weight_id": "W", "variable_ref": "q1", "negative_values_observed": True, "normalization": "NONE", "trimming": "NONE"}]
    elif mutation == "unmatched_rm_member":
        spec["questions"][0].update({"question_type": "MENTION", "parent_question_ref": "ABSENT"})
    elif mutation == "contradictory_category":
        duplicate = deepcopy(spec["questions"][0]["categories"][0]); duplicate.update({"category_id": "Q1_OTHER", "label": "Contradiction"}); spec["questions"][0]["categories"].append(duplicate)
    elif mutation == "ambiguous_universe":
        spec["universes"][0]["rule_state"] = "AMBIGUOUS"
    elif mutation == "unsupported_question_type":
        spec["questions"][0]["question_type"] = "FREE_TEXT_AI"
    elif mutation == "duplicate_question":
        spec["questions"].append(deepcopy(spec["questions"][0]))
    elif mutation == "invalid_confidence":
        spec["significance_requests"] = [{"significance_request_id": "SIG", "confidence": 0.975, "policy_ref": "B2_V1"}]
    elif mutation == "missing_project_id":
        del spec["project"]["project_id"]
    elif mutation == "invalid_output_reference":
        spec["output_requests"][0]["banner_refs"] = ["ABSENT"]
    elif mutation == "ai_requires_human":
        spec["ai_interpretations"] = [{"decision_id": "AI_1", "source_evidence": "questionnaire:p1", "proposed_interpretation": "Universe proposal", "human_approval_required": True, "release_state": "PROPOSED", "provenance": "B3_V1"}]
    else:
        raise AssertionError(mutation)


@pytest.mark.parametrize("case", load("invalid_ambiguous_cases.json"), ids=lambda case: case["case_id"])
def test_invalid_and_ambiguous_fixtures_fail_closed(case: dict) -> None:
    spec = load("minimal_project_spec.json")
    mutate(spec, case["mutation"])
    result = validate_project(spec)
    assert result.validation_status == case["expected_status"]
    assert not result.ready_for_execution
    assert case["expected_code"] in {item.code for item in result.errors}


def test_intake_result_is_not_a_statistical_result() -> None:
    result = validate_project(FIXTURES / "minimal_project_spec.json")
    assert not hasattr(result, "values")
    assert not hasattr(result, "bases")
    assert not hasattr(result, "significance_relations")


def test_display_intent_cannot_change_analytical_payload() -> None:
    spec = load("minimal_project_spec.json")
    baseline = validate_project(spec)
    spec["output_requests"][0].update({"display_decimals": 3, "web_included": False})
    changed = validate_project(spec)
    assert baseline.ready_for_execution and changed.ready_for_execution
    assert spec["questions"] == load("minimal_project_spec.json")["questions"]


def test_policy_authority_is_fail_closed() -> None:
    spec = load("minimal_project_spec.json")
    spec["provenance"]["b1_policy_ref"] = "CUSTOM"
    result = validate_project(spec)
    assert result.validation_status == "VALIDATION_FAILED"
    assert "POLICY_AUTHORITY" in {item.code for item in result.errors}
