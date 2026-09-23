from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from src.analytics_core.formula_registry import FORMULA_REGISTRY_VERSION
from src.package_authoring.contract import PackageAuthoringError, validate_execution_release
from src.project_intake.contract import project_spec_fingerprint, validate_project


EXECUTION_RELEASE_DRAFT_AUTHORING_VERSION = "EXPLORA_EXECUTION_RELEASE_DRAFT_AUTHORING_V1"
QUALIFIED_TYPES = {"RU", "RM", "LOOP_RU", "LOOP_NUMERICO"}
REQUIRED_METADATA = (
    "release_spec_id", "release_spec_version", "package_id", "package_version",
    "dataset_version", "internal_project_name",
)
REQUIRED_AUTHORITY = (
    "dataset_filename", "dataset_sha256", "questionnaire_filename",
    "questionnaire_sha256", "datamap_ref",
)


@dataclass(frozen=True)
class ExecutionReleaseDraftResult:
    status: str
    execution_release: dict[str, Any] | None
    execution_release_fingerprint: str | None
    errors: tuple[dict[str, str], ...]
    warnings: tuple[dict[str, str], ...]
    b3_status: str


def canonical_release_json(release: Mapping[str, Any]) -> str:
    return json.dumps(release, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _result(status: str, errors: list[dict[str, str]], release=None):
    fingerprint = None if release is None else sha256(canonical_release_json(release).encode()).hexdigest()
    return ExecutionReleaseDraftResult(status, release, fingerprint, tuple(errors), (), "PENDING_HUMAN_RELEASE")


def _weight_mode(project: Mapping[str, Any]) -> tuple[str, str | None, str]:
    default = project.get("default_weight_ref")
    if default:
        return "weighted", None, "PROJECT_DEFAULT"
    return "unweighted", None, "EXPLICITLY_UNWEIGHTED"


def _canonical_states(value: Any, path: str, errors: list[dict[str, str]]) -> list[Any] | None:
    if not isinstance(value, (list, tuple)) or not value:
        errors.append(_issue("RM_RESPONSE_STATE_REQUIRED", path, "An explicit non-empty response-state list is required."))
        return None
    states = list(value)
    try:
        encoded = [json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False) for item in states]
    except (TypeError, ValueError):
        errors.append(_issue("RM_RESPONSE_STATE_INVALID", path, "Response states must be canonically serializable."))
        return None
    if len(encoded) != len(set(encoded)):
        errors.append(_issue("RM_RESPONSE_STATE_DUPLICATE", path, "Response states must not contain duplicates."))
        return None
    return [item for _, item in sorted(zip(encoded, states), key=lambda pair: pair[0])]


def _rm_authority(
    question: Mapping[str, Any],
    configured: Mapping[str, Any] | None,
    errors: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, list[Any]]] | None:
    qid = question["question_id"]
    if not isinstance(configured, Mapping):
        errors.append(_issue("RM_RESPONSE_STATE_AUTHORITY_REQUIRED", f"rm_response_states.{qid}", "RM physical response states require an explicit human/configuration decision."))
        return None
    required = {"selected_values", "not_selected_values", "ordinary_missing_values"}
    if set(configured) != required:
        errors.append(_issue("RM_RESPONSE_STATE_AUTHORITY_INVALID", f"rm_response_states.{qid}", "RM authority fields must be selected_values, not_selected_values, and ordinary_missing_values."))
        return None
    states = {name: _canonical_states(configured.get(name), f"rm_response_states.{qid}.{name}", errors) for name in sorted(required)}
    if any(value is None for value in states.values()):
        return None
    encoded = {name: {canonical_release_json({"value": item}) for item in values} for name, values in states.items()}
    if any(encoded[left] & encoded[right] for index, left in enumerate(sorted(required)) for right in sorted(required)[index + 1:]):
        errors.append(_issue("RM_RESPONSE_STATES_OVERLAP", f"rm_response_states.{qid}", "RM response-state domains must be pairwise disjoint."))
        return None

    variables = question["source_variables"]
    categories = question.get("categories", [])
    label_evidence = categories if len(categories) == len(variables) else []
    bindings = []
    for index, variable in enumerate(variables):
        evidence = label_evidence[index] if label_evidence else None
        binding = {
            "option_id": str(evidence["category_id"]) if evidence else f"{qid}_OPTION_{index + 1}",
            "variable_ref": variable,
        }
        if evidence and isinstance(evidence.get("label"), str) and evidence["label"]:
            binding["label"] = evidence["label"]
        bindings.append(binding)
    return bindings, states  # type: ignore[return-value]


def author_execution_release_draft(
    project_spec: Mapping[str, Any],
    source_authority: Mapping[str, Any],
    operator_metadata: Mapping[str, Any],
    rm_response_states: Mapping[str, Mapping[str, Any]] | None = None,
) -> ExecutionReleaseDraftResult:
    errors: list[dict[str, str]] = []
    intake = validate_project(project_spec)
    if not intake.ready_for_execution:
        errors.append(_issue("PROJECT_SPEC_NOT_READY", "project_spec", "Project Spec must be READY_FOR_EXECUTION."))
    for key in REQUIRED_METADATA:
        if not isinstance(operator_metadata.get(key), str) or not operator_metadata[key].strip():
            errors.append(_issue("RELEASE_METADATA_REQUIRED", f"operator_metadata.{key}", f"{key} requires explicit operator input."))
    for key in REQUIRED_AUTHORITY:
        if not isinstance(source_authority.get(key), str) or not source_authority[key].strip():
            errors.append(_issue("SOURCE_AUTHORITY_REQUIRED", f"source_authority.{key}", f"{key} is required."))
    questions = list(project_spec.get("questions", []))
    unsupported = sorted({str(item.get("question_type")) for item in questions if item.get("question_type") not in QUALIFIED_TYPES})
    if unsupported:
        errors.append(_issue("UNSUPPORTED_QUESTION_TYPE", "project_spec.questions", f"Unqualified types: {', '.join(unsupported)}"))
    if project_spec.get("banners") or project_spec.get("filters"):
        errors.append(_issue("RELEASE_RULE_BINDINGS_REQUIRED", "project_spec", "Banner/filter release members require explicit configuration."))
    if project_spec.get("significance_requests"):
        errors.append(_issue("UNSUPPORTED_SIGNIFICANCE", "project_spec.significance_requests", "Significance is not auto-authored."))
    if errors:
        return _result("ER_DRAFT_REQUIRES_HUMAN_DECISION", errors)

    dataset_variables = {item["variable_id"]: item for item in project_spec["dataset"]["variables"]}
    released_questions, structures, metrics = [], [], []
    mode, weight_ref, weight_choice = _weight_mode(project_spec)
    for question in sorted(questions, key=lambda item: item["question_id"]):
        qid, qtype = question["question_id"], question["question_type"]
        structure_id, metric_id = question.get("structure_ref"), f"METRIC_{qid}"
        if not isinstance(structure_id, str) or not structure_id:
            errors.append(_issue("STRUCTURE_IDENTITY_REQUIRED", f"questions.{qid}.structure_ref", "Project Spec structure identity is required."))
            continue
        formula = "MEAN" if qtype == "LOOP_NUMERICO" else "RM_RESPONDENT_PROPORTION" if qtype == "RM" else "PROPORTION"
        released_questions.append({
            "question_id": qid,
            "analytical_role": "repeated_measure" if qtype.startswith("LOOP_") else "multiple_response" if qtype == "RM" else "single_response",
            "structure_ref": structure_id,
            "metric_refs": [metric_id],
            "weight_behavior": mode,
        })
        categories = question.get("categories", [])
        category_bindings = [{"category_id": item["category_id"], "raw_value": item["raw_value"], "label": item["label"]} for item in categories]
        missing = sorted({value for variable in question["source_variables"] for value in dataset_variables[variable].get("missing_values", [])}, key=str)
        structure = {
            "structure_id": structure_id, "question_id": qid, "structure_type": qtype,
            "category_bindings": category_bindings,
            "applicability_refs": {"question": question["universe_ref"]},
            "selected_values": [], "not_selected_values": [], "ordinary_missing_values": missing,
            "completion_policy": "explicit_response", "duplicate_policy": "error",
            "exclusive_option_ids": [], "storage_encoding": "multiple_numeric_variables" if len(question["source_variables"]) > 1 else "single_numeric_variable",
            "respondent_denominator_behavior": "VALID_RESPONSE", "response_state_version": "M4_STRUCTURE_V1",
        }
        if qtype == "RM":
            authority = _rm_authority(question, (rm_response_states or {}).get(qid), errors)
            if authority is None:
                continue
            option_bindings, response_states = authority
            structure.update({
                "option_bindings": option_bindings,
                **response_states,
                "completion_policy": "explicit_dichotomous_state_per_option",
                "storage_encoding": "dichotomous_columns",
                "respondent_denominator_behavior": "ELIGIBLE_RESPONDENT",
                "mention_denominator_behavior": "SELECTED_MENTIONS",
                "mention_denominator_scope": {"schema_version": "M4_MENTION_SCOPE_IDENTITY_V1", "scope_type": "PARENT_RM", "scope_ref": structure_id},
            })
        else:
            structure["variable_bindings"] = [{"variable_ref": variable} for variable in question["source_variables"]]
        if qtype.startswith("LOOP_"):
            iterations = question.get("loop_iterations", [])
            if len(iterations) != len(question["source_variables"]):
                errors.append(_issue("LOOP_ITERATION_MAPPING_INCOMPLETE", f"questions.{qid}", "Loop iteration mapping is incomplete."))
                continue
            structure["loop_iterations"] = [{
                "iteration_id": item["iteration_id"], "order": item["order"],
                "label": item.get("source_label") or item["iteration_id"],
                "variable_ref": item["variable_ref"],
                "response_domain": [category["raw_value"] for category in categories] if qtype == "LOOP_RU" else [],
            } for item in iterations]
            structure["variable_bindings"] = [{"binding_id": f"B_{index}", "variable_ref": item["variable_ref"], "loop_instance_id": item["iteration_id"]} for index, item in enumerate(iterations, 1)]
            structure["storage_encoding"] = "single_numeric_variable"
        structures.append(structure)
        metrics.append({
            "metric_id": metric_id, "metric_type": "MEAN" if qtype == "LOOP_NUMERICO" else "RM_RESPONDENT_PROPORTION" if qtype == "RM" else "PROPORTION",
            "formula_id": formula, "question_ref": qid, "universe_ref": question["universe_ref"],
            "denominator_policy": "ELIGIBLE_RESPONDENT" if qtype == "RM" else "VALID_RESPONSE", "missing_behavior": "EXCLUDE",
            "weight_behavior": mode, "significance": {"status": "none", "supported": False},
            "parameters": ({"mention_denominator_scope": {"schema_version": "M4_MENTION_SCOPE_IDENTITY_V1", "scope_type": "PARENT_RM", "scope_ref": structure_id}} if qtype == "RM" else {}),
        })
    if errors:
        return _result("ER_DRAFT_REQUIRES_HUMAN_DECISION", errors)

    weights = [{
        "weight_id": item["weight_id"], "variable_ref": item["variable_ref"],
        "provenance": "PROJECT_SPEC_HUMAN_APPROVED", "scope": "project",
        "permitted_analysis_overrides": [], "missing_policy": "EXCLUDE_AND_QA",
        "non_numeric_policy": "EXCLUDE_AND_QA", "non_finite_policy": "FAIL",
        "zero_policy": "VALID", "negative_policy": "UNSUPPORTED_V1",
        "normalization": item.get("normalization", "NONE"), "trimming": item.get("trimming", "NONE"),
        "weighted_significance": False,
    } for item in project_spec.get("weights", [])]
    requests = []
    metric_by_question = {item["question_ref"]: item["metric_id"] for item in metrics}
    question_by_id = {item["question_id"]: item for item in questions}
    for output in sorted(project_spec["output_requests"], key=lambda item: item["output_request_id"]):
        if output.get("excel_included") or not output.get("web_included"):
            errors.append(_issue("UNSUPPORTED_OUTPUT_INTENT", f"output_requests.{output['output_request_id']}", "Gate 51 supports WEB-only output intent."))
            continue
        for qid in sorted(output["question_refs"]):
            requests.append({
                "request_id": f"REQUEST_{output['output_request_id']}_{qid}", "output_request_ref": output["output_request_id"],
                "question_ref": qid, "metric_refs": [metric_by_question[qid]], "universe_ref": question_by_id[qid]["universe_ref"],
                "weight_ref": weight_ref, "weight_choice": weight_choice, "filters": [], "banner": None,
                "significance_ref": None, "significance_status": "NOT_REQUESTED", "purpose": "Project Spec WEB output",
            })
    if errors:
        return _result("ER_DRAFT_REQUIRES_HUMAN_DECISION", errors)
    release = {
        "schema_version": "EXPLORA_PROJECT_EXECUTION_RELEASE_V1",
        "release_spec_id": operator_metadata["release_spec_id"], "release_spec_version": operator_metadata["release_spec_version"],
        "project_id": project_spec["project"]["project_id"], "project_spec_fingerprint": project_spec_fingerprint(project_spec),
        "package": {**{key: operator_metadata[key] for key in ("package_id", "package_version", "dataset_version", "internal_project_name")}, "default_execution_mode": "LEGACY"},
        "source_authority": {
            "dataset_filename": source_authority["dataset_filename"], "dataset_sha256": source_authority["dataset_sha256"].upper(),
            "questionnaire_filename": source_authority["questionnaire_filename"], "questionnaire_sha256": source_authority["questionnaire_sha256"].upper(),
            "datamap_ref": source_authority["datamap_ref"], "mapping_authority": EXECUTION_RELEASE_DRAFT_AUTHORING_VERSION,
        },
        "policy_refs": {"b1": "B1_V1", "b2": "B2_V1", "b3": "B3_V1", "formula_registry": FORMULA_REGISTRY_VERSION},
        "release_decision": {"human_decision_id": None, "human_decision_basis": None, "release_mode": "MANUAL", "released_at": None, "approved": False},
        "questions": released_questions, "structures": structures, "metrics": metrics,
        "weights": weights, "banners": [], "filters": [], "significance": [], "requests": requests,
    }
    try:
        validate_execution_release(project_spec, release, require_approved=False)
    except (PackageAuthoringError, ValueError, KeyError, TypeError) as exc:
        return _result("ER_DRAFT_INVALID", [_issue("VALIDATION_FAILED", "execution_release", str(exc))], release)
    return _result("ER_DRAFT_VALID", [], release)
