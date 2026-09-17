from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def canonical_payload(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: canonical_payload(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): canonical_payload(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (tuple, list)):
        return [canonical_payload(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return {"scalar_type": "missing", "value": None}
        if not math.isfinite(value):
            raise ValueError("non-finite canonical scalar is unsupported")
        return {"scalar_type": "number", "value": str(int(value)) if value.is_integer() else repr(value)}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"scalar_type": "number", "value": str(value)}
    if value is None:
        return {"scalar_type": "missing", "value": None}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonical_payload(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def runtime_fingerprint_payload(runtime: Any) -> dict[str, Any]:
    manifest = runtime.manifest
    return {
        "schema_version": "CanonicalRuntimeInput/V1-derived-for-Gate28",
        "project_id": runtime.project_id,
        "source_sha256": runtime.source_fingerprint,
        "source_rows": runtime.source_n,
        "package_id": manifest.package_id,
        "package_version": manifest.package_version,
        "package_sha256": runtime.package_fingerprint,
        "manifest_spec_hash": manifest.package_spec_hash,
        "default_execution_mode": manifest.default_execution_mode,
        "dual_run_executed": manifest.dual_run_executed,
        "canonical_result_generated": manifest.canonical_result_generated,
    }


def runtime_fingerprint(runtime: Any) -> str:
    return hashlib.sha256(json.dumps(runtime_fingerprint_payload(runtime), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def object_spec_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("spec_hash", None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest().upper()
