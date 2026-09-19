from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


PROJECT_SPEC_SCHEMA_VERSION = "EXPLORA_PROJECT_SPEC_V1"
SUPPORTED_QUESTION_TYPES = {
    "RU", "RM", "MENTION", "PARENT_RM", "NUMERIC", "SCALE",
    "GRID_ESCALA", "GRID_RM", "LOOP_RM", "LOOP_RU", "LOOP_NUMERICO",
}
VALID_STATUSES = {
    "DRAFT", "VALIDATION_FAILED", "NEEDS_HUMAN_DECISION",
    "READY_FOR_EXECUTION", "EXECUTED", "QA_FAILED", "RELEASE_CANDIDATE",
}
ISSUE_LEVELS = {"INFORMATIONAL", "WARNING", "BLOCKING", "HUMAN_DECISION_REQUIRED"}


@dataclass(frozen=True)
class IntakeIssue:
    code: str
    level: str
    path: str
    message: str


@dataclass(frozen=True)
class IntakeResult:
    schema_version: str
    project_id: str | None
    spec_version: str | None
    project_spec_fingerprint: str
    source_fingerprints: tuple[str, ...]
    validation_status: str
    errors: tuple[IntakeIssue, ...]
    warnings: tuple[IntakeIssue, ...]
    ambiguity_decisions: tuple[str, ...]
    unsupported_capabilities: tuple[str, ...]
    ready_for_execution: bool


def _load(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return json.loads(json.dumps(value))
    with Path(value).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("Project Spec root must be an object")
    return payload


def canonical_project_spec_json(value: Mapping[str, Any] | str | Path) -> str:
    payload = _load(value)
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def project_spec_fingerprint(value: Mapping[str, Any] | str | Path) -> str:
    return hashlib.sha256(canonical_project_spec_json(value).encode("utf-8")).hexdigest()


def validate_project(value: Mapping[str, Any] | str | Path) -> IntakeResult:
    spec = _load(value)
    issues: list[IntakeIssue] = []
    unsupported: list[str] = []

    def issue(code: str, level: str, path: str, message: str) -> None:
        issues.append(IntakeIssue(code, level, path, message))

    def required_text(container: Mapping[str, Any], key: str, path: str) -> str | None:
        candidate = container.get(key)
        if not isinstance(candidate, str) or not candidate.strip():
            issue("REQUIRED_FIELD", "BLOCKING", f"{path}.{key}", f"{key} is required")
            return None
        return candidate

    if spec.get("schema_version") != PROJECT_SPEC_SCHEMA_VERSION:
        issue("UNSUPPORTED_SCHEMA", "BLOCKING", "schema_version", "Unsupported Project Spec schema")
    project = spec.get("project") if isinstance(spec.get("project"), dict) else {}
    project_id = required_text(project, "project_id", "project")
    required_text(project, "display_name", "project")
    required_text(project, "project_version", "project")
    spec_version = required_text(project, "spec_version", "project")

    dataset = spec.get("dataset") if isinstance(spec.get("dataset"), dict) else {}
    required_text(dataset, "source_id", "dataset")
    required_text(dataset, "input_type", "dataset")
    fingerprint = required_text(dataset, "fingerprint", "dataset")
    required_text(dataset, "respondent_id_variable", "dataset")
    if dataset.get("duplicate_row_policy") not in {"FAIL", "ALLOW_EXPLICIT"}:
        issue("DUPLICATE_POLICY", "BLOCKING", "dataset.duplicate_row_policy", "Duplicate-row policy must be explicit")
    variables = dataset.get("variables") if isinstance(dataset.get("variables"), list) else []
    variable_names = _unique_ids(variables, "variable_id", "dataset.variables", issue)
    for index, variable in enumerate(variables):
        if variable.get("data_type") not in {"INTEGER", "NUMBER", "STRING", "BOOLEAN", "DATE"}:
            issue("VARIABLE_TYPE", "BLOCKING", f"dataset.variables[{index}].data_type", "Unsupported variable data type")

    questions = spec.get("questions") if isinstance(spec.get("questions"), list) else []
    question_ids = _unique_ids(questions, "question_id", "questions", issue)
    category_ids: set[str] = set()
    for q_index, question in enumerate(questions):
        qtype = question.get("question_type")
        if qtype not in SUPPORTED_QUESTION_TYPES:
            issue("UNSUPPORTED_QUESTION_TYPE", "BLOCKING", f"questions[{q_index}].question_type", "Question type is not supported by current Core")
            unsupported.append(str(qtype))
        source_variables = question.get("source_variables", [])
        for source in source_variables:
            if source not in variable_names:
                issue("UNKNOWN_DATASET_VARIABLE", "BLOCKING", f"questions[{q_index}].source_variables", f"Unknown variable: {source}")
        categories = question.get("categories", [])
        raw_labels: dict[str, str] = {}
        local_ids = _unique_ids(categories, "category_id", f"questions[{q_index}].categories", issue)
        category_ids.update(local_ids)
        for c_index, category in enumerate(categories):
            raw_key = json.dumps(category.get("raw_value"), sort_keys=True)
            label = str(category.get("label", ""))
            if raw_key in raw_labels and raw_labels[raw_key] != label:
                issue("CONTRADICTORY_CATEGORY", "BLOCKING", f"questions[{q_index}].categories[{c_index}]", "One raw value has contradictory labels")
            raw_labels[raw_key] = label
        if qtype == "MENTION" and question.get("parent_question_ref") not in question_ids:
            issue("UNMATCHED_RM_MEMBER", "BLOCKING", f"questions[{q_index}].parent_question_ref", "Mention must reference a declared parent question")

    universes = spec.get("universes") if isinstance(spec.get("universes"), list) else []
    universe_ids = _unique_ids(universes, "universe_id", "universes", issue)
    for index, universe in enumerate(universes):
        if universe.get("rule_state") == "AMBIGUOUS":
            issue("AMBIGUOUS_UNIVERSE", "HUMAN_DECISION_REQUIRED", f"universes[{index}]", "Universe requires an accepted deterministic rule")
        if not isinstance(universe.get("expression"), dict):
            issue("UNIVERSE_EXPRESSION", "BLOCKING", f"universes[{index}].expression", "Universe expression must be structured")
    for index, question in enumerate(questions):
        if question.get("universe_ref") not in universe_ids:
            issue("UNKNOWN_UNIVERSE", "BLOCKING", f"questions[{index}].universe_ref", "Question references an unknown universe")

    weights = spec.get("weights") if isinstance(spec.get("weights"), list) else []
    weight_ids = _unique_ids(weights, "weight_id", "weights", issue)
    for index, weight in enumerate(weights):
        if weight.get("variable_ref") not in variable_names:
            issue("UNKNOWN_WEIGHT_VARIABLE", "BLOCKING", f"weights[{index}].variable_ref", "Weight variable is absent")
        if weight.get("negative_values_observed") is True:
            issue("NEGATIVE_WEIGHT", "BLOCKING", f"weights[{index}]", "Negative weights are unsupported by B1 V1")
        if weight.get("normalization", "NONE") != "NONE" or weight.get("trimming", "NONE") != "NONE":
            issue("B1_POLICY_CONFLICT", "BLOCKING", f"weights[{index}]", "B1 V1 forbids implicit normalization or trimming")
    default_weight = spec.get("default_weight_ref")
    if default_weight is not None and default_weight not in weight_ids:
        issue("UNKNOWN_DEFAULT_WEIGHT", "BLOCKING", "default_weight_ref", "Default weight is not declared")

    banner_ids = _validate_rules(spec, "banners", "banner_id", variable_names, universe_ids, issue)
    filter_ids = _validate_rules(spec, "filters", "filter_id", variable_names, universe_ids, issue)
    significance = spec.get("significance_requests") if isinstance(spec.get("significance_requests"), list) else []
    _unique_ids(significance, "significance_request_id", "significance_requests", issue)
    for index, request in enumerate(significance):
        if request.get("confidence") not in {0.90, 0.95, 0.99}:
            issue("INVALID_CONFIDENCE", "BLOCKING", f"significance_requests[{index}].confidence", "B2 supports 0.90, 0.95, or 0.99")
        if request.get("policy_ref") != "B2_V1":
            issue("B2_POLICY_REF", "BLOCKING", f"significance_requests[{index}].policy_ref", "Significance must reference B2_V1")

    outputs = spec.get("output_requests") if isinstance(spec.get("output_requests"), list) else []
    for index, output in enumerate(outputs):
        for ref in output.get("banner_refs", []):
            if ref not in banner_ids:
                issue("UNKNOWN_BANNER", "BLOCKING", f"output_requests[{index}].banner_refs", f"Unknown banner: {ref}")
        for ref in output.get("filter_refs", []):
            if ref not in filter_ids:
                issue("UNKNOWN_FILTER", "BLOCKING", f"output_requests[{index}].filter_refs", f"Unknown filter: {ref}")

    ambiguity_ids: list[str] = []
    ambiguities = spec.get("ambiguities") if isinstance(spec.get("ambiguities"), list) else []
    _unique_ids(ambiguities, "ambiguity_id", "ambiguities", issue)
    for index, ambiguity in enumerate(ambiguities):
        level = ambiguity.get("classification")
        if level not in ISSUE_LEVELS:
            issue("AMBIGUITY_CLASS", "BLOCKING", f"ambiguities[{index}].classification", "Invalid ambiguity classification")
        if level in {"BLOCKING", "HUMAN_DECISION_REQUIRED"} and ambiguity.get("state") != "RESOLVED":
            issue("UNRESOLVED_AMBIGUITY", level, f"ambiguities[{index}]", "Material ambiguity is unresolved")
            ambiguity_ids.append(str(ambiguity.get("ambiguity_id", "")))

    ai_decisions = spec.get("ai_interpretations") if isinstance(spec.get("ai_interpretations"), list) else []
    _unique_ids(ai_decisions, "decision_id", "ai_interpretations", issue)
    for index, decision in enumerate(ai_decisions):
        for key in ("source_evidence", "proposed_interpretation", "release_state", "provenance"):
            required_text(decision, key, f"ai_interpretations[{index}]")
        if decision.get("human_approval_required") and decision.get("release_state") != "HUMAN_APPROVED":
            issue("AI_HUMAN_APPROVAL_REQUIRED", "HUMAN_DECISION_REQUIRED", f"ai_interpretations[{index}]", "B3 requires human approval before release")
            ambiguity_ids.append(str(decision.get("decision_id", "")))

    provenance = spec.get("provenance") if isinstance(spec.get("provenance"), dict) else {}
    for key in ("created_at", "created_by", "source_refs", "b1_policy_ref", "b2_policy_ref", "b3_policy_ref"):
        if not provenance.get(key):
            issue("PROVENANCE_REQUIRED", "BLOCKING", f"provenance.{key}", "Reproducibility provenance is required")
    if provenance.get("b1_policy_ref") != "B1_V1" or provenance.get("b2_policy_ref") != "B2_V1" or provenance.get("b3_policy_ref") != "B3_V1":
        issue("POLICY_AUTHORITY", "BLOCKING", "provenance", "Project Spec must preserve B1/B2/B3 authority")

    errors = tuple(item for item in issues if item.level in {"BLOCKING", "HUMAN_DECISION_REQUIRED"})
    warnings = tuple(item for item in issues if item.level in {"WARNING", "INFORMATIONAL"})
    needs_human = any(item.level == "HUMAN_DECISION_REQUIRED" for item in errors)
    status = "NEEDS_HUMAN_DECISION" if needs_human else "VALIDATION_FAILED" if errors else "READY_FOR_EXECUTION"
    if status not in VALID_STATUSES:
        raise AssertionError("invalid internal intake status")
    source_fingerprints = tuple(sorted(filter(None, [fingerprint, *spec.get("source_metadata_fingerprints", [])])))
    return IntakeResult(
        schema_version=PROJECT_SPEC_SCHEMA_VERSION,
        project_id=project_id,
        spec_version=spec_version,
        project_spec_fingerprint=project_spec_fingerprint(spec),
        source_fingerprints=source_fingerprints,
        validation_status=status,
        errors=errors,
        warnings=warnings,
        ambiguity_decisions=tuple(sorted(set(filter(None, ambiguity_ids)))),
        unsupported_capabilities=tuple(sorted(set(unsupported))),
        ready_for_execution=status == "READY_FOR_EXECUTION",
    )


def _unique_ids(items: list[Any], key: str, path: str, issue: Any) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        value = item.get(key) if isinstance(item, dict) else None
        if not isinstance(value, str) or not value.strip():
            issue("STABLE_ID_REQUIRED", "BLOCKING", f"{path}[{index}].{key}", f"{key} is required")
        elif value in seen:
            issue("DUPLICATE_STABLE_ID", "BLOCKING", f"{path}[{index}].{key}", f"Duplicate stable ID: {value}")
        else:
            seen.add(value)
    return seen


def _validate_rules(spec: dict[str, Any], section: str, id_key: str, variables: set[str], universes: set[str], issue: Any) -> set[str]:
    rules = spec.get(section) if isinstance(spec.get(section), list) else []
    ids = _unique_ids(rules, id_key, section, issue)
    for index, rule in enumerate(rules):
        if rule.get("variable_ref") not in variables:
            issue("UNKNOWN_RULE_VARIABLE", "BLOCKING", f"{section}[{index}].variable_ref", "Rule variable is absent")
        if rule.get("universe_ref") not in universes:
            issue("UNKNOWN_RULE_UNIVERSE", "BLOCKING", f"{section}[{index}].universe_ref", "Rule universe is absent")
        if not isinstance(rule.get("rule"), dict):
            issue("RULE_EXPRESSION", "BLOCKING", f"{section}[{index}].rule", "Rule must be structured")
    return ids
