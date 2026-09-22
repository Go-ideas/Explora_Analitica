from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from src.analytics_core.execution_adapter import CanonicalExecutionContext, SliceExecutionAuthority, execute_canonical_request
from src.analytics_core.results import make_slice
from src.analytics_core.structure import StructureEvaluationContext, evaluate_structure
from src.analytics_core.universe import UniverseEvaluationContext, UniverseEvaluator, UniverseEvaluationResult
from src.analytics_core.weights import WeightEvaluationContext, evaluate_weighted_base
from src.canonical_materialization.materializer import materialize_project
from src.canonical_materialization.models import CanonicalExecutionEvidence, CanonicalRuntimeInput, MaterializationError
from src.canonical_materialization.qa import assert_pre_m2_qa_pass
from src.canonical_materialization.request import build_request_snapshot, m5_request_snapshot
from src.contracts.models import (
    CategoryOptionBinding,
    MentionScopeIdentity,
    MetricSpec,
    ProjectSpec,
    QuestionSpec,
    ReleaseMetadata,
    StructureSpec,
    UniverseExpression,
    UniverseRef,
    UniverseSpec,
    VariableBinding,
    WeightSpec,
)
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode, StructureAuthorityMode


STORAGE_ENCODING_MAP = {"single_numeric_variable": "single_variable", "dichotomous_columns": "one_column_per_option"}
COMPLETION_POLICY_MAP = {"explicit_dichotomous_state_per_option": "explicit_response"}


def run_canonical_project(
    *,
    source_path: str | Path,
    package_path: str | Path,
    request_ids: tuple[str, ...],
    expected_source_sha256: str | None = None,
    expected_package_sha256: str | None = None,
    expected_runtime_fingerprint: str | None = None,
) -> CanonicalExecutionEvidence:
    runtime = materialize_project(
        source_path=source_path,
        package_path=package_path,
        expected_source_sha256=expected_source_sha256,
        expected_package_sha256=expected_package_sha256,
        expected_runtime_fingerprint=expected_runtime_fingerprint,
    )
    assert_pre_m2_qa_pass(runtime)
    requests = {request_id: build_request_snapshot(runtime, request_id) for request_id in request_ids}
    results = {request_id: _execute_request(runtime, request_id) for request_id in request_ids}
    return CanonicalExecutionEvidence(runtime=runtime, requests=requests, results=results, qa_events=runtime.qa_events)


def _execute_request(runtime: CanonicalRuntimeInput, request_id: str):
    request = _one(runtime.package.requests.get("requests", ()), "request_id", request_id)
    project = _project_spec(runtime)
    universes = _universe_specs(runtime)
    universe_result = _universe_result(runtime, universes)
    question = _question_spec(runtime, str(request["question_ref"]))
    structure = _structure_spec(runtime, question.structure_ref or "")
    structure_result = evaluate_structure(
        project_spec=project,
        question_spec=question,
        structure_spec=structure,
        context=StructureEvaluationContext(
            respondent_ids=runtime.respondent_ids,
            values_by_variable=runtime.values_by_variable,
            universe_results={universe_result.universe_ref.universe_id: universe_result},
            available_variables=set(runtime.values_by_variable),
            category_ids={category.category_id for category in structure.category_bindings},
            universe_ids=set(universes),
            traceability={"runtime_fingerprint": runtime.fingerprint},
        ),
        authority_mode=StructureAuthorityMode.RELEASED_SPEC,
    )
    explicitly_unweighted = request.get("weight_choice") == "EXPLICITLY_UNWEIGHTED"
    weight_specs = () if explicitly_unweighted else _weight_specs(runtime)
    weight_result = evaluate_weighted_base(
        universe_result,
        WeightEvaluationContext(
            respondent_ids=runtime.respondent_ids,
            weight_values={spec.variable_ref: runtime.values_by_variable[spec.variable_ref]
                           for spec in weight_specs},
            weight_specs=weight_specs,
            project_spec=replace(project, default_weight_ref=None) if explicitly_unweighted else project,
            project_id=runtime.project_id,
            dataset_fingerprint=runtime.source_fingerprint,
            analysis_config_version=runtime.package.package_version,
            traceability={"runtime_fingerprint": runtime.fingerprint},
        ),
        analysis_weight_override=None if explicitly_unweighted else request.get("weight_ref"),
        significance_requested=bool(request.get("significance_ref")),
    )
    return execute_canonical_request(
        CanonicalExecutionContext(
            project_id=runtime.project_id,
            dataset_fingerprint=runtime.source_fingerprint,
            project_spec_ref=project.spec_id,
            request=m5_request_snapshot(runtime, request_id),
            question_id=question.question_id,
            structure_ref=structure.structure_id,
            structure_result=structure_result,
            universe_result=universe_result,
            metric_specs=tuple(_metric_spec(runtime, metric_id) for metric_id in request["metric_refs"]),
            runtime_fingerprint=runtime.fingerprint,
            slices=tuple(_slices(runtime, request, universe_result)),
            weight_result=weight_result if weight_result.active_weight_id else None,
            result_run_id=f"canonical-materialization-{request_id.lower()}",
            b3_release_evidence=True,
            provenance_refs=(f"package:{runtime.package.package_id}", f"package_sha:{runtime.package_fingerprint}"),
        )
    )


def _release(runtime: CanonicalRuntimeInput) -> ReleaseMetadata:
    manifest = runtime.package.manifest
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by=str(manifest.get("human_decision_id", "released-package")),
        decided_at=str(manifest.get("released_at", "")),
        policy_id=str(manifest.get("human_decision_id", "released-package")),
        policy_version=runtime.package.package_version,
        source_hash=runtime.source_fingerprint,
    )


def _project_spec(runtime: CanonicalRuntimeInput) -> ProjectSpec:
    project = runtime.package.project
    return ProjectSpec(
        spec_id=str(project["project_id"]),
        version=str(project["spec_version"]),
        release=_release(runtime),
        project_id=str(project["project_id"]),
        dataset_fingerprint=runtime.source_fingerprint,
        respondent_id_binding=runtime.respondent_identity_mode,
        project_universe_ref=str(project.get("universe_spec_refs", ("",))[0]),
        default_weight_ref=project.get("default_weight_ref"),
    )


def _universe_specs(runtime: CanonicalRuntimeInput) -> dict[str, UniverseSpec]:
    specs = {}
    for item in runtime.package.universes:
        expr = item["expression"]
        specs[item["universe_id"]] = UniverseSpec(
            spec_id=item["universe_id"],
            version=item["spec_version"],
            release=_release(runtime),
            expression=UniverseExpression(expr["op"], (expr["variable_ref"], tuple(expr.get("values", ())))),
        )
    return specs


def _universe_result(runtime: CanonicalRuntimeInput, universes: dict[str, UniverseSpec]) -> UniverseEvaluationResult:
    universe = next(iter(universes.values()))
    return UniverseEvaluator().evaluate(
        universe,
        UniverseEvaluationContext(
            respondent_ids=runtime.respondent_ids,
            field_values=runtime.values_by_variable,
            universe_registry=universes,
            traceability={"runtime_fingerprint": runtime.fingerprint},
        ),
    )


def _question_spec(runtime: CanonicalRuntimeInput, question_id: str) -> QuestionSpec:
    item = _one(runtime.package.questions, "question_id", question_id)
    return QuestionSpec(
        spec_id=item.get("question_spec_id") or f"QSP_{question_id}",
        version=item["spec_version"],
        release=_release(runtime),
        question_id=question_id,
        physical_type=item.get("physical_type") or "released",
        analytic_role=item.get("analytic_role") or "benchmark",
        universe_ref=str(item["universe_ref"]),
        metric_refs=tuple(item.get("metric_refs", ())),
        structure_ref=item.get("structure_ref"),
    )


def _structure_spec(runtime: CanonicalRuntimeInput, structure_id: str) -> StructureSpec:
    item = _one(runtime.package.structures, "structure_id", structure_id)
    if item["structure_type"] == "RM":
        variables = tuple(VariableBinding(binding_id=b["option_id"], variable_ref=b["variable_ref"], option_id=b["option_id"]) for b in item.get("option_bindings", ()))
        categories = ()
    else:
        variables = tuple(VariableBinding(binding_id=b["variable_ref"], variable_ref=b["variable_ref"]) for b in item.get("variable_bindings", ()))
        categories = tuple(CategoryOptionBinding(binding_id=c["category_id"], category_id=c["category_id"], raw_values=(c["raw_value"],), label=c.get("label", "")) for c in item.get("category_bindings", ()))
    scope = item.get("mention_denominator_scope")
    if isinstance(scope, dict):
        scope = MentionScopeIdentity(**scope)
    return StructureSpec(
        spec_id=item["structure_id"],
        version=item["spec_version"],
        release=_release(runtime),
        structure_id=item["structure_id"],
        structure_type=item["structure_type"],
        parent_question_ref=item["question_id"],
        variable_bindings=variables,
        category_bindings=categories,
        applicability_refs={key: UniverseRef(value) for key, value in item.get("applicability_refs", {}).items()},
        selected_values=tuple(item.get("selected_values", ())),
        not_selected_values=tuple(item.get("not_selected_values", ())),
        ordinary_missing_values=tuple(item.get("ordinary_missing_values", ())),
        completion_policy=COMPLETION_POLICY_MAP.get(item.get("completion_policy"), item.get("completion_policy", "explicit_response")),
        duplicate_policy=item.get("duplicate_policy", "error"),
        exclusive_option_ids=tuple(item.get("exclusive_option_ids", ())),
        storage_encoding=STORAGE_ENCODING_MAP.get(item.get("storage_encoding"), item.get("storage_encoding", "single_variable")),
        mention_denominator_scope=scope,
        structural_zero_provenance=item.get("structural_zero_provenance"),
        structural_missing_semantics=item.get("structural_missing_semantics"),
        response_state_version=item.get("response_state_version", "M4_STRUCTURE_V1"),
    )


def _metric_spec(runtime: CanonicalRuntimeInput, metric_id: str) -> MetricSpec:
    item = _one(runtime.package.metrics, "metric_id", metric_id)
    parameters = dict(item.get("parameters", {}))
    if isinstance(parameters.get("mention_denominator_scope"), dict):
        parameters["mention_denominator_scope"] = MentionScopeIdentity(**parameters["mention_denominator_scope"])
    significance = item.get("significance", {})
    return MetricSpec(
        spec_id=item["metric_id"],
        version=item["spec_version"],
        release=_release(runtime),
        metric_id=item["metric_id"],
        formula_id=item["formula_id"],
        question_ref=item["question_ref"],
        universe_ref=item["universe_ref"],
        denominator_policy=item["denominator_policy"],
        missing_behavior=item["missing_behavior"],
        weight_behavior=item.get("weight_behavior", "unweighted"),
        significance_family=significance.get("test_family") or significance.get("status") or "none",
        significance_supported=bool(significance.get("supported", False)),
        parameters=parameters,
    )


def _weight_specs(runtime: CanonicalRuntimeInput) -> tuple[WeightSpec, ...]:
    specs = []
    for item in runtime.package.weights.get("weights", ()):
        specs.append(WeightSpec(
            spec_id=item.get("spec_id") or item["weight_id"],
            version=item["spec_version"], release=_release(runtime),
            weight_id=item["weight_id"], variable_ref=item["variable_ref"],
            provenance=item["provenance"], scope=item["scope"],
            permitted_analysis_overrides=tuple(item.get("permitted_analysis_overrides", ())),
            missing_policy=item["missing_policy"], non_numeric_policy=item["non_numeric_policy"],
            non_finite_policy=item["non_finite_policy"], zero_policy=item["zero_policy"],
            negative_policy=item["negative_policy"], normalization=item["normalization"],
            trimming=item["trimming"], weighted_significance=bool(item["weighted_significance"]),
            is_project_default=bool(item.get("is_project_default", False)),
        ))
    return tuple(specs)


def _slices(runtime: CanonicalRuntimeInput, request: dict[str, Any], universe_result: UniverseEvaluationResult):
    base_filter = {respondent_id: True for respondent_id in runtime.respondent_ids}
    filter_refs = []
    for item in request.get("filters", ()):
        spec = _one(runtime.package.banner_filters.get("filters", ()), "filter_id", item["filter_ref"])
        allowed = {member["raw_value"] for member in spec["members"] if member["member_id"] in set(item["member_ids"])}
        values = runtime.values_by_variable[spec["physical_variable_ref"]]
        base_filter = {respondent_id: base_filter[respondent_id] and values[respondent_id] in allowed for respondent_id in runtime.respondent_ids}
        filter_refs.append(f"{item['filter_ref']}:{'|'.join(item['member_ids'])}")
    if not request.get("banner"):
        slice_item = make_slice(is_total=not filter_refs, filter_refs=tuple(filter_refs), configuration={"filters": tuple(filter_refs)} if filter_refs else {"scope": "TOTAL"})
        yield SliceExecutionAuthority(slice_item, _slice_universe(runtime, universe_result, base_filter, request["universe_ref"]))
        return
    banner = request["banner"]
    spec = _one(runtime.package.banner_filters.get("banners", ()), "banner_id", banner["banner_ref"])
    values = runtime.values_by_variable[spec["physical_variable_ref"]]
    for member in spec["members"]:
        if member["member_id"] not in set(banner["member_ids"]):
            continue
        mask = {respondent_id: base_filter[respondent_id] and values[respondent_id] == member["raw_value"] for respondent_id in runtime.respondent_ids}
        slice_item = make_slice(is_total=False, banner_dimension_id=spec["dimension_id"], member_id=member["member_id"], filter_refs=tuple(filter_refs), configuration={"banner_ref": spec["banner_id"], "raw_value": member["raw_value"]}, label=member.get("label"))
        yield SliceExecutionAuthority(slice_item, _slice_universe(runtime, universe_result, mask, request["universe_ref"]))


def _slice_universe(runtime: CanonicalRuntimeInput, universe_result: UniverseEvaluationResult, mask: dict[str, bool], universe_ref: str) -> UniverseEvaluationResult:
    final = {respondent_id: universe_result.respondent_mask.get(respondent_id, False) and mask.get(respondent_id, False) for respondent_id in runtime.respondent_ids}
    eligible = sum(1 for value in final.values() if value)
    return replace(universe_result, universe_ref=UniverseRef(universe_ref), respondent_mask=final, input_n=len(final), eligible_n=eligible, excluded_n=len(final) - eligible, traceability={"source": "canonical materialization request slice"})


def _one(collection, key: str, value: str) -> dict:
    matches = [item for item in collection if item.get(key) == value]
    if not matches:
        raise MaterializationError(f"required reference cannot be resolved: {value}")
    if len(matches) > 1:
        raise MaterializationError(f"ambiguous released reference: {value}")
    return matches[0]
