from __future__ import annotations

from dataclasses import replace

from src.analytics_core.result_identity import canonical_payload, stable_json
from src.contracts.models import CanonicalResult, ReleaseMetadata
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode

from .qualification import QualifiedMaster
from .renderer import (
    BUILD, MASTER, NUMERIC, VISUAL, RenderRequest, configuration_fingerprint,
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
    request = RenderRequest(
        (run,), stable_json(spec), master, master.writable_slots,
        "BENCHMARK_A_PRODUCTION_MASTER_V1", "1.0.0",
        _release("GATE38_REVIEW", "1.0.0", "PENDING"),
        _release("GATE38_MASTER_QUALIFICATION", master.version, master.artifact_sha256),
        renderer_build=BUILD,
    )
    return replace(request, configuration_release=_release(
        "GATE38_REVIEW", "1.0.0", configuration_fingerprint(request)))
