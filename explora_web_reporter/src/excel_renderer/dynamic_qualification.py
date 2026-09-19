"""Versioned Production Master qualification loader for Dynamic Regions."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile
import hashlib

from .dynamic_region import (
    Bounds, DYNAMIC_BUILD, DYNAMIC_CONTRACT, DYNAMIC_QUALIFICATION_SCHEMA,
    DynamicField, DynamicMasterQualification, DynamicRegionDeclaration,
    DynamicRegionFormulaPolicy, DynamicRegionStylePolicy,
)
from .renderer import RenderError, Slot, require, sha

PRODUCTION_DYNAMIC_QUALIFICATION = "M7_PRODUCTION_DYNAMIC_REGION_QUALIFICATION_V1"


def load_dynamic_qualified_master(manifest_path: Path, master_path: Path) -> DynamicMasterQualification:
    try:
        data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RenderError("Invalid Dynamic Production qualification manifest") from exc
    required = {"schema_version", "master_id", "master_version", "filename", "master_sha256",
        "baseline_version", "baseline_filename", "baseline_sha256", "vba_project_sha256",
        "region_contract_version", "renderer_build", "qualification_status", "declarations",
        "style_policies", "formula_policies", "fixed_slots", "lineage"}
    require(isinstance(data, dict) and set(data) == required, "Invalid Dynamic Production qualification fields")
    require(data["schema_version"] == PRODUCTION_DYNAMIC_QUALIFICATION
            and data["region_contract_version"] == DYNAMIC_CONTRACT
            and data["renderer_build"] == DYNAMIC_BUILD, "Unsupported Dynamic Production qualification")
    require(data["master_version"] == "1.2.0" and data["baseline_version"] == "1.1.0"
            and data["qualification_status"] == "CANDIDATE", "Wrong Dynamic Production lineage")
    require(Path(master_path).name == data["filename"] and sha(master_path) == data["master_sha256"],
            "Dynamic Production Master identity mismatch")
    with ZipFile(master_path) as package:
        vba = hashlib.sha256(package.read("xl/vbaProject.bin")).hexdigest()
    require(vba == data["vba_project_sha256"], "Dynamic Production VBA identity mismatch")
    try:
        declarations = []
        for item in data["declarations"]:
            item = dict(item)
            item["owned_envelope"] = Bounds(**item["owned_envelope"])
            item["field_columns"] = tuple(DynamicField(**field) for field in item["field_columns"])
            declarations.append(DynamicRegionDeclaration(**item))
        styles = tuple(DynamicRegionStylePolicy(**{**item,
            "owned_attributes": tuple(item["owned_attributes"]),
            "unsupported_attributes": tuple(item["unsupported_attributes"])}) for item in data["style_policies"])
        formulas = tuple(DynamicRegionFormulaPolicy(**{**item,
            "source_formula_cells": tuple(item["source_formula_cells"]),
            "target_field_offsets": tuple(item["target_field_offsets"])}) for item in data["formula_policies"])
        slots = tuple(Slot(**item) for item in data["fixed_slots"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RenderError("Malformed Dynamic Production qualification mapping") from exc
    return DynamicMasterQualification(DYNAMIC_QUALIFICATION_SCHEMA, data["master_id"],
        data["master_version"], data["master_sha256"], DYNAMIC_CONTRACT,
        tuple(declarations), styles, formulas, slots)
