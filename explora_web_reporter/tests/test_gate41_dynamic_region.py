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
    _protected, _validate_dynamic_output, _vba,
)
from src.analytics_core.result_identity import result_fingerprint, stable_json
from src.contracts.vocabulary import StatisticalState
from src.excel_renderer.renderer import SIGNIFICANCE, sha, sha_bytes
from m7b_fixtures import source_result
from test_gate39_significance_presentation import core_result

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
    f = replace(req.qualification.formula_policies[0], propagation_axis="ROWS")
    q = replace(req.qualification, declarations=(d, req.qualification.declarations[1]),
                style_policies=(s, req.qualification.style_policies[1]), formula_policies=(f,))
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


@pytest.mark.parametrize("region_id,axis,rows,columns", [
    ("table_region", "ROWS", 2, 1), ("table_region", "COLUMNS", 1, 2),
    ("table_region", "ROWS_AND_COLUMNS", 2, 2), ("range_region", "ROWS", 2, 1),
    ("range_region", "COLUMNS", 1, 2), ("range_region", "ROWS_AND_COLUMNS", 2, 2),
])
def test_each_region_kind_and_growth_axis_positive(master, tmp_path, region_id, axis, rows, columns):
    req = request(master, rows=max(rows, 1), columns=max(columns, 1))
    declarations, policies = list(req.qualification.declarations), list(req.qualification.style_policies)
    index = 0 if region_id == "table_region" else 1
    declarations[index] = replace(declarations[index], growth_dimensions=axis)
    policies[index] = replace(policies[index], propagation_axis=axis)
    formula_policies = req.qualification.formula_policies
    if index == 0:
        formula_policies = (replace(formula_policies[0], propagation_axis=axis),)
    bindings = list(req.bindings)
    bindings[index] = replace(bindings[index], requested_rows=rows, requested_columns=columns,
        ordered_record_ids=tuple(v.value_id for v in req.results[0].values[:rows]),
        field_bindings=bindings[index].field_bindings[:columns],
        display_profile_refs=bindings[index].display_profile_refs[:columns])
    other = 1 - index
    bindings[other] = replace(bindings[other], requested_rows=1, requested_columns=1,
        ordered_record_ids=(req.results[0].values[0].value_id,), field_bindings=bindings[other].field_bindings[:1],
        display_profile_refs=bindings[other].display_profile_refs[:1])
    q = replace(req.qualification, declarations=tuple(declarations), style_policies=tuple(policies),
                formula_policies=formula_policies)
    req = replace(req, qualification=q, bindings=tuple(bindings))
    plan = plan_dynamic_render(req, master)
    validation = next(o for o in plan.dynamic_operations
                      if o.region_id == region_id and o.operation_type == "VALIDATE_REGION")
    assert (validation.after_bounds.rows, validation.after_bounds.columns) == (rows, columns)
    output = tmp_path / f"{region_id}-{axis}.xlsm"
    evidence = render_dynamic(req, master, output, plan=plan)
    assert evidence["output_validation_sha256"]
    workbook = load_workbook(output, keep_vba=True)
    try:
        if region_id == "table_region":
            assert workbook["dynamic_table"].tables["Gate41DynamicTable"].ref == f"A1:{chr(64 + columns)}{rows + 1}"
        else:
            assert workbook["dynamic_range"].cell(rows, columns).value is not None
            if axis == "ROWS": assert workbook["dynamic_range"]["B1"].value is None
            if axis == "COLUMNS": assert workbook["dynamic_range"]["A2"].value is None
    finally:
        workbook.close(); workbook.vba_archive.close()


def significance_envelope(run):
    comparison = run.comparisons[0]
    bindings = []
    for value in run.values:
        if value.slice_id not in (comparison.left_slice_id, comparison.right_slice_id):
            continue
        bindings.append({"comparison_id": comparison.comparison_id, "family_id": comparison.family_id,
            "test_id": comparison.test_id, "test_version": comparison.test_version, "value_id": value.value_id,
            "slice_id": value.slice_id, "member_id": comparison.left_member_id if value.slice_id == comparison.left_slice_id
            else comparison.right_member_id, "direction": comparison.direction,
            "token_id": f"marker_{len(bindings)}", "display_text": "*"})
    return stable_json({"schema_version": SIGNIFICANCE, "token_set_id": "GATE41_DYNAMIC_MARKERS_V1",
        "revision": 1, "authority_ref": "GATE41_CORE_SIGNIFICANCE", "result_run_id": run.result_run_id,
        "result_fingerprint": run.result_fingerprint, "comparison_bindings": bindings,
        "legend": [{"token_id": item["token_id"], "meaning": "Canonical Core significance marker",
                    "comparison_refs": [comparison.comparison_id]} for item in bindings]})


def significance_request(path, run=None):
    run = run or core_result()
    raw = significance_envelope(run)
    ref = sha_bytes(raw)
    q = qualification(path)
    marker = DynamicField("marker", "__SIGNIFICANCE_TOKEN__", 2, "SIGNIFICANCE_TOKEN", "exact_text")
    q = replace(q, declarations=(q.declarations[0], replace(q.declarations[1],
                field_columns=(*q.declarations[1].field_columns, marker))))
    values = tuple(v for v in run.values if v.slice_id in (run.comparisons[0].left_slice_id,
                                                            run.comparisons[0].right_slice_id))
    ids = tuple(v.value_id for v in values)
    bindings = (DynamicRegionBinding("table_region", run.result_run_id, "value", ids, ("estimate",),
                    len(ids), 1, ("PROPORTION",)),
                DynamicRegionBinding("range_region", run.result_run_id, "value", ids,
                    ("estimate", "status", "marker"), len(ids), 3,
                    ("PROPORTION", "LITERAL", "SIGNIFICANCE_TOKEN"), (ref,)))
    return DynamicRenderRequest((run,), q, DYNAMIC_BINDING_SCHEMA, bindings, (raw,))


def test_dynamic_significance_visible_traceable_and_contracts(master, tmp_path):
    req = significance_request(master)
    plan = plan_dynamic_render(req, master)
    markers = [write for write in plan.writes if write.token_id]
    assert len(markers) == 2
    assert all(write.comparison_id == req.results[0].comparisons[0].comparison_id for write in markers)
    output = tmp_path / "significance.xlsm"
    render_dynamic(req, master, output, plan=plan)
    workbook = load_workbook(output, keep_vba=True)
    try:
        assert [workbook["dynamic_range"][cell].value for cell in ("C1", "C2")] == ["*", "*"]
    finally:
        workbook.close(); workbook.vba_archive.close()
    grown_evidence = render_dynamic(req, master, tmp_path / "grown.xlsm", plan=plan)
    small_bindings = tuple(replace(binding, ordered_record_ids=binding.ordered_record_ids[:1], requested_rows=1)
                           for binding in req.bindings)
    small = replace(req, bindings=small_bindings, lineage=lineage_from(plan, grown_evidence))
    render_dynamic(small, tmp_path / "grown.xlsm", tmp_path / "small.xlsm")
    workbook = load_workbook(tmp_path / "small.xlsm", keep_vba=True)
    try:
        assert workbook["dynamic_range"]["C1"].value == "*"
        assert workbook["dynamic_range"]["C2"].value is None
    finally:
        workbook.close(); workbook.vba_archive.close()


@pytest.mark.parametrize("defect,error", [
    ("missing_ref", "Unknown/unpinned"), ("checksum", "Unknown/unpinned"),
    ("comparison", "Invalid significance assertion"), ("value", "Invalid significance assertion"),
    ("slice", "Token target mismatch"), ("member", "Token target mismatch"),
    ("direction", "Contradictory token identity"), ("unused", "Unknown/unpinned"),
])
def test_dynamic_significance_fail_closed(master, defect, error):
    req = significance_request(master)
    if defect == "missing_ref":
        req = replace(req, bindings=(req.bindings[0], replace(req.bindings[1],
                      significance_presentation_refs=("0" * 64,))))
    elif defect == "unused":
        req = replace(req, bindings=tuple(replace(b, significance_presentation_refs=()) for b in req.bindings))
    else:
        envelope = json.loads(req.significance_json[0])
        if defect == "checksum":
            envelope["authority_ref"] = "CHANGED"
            req = replace(req, significance_json=(stable_json(envelope),))
        else:
            key = {"comparison": "comparison_id", "value": "value_id", "slice": "slice_id",
                   "member": "member_id", "direction": "direction"}[defect]
            envelope["comparison_bindings"][0][key] = "WRONG"
            raw = stable_json(envelope)
            req = replace(req, significance_json=(raw,), bindings=(req.bindings[0],
                replace(req.bindings[1], significance_presentation_refs=(sha_bytes(raw),))))
    with pytest.raises(RenderError, match=error):
        plan_dynamic_render(req, master)


@pytest.mark.parametrize("status", [StatisticalState.NOT_SIGNIFICANT, StatisticalState.INELIGIBLE])
def test_dynamic_significance_requires_significant_relation(master, status):
    run = core_result()
    unsigned = replace(run, comparisons=(replace(run.comparisons[0], status=status),))
    fp = result_fingerprint(unsigned)
    run = replace(unsigned, result_fingerprint=fp, manifest=replace(unsigned.manifest, result_fingerprint=fp))
    with pytest.raises(RenderError, match="Invalid significance assertion"):
        plan_dynamic_render(significance_request(master, run), master)


def test_fixed_slot_named_and_table_backed_resolution(master):
    req = request(master)
    safe = (Slot("named_safe", "presentation", "numeric", "exact_numeric", name="Gate41ProtectedName"),
            Slot("table_safe", "presentation", "literal", "exact_text",
                 table="CertificationResults", row=0, column="value"))
    plan_dynamic_render(replace(req, qualification=replace(req.qualification, fixed_slots=safe)), master)
    collision = Slot("table_collision", "presentation", "numeric", "exact_numeric",
                     table="Gate41DynamicTable", row=0, column="estimate")
    with pytest.raises(RenderError, match="fixed-slot"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification, fixed_slots=(collision,))), master)
    with pytest.raises(RenderError, match="Ambiguous/unresolvable"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification,
            fixed_slots=(replace(collision, table="MISSING"),))), master)


@pytest.mark.parametrize("defect", ["empty_source", "multiple_source", "negative_offset",
                                     "duplicate_offset", "wrong_axis", "not_formula"])
def test_formula_policy_hardening(master, defect):
    req = request(master, rows=2, columns=3)
    policy = req.qualification.formula_policies[0]
    if defect == "empty_source": policy = replace(policy, source_formula_cells=())
    elif defect == "multiple_source": policy = replace(policy, source_formula_cells=("dynamic_table!C2", "dynamic_table!C3"))
    elif defect == "negative_offset": policy = replace(policy, target_field_offsets=(-1,))
    elif defect == "duplicate_offset": policy = replace(policy, target_field_offsets=(2, 2))
    elif defect == "wrong_axis": policy = replace(policy, propagation_axis="ROWS")
    else: policy = replace(policy, source_formula_cells=("dynamic_table!A2",))
    with pytest.raises(RenderError, match="formula|Formula"):
        plan_dynamic_render(replace(req, qualification=replace(req.qualification, formula_policies=(policy,))), master)


def test_formula_inventory_and_unplanned_mutation_readback(master, tmp_path):
    req = request(master, rows=2, columns=3)
    plan = plan_dynamic_render(req, master)
    output = tmp_path / "valid.xlsm"
    render_dynamic(req, master, output, plan=plan)
    workbook = load_workbook(output, keep_vba=True)
    try:
        workbook["dynamic_table"]["C3"] = "=1+9"
        workbook.save(tmp_path / "bad-formula.xlsm")
    finally:
        workbook.close(); workbook.vba_archive.close()
    with pytest.raises(RenderError, match="formula inventory"):
        _validate_dynamic_output(master, tmp_path / "bad-formula.xlsm", req, plan)
    workbook = load_workbook(output, keep_vba=True)
    try:
        workbook["dynamic_range"]["D6"] = "UNPLANNED"
        workbook.save(tmp_path / "bad-unplanned.xlsm")
    finally:
        workbook.close(); workbook.vba_archive.close()
    with pytest.raises(RenderError, match="Unplanned"):
        _validate_dynamic_output(master, tmp_path / "bad-unplanned.xlsm", req, plan)


def test_provenance_role_positive_and_invalid_field(master, tmp_path):
    req = request(master)
    field = DynamicField("project", "project_id", 0, "LITERAL", "exact_text")
    declaration = replace(req.qualification.declarations[1], field_columns=(field,))
    q = replace(req.qualification, declarations=(req.qualification.declarations[0], declaration))
    binding = DynamicRegionBinding("range_region", req.results[0].result_run_id, "provenance",
        (req.results[0].result_run_id,), ("project",), 1, 1, ("LITERAL",))
    provenance_req = replace(req, qualification=q, bindings=(req.bindings[0], binding))
    output = tmp_path / "provenance.xlsm"
    render_dynamic(provenance_req, master, output)
    workbook = load_workbook(output, keep_vba=True)
    try:
        assert workbook["dynamic_range"]["A1"].value == req.results[0].project_id
    finally:
        workbook.close(); workbook.vba_archive.close()
    bad_field = replace(field, source_field="invented_metadata")
    bad_q = replace(q, declarations=(q.declarations[0], replace(declaration, field_columns=(bad_field,))))
    with pytest.raises(RenderError, match="Unknown provenance field"):
        plan_dynamic_render(replace(provenance_req, qualification=bad_q), master)
