from dataclasses import replace
import json
from pathlib import Path

from openpyxl import load_workbook
import pytest

from src.excel_renderer import (
    Bounds, DynamicField, DynamicMasterQualification, DynamicRegionBinding,
    DynamicRegionDeclaration, DynamicRegionFormulaPolicy, DynamicRegionStylePolicy,
    DynamicRenderRequest, RenderError, Slot, lineage_from, plan_dynamic_render, render_dynamic,
)
from src.excel_renderer.dynamic_region import (
    DYNAMIC_BINDING_SCHEMA, DYNAMIC_CONTRACT, DYNAMIC_PLAN, DYNAMIC_QUALIFICATION_SCHEMA,
    _protected, _vba,
)
from src.analytics_core.result_identity import result_fingerprint
from src.excel_renderer.renderer import sha
from m7b_fixtures import source_result

FIXTURE = Path(__file__).parent / "fixtures/gate41/dynamic_region_runtime_fixture.xlsm"


def qualification(path, *, declarations=None, styles=None, formulas=None, fixed_slots=()):
    table_fields = (
        DynamicField("estimate", "estimate", 0, "PROPORTION", "exact_numeric"),
        DynamicField("status", "value_status", 1, "LITERAL", "exact_text"),
        DynamicField("display", "__PRESENTATION_FORMULA__", 2, "LITERAL", "exact_text"),
    )
    range_fields = (
        DynamicField("estimate", "estimate", 0, "PROPORTION", "exact_numeric"),
        DynamicField("status", "value_status", 1, "LITERAL", "exact_text"),
    )
    declarations = declarations or (
        DynamicRegionDeclaration("table_region", "presentation", "presentation", "dynamic_table",
            "TABLE", "Gate41DynamicTable", None, "ROWS_AND_COLUMNS", 1, 1, 5, 3,
            Bounds(1, 2, 3, 6), table_fields, "table_style", "table_formula"),
        DynamicRegionDeclaration("range_region", "presentation", "presentation", "dynamic_range",
            "RANGE", None, "Gate41RangeAnchor", "ROWS_AND_COLUMNS", 1, 1, 6, 4,
            Bounds(1, 1, 4, 6), range_fields, "range_style"),
    )
    styles = styles or (
        DynamicRegionStylePolicy("table_style", "table_region", "dynamic_table!A2",
            "ROWS_AND_COLUMNS", ("font", "fill", "border", "alignment", "protection"),
            table_style_policy="PRESERVE_EXISTING_TABLE_STYLE"),
        DynamicRegionStylePolicy("range_style", "range_region", "dynamic_range!A1",
            "ROWS_AND_COLUMNS", ("font", "fill", "border", "alignment", "protection")),
    )
    formulas = formulas if formulas is not None else (
        DynamicRegionFormulaPolicy("table_formula", "table_region", "PRESENTATION_ONLY",
            ("dynamic_table!C2",), (2,), "ROWS_AND_COLUMNS"),
    )
    return DynamicMasterQualification(DYNAMIC_QUALIFICATION_SCHEMA, "GATE41_SYNTHETIC_MASTER", "V1",
        sha(path), DYNAMIC_CONTRACT, declarations, styles, formulas, fixed_slots)


def request(path, rows=1, columns=1, *, q=None):
    run = source_result()
    if rows > 1:
        values = tuple(replace(run.values[0], value_id=f"value_{index}", estimate=0.5 + index / 10,
                               semantic_order=index + 1) for index in range(rows))
        unsigned = replace(run, values=values)
        fp = result_fingerprint(unsigned)
        run = replace(unsigned, result_fingerprint=fp,
                      manifest=replace(unsigned.manifest, result_fingerprint=fp))
    ids = tuple(v.value_id for v in run.values[:rows])
    # Repeat distinct canonical records only when the source fixture exposes enough values.
    assert len(ids) == rows
    q = q or qualification(path)
    bindings = (
        DynamicRegionBinding("table_region", run.result_run_id, "value", ids,
            ("estimate", "status", "display")[:columns], rows, columns,
            ("PROPORTION", "LITERAL", "LITERAL")[:columns]),
        DynamicRegionBinding("range_region", run.result_run_id, "value", ids,
            ("estimate", "status")[:min(columns, 2)], rows, min(columns, 2),
            ("PROPORTION", "LITERAL")[:min(columns, 2)]),
    )
    return DynamicRenderRequest((run,), q, DYNAMIC_BINDING_SCHEMA, bindings)


@pytest.fixture
def master(tmp_path):
    path = tmp_path / "master.xlsm"
    path.write_bytes(FIXTURE.read_bytes())
    return path


def test_fixture_is_reproducible_and_non_customer():
    provenance = json.loads(FIXTURE.with_name("dynamic_region_runtime_fixture_provenance.json").read_text())
    assert provenance["fixture_sha256"] == sha(FIXTURE)
    assert not provenance["customer_workbook_used"] and not provenance["customer_data_used"]


def test_rows_columns_both_region_types_and_deterministic_plan(master):
    req = request(master, rows=2, columns=2)
    first = plan_dynamic_render(req, master)
    second = plan_dynamic_render(req, master)
    assert first == second and first.plan_version == DYNAMIC_PLAN
    assert {o.operation_type for o in first.dynamic_operations} >= {
        "VALIDATE_REGION", "RESIZE_TABLE", "PROPAGATE_STYLE", "WRITE_CELL"}
    assert [w.record_id for w in first.writes if w.region_id == "range_region" and w.field_id == "estimate"] == [
        v.value_id for v in req.results[0].values[:2]]


def test_render_table_range_formula_literal_numeric_vba_and_logical_determinism(master, tmp_path):
    req = request(master, rows=2, columns=2)
    plan = plan_dynamic_render(req, master)
    a = tmp_path / "a.xlsm"
    b = tmp_path / "b.xlsm"
    ea = render_dynamic(req, master, a, plan=plan)
    eb = render_dynamic(req, master, b, plan=plan)
    assert ea["qa"] == "PASS" and ea["vba_before"] == ea["vba_after"]
    assert ea["logical_output_sha256"] == eb["logical_output_sha256"]
    w = load_workbook(a, keep_vba=True, data_only=False)
    try:
        assert w["dynamic_table"].tables["Gate41DynamicTable"].ref == "A1:B3"
        assert w["dynamic_table"]["A2"].value == 0.5
        assert w["dynamic_table"]["B2"].value == "OK"
        assert w["dynamic_range"]["A1"].value == 0.5
    finally:
        w.close(); w.vba_archive.close()


def test_presentation_formula_propagation(master, tmp_path):
    req = request(master, rows=2, columns=3)
    output = tmp_path / "formula.xlsm"
    render_dynamic(req, master, output)
    w = load_workbook(output, keep_vba=True, data_only=False)
    try:
        assert w["dynamic_table"]["C2"].data_type == "f"
        assert w["dynamic_table"]["C3"].data_type == "f"
    finally:
        w.close(); w.vba_archive.close()


def test_growth_then_contraction_clears_stale(master, tmp_path):
    grown_req = request(master, rows=2, columns=2)
    grown_plan = plan_dynamic_render(grown_req, master)
    grown = tmp_path / "grown.xlsm"
    evidence = render_dynamic(grown_req, master, grown, plan=grown_plan)
    small = request(grown, rows=1, columns=1, q=replace(grown_req.qualification,
        master_sha256=grown_req.qualification.master_sha256))
    small = replace(small, lineage=lineage_from(grown_plan, evidence),
                    qualification=grown_req.qualification)
    output = tmp_path / "contracted.xlsm"
    plan = plan_dynamic_render(small, grown)
    assert any(o.operation_type == "CLEAR_OWNED_STALE" for o in plan.dynamic_operations)
    render_dynamic(small, grown, output, plan=plan)
    w = load_workbook(output, keep_vba=True)
    try:
        assert w["dynamic_table"]["A3"].value is None
        assert w["dynamic_table"]["B2"].value is None
        assert w["dynamic_range"]["A2"].value is None
    finally:
        w.close(); w.vba_archive.close()


@pytest.mark.parametrize("change,message", [
    (lambda r: replace(r, binding_schema_version="WRONG"), "binding contract"),
    (lambda r: replace(r, renderer_build="WRONG"), "build"),
    (lambda r: replace(r, qualification=replace(r.qualification, master_sha256="0" * 64)), "Master hash"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], region_id="unknown"), r.bindings[1])), "Unknown region"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], requested_rows=6), r.bindings[1])), "overflow"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], requested_columns=4), r.bindings[1])), "overflow"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], ordered_record_ids=("missing",)), r.bindings[1])), "Missing canonical"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], field_bindings=("*",)), r.bindings[1])), "implicit field"),
    (lambda r: replace(r, bindings=(replace(r.bindings[0], requested_rows=2), r.bindings[1])), "Cardinality"),
])
def test_fail_closed_request_defects(master, change, message):
    with pytest.raises(RenderError, match=message):
        plan_dynamic_render(change(request(master)), master)


def test_unauthorized_dimensions(master):
    req = request(master, rows=2, columns=2)
    d = replace(req.qualification.declarations[0], growth_dimensions="ROWS")
    s = replace(req.qualification.style_policies[0], propagation_axis="ROWS")
    q = replace(req.qualification, declarations=(d, req.qualification.declarations[1]),
                style_policies=(s, req.qualification.style_policies[1]))
    with pytest.raises(RenderError, match="unauthorized column"):
        plan_dynamic_render(replace(req, qualification=q), master)


@pytest.mark.parametrize("kind,bounds,table,anchor,message", [
    ("RANGE", Bounds(1, 1, 2, 1), None, "MissingAnchor", "Missing named anchor"),
    ("TABLE", Bounds(1, 2, 2, 2), "MissingTable", None, "Missing/wrong table"),
])
def test_missing_physical_binding(master, kind, bounds, table, anchor, message):
    req = request(master)
    d = replace(req.qualification.declarations[0], region_kind=kind, table_id=table,
                anchor_name=anchor, owned_envelope=bounds, max_rows=1, max_columns=2)
    policy = replace(req.qualification.style_policies[0],
                     table_style_policy="NOT_APPLICABLE" if kind == "RANGE" else "PRESERVE_EXISTING_TABLE_STYLE")
    q = replace(req.qualification, declarations=(d, req.qualification.declarations[1]),
                style_policies=(policy, req.qualification.style_policies[1]))
    with pytest.raises(RenderError, match=message):
        plan_dynamic_render(replace(req, qualification=q), master)


def test_duplicate_and_overlap_fail_closed(master):
    req = request(master)
    duplicate = replace(req.qualification.declarations[1], region_id="table_region")
    with pytest.raises(RenderError, match="Duplicate region"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification,
            declarations=(req.qualification.declarations[0], duplicate))), master)
    overlap = replace(req.qualification.declarations[1], sheet="dynamic_table",
        owned_envelope=Bounds(1, 2, 4, 7))
    with pytest.raises(RenderError, match="overlap"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification,
            declarations=(req.qualification.declarations[0], overlap))), master)


def test_formula_and_style_policy_fail_closed(master):
    req = request(master)
    bad_formula = replace(req.qualification.formula_policies[0], classification="ANALYTICAL")
    with pytest.raises(RenderError, match="Analytical"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification,
            formula_policies=(bad_formula,))), master)
    bad_style = replace(req.qualification.style_policies[0], template_cell="dynamic_table!Z99")
    with pytest.raises(RenderError, match="Unknown style"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification,
            style_policies=(bad_style, req.qualification.style_policies[1]))), master)


@pytest.mark.parametrize("anchor,envelope,template,message", [
    ("Gate41MergedAnchor", Bounds(1, 1, 2, 1), "collision_fixture!A1", "Merged-cell"),
    ("Gate41ProtectedName", Bounds(4, 1, 5, 1), "collision_fixture!E1", "Protected/non-owned"),
    ("Gate41FormulaAnchor", Bounds(6, 1, 7, 1), "collision_fixture!G1", "Unallowlisted formula"),
])
def test_physical_collision_surfaces_fail_closed(master, anchor, envelope, template, message):
    base = request(master)
    declaration = DynamicRegionDeclaration("collision_region", "presentation", "presentation",
        "collision_fixture", "RANGE", None, anchor, "COLUMNS", 1, 1, 1, 2,
        envelope, (DynamicField("estimate", "estimate", 0, "PROPORTION", "exact_numeric"),),
        "collision_style")
    style = DynamicRegionStylePolicy("collision_style", "collision_region", template,
        "COLUMNS", ("font",), table_style_policy="NOT_APPLICABLE")
    q = replace(base.qualification, declarations=(declaration,), style_policies=(style,), formula_policies=())
    binding = DynamicRegionBinding("collision_region", base.results[0].result_run_id, "value",
        (base.results[0].values[0].value_id,), ("estimate",), 1, 1, ("PROPORTION",))
    with pytest.raises(RenderError, match=message):
        plan_dynamic_render(replace(base, qualification=q, bindings=(binding,)), master)


def test_fixed_slot_collision_fails_closed(master):
    req = request(master)
    q = replace(req.qualification,
                fixed_slots=(Slot("fixed", "presentation", "numeric", "exact_numeric",
                                  name="Gate41RangeAnchor"),))
    with pytest.raises(RenderError, match="fixed-slot"):
        plan_dynamic_render(replace(req, qualification=q), master)


def test_protected_surface_and_vba_oracles_detect_mutation(master, tmp_path):
    req = request(master)
    before = _protected(master, req.qualification.declarations)
    changed = tmp_path / "protected_changed.xlsm"
    workbook = load_workbook(master, keep_vba=True)
    try:
        workbook["collision_fixture"]["D1"] = "MUTATED"
        workbook.save(changed)
    finally:
        workbook.close(); workbook.vba_archive.close()
    assert _protected(changed, req.qualification.declarations) != before
    assert _vba(changed) == _vba(master)


def test_unverifiable_lineage_and_no_partial_publication(master, tmp_path):
    req = request(master)
    bad = replace(req, lineage=replace(lineage_from(plan_dynamic_render(req, master), {
        "output_sha256": sha(master), "region_bounds": ()}), prior_plan_sha256=""))
    output = tmp_path / "must_not_exist.xlsm"
    with pytest.raises(RenderError, match="previous active footprint"):
        render_dynamic(bad, master, output)
    assert not output.exists()
