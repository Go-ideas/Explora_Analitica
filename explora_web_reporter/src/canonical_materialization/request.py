from __future__ import annotations

from dataclasses import replace

from src.analytics_core.results import make_request_snapshot
from src.canonical_materialization.fingerprints import fingerprint
from src.canonical_materialization.models import CANONICAL_REQUEST_SCHEMA_VERSION, CanonicalRequestSnapshot, CanonicalRuntimeInput, MaterializationError


def build_request_snapshot(runtime: CanonicalRuntimeInput, request_id: str) -> CanonicalRequestSnapshot:
    request = _released_request(runtime, request_id)
    question_id = str(request["question_ref"])
    structure_ref = _question_structure_ref(runtime, question_id)
    metrics = tuple(_metric(runtime, metric_id) for metric_id in request["metric_refs"])
    snapshot = CanonicalRequestSnapshot(
        schema_version=CANONICAL_REQUEST_SCHEMA_VERSION,
        project_id=runtime.project_id,
        request_id=request_id,
        question_id=question_id,
        structure_ref=structure_ref,
        universe_ref=str(request["universe_ref"]),
        weight_ref=request.get("weight_ref"),
        metric_refs=tuple(metric["metric_id"] for metric in metrics),
        formula_refs=tuple(metric["formula_id"] for metric in metrics),
        filters=tuple(request.get("filters", ())),
        banner=request.get("banner"),
        significance_ref=request.get("significance_ref"),
        runtime_fingerprint=runtime.fingerprint,
        package_fingerprint=runtime.package_fingerprint,
        spec_refs=_spec_refs(runtime, question_id, structure_ref, metrics, request),
    )
    return replace(snapshot, request_fingerprint=fingerprint(snapshot))


def m5_request_snapshot(runtime: CanonicalRuntimeInput, request_id: str):
    request = _released_request(runtime, request_id)
    filters = {item["filter_ref"]: tuple(item["member_ids"]) for item in request.get("filters", ())}
    execution_options = {"slice_authority": "explicit_total"} if not request.get("filters") and not request.get("banner") else {}
    return replace(
        make_request_snapshot(
            question_ids=(request["question_ref"],),
            metric_refs=tuple(request["metric_refs"]),
            banner_config=request.get("banner") or {},
            filters=filters,
            weight_override=request.get("weight_ref"),
            compatibility_profile="CANONICAL_MATERIALIZATION_V1",
            execution_options=execution_options,
        ),
        request_id=request_id,
    )


def _released_request(runtime: CanonicalRuntimeInput, request_id: str) -> dict:
    matches = [request for request in runtime.package.requests.get("requests", ()) if request.get("request_id") == request_id]
    if not matches:
        raise MaterializationError(f"missing Request ref: {request_id}")
    if len(matches) > 1:
        raise MaterializationError(f"ambiguous Request ref: {request_id}")
    return matches[0]


def _question_structure_ref(runtime: CanonicalRuntimeInput, question_id: str) -> str:
    matches = [question for question in runtime.package.questions if question.get("question_id") == question_id]
    if len(matches) != 1 or not matches[0].get("structure_ref"):
        raise MaterializationError(f"missing Structure ref for question: {question_id}")
    return str(matches[0]["structure_ref"])


def _metric(runtime: CanonicalRuntimeInput, metric_id: str) -> dict:
    matches = [metric for metric in runtime.package.metrics if metric.get("metric_id") == metric_id]
    if not matches:
        raise MaterializationError(f"missing Metric ref: {metric_id}")
    if len(matches) > 1:
        raise MaterializationError(f"ambiguous Metric ref: {metric_id}")
    return matches[0]


def _spec_refs(runtime: CanonicalRuntimeInput, question_id: str, structure_ref: str, metrics: tuple[dict, ...], request: dict) -> dict[str, str]:
    refs = {"package": runtime.package.spec_hash, request["request_id"]: str(request.get("spec_hash", ""))}
    for collection, key_name, id_value in ((runtime.package.questions, "question_id", question_id), (runtime.package.structures, "structure_id", structure_ref)):
        for item in collection:
            if item.get(key_name) == id_value and item.get("spec_hash"):
                refs[id_value] = str(item["spec_hash"])
    for metric in metrics:
        if metric.get("spec_hash"):
            refs[str(metric["metric_id"])] = str(metric["spec_hash"])
    return refs
