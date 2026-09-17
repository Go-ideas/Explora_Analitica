from __future__ import annotations

from src.canonical_materialization.models import CanonicalRuntimeInput, MaterializationError
from src.canonical_materialization.orchestrator import _one
from src.web_canonical.identity_bridge import LegacyIdentityBridge
from src.web_canonical.legacy_projection import _stable_text


def legacy_identity_bridge(runtime: CanonicalRuntimeInput, request_id: str) -> LegacyIdentityBridge:
    request = _one(runtime.package.requests["requests"], "request_id", request_id)
    question = _one(runtime.package.questions, "question_id", request["question_ref"])
    structure = _one(runtime.package.structures, "structure_id", question["structure_ref"])
    if structure["structure_type"] == "RU":
        variables = structure.get("variable_bindings", ())
        if len(variables) != 1:
            raise MaterializationError("Legacy RU bridge requires one physical variable")
        rows = tuple((c["category_id"], variables[0]["variable_ref"], _stable_text(c["raw_value"])) for c in structure["category_bindings"])
    elif structure["structure_type"] == "RM" and structure.get("storage_encoding") == "dichotomous_columns":
        rows = tuple((o["option_id"], o["variable_ref"], None) for o in structure["option_bindings"])
    else:
        raise MaterializationError("Unsupported Legacy bridge structure")
    banner_members = ()
    if request.get("banner"):
        banner = _one(runtime.package.banner_filters["banners"], "banner_id", request["banner"]["banner_ref"])
        requested = request["banner"]["member_ids"]
        members = [_one(banner["members"], "member_id", member) for member in requested]
        banner_members = tuple((banner["dimension_id"], m["member_id"], banner["physical_variable_ref"], _stable_text(m["raw_value"])) for m in members)
    bridge = LegacyIdentityBridge(question["question_id"], structure["structure_id"], structure["structure_type"], rows, banner_members, (f"runtime_fp:{runtime.fingerprint}", f"package_sha:{runtime.package_fingerprint}", f"structure_ref:{structure['structure_id']}", f"structure_spec:{structure['spec_hash']}"))
    bridge.validate()
    return bridge
