from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping
from uuid import uuid4


VOLATILE_FINGERPRINT_KEYS = frozenset(
    {
        "result_run_id",
        "result_fingerprint",
        "request_id",
        "base_id",
        "value_id",
        "comparison_id",
        "qa_id",
        "created_at",
        "execution_timestamp",
        "packaging_timestamp",
        "label",
        "display_label",
        "worksheet",
        "worksheet_coordinate",
        "chart_id",
        "css",
        "renderer_metadata",
        "significance_refs",
        "qa_refs",
        "provenance_refs",
        "manifest",
        "qa",
        "issue_id",
    }
)


def new_result_run_id() -> str:
    return f"m5-run-{uuid4().hex}"


def stable_json(value: Any) -> str:
    return json.dumps(
        canonical_payload(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def result_fingerprint(value: Any) -> str:
    semantic_payload = _fingerprint_payload(
        canonical_payload(value, omit_keys=VOLATILE_FINGERPRINT_KEYS)
    )
    return hashlib.sha256(
        json.dumps(
            semantic_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def make_id(prefix: str, payload: Any) -> str:
    return f"{prefix}_{fingerprint(payload)[:24]}"


def request_identity(payload: Mapping[str, Any]) -> tuple[str, str]:
    semantic = {
        "question_ids": tuple(payload.get("question_ids", ())),
        "metric_refs": tuple(payload.get("metric_refs", ())),
        "banner_config": payload.get("banner_config", {}),
        "filters": payload.get("filters", {}),
        "weight_override": payload.get("weight_override"),
        "compatibility_profile": payload.get("compatibility_profile"),
        "execution_options": payload.get("execution_options", {}),
    }
    cleaned = canonical_payload(semantic, omit_keys=frozenset({"label"}))
    request_fp = fingerprint(cleaned)
    return make_id("request", cleaned), request_fp


def slice_identity(payload: Mapping[str, Any]) -> tuple[str, str]:
    semantic = {
        "is_total": bool(payload.get("is_total", False)),
        "banner_dimension_id": payload.get("banner_dimension_id"),
        "member_id": payload.get("member_id"),
        "filter_refs": tuple(payload.get("filter_refs", ())),
        "configuration": payload.get("configuration", {}),
    }
    cleaned = canonical_payload(semantic, omit_keys=frozenset({"label"}))
    slice_fp = fingerprint(cleaned)
    return make_id("slice", cleaned), slice_fp


def canonical_payload(
    value: Any,
    *,
    omit_keys: frozenset[str] = frozenset(),
) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: canonical_payload(
                getattr(value, item.name),
                omit_keys=omit_keys,
            )
            for item in fields(value)
            if item.name not in omit_keys
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): canonical_payload(value[key], omit_keys=omit_keys)
            for key in sorted(value, key=lambda item: str(item))
            if str(key) not in omit_keys
        }
    if isinstance(value, (tuple, list)):
        return [canonical_payload(item, omit_keys=omit_keys) for item in value]
    return value


def _fingerprint_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized = {
            str(key): _fingerprint_payload(item)
            for key, item in value.items()
        }
        if (
            isinstance(normalized.get("release"), Mapping)
            and isinstance(normalized["release"].get("reasons"), list)
        ):
            normalized["release"]["reasons"] = sorted(
                normalized["release"]["reasons"],
                key=lambda item: stable_json(item),
            )
        for collection in (
            "slices",
            "bases",
            "values",
            "comparisons",
            "qa_events",
        ):
            if isinstance(normalized.get(collection), list):
                normalized[collection] = sorted(
                    normalized[collection],
                    key=lambda item: stable_json(item),
                )
        return normalized
    if isinstance(value, list):
        return [_fingerprint_payload(item) for item in value]
    return value
