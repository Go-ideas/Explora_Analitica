from dataclasses import replace
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from scripts.validate_gate19_corrective import PACKAGE_SHA, REQUEST_IDS, RUNTIME_FP, SOURCE_SHA
from src.analytics_core.result_identity import stable_json
from src.canonical_materialization.orchestrator import run_canonical_project
from src.excel_renderer import (
    RenderError, benchmark_a_request, load_qualified_master, plan_render, render,
    validate_output, vba_sha256,
)
from src.excel_renderer.renderer import configuration_fingerprint

MASTER = Path(__file__).parents[1] / "production_masters" / "EXPLORA_PRODUCTION_MASTER_V1.xlsm"
QUALIFICATION = MASTER.with_suffix(".qualification.json")
MASTER_SHA = "a8313adf706016b30b8837a7bc42cb80c7ccc281f2663616a7f22b8daa8d10dd"
VBA_SHA = "0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758"


@pytest.fixture(scope="module")
def qualified():
    return load_qualified_master(QUALIFICATION, MASTER)


@pytest.fixture(scope="module")
def benchmark_run():
    inputs = Path(__file__).resolve().parents[3] / "_gate19_inputs" / "benchmark_a"
    execution = run_canonical_project(
        source_path=inputs / "FUNSMX_297140_20260914.sav",
        package_path=inputs / "BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip",
        request_ids=REQUEST_IDS, expected_source_sha256=SOURCE_SHA,
        expected_package_sha256=PACKAGE_SHA, expected_runtime_fingerprint=RUNTIME_FP,
    )
    return execution.results["BA-01"]


@pytest.fixture(scope="module")
def production_request(qualified, benchmark_run):
    return benchmark_a_request(qualified, benchmark_run)


def resign(request):
    pending = replace(request.configuration_release, source_hash="PENDING")
    candidate = replace(request, configuration_release=pending)
    return replace(candidate, configuration_release=replace(
        candidate.configuration_release, source_hash=configuration_fingerprint(candidate)))


def test_master_identity_and_vba_are_qualified(qualified):
    assert qualified.manifest.master_id == "EXPLORA_PRODUCTION_MASTER_V1"
    assert qualified.manifest.version == "1.1.0"
    assert hashlib.sha256(MASTER.read_bytes()).hexdigest() == MASTER_SHA
    assert vba_sha256(MASTER) == VBA_SHA


def test_benchmark_a_plan_is_deterministic(production_request):
    first = plan_render(production_request, MASTER)
    second = plan_render(production_request, MASTER)
    assert first == second
    assert first.plan_sha256 == second.plan_sha256
    assert len(first.writes) > 1000


def test_first_integration_is_binary_deterministic_and_preserves_vba(tmp_path, production_request):
    plan = plan_render(production_request, MASTER)
    first, second = tmp_path / "first.xlsm", tmp_path / "second.xlsm"
    evidence_first = render(production_request, MASTER, first, plan=plan)
    evidence_second = render(production_request, MASTER, second, plan=plan)
    assert first.read_bytes() == second.read_bytes()
    assert vba_sha256(first) == vba_sha256(second) == VBA_SHA
    assert evidence_first == evidence_second
    assert evidence_first["vba_before"] == evidence_first["vba_after"] == VBA_SHA
    assert evidence_first["untouched_parts_exact"] is True
    assert evidence_first["undeclared_cells_preserved"] is True


@pytest.mark.parametrize("field,value,error", [
    ("master_id", "WRONG", "Wrong Master ID"),
    ("master_version", "2.0.0", "Unsupported Master version"),
    ("master_sha256", "0" * 64, "Unexpected Master fingerprint"),
    ("qualification_status", "PENDING", "not qualified"),
    ("renderer_build", "UNKNOWN", "Unsupported renderer build"),
])
def test_manifest_identity_fail_closed(tmp_path, field, value, error):
    data = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    data[field] = value
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RenderError, match=error):
        load_qualified_master(path, MASTER)


def test_incomplete_mapping_fails_closed(production_request):
    request = replace(production_request, slots=production_request.slots[:-1])
    with pytest.raises(RenderError, match="slot coverage"):
        plan_render(resign(request), MASTER)


def test_missing_target_fails_closed(production_request):
    slots = (replace(production_request.slots[0], name="MissingTarget"), *production_request.slots[1:])
    request = replace(production_request, slots=slots, master=replace(production_request.master, writable_slots=slots))
    with pytest.raises(RenderError, match="Missing workbook target"):
        plan_render(resign(request), MASTER)


def test_ambiguous_duplicate_target_fails_closed(production_request):
    slots = list(production_request.slots)
    slots[1] = replace(slots[1], name=slots[0].name, status_name=slots[0].status_name,
                       label_name=slots[0].label_name)
    request = replace(production_request, slots=tuple(slots), master=replace(
        production_request.master, writable_slots=tuple(slots)))
    with pytest.raises(RenderError, match="Duplicate/ambiguous target"):
        plan_render(resign(request), MASTER)


def test_incompatible_target_type_fails_closed(production_request):
    slots = (replace(production_request.slots[0], kind="literal"), *production_request.slots[1:])
    request = replace(production_request, slots=slots, master=replace(production_request.master, writable_slots=slots))
    with pytest.raises(RenderError, match="Incompatible target storage mode"):
        plan_render(resign(request), MASTER)


@pytest.mark.parametrize("profile", ["UNKNOWN_PROFILE", "SIGNIFICANCE_TOKEN"])
def test_invalid_profile_or_token_fails_closed(production_request, profile):
    spec = json.loads(production_request.visual_spec_json)
    spec["sections"][0]["visuals"][0]["display_profile_ref"] = profile
    request = resign(replace(production_request, visual_spec_json=stable_json(spec)))
    with pytest.raises(RenderError):
        plan_render(request, MASTER)


def test_incompatible_canonical_result_fails_closed(production_request):
    run = replace(production_request.results[0], result_schema_version="UNKNOWN")
    request = resign(replace(production_request, results=(run,)))
    with pytest.raises((RenderError, ValueError)):
        plan_render(request, MASTER)


def test_tampered_plan_fails_closed(tmp_path, production_request):
    plan = plan_render(production_request, MASTER)
    bad = replace(plan, plan_sha256="0" * 64)
    with pytest.raises(RenderError, match="tampered Render Plan"):
        render(production_request, MASTER, tmp_path / "bad.xlsm", plan=bad)


def test_formula_or_protected_surface_mutation_is_detected(tmp_path, production_request):
    plan = plan_render(production_request, MASTER)
    output = tmp_path / "rendered.xlsm"
    render(production_request, MASTER, output, plan=plan)
    broken = tmp_path / "broken.xlsm"
    with ZipFile(output) as source, ZipFile(broken, "w", ZIP_DEFLATED) as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                payload = payload.replace(b"<f>1+1</f>", b"<f>2+2</f>")
            target.writestr(item, payload)
    with pytest.raises(RenderError):
        validate_output(MASTER, broken, plan)


def test_vba_mutation_fails_qualification(tmp_path):
    broken = tmp_path / MASTER.name
    with ZipFile(MASTER) as source, ZipFile(broken, "w", ZIP_DEFLATED) as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "xl/vbaProject.bin":
                payload += b"UNAUTHORIZED"
            target.writestr(item, payload)
    data = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    data["master_sha256"] = hashlib.sha256(broken.read_bytes()).hexdigest()
    manifest = tmp_path / "qualification.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RenderError, match="VBA fingerprint"):
        load_qualified_master(manifest, broken)


def test_corrupt_ooxml_fails_closed(tmp_path):
    broken = tmp_path / MASTER.name
    broken.write_bytes(b"not-a-zip")
    data = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    data["master_sha256"] = hashlib.sha256(broken.read_bytes()).hexdigest()
    manifest = tmp_path / "qualification.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RenderError, match="valid VBA project"):
        load_qualified_master(manifest, broken)


def test_nondeterministic_contract_resolution_fails_closed(production_request):
    spec = json.loads(production_request.visual_spec_json)
    spec["sections"][0]["visuals"].append(dict(spec["sections"][0]["visuals"][0]))
    request = resign(replace(production_request, visual_spec_json=stable_json(spec)))
    with pytest.raises(RenderError, match="Duplicate visual"):
        plan_render(request, MASTER)
