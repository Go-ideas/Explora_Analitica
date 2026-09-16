from __future__ import annotations

import hashlib
from typing import Any

from src.analytics_core.result_identity import stable_json
from src.contracts.models import CanonicalResult
from src.contracts.vocabulary import ExecutionMode


def canonical_cache_key(
    result: CanonicalResult,
    *,
    execution_mode: ExecutionMode | str = ExecutionMode.CANONICAL_V1,
    presentation_identity: str = "default",
    slice_ids: tuple[str, ...] = (),
) -> str:
    request = result.request
    manifest = result.manifest
    payload: dict[str, Any] = {
        "execution_mode": str(getattr(execution_mode, "value", execution_mode)),
        "project_id": result.project_id,
        "result_run_id": result.result_run_id,
        "result_fingerprint": result.result_fingerprint,
        "request_fingerprint": (
            request.request_fingerprint if request is not None else None
        ),
        "schema_version": result.result_schema_version,
        "core_version": result.core_version,
        "source_spec_refs": (
            manifest.source_spec_refs if manifest is not None else ()
        ),
        "presentation_identity": presentation_identity,
        "slice_ids": tuple(sorted(slice_ids)),
    }
    digest = hashlib.sha256(stable_json(payload).encode("utf-8")).hexdigest()
    return f"m6-canonical-web-{digest}"
