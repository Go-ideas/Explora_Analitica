from __future__ import annotations

import json
from typing import Any, Mapping

from src.analytics_core.result_identity import canonical_payload
from src.analytics_core.result_identity import stable_json
from src.contracts.models import (
    CanonicalBase,
    CanonicalReleaseState,
    CanonicalResult,
    CanonicalResultManifest,
    CanonicalSlice,
    CanonicalValue,
    QAEvent,
    QAEnvelope,
    QAIssue,
    RequestSnapshot,
    SignificanceRelation,
    UniverseRef,
)
from src.contracts.validators import validate_canonical_result


COLLECTION_SORT_KEYS = {
    "slices": "slice_id",
    "bases": "base_id",
    "values": "value_id",
    "comparisons": "comparison_id",
    "qa_events": "qa_id",
}


def to_canonical_data(result: CanonicalResult) -> dict[str, Any]:
    validate_canonical_result(result)
    data = canonical_payload(result)
    if (
        isinstance(data.get("release"), dict)
        and isinstance(data["release"].get("reasons"), list)
    ):
        data["release"]["reasons"] = sorted(
            data["release"]["reasons"],
            key=lambda item: stable_json(item),
        )
    for collection, key in COLLECTION_SORT_KEYS.items():
        data[collection] = sorted(
            data.get(collection, ()),
            key=lambda item: (
                item.get("semantic_order") is None,
                item.get("semantic_order"),
                stable_json(item),
            ),
        )
    return data


def to_canonical_json(result: CanonicalResult) -> str:
    return json.dumps(
        to_canonical_data(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def from_canonical_data(data: Mapping[str, Any]) -> CanonicalResult:
    payload = dict(data)
    if payload.get("qa"):
        qa_payload = dict(payload["qa"])
        qa_payload["issues"] = tuple(
            QAIssue(**item) for item in qa_payload.get("issues", ())
        )
        payload["qa"] = QAEnvelope(**qa_payload)
    if payload.get("manifest"):
        payload["manifest"] = CanonicalResultManifest(**payload["manifest"])
    if payload.get("request"):
        payload["request"] = RequestSnapshot(**payload["request"])
    payload["slices"] = tuple(CanonicalSlice(**item) for item in payload.get("slices", ()))
    bases = []
    for item in payload.get("bases", ()):
        base_payload = dict(item)
        if isinstance(base_payload.get("universe_ref"), Mapping):
            base_payload["universe_ref"] = UniverseRef(
                **base_payload["universe_ref"]
            )
        bases.append(CanonicalBase(**base_payload))
    payload["bases"] = tuple(bases)
    payload["values"] = tuple(CanonicalValue(**item) for item in payload.get("values", ()))
    payload["comparisons"] = tuple(
        SignificanceRelation(**item) for item in payload.get("comparisons", ())
    )
    payload["qa_events"] = tuple(QAEvent(**item) for item in payload.get("qa_events", ()))
    if payload.get("release"):
        payload["release"] = CanonicalReleaseState(**payload["release"])
    return CanonicalResult(**payload)


def from_canonical_json(text: str) -> CanonicalResult:
    return from_canonical_data(json.loads(text))
