from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from .renderer import (
    BUILD, MAPPING, MASTER, NUMERIC, SIGNIFICANCE, VISUAL,
    MasterManifest, RenderError, Slot, TableBinding, require,
)

VBA_PRESERVATION = "M7_VBA_PRESERVATION_V1"
PROVENANCE = "M7_PROVENANCE_DETERMINISM_V1"
QUALIFICATION_SCHEMA = "M7_PRODUCTION_MASTER_QUALIFICATION_V1"


@dataclass(frozen=True)
class QualifiedMaster:
    manifest: MasterManifest
    qualification: dict


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vba_sha256(path: Path) -> str:
    try:
        with ZipFile(path) as package:
            payload = package.read("xl/vbaProject.bin")
    except (BadZipFile, KeyError) as exc:
        raise RenderError("Qualified Master requires a valid VBA project") from exc
    return hashlib.sha256(payload).hexdigest()


def load_qualified_master(manifest_path: Path, master_path: Path) -> QualifiedMaster:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RenderError("Invalid qualification manifest") from exc
    required = {
        "schema_version", "master_id", "master_version", "filename", "master_sha256",
        "vba_present", "vba_project_sha256", "contracts", "renderer_build",
        "qualification_status", "supported_capabilities", "unsupported_capabilities",
        "roles", "writable_slots", "presentation_formulas",
    }
    require(isinstance(data, dict) and set(data) == required, "Invalid qualification manifest fields")
    require(data["schema_version"] == QUALIFICATION_SCHEMA, "Unsupported qualification schema")
    require(data["master_id"] == "EXPLORA_PRODUCTION_MASTER_V1", "Wrong Master ID")
    require(data["master_version"] in ("1.0.0", "1.1.0"), "Unsupported Master version")
    require(data["filename"] == master_path.name, "Master filename mismatch")
    require(data["qualification_status"] == "QUALIFIED", "Master is not qualified")
    require(data["renderer_build"] == BUILD, "Unsupported renderer build")
    contracts = data["contracts"]
    expected = {
        "visual_spec": VISUAL, "master_interface": MASTER, "mapping": MAPPING,
        "numeric_display": NUMERIC, "significance_presentation": SIGNIFICANCE,
        "vba_preservation": VBA_PRESERVATION, "provenance_determinism": PROVENANCE,
    }
    require(contracts == expected, "Incompatible frozen contract references")
    require(data["vba_present"] is True, "Production Master VBA requirement mismatch")
    require(_sha256(master_path) == data["master_sha256"], "Unexpected Master fingerprint")
    require(_vba_sha256(master_path) == data["vba_project_sha256"], "Unexpected VBA fingerprint")
    require(isinstance(data["supported_capabilities"], list) and data["supported_capabilities"],
            "Missing supported capabilities")
    require(isinstance(data["unsupported_capabilities"], list), "Invalid coverage gaps")
    try:
        roles = tuple(TableBinding(**item) for item in data["roles"])
        slots = tuple(Slot(**item) for item in data["writable_slots"])
        formulas = tuple(tuple(item) for item in data["presentation_formulas"])
    except (TypeError, ValueError) as exc:
        raise RenderError("Invalid Master interface mapping") from exc
    require(len({role.role_id for role in roles}) == len(roles), "Ambiguous Master roles")
    require(len({slot.slot_id for slot in slots}) == len(slots), "Ambiguous Master targets")
    manifest = MasterManifest(
        data["master_id"], data["master_version"], data["master_sha256"], MASTER,
        (VISUAL,), roles, slots, formulas,
    )
    return QualifiedMaster(manifest, data)


def vba_sha256(path: Path) -> str:
    return _vba_sha256(path)
