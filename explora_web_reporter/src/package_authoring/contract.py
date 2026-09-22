from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from src.analytics_core.formula_registry import FORMULA_REGISTRY, FORMULA_REGISTRY_VERSION
from src.project_intake.contract import project_spec_fingerprint, validate_project


EXECUTION_RELEASE_SCHEMA_VERSION = "EXPLORA_PROJECT_EXECUTION_RELEASE_V1"
POLICY_REFS = {
    "b1": "B1_V1", "b2": "B2_V1", "b3": "B3_V1",
    "formula_registry": FORMULA_REGISTRY_VERSION,
}
STATISTICAL_RESULT_FIELDS = {
    "row_count", "source_n", "runtime_n", "weighted_base", "effective_n",
    "estimate", "numerator", "denominator", "p_value", "observed_count",
    "canonical_result", "exclusive_violations_observed", "missing_by_option",
}


class PackageAuthoringError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedExecutionRelease:
    project_spec: dict[str, Any]
    execution_release: dict[str, Any]
    project_spec_fingerprint: str


def _load(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return json.loads(json.dumps(value))
    payload = json.loads(Path(value).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PackageAuthoringError("contract root must be an object")
    return payload


def _ids(items: Any, key: str, section: str, *, allow_empty: bool = False) -> set[str]:
    if not isinstance(items, list) or (not items and not allow_empty):
        raise PackageAuthoringError(f"{section} must be a {'possibly empty ' if allow_empty else 'non-empty '}list")
    values: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get(key), str) or not item[key]:
            raise PackageAuthoringError(f"{section}.{key} is required")
        values.append(item[key])
    if len(values) != len(set(values)):
        raise PackageAuthoringError(f"duplicate {section}.{key}")
    return set(values)


def _reject_statistical_fields(value: Any, path: str = "execution_release") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in STATISTICAL_RESULT_FIELDS:
                raise PackageAuthoringError(f"statistical-result field is forbidden in authoring: {path}.{key}")
            _reject_statistical_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_statistical_fields(child, f"{path}[{index}]")


def _required_text(container: Mapping[str, Any], fields: set[str], label: str) -> None:
    if any(not isinstance(container.get(field), str) or not container[field].strip() for field in fields):
        raise PackageAuthoringError(f"{label} contains a missing identity or decision value")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9A-Fa-f]{64}", value) is not None


def validate_execution_release(
    project_spec: Mapping[str, Any] | str | Path,
    execution_release: Mapping[str, Any] | str | Path,
) -> ValidatedExecutionRelease:
    project = _load(project_spec)
    release = _load(execution_release)
    intake = validate_project(project)
    if not intake.ready_for_execution:
        raise PackageAuthoringError("Project Spec is not READY_FOR_EXECUTION")
    required = {
        "schema_version", "release_spec_id", "release_spec_version", "project_id",
        "project_spec_fingerprint", "package", "source_authority", "policy_refs",
        "release_decision", "questions", "structures", "metrics", "weights",
        "banners", "filters", "significance", "requests",
    }
    if set(release) != required:
        raise PackageAuthoringError(f"Execution Release fields mismatch: {sorted(set(release) ^ required)}")
    if release["schema_version"] != EXECUTION_RELEASE_SCHEMA_VERSION:
        raise PackageAuthoringError("unsupported Execution Release schema")
    fingerprint = project_spec_fingerprint(project)
    if release["project_spec_fingerprint"] != fingerprint:
        raise PackageAuthoringError("Project Spec fingerprint mismatch")
    if release["project_id"] != project["project"]["project_id"]:
        raise PackageAuthoringError("project identity mismatch")
    if release["policy_refs"] != POLICY_REFS:
        raise PackageAuthoringError("accepted B1/B2/B3/Core policy identities are required")
    package = release["package"]
    if not isinstance(package, dict) or set(package) != {
        "package_id", "package_version", "dataset_version", "default_execution_mode"
    } or package["default_execution_mode"] != "LEGACY":
        raise PackageAuthoringError("invalid package release configuration")
    _required_text(package, {"package_id", "package_version", "dataset_version"}, "package")
    authority = release["source_authority"]
    if not isinstance(authority, dict) or set(authority) != {
        "dataset_filename", "dataset_sha256", "questionnaire_filename",
        "questionnaire_sha256", "datamap_ref", "mapping_authority",
    }:
        raise PackageAuthoringError("incomplete source authority")
    _required_text(authority, {"dataset_filename", "questionnaire_filename", "datamap_ref", "mapping_authority"}, "source authority")
    declared = str(project["dataset"]["fingerprint"]).removeprefix("sha256:").upper()
    if not _is_sha256(declared) or not _is_sha256(authority["dataset_sha256"]) or not _is_sha256(authority["questionnaire_sha256"]) or authority["dataset_sha256"].upper() != declared:
        raise PackageAuthoringError("source authority fingerprint mismatch")
    decision = release["release_decision"]
    if not isinstance(decision, dict) or set(decision) != {
        "human_decision_id", "human_decision_basis", "release_mode", "released_at", "approved"
    } or decision["approved"] is not True or decision["release_mode"] != "MANUAL":
        raise PackageAuthoringError("B3 human release decision is required")
    _required_text(decision, {"human_decision_id", "human_decision_basis", "released_at"}, "B3 release decision")
    _reject_statistical_fields(release)

    project_questions = {item["question_id"] for item in project["questions"]}
    project_universes = {item["universe_id"] for item in project["universes"]}
    project_weights = {item["weight_id"] for item in project["weights"]}
    project_banners = {item["banner_id"] for item in project["banners"]}
    project_filters = {item["filter_id"] for item in project["filters"]}
    project_significance = {item["significance_request_id"] for item in project["significance_requests"]}
    project_outputs = {item["output_request_id"] for item in project["output_requests"]}
    question_ids = _ids(release["questions"], "question_id", "questions")
    structure_ids = _ids(release["structures"], "structure_id", "structures")
    metric_ids = _ids(release["metrics"], "metric_id", "metrics")
    request_ids = _ids(release["requests"], "request_id", "requests")
    weight_ids = _ids(release["weights"], "weight_id", "weights", allow_empty=True)
    banner_ids = _ids(release["banners"], "banner_id", "banners", allow_empty=True)
    filter_ids = _ids(release["filters"], "filter_id", "filters", allow_empty=True)
    significance_ids = _ids(release["significance"], "significance_id", "significance", allow_empty=True)
    if question_ids != project_questions or weight_ids != project_weights or banner_ids != project_banners or filter_ids != project_filters or significance_ids != project_significance:
        raise PackageAuthoringError("Execution Release identity inventory differs from Project Spec")
    if request_ids != project_outputs:
        raise PackageAuthoringError("one approved ER request is required per Project Spec output request")

    variables = {item["variable_id"] for item in project["dataset"]["variables"]}
    for item in release["questions"]:
        if item.get("structure_ref") not in structure_ids or not item.get("metric_refs") or not set(item["metric_refs"]).issubset(metric_ids):
            raise PackageAuthoringError("question has dangling structure or metric references")
    for item in release["structures"]:
        if item.get("question_id") not in question_ids or item.get("structure_type") not in {"RU", "RM", "GRID_ESCALA", "GRID_RM", "LOOP_RM", "LOOP_RU", "LOOP_NUMERICO"}:
            raise PackageAuthoringError("unsupported or dangling structure")
        bindings = item.get("option_bindings", []) if item.get("structure_type") == "RM" else item.get("variable_bindings", [])
        if not bindings or any(binding.get("variable_ref") not in variables for binding in bindings):
            raise PackageAuthoringError("structure physical binding is missing or ambiguous")
        required_semantics = {"completion_policy", "storage_encoding", "duplicate_policy",
                              "applicability_refs", "respondent_denominator_behavior"}
        if not required_semantics.issubset(item) or not item["applicability_refs"]:
            raise PackageAuthoringError("structure semantics are incomplete")
        if item["structure_type"] in {"RM", "GRID_RM", "LOOP_RM"}:
            rm_required = {"selected_values", "not_selected_values", "ordinary_missing_values",
                           "mention_denominator_behavior", "mention_denominator_scope",
                           "exclusive_option_ids"}
            if not rm_required.issubset(item) or not item.get("option_bindings"):
                raise PackageAuthoringError("RM semantics and explicit option bindings are required")
            states = [set(item[name]) for name in ("selected_values", "not_selected_values", "ordinary_missing_values")]
            if any(not state for state in states) or any(states[i] & states[j] for i in range(3) for j in range(i + 1, 3)):
                raise PackageAuthoringError("RM response states must be complete and disjoint")
    for item in release["metrics"]:
        if item.get("formula_id") not in FORMULA_REGISTRY or item.get("question_ref") not in question_ids or item.get("universe_ref") not in project_universes:
            raise PackageAuthoringError("metric formula or reference is unsupported")
        if item.get("weight_behavior") not in {"unweighted", "weighted"}:
            raise PackageAuthoringError("metric weight behavior must be explicit")
        if not all(key in item for key in ("denominator_policy", "missing_behavior", "significance", "parameters")):
            raise PackageAuthoringError("MetricSpec configuration is incomplete")
    default_weight = project.get("default_weight_ref")
    if default_weight not in weight_ids and default_weight is not None:
        raise PackageAuthoringError("B1 default weight is not released")
    for item in release["weights"]:
        required_b1 = {"weight_id", "variable_ref", "provenance", "scope", "missing_policy",
                       "non_numeric_policy", "non_finite_policy", "zero_policy", "negative_policy",
                       "normalization", "trimming", "weighted_significance"}
        if not required_b1.issubset(item) or item["variable_ref"] not in variables:
            raise PackageAuthoringError("B1 weight release configuration is incomplete")
    for collection, identity in ((release["banners"], "banner_id"), (release["filters"], "filter_id")):
        for item in collection:
            if item.get("physical_variable_ref") not in variables or not item.get("members"):
                raise PackageAuthoringError(f"{identity} member configuration is incomplete")
            member_ids = [member.get("member_id") for member in item["members"]]
            if None in member_ids or len(member_ids) != len(set(member_ids)):
                raise PackageAuthoringError(f"duplicate or missing {identity} member")
    for item in release["requests"]:
        if item.get("question_ref") not in question_ids or not set(item.get("metric_refs", [])).issubset(metric_ids) or item.get("universe_ref") not in project_universes:
            raise PackageAuthoringError("request contains dangling references")
        if item.get("weight_ref") is not None and item["weight_ref"] not in weight_ids:
            raise PackageAuthoringError("request weight is not released by B1")
        if item.get("significance_ref") is not None and item["significance_ref"] not in significance_ids:
            raise PackageAuthoringError("request significance is not released by B2")
        for applied in item.get("filters", []):
            if applied.get("filter_ref") not in filter_ids or not applied.get("member_ids"):
                raise PackageAuthoringError("request filter binding is incomplete")
        banner = item.get("banner")
        if banner is not None and (banner.get("banner_ref") not in banner_ids or not banner.get("member_ids")):
            raise PackageAuthoringError("request banner binding is incomplete")
    requests_by_id = {item["request_id"]: item for item in release["requests"]}
    for output in project["output_requests"]:
        request = requests_by_id[output["output_request_id"]]
        if output.get("question_refs") != [request["question_ref"]]:
            raise PackageAuthoringError("implicit request splitting is forbidden")
    if weight_ids:
        for item in release["requests"]:
            if item.get("weight_ref") is None and item.get("weight_choice") != "EXPLICITLY_UNWEIGHTED":
                raise PackageAuthoringError("weight configuration cannot silently become unweighted")
    for item in release["significance"]:
        required_b2 = {"significance_id", "question_ref", "metric_refs", "banner_ref",
                       "family_id", "family_members", "sample_relationship", "confidence",
                       "weight_compatibility"}
        if not required_b2.issubset(item) or item["question_ref"] not in question_ids or not set(item["metric_refs"]).issubset(metric_ids) or item["banner_ref"] not in banner_ids:
            raise PackageAuthoringError("B2 significance family configuration is incomplete")
        if item["sample_relationship"] != "INDEPENDENT" or item["confidence"] not in {0.90, 0.95, 0.99}:
            raise PackageAuthoringError("unsupported B2 significance configuration")
    return ValidatedExecutionRelease(project, release, fingerprint)
