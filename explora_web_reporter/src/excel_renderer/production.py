from __future__ import annotations

from dataclasses import replace

from src.analytics_core.result_identity import canonical_payload, stable_json
from src.contracts.models import CanonicalResult, ReleaseMetadata
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode

from .qualification import QualifiedMaster
from .renderer import (
    BUILD, MASTER, NUMERIC, SIGNIFICANCE, VISUAL, RenderRequest,
    configuration_fingerprint, sha_bytes,
)


def _release(authority: str, version: str, checksum: str) -> ReleaseMetadata:
    return ReleaseMetadata(ReleaseLifecycle.RELEASED, ReleaseMode.MANUAL, authority,
                           "2026-09-19", "GATE38_QUALIFIED", version, checksum)


def benchmark_a_request(qualified: QualifiedMaster, run: CanonicalResult) -> RenderRequest:
    """Bind one authoritative Benchmark A run to every qualified V1 presentation slot."""
    value = next(item for item in run.values if str(item.value_status) == "OK" and item.estimate is not None)
    base = next(item for item in run.bases if item.unweighted_n is not None)
    bindings = (
        ("value", value.value_id, "estimate", "benchmark_result", str(value.unit), value.value_id),
        ("base", base.base_id, "unweighted_n", "benchmark_base", "unweighted_n", base.base_id),
        ("provenance", run.result_run_id, "project_id", "project_identity", "LITERAL", None),
    )
    visuals = []
    for index, (role, record_id, field, slot, profile, label) in enumerate(bindings):
        visuals.append({
            "visual_id": f"benchmark_a_{slot}", "order": index, "role": "provenance" if role == "provenance" else ("base_table" if role == "base" else "result_table"),
            "source_bindings": [{"result_run_id": run.result_run_id, "record_role": role,
                                 "record_id": record_id, "field_name": field, "slot_id": slot}],
            "labels": [] if label is None else [{"text": label, "language": "technical", "source_ref": record_id}],
            "display_profile_ref": profile, "warning_refs": [], "significance_presentation_refs": [],
        })
    spec = {
        "schema_version": VISUAL, "visual_spec_id": "BENCHMARK_A_PRODUCTION_MASTER_V1",
        "revision": 1, "project_id": run.project_id,
        "result_refs": [{"result_run_id": run.result_run_id,
                         "result_fingerprint": run.result_fingerprint,
                         "request_fingerprint": run.request.request_fingerprint}],
        "master_interface_version": MASTER, "numeric_profile_version": NUMERIC,
        "provenance_refs": [run.project_spec_ref],
        "sections": [{"section_id": "benchmark_a_first_integration", "order": 0,
                      "sheet_role": "presentation",
                      "title": {"text": "Benchmark A", "language": "technical"},
                      "visuals": visuals}],
    }
    master = qualified.manifest
    slots = tuple(slot for slot in master.writable_slots if slot.slot_id in {
        "benchmark_result", "benchmark_base", "project_identity"})
    request = RenderRequest(
        (run,), stable_json(spec), master, slots,
        "BENCHMARK_A_PRODUCTION_MASTER_V1", "1.0.0",
        _release("GATE38_REVIEW", "1.0.0", "PENDING"),
        _release("GATE38_MASTER_QUALIFICATION", master.version, master.artifact_sha256),
        renderer_build=BUILD,
    )
    return replace(request, configuration_release=_release(
        "GATE38_REVIEW", "1.0.0", configuration_fingerprint(request)))


def significance_qualification_request(
    qualified: QualifiedMaster,
    run: CanonicalResult,
    *,
    comparison_id: str,
    value_id: str,
    token_id: str,
    display_text: str,
) -> RenderRequest:
    """Bind one Core-generated canonical relation to the declared Master target."""
    comparison = next((item for item in run.comparisons if item.comparison_id == comparison_id), None)
    value = next((item for item in run.values if item.value_id == value_id), None)
    if comparison is None or value is None:
        raise ValueError("Missing canonical significance source")
    envelope = {
        "schema_version": SIGNIFICANCE,
        "token_set_id": "GATE39_CANONICAL_MARKERS_V1",
        "revision": 1,
        "authority_ref": "GATE39_HUMAN_REVIEWED_PRESENTATION",
        "result_run_id": run.result_run_id,
        "result_fingerprint": run.result_fingerprint,
        "comparison_bindings": [{
            "comparison_id": comparison.comparison_id,
            "family_id": comparison.family_id,
            "test_id": comparison.test_id,
            "test_version": comparison.test_version,
            "value_id": value.value_id,
            "slice_id": value.slice_id,
            "member_id": comparison.left_member_id if value.slice_id == comparison.left_slice_id
            else comparison.right_member_id,
            "direction": comparison.direction,
            "token_id": token_id,
            "display_text": display_text,
        }],
        "legend": [{
            "token_id": token_id,
            "meaning": "Canonical Core significance marker",
            "comparison_refs": [comparison.comparison_id],
        }],
    }
    token_json = stable_json(envelope)
    token_checksum = sha_bytes(token_json)
    binding = {"result_run_id": run.result_run_id, "record_role": "comparison",
               "record_id": comparison.comparison_id, "field_name": "status",
               "slot_id": "significance_marker"}
    spec = {
        "schema_version": VISUAL,
        "visual_spec_id": "GATE39_SIGNIFICANCE_QUALIFICATION_V1",
        "revision": 1,
        "project_id": run.project_id,
        "result_refs": [{"result_run_id": run.result_run_id,
                         "result_fingerprint": run.result_fingerprint,
                         "request_fingerprint": run.request.request_fingerprint}],
        "master_interface_version": MASTER,
        "numeric_profile_version": NUMERIC,
        "provenance_refs": [run.project_spec_ref, comparison.comparison_id],
        "sections": [{
            "section_id": "canonical_significance",
            "order": 0,
            "sheet_role": "presentation",
            "title": {"text": "Significance", "language": "technical"},
            "visuals": [{
                "visual_id": "canonical_significance_marker",
                "order": 0,
                "role": "significance_table",
                "source_bindings": [binding],
                "labels": [],
                "display_profile_ref": "SIGNIFICANCE_TOKEN",
                "warning_refs": [],
                "significance_presentation_refs": [token_checksum],
            }],
        }],
    }
    master = qualified.manifest
    slot = next(item for item in master.writable_slots if item.slot_id == "significance_marker")
    request = RenderRequest(
        (run,), stable_json(spec), master, (slot,),
        "GATE39_SIGNIFICANCE_QUALIFICATION_V1", "1.0.0",
        _release("GATE39_REVIEW", "1.0.0", "PENDING"),
        _release("GATE39_MASTER_QUALIFICATION", master.version, master.artifact_sha256),
        significance_json=(token_json,), renderer_build=BUILD,
    )
    return replace(request, configuration_release=_release(
        "GATE39_REVIEW", "1.0.0", configuration_fingerprint(request)))
