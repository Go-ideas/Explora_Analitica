from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from src.project_intake.contract import IntakeResult, validate_project


PROJECT_SPEC_DRAFT_AUTHORING_VERSION = "EXPLORA_PROJECT_SPEC_DRAFT_AUTHORING_V1"
QUALIFIED_ANALYTICAL_TYPES = {"RU", "RM", "LOOP_RU", "LOOP_NUMERICO"}
CONFIGURATION_TYPES = {"RESPONDENT_ID", "WEIGHT", "META_CONTROL"}
REQUIRED_OPERATOR_METADATA = ("project_id", "display_name", "project_version", "spec_version")


@dataclass(frozen=True)
class DraftAuthoringResult:
    status: str
    project_spec: dict[str, Any] | None
    project_spec_fingerprint: str | None
    errors: tuple[dict[str, Any], ...]
    warnings: tuple[dict[str, Any], ...]
    ambiguities: tuple[dict[str, Any], ...]
    authoring_evidence: dict[str, Any]
    validation: IntakeResult | None


def canonical_draft_json(project_spec: Mapping[str, Any]) -> str:
    return json.dumps(project_spec, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Mapping[str, Any]) -> str:
    return sha256(canonical_draft_json(value).encode("utf-8")).hexdigest()


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _stable_id(value: str, *, fallback: str) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip()).strip("_").upper()
    return candidate or fallback


def _natural_key(value: str) -> tuple[Any, ...]:
    return tuple(int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value))


def _category_sort_key(item: Mapping[str, Any]) -> tuple[str, str]:
    raw = item.get("raw_value")
    return (type(raw).__name__, json.dumps(raw, ensure_ascii=True, sort_keys=True, default=str))


def _categories(
    question_id: str,
    variables: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    domains: list[list[dict[str, Any]]] = []
    for variable in variables:
        labels = variable.get("value_labels", [])
        if not isinstance(labels, list) or not labels:
            return [], _issue(
                "CATEGORY_METADATA_MISSING",
                f"variables.{variable.get('variable', '')}.value_labels",
                "Approved categorical structure has no deterministic SPSS value labels.",
            )
        domains.append(sorted(labels, key=_category_sort_key))
    canonical_domains = [
        [(item.get("raw_value"), str(item.get("label", ""))) for item in domain]
        for domain in domains
    ]
    if any(domain != canonical_domains[0] for domain in canonical_domains[1:]):
        return [], _issue(
            "CATEGORY_METADATA_INCOMPATIBLE",
            f"questions.{question_id}.categories",
            "Approved grouped variables have incompatible SPSS category domains.",
        )
    categories = []
    for order, item in enumerate(domains[0], start=1):
        raw_value = item.get("raw_value")
        label = str(item.get("label", "")).strip()
        if not label:
            return [], _issue(
                "CATEGORY_LABEL_MISSING",
                f"questions.{question_id}.categories[{order - 1}]",
                "SPSS category label is empty.",
            )
        identity = _canonical_hash(raw_value)[:12].upper()
        categories.append({
            "category_id": f"{question_id}_CAT_{identity}",
            "raw_value": raw_value,
            "canonical_value": str(raw_value),
            "label": label,
            "order": order,
            "included": True,
            "special": False,
        })
    return categories, None


def _result(
    status: str,
    *,
    errors: list[dict[str, Any]],
    evidence: dict[str, Any],
    project_spec: dict[str, Any] | None = None,
    validation: IntakeResult | None = None,
) -> DraftAuthoringResult:
    ambiguities = tuple(error for error in errors if error["code"].startswith(("CATEGORY_", "HUMAN_")))
    warnings = tuple(asdict(item) for item in validation.warnings) if validation else ()
    return DraftAuthoringResult(
        status=status,
        project_spec=project_spec,
        project_spec_fingerprint=None if project_spec is None else _fingerprint(project_spec),
        errors=tuple(errors),
        warnings=warnings,
        ambiguities=ambiguities,
        authoring_evidence=evidence,
        validation=validation,
    )


def author_project_spec_draft(
    source_analysis: Mapping[str, Any],
    structure_review: Mapping[str, Any],
    operator_metadata: Mapping[str, Any],
) -> DraftAuthoringResult:
    analysis_fp = _canonical_hash(source_analysis)
    review_fp = _canonical_hash(structure_review)
    evidence: dict[str, Any] = {
        "authoring_version": PROJECT_SPEC_DRAFT_AUTHORING_VERSION,
        "source_analysis_fingerprint": analysis_fp,
        "structure_review_fingerprint": review_fp,
        "human_review_authority": structure_review.get("authority"),
        "excluded_items": [],
        "available_configuration_variables": [],
        "authoring_rules": [
            "PROJECT_TOTAL_UNIVERSE_TRUE_EXPRESSION",
            "WEB_ONLY_OUTPUT_FOR_APPROVED_ANALYTICAL_QUESTIONS",
            "NO_WEIGHT_WHEN_NONE_HUMAN_APPROVED",
            "EMPTY_BANNERS_FILTERS_SIGNIFICANCE",
        ],
    }
    errors: list[dict[str, Any]] = []
    if source_analysis.get("schema_version") != "EXPLORA_SOURCE_ANALYSIS_V1":
        errors.append(_issue("SOURCE_ANALYSIS_SCHEMA", "source_analysis.schema_version", "EXPLORA_SOURCE_ANALYSIS_V1 is required."))
    if structure_review.get("schema_version") != "EXPLORA_STRUCTURE_REVIEW_V1":
        errors.append(_issue("STRUCTURE_REVIEW_SCHEMA", "structure_review.schema_version", "EXPLORA_STRUCTURE_REVIEW_V1 is required."))
    if structure_review.get("status") != "READY_FOR_PROJECT_SPEC_DRAFT":
        errors.append(_issue("HUMAN_REVIEW_NOT_READY", "structure_review.status", "Structure Review must be READY_FOR_PROJECT_SPEC_DRAFT."))
    for key in REQUIRED_OPERATOR_METADATA:
        if not isinstance(operator_metadata.get(key), str) or not str(operator_metadata[key]).strip():
            errors.append(_issue("HUMAN_PROJECT_METADATA_REQUIRED", f"operator_metadata.{key}", f"{key} requires explicit operator input."))
    if errors:
        return _result("DRAFT_REQUIRES_HUMAN_DECISION", errors=errors, evidence=evidence)

    variables = {
        str(item.get("variable")): item
        for item in source_analysis.get("variables", [])
        if isinstance(item, Mapping) and item.get("variable")
    }
    approved = [item for item in structure_review.get("items", []) if item.get("review_state") == "APPROVED"]
    excluded = [item for item in structure_review.get("items", []) if item.get("review_state") == "EXCLUDED"]
    evidence["excluded_items"] = [
        {"item_id": item.get("item_id"), "final_type": item.get("final_type"), "variables": list(item.get("variables", []))}
        for item in sorted(excluded, key=lambda item: str(item.get("item_id", "")))
    ]
    respondent_items = [item for item in approved if item.get("final_type") == "RESPONDENT_ID"]
    if len(respondent_items) != 1:
        errors.append(_issue(
            "HUMAN_RESPONDENT_ID_REQUIRED",
            "structure_review.items",
            "Exactly one human-approved respondent ID is required.",
        ))
    elif len(respondent_items[0].get("variables", [])) != 1:
        errors.append(_issue("HUMAN_RESPONDENT_ID_INVALID", "structure_review.items", "Respondent ID must bind exactly one source variable."))

    analytical = [item for item in approved if item.get("final_type") in QUALIFIED_ANALYTICAL_TYPES]
    unsupported = [
        item for item in approved
        if item.get("final_type") not in QUALIFIED_ANALYTICAL_TYPES | CONFIGURATION_TYPES
    ]
    for item in unsupported:
        errors.append(_issue(
            "HUMAN_UNSUPPORTED_ANALYTICAL_TYPE",
            f"structure_review.items.{item.get('item_id')}",
            f"Approved type {item.get('final_type')} is not qualified for draft authoring.",
        ))
    if not analytical:
        errors.append(_issue("HUMAN_ANALYTICAL_SCOPE_REQUIRED", "structure_review.items", "At least one qualified analytical item must be approved."))
    required_variables = {
        str(variable)
        for item in approved
        for variable in item.get("variables", [])
    }
    missing_variables = sorted(required_variables - set(variables))
    for variable in missing_variables:
        errors.append(_issue("SOURCE_VARIABLE_MISSING", f"source_analysis.variables.{variable}", "Approved source variable is absent."))
    if errors:
        return _result("DRAFT_REQUIRES_HUMAN_DECISION", errors=errors, evidence=evidence)

    questions: list[dict[str, Any]] = []
    seen_question_ids: set[str] = set()
    for item in sorted(analytical, key=lambda value: str(value.get("item_id", ""))):
        final_type = str(item["final_type"])
        source_variables = sorted((str(value) for value in item.get("variables", [])), key=_natural_key)
        if not source_variables:
            errors.append(_issue(
                "ANALYTICAL_BINDING_REQUIRED",
                f"structure_review.items.{item.get('item_id')}",
                "Approved analytical item has no source-variable binding.",
            ))
            continue
        if final_type.startswith("LOOP_") and len(source_variables) < 2:
            errors.append(_issue(
                "LOOP_ITERATION_MAPPING_INCOMPLETE",
                f"structure_review.items.{item.get('item_id')}.variables",
                "Qualified LOOP authoring requires at least two ordered member variables.",
            ))
            continue
        logical_name = str(item.get("item_id", "")).split("::", 1)[-1]
        question_id = _stable_id(logical_name, fallback="QUESTION")
        if question_id in seen_question_ids:
            errors.append(_issue("DUPLICATE_LOGICAL_QUESTION", f"questions.{question_id}", "Duplicate logical question identity."))
            continue
        seen_question_ids.add(question_id)
        source_rows = [variables[name] for name in source_variables]
        categories: list[dict[str, Any]] = []
        if final_type in {"RU", "RM", "LOOP_RU"}:
            categories, category_error = _categories(question_id, source_rows)
            if category_error:
                errors.append(category_error)
                continue
        display_label = next((str(row.get("label", "")).strip() for row in source_rows if str(row.get("label", "")).strip()), logical_name)
        question = {
            "question_id": question_id,
            "question_type": final_type,
            "source_variables": source_variables,
            "display_label": display_label,
            "universe_ref": "U_PROJECT_TOTAL",
            "structure_ref": f"STRUCTURE_{question_id}",
            "categories": categories,
        }
        if final_type.startswith("LOOP_"):
            question["loop_iterations"] = [
                {
                    "iteration_id": f"{question_id}_ITER_{order}",
                    "order": order,
                    "variable_ref": variable,
                    "source_label": str(variables[variable].get("label", "")),
                }
                for order, variable in enumerate(source_variables, start=1)
            ]
        questions.append(question)
    if errors:
        return _result("DRAFT_REQUIRES_HUMAN_DECISION", errors=errors, evidence=evidence)

    respondent_variable = str(respondent_items[0]["variables"][0])
    weight_items = [item for item in approved if item.get("final_type") == "WEIGHT"]
    weights = []
    for index, item in enumerate(sorted(weight_items, key=lambda value: str(value.get("item_id", ""))), start=1):
        if len(item.get("variables", [])) != 1:
            errors.append(_issue("HUMAN_WEIGHT_INVALID", f"structure_review.items.{item.get('item_id')}", "Weight must bind exactly one source variable."))
            continue
        variable = str(item["variables"][0])
        weights.append({
            "weight_id": f"WEIGHT_{index}",
            "variable_ref": variable,
            "validation_state": "HUMAN_APPROVED_SOURCE_VARIABLE",
            "normalization": "NONE",
            "trimming": "NONE",
            "policy_ref": "B1_V1",
        })
    if errors:
        return _result("DRAFT_REQUIRES_HUMAN_DECISION", errors=errors, evidence=evidence)

    config_items = [item for item in approved if item.get("final_type") == "META_CONTROL"]
    evidence["available_configuration_variables"] = sorted({
        str(variable) for item in config_items for variable in item.get("variables", [])
    })
    dataset_sha = str(source_analysis.get("dataset", {}).get("sha256", "")).strip()
    if not dataset_sha:
        errors.append(_issue("SOURCE_DATASET_FINGERPRINT_REQUIRED", "source_analysis.dataset.sha256", "Dataset fingerprint is required."))
        return _result("DRAFT_REQUIRES_HUMAN_DECISION", errors=errors, evidence=evidence)
    metadata_fingerprints = [f"sha256:{analysis_fp}", f"sha256:{review_fp}"]
    for source_name in ("questionnaire", "datamap"):
        source = source_analysis.get(source_name)
        if isinstance(source, Mapping) and source.get("sha256"):
            metadata_fingerprints.append(f"sha256:{str(source['sha256']).lower()}")

    dataset_variables = []
    for name, item in sorted(variables.items(), key=lambda pair: _natural_key(pair[0])):
        dataset_variables.append({
            "variable_id": name,
            "source_name": name,
            "data_type": item.get("data_type"),
            "missing_values": list(item.get("missing_user_values", [])),
            "missing_ranges": list(item.get("missing_ranges", [])),
        })
    project_spec = {
        "schema_version": "EXPLORA_PROJECT_SPEC_V1",
        "project": {key: str(operator_metadata[key]).strip() for key in REQUIRED_OPERATOR_METADATA},
        "dataset": {
            "source_id": f"DATASET_{dataset_sha[:12].upper()}",
            "input_type": "SAV",
            "fingerprint": f"sha256:{dataset_sha.lower()}",
            "respondent_id_variable": respondent_variable,
            "duplicate_row_policy": "FAIL",
            "variables": dataset_variables,
        },
        "source_metadata_fingerprints": sorted(set(metadata_fingerprints)),
        "questions": questions,
        "universes": [{
            "universe_id": "U_PROJECT_TOTAL",
            "parent_universe_ref": None,
            "source_variables": [],
            "expression": {"operator": "true", "args": []},
            "rule_state": "DETERMINISTIC",
            "execution_scope": "PROJECT",
        }],
        "weights": weights,
        "default_weight_ref": weights[0]["weight_id"] if len(weights) == 1 else None,
        "banners": [],
        "filters": [],
        "significance_requests": [],
        "derived_variables": [],
        "output_requests": [{
            "output_request_id": "OUT_INITIAL_WEB",
            "question_refs": [question["question_id"] for question in questions],
            "banner_refs": [],
            "filter_refs": [],
            "web_included": True,
            "excel_included": False,
            "display_decimals": 2,
        }],
        "ambiguities": [],
        "ai_interpretations": [],
        "provenance": {
            "created_at": "DETERMINISTIC_DRAFT_NO_WALL_CLOCK",
            "created_by": "HUMAN_REVIEWED_OPERATOR_CONSOLE",
            "source_refs": sorted(set([
                f"dataset_sha256:{dataset_sha.upper()}",
                f"source_analysis_sha256:{analysis_fp.upper()}",
                f"structure_review_sha256:{review_fp.upper()}",
                *[f"{name}_sha256:{str(source_analysis[name]['sha256']).upper()}" for name in ("questionnaire", "datamap") if isinstance(source_analysis.get(name), Mapping) and source_analysis[name].get("sha256")],
            ])),
            "authoring_version": PROJECT_SPEC_DRAFT_AUTHORING_VERSION,
            "human_review_authority": structure_review.get("authority"),
            "b1_policy_ref": "B1_V1",
            "b2_policy_ref": "B2_V1",
            "b3_policy_ref": "B3_V1",
        },
        "authoring_evidence": evidence,
    }
    validation = validate_project(project_spec)
    validator_errors = [asdict(item) for item in validation.errors]
    status = "DRAFT_VALID" if validation.ready_for_execution else (
        "DRAFT_REQUIRES_HUMAN_DECISION"
        if validation.validation_status == "NEEDS_HUMAN_DECISION"
        else "DRAFT_INVALID"
    )
    return _result(
        status,
        errors=validator_errors,
        evidence=evidence,
        project_spec=project_spec,
        validation=validation,
    )
