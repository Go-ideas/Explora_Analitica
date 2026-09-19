from dataclasses import replace
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import load_workbook
import pytest

from src.analytics_core.execution_adapter import (
    CanonicalExecutionContext, SliceExecutionAuthority, execute_canonical_request,
)
from src.analytics_core.result_identity import canonical_payload, request_identity, stable_json
from src.analytics_core.results import make_slice
from src.analytics_core.serialization import from_canonical_json, to_canonical_json
from src.analytics_core.significance import ProportionComparisonInput, ProportionFamilyRequest
from src.contracts.models import ReleaseMetadata, SignificanceSpec
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode, StatisticalState
from src.excel_renderer import RenderError, plan_render, render, validate_output, vba_sha256
from src.excel_renderer.production import significance_qualification_request
from src.excel_renderer.qualification import load_qualified_master
from src.excel_renderer.renderer import configuration_fingerprint, sha, sha_bytes
from test_m5_execution_adapter import metric, request, ru_result, universe


MASTER = Path(__file__).parents[1] / "production_masters" / "EXPLORA_PRODUCTION_MASTER_V1.xlsm"
QUALIFICATION = MASTER.with_suffix(".qualification.json")
MASTER_SHA = "a8313adf706016b30b8837a7bc42cb80c7ccc281f2663616a7f22b8daa8d10dd"
VBA_SHA = "0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758"
FIXTURE_ID = "B2_SYNTHETIC_PROPORTION_QUALIFICATION_V1"
FIXTURE_SHA = "c1ba658901612eea212245973f84cd2b361f95013916e1f1136033dca0ce47e1"


def significance_spec(confidence=0.95):
    release = ReleaseMetadata(ReleaseLifecycle.RELEASED, ReleaseMode.REVIEW, "B2_REVIEW",
                              "2026-09-19", "B2", "B2_V1", "SIGNIFICANCE_POLICY_CANONICAL")
    return SignificanceSpec("B2_QUALIFICATION", "1.0.0", release, "pooled_z",
                            confidence=confidence, alpha=1-confidence)


def core_result(confidence=0.95, left=70, right=30, left_n=100, right_n=100):
    slices = (
        SliceExecutionAuthority(make_slice(is_total=False, banner_ref="B", member_ids=("A",),
            configuration={"fixture": FIXTURE_ID, "member": "A"}), universe()),
        SliceExecutionAuthority(make_slice(is_total=False, banner_ref="B", member_ids=("B",),
            configuration={"fixture": FIXTURE_ID, "member": "B"}), universe()),
    )
    comparison = ProportionComparisonInput(
        "A", "B", slices[0].slice.slice_id, slices[1].slice.slice_id,
        left, right, left_n, right_n,
    )
    family = ProportionFamilyRequest(
        significance_spec(confidence), "Q_RU", "M_PROP", "banner", "family_gate39", (comparison,))
    snapshot = replace(request("GATE39_REQUEST"), question_ids=("Q_RU",), metric_refs=("M_PROP",))
    _, request_fingerprint = request_identity(canonical_payload(snapshot))
    snapshot = replace(snapshot, request_fingerprint=request_fingerprint)
    return execute_canonical_request(CanonicalExecutionContext(
        project_id="GATE39_QUALIFICATION", dataset_fingerprint=FIXTURE_SHA,
        project_spec_ref="GATE39_SYNTHETIC_PROJECT_SPEC", request=snapshot,
        question_id="Q_RU", structure_ref="STR_RU", structure_result=ru_result(),
        universe_result=universe(), metric_specs=(metric("M_PROP", "proportion/v1",
            parameters={"category_id": "A"}),), runtime_fingerprint=FIXTURE_SHA,
        slices=slices, significance_families=(family,), result_run_id="gate39-core-run",
        b3_release_evidence=True, provenance_refs=(f"fixture:{FIXTURE_ID}", f"fixture_sha256:{FIXTURE_SHA}")))


def qualified():
    return load_qualified_master(QUALIFICATION, MASTER)


def request_for(run, target="left", text="*"):
    comparison = run.comparisons[0]
    slice_id = comparison.left_slice_id if target == "left" else comparison.right_slice_id
    value = next(item for item in run.values if item.slice_id == slice_id)
    return significance_qualification_request(
        qualified(), run, comparison_id=comparison.comparison_id, value_id=value.value_id,
        token_id="canonical_marker", display_text=text)


@pytest.mark.parametrize("confidence", [0.90, 0.95, 0.99])
def test_core_generated_supported_confidence_is_visibly_presented(tmp_path, confidence):
    run = core_result(confidence)
    assert run.comparisons[0].status is StatisticalState.SIGNIFICANT
    request = request_for(run)
    plan = plan_render(request, MASTER)
    output = tmp_path / f"confidence-{confidence}.xlsm"
    render(request, MASTER, output, plan=plan)
    workbook = load_workbook(output, keep_vba=True, data_only=False)
    try:
        assert workbook["presentation"]["E2"].value == "*"
        assert workbook["presentation"]["H2"].value == "SIGNIFICANT"
    finally:
        workbook.close()
        workbook.vba_archive.close()


def test_canonical_serialization_materializes_core_relation_unchanged():
    run = core_result()
    restored = from_canonical_json(to_canonical_json(run))
    assert canonical_payload(restored.comparisons) == canonical_payload(run.comparisons)
    assert restored.result_fingerprint == run.result_fingerprint


@pytest.mark.parametrize("values,reason", [((52, 48, 100, 100), "NOT_SIGNIFICANT"),
    ((20, 15, 29, 30), "INELIGIBLE_MINIMUM_BASE"),
    ((1, 0, 100, 100), "INELIGIBLE_EXPECTED_COUNT")])
def test_non_significant_and_ineligible_never_become_visible_markers(values, reason):
    run = core_result(left=values[0], right=values[1], left_n=values[2], right_n=values[3])
    relation = run.comparisons[0]
    assert reason == str(relation.status) or any(reason in ref for ref in relation.provenance_refs)
    with pytest.raises(RenderError, match="Invalid significance assertion"):
        plan_render(request_for(run), MASTER)


@pytest.mark.parametrize("left,right,target,direction", [
    (70, 30, "left", "LEFT_GREATER"), (30, 70, "right", "RIGHT_GREATER")])
def test_direction_and_reference_are_canonical_and_traceable(left, right, target, direction):
    run = core_result(left=left, right=right)
    relation = run.comparisons[0]
    assert relation.direction == direction
    plan = plan_render(request_for(run, target=target), MASTER)
    marker = next(write for write in plan.writes if write.slot_id == "significance_marker")
    assert marker.record_id == relation.comparison_id
    assert marker.token_id == "canonical_marker"
    assert marker.cell == "E2"


def test_missing_canonical_relation_cannot_be_recomputed_from_values_or_bases():
    run = core_result()
    without_relation = replace(run, comparisons=())
    with pytest.raises(ValueError, match="Missing canonical significance source"):
        significance_qualification_request(qualified(), without_relation,
            comparison_id=run.comparisons[0].comparison_id, value_id=run.values[0].value_id,
            token_id="canonical_marker", display_text="*")


@pytest.mark.parametrize("defect,error", [
    ("malformed_token", "Malformed contract JSON"),
    ("unsupported_contract", "Unsupported token contract"),
    ("invalid_reference", "Token target mismatch"),
    ("missing_target", "Missing workbook target"),
    ("wrong_master", "Master hash mismatch"),
])
def test_fail_closed_presentation_boundaries(defect, error):
    run = core_result()
    request = request_for(run)
    if defect == "malformed_token":
        raw = "{"
        spec = json.loads(request.visual_spec_json)
        spec["sections"][0]["visuals"][0]["significance_presentation_refs"] = [sha_bytes(raw)]
        request = replace(request, significance_json=(raw,), visual_spec_json=stable_json(spec))
    elif defect == "unsupported_contract":
        token = json.loads(request.significance_json[0])
        token["schema_version"] = "UNKNOWN"
        raw = stable_json(token)
        spec = json.loads(request.visual_spec_json)
        spec["sections"][0]["visuals"][0]["significance_presentation_refs"] = [sha_bytes(raw)]
        request = replace(request, significance_json=(raw,), visual_spec_json=stable_json(spec))
        request = replace(request, configuration_release=replace(
            request.configuration_release, source_hash=configuration_fingerprint(request)))
    elif defect == "invalid_reference":
        token = json.loads(request.significance_json[0])
        token["comparison_bindings"][0]["slice_id"] = "wrong"
        raw = stable_json(token)
        spec = json.loads(request.visual_spec_json)
        spec["sections"][0]["visuals"][0]["significance_presentation_refs"] = [sha_bytes(raw)]
        request = replace(request, significance_json=(raw,), visual_spec_json=stable_json(spec))
        request = replace(request, configuration_release=replace(
            request.configuration_release, source_hash=configuration_fingerprint(request)))
    elif defect == "missing_target":
        slot = replace(request.slots[0], name="MissingSignificanceTarget")
        request = replace(request, slots=(slot,), master=replace(request.master, writable_slots=(slot,)))
        request = replace(request, configuration_release=replace(
            request.configuration_release, source_hash=configuration_fingerprint(request)))
    else:
        request = replace(request, master=replace(request.master, artifact_sha256="0" * 64))
    request = replace(request, master_release=replace(
        request.master_release, source_hash=request.master.artifact_sha256))
    request = replace(request, configuration_release=replace(
        request.configuration_release, source_hash=configuration_fingerprint(request)))
    with pytest.raises(RenderError, match=error):
        plan_render(request, MASTER)


def test_render_is_binary_deterministic_and_preserves_protected_surfaces(tmp_path):
    request = request_for(core_result())
    first_plan = plan_render(request, MASTER)
    second_plan = plan_render(request, MASTER)
    assert first_plan == second_plan
    first, second = tmp_path / "first.xlsm", tmp_path / "second.xlsm"
    first_evidence = render(request, MASTER, first, plan=first_plan)
    second_evidence = render(request, MASTER, second, plan=second_plan)
    assert first.read_bytes() == second.read_bytes()
    assert sha(first) == sha(second)
    assert first_evidence == second_evidence
    assert first_evidence["undeclared_cells_preserved"] is True
    assert first_evidence["untouched_parts_exact"] is True
    assert vba_sha256(MASTER) == vba_sha256(first) == vba_sha256(second) == VBA_SHA
    validate_output(MASTER, first, first_plan)


def test_protected_surface_and_vba_mutation_fail_closed(tmp_path):
    request = request_for(core_result())
    plan = plan_render(request, MASTER)
    rendered = tmp_path / "rendered.xlsm"
    render(request, MASTER, rendered, plan=plan)
    broken = tmp_path / "broken.xlsm"
    with ZipFile(rendered) as source, ZipFile(broken, "w", ZIP_DEFLATED) as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "xl/vbaProject.bin":
                payload += b"UNAUTHORIZED"
            target.writestr(item, payload)
    with pytest.raises(RenderError):
        validate_output(MASTER, broken, plan)


def test_master_identity_and_fixture_are_frozen():
    master = qualified()
    assert master.manifest.master_id == "EXPLORA_PRODUCTION_MASTER_V1"
    assert master.manifest.version == "1.1.0"
    assert sha(MASTER) == MASTER_SHA
    assert vba_sha256(MASTER) == VBA_SHA
    assert FIXTURE_ID == "B2_SYNTHETIC_PROPORTION_QUALIFICATION_V1"
