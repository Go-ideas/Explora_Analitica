from dataclasses import replace
import json
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.workbook.defined_name import DefinedName
import pytest

from scripts.gate36_certification import check_interface, inspect_package
from src.analytics_core.result_identity import result_fingerprint, stable_json
from src.contracts.vocabulary import StatisticalState, ValueStatus, ValueUnit
from src.excel_renderer import RenderError, Slot, plan_render, render, validate_output
from src.excel_renderer import renderer as engine
from m7b_fixtures import (
    FIXTURE, FIXTURE_SHA, VBA_SHA, build_test_master, release, request_for,
    resign, source_result,
)


@pytest.fixture
def setup(tmp_path):
    path = tmp_path / "master.xlsm"
    master = build_test_master(path)
    return path, request_for(master)


def spec_change(request, change):
    spec = json.loads(request.visual_spec_json)
    change(spec)
    return resign(replace(request, visual_spec_json=stable_json(spec)))


def slot_change(request, **kwargs):
    slots = (replace(request.slots[0], **kwargs),)
    return resign(replace(request, slots=slots, master=replace(request.master, writable_slots=slots)))


def input_changed(request, path):
    checksum = engine.sha(path)
    return resign(replace(request, master=replace(request.master, artifact_sha256=checksum),
                          master_release=release(checksum)))


def rewrite_zip(path, part, data):
    staged = path.with_name("defect.xlsm")
    with ZipFile(path) as a, ZipFile(staged, "w") as b:
        for item in a.infolist():
            b.writestr(item, data if item.filename == part else a.read(item.filename))
    staged.replace(path)


def test_authorized_fixture_identity_and_vba():
    assert engine.sha(FIXTURE) == FIXTURE_SHA
    info = inspect_package(FIXTURE)
    assert info["vba_sha256"] == VBA_SHA
    assert info["macro_type"]
    check_interface(FIXTURE)


def test_fixture_provenance_and_no_customer_or_event_source():
    root = FIXTURE.parent
    data = json.loads((root / "generic_macro_renderer_fixture_provenance.json").read_text())
    assert data["fixture_sha256"] == FIXTURE_SHA
    assert data["vba_sha256"] == VBA_SHA
    assert not data["customer_vba_used"] and not data["customer_xlsm_source"]
    assert data["autoexec_event_source"] == "NONE DETECTED"
    source = (root / "Module1.bas").read_text().lower()
    assert "sub say_hello()" in source
    for token in ("auto_open", "workbook_open", "worksheet_", "shell", "wscript", "powershell"):
        assert token not in source


def test_plan_is_pure_and_deterministic(setup):
    path, request = setup
    before = engine.sha(path)
    a, b = plan_render(request, path), plan_render(request, path)
    assert a == b and a.plan_sha256 == b.plan_sha256
    assert engine.sha(path) == before
    assert len(a.writes) == len({(p.sheet, p.cell) for p in a.writes})
    p = next(w for w in a.writes if w.slot_id == "official_value")
    assert (p.record_role, p.record_id, p.field_name, p.value, p.number_format) == (
        "value", request.results[0].values[0].value_id, "estimate", 0.5, "0.0%")


def test_single_write_vba_and_reopen(setup, tmp_path):
    path, request = setup
    before = engine.sha(path)
    plan = plan_render(request, path)
    evidence = render(request, path, tmp_path / "out.xlsm", plan=plan)
    assert evidence["qa"] == "PASS"
    assert evidence["vba_before"] == evidence["vba_after"] == VBA_SHA
    assert engine.sha(path) == before
    assert evidence["actual_targets"] == [(p.sheet, p.cell) for p in plan.writes]
    assert evidence["undeclared_cells_preserved"]
    assert evidence["untouched_parts_exact"]
    w = load_workbook(tmp_path / "out.xlsm", keep_vba=True)
    try:
        assert w["presentation"]["B2"].value == 0.5
        assert w["presentation"]["E1"].value == "=1+1"
        assert w["presentation"]["D1"].value == "MASTER_OWNED"
        assert w["presentation"]["D3"].value == "USER_EDITABLE"
        assert w["presentation"]["G1"].value == "OK"
        chunks = []
        for row in w["canonical_payload"].iter_rows(min_row=2, values_only=True):
            if row[0] is not None:
                record = dict(zip(engine.audit_columns("canonical_payload"), [json.loads(x) for x in row]))
                chunks.append(record)
        payload = "".join(c["payload"] for c in sorted(chunks, key=lambda c: c["chunk_id"]))
        assert payload == plan.canonical_json[0]
        assert chunks[0]["checksum"] == engine.sha_bytes(payload)
        mapping = json.loads(w["cell_map"]["C2"].value)
        assert mapping["status_sidecar"]["field_name"] == "value_status"
        assert mapping["status_sidecar"]["cell"] == "G1"
        assert mapping["label_target"]["cell"] == "A2"
        assert all(c.value is None for row in w["bases"].iter_rows(min_row=3) for c in row)
    finally:
        w.close()
        w.vba_archive.close()


@pytest.mark.parametrize("prefix", ["=1+1", "+1", "-1", "@SUM(A1)", " =1", "\t=1"])
def test_multiple_writes_literal_safety(tmp_path, prefix):
    slots = (Slot("official_value", "presentation", "numeric", "exact_numeric", name="RendererSlot",
                  status_name="ValueStatusSlot"),
             Slot("question_label", "presentation", "literal", "exact_text", name="LiteralSlot",
                  status_name="TextStatusSlot"))
    path = tmp_path / "master.xlsm"
    master = build_test_master(path, slots)
    run = source_result()
    value = replace(run.values[0], question_id=prefix)
    base = replace(run.bases[0], question_id=prefix)
    run = replace(run, values=(value,), bases=(base,))
    fp = result_fingerprint(run)
    run = replace(run, result_fingerprint=fp, manifest=replace(run.manifest, result_fingerprint=fp))
    bindings = [{"result_run_id": run.result_run_id, "record_role": "value", "record_id": value.value_id,
                 "field_name": field, "slot_id": slot.slot_id} for field, slot in zip(("estimate", "question_id"), slots)]
    request = request_for(master, run, bindings, ["PROPORTION", "LITERAL"])
    render(request, path, tmp_path / "out.xlsm")
    w = load_workbook(tmp_path / "out.xlsm", keep_vba=True)
    try:
        assert w["presentation"]["F1"].value == prefix
        assert w["presentation"]["F1"].data_type == "s"
    finally:
        w.close()
        w.vba_archive.close()


def test_table_body_binding(setup, tmp_path):
    path, request = setup
    request = slot_change(request, name=None, table="CertificationResults", row=0, column="value")
    evidence = render(request, path, tmp_path / "out.xlsm")
    assert ("presentation", "B2") in evidence["actual_targets"]


@pytest.mark.parametrize("source_status", list(StatisticalState))
def test_supplied_significance_token(tmp_path, source_status):
    slot = Slot("letters", "presentation", "literal", "exact_text", name="LiteralSlot", status_name="TextStatusSlot",
                significance_token_id="supplied_token")
    path = tmp_path / "master.xlsm"
    master = build_test_master(path, (slot,))
    run = source_result()
    # Existing fixture comparison identity is copied; no test/p-value is calculated.
    from m6_fixtures import result_with_significance
    original = result_with_significance(StatisticalState.SIGNIFICANT).comparisons[0]
    comparison = replace(original, status=source_status,
                         left_slice_id=run.values[0].slice_id, left_member_id=None,
                         question_id=run.values[0].question_id, metric_id=run.values[0].metric_id)
    run = replace(run, comparisons=(comparison,))
    fp = result_fingerprint(run)
    run = replace(run, result_fingerprint=fp, manifest=replace(run.manifest, result_fingerprint=fp))
    token = {"schema_version": engine.SIGNIFICANCE, "token_set_id": "GENERIC_LETTERS", "revision": 1,
             "authority_ref": "HUMAN_REVIEWED_TEST_PRESENTATION", "result_run_id": run.result_run_id,
             "result_fingerprint": fp,
             "comparison_bindings": [{"comparison_id": comparison.comparison_id, "family_id": comparison.family_id,
                 "test_id": comparison.test_id, "test_version": comparison.test_version,
                 "value_id": run.values[0].value_id, "slice_id": run.values[0].slice_id, "member_id": None,
                 "direction": comparison.direction, "token_id": "supplied_token", "display_text": "=A"}],
             "legend": [{"token_id": "supplied_token", "meaning": "Supplied test-only annotation",
                         "comparison_refs": [comparison.comparison_id]}]}
    binding = [{"result_run_id": run.result_run_id, "record_role": "comparison", "record_id": comparison.comparison_id,
                "field_name": "status", "slot_id": "letters"}]
    request = request_for(master, run, binding, ["SIGNIFICANCE_TOKEN"], (stable_json(token),))
    if source_status != StatisticalState.SIGNIFICANT:
        with pytest.raises(RenderError, match="Invalid significance assertion"):
            plan_render(request, path)
        return
    plan = plan_render(request, path)
    assert plan.writes[0].token_id == "supplied_token"
    render(request, path, tmp_path / "out.xlsm")
    # Non-significant source cannot be relabeled by presentation configuration.
    bad_token = json.loads(stable_json(token))
    bad_token["comparison_bindings"][0]["family_id"] = "wrong_family"
    bad = request_for(master, run, binding, ["SIGNIFICANCE_TOKEN"], (stable_json(bad_token),))
    with pytest.raises(RenderError, match="Contradictory"):
        plan_render(bad, path)


@pytest.mark.parametrize("defect", ["missing_result", "missing_mapping", "unknown_mapping_version", "unknown_build",
    "missing_target", "protected_formula", "target_type", "undeclared_role", "undeclared_table",
    "unknown_column", "capacity", "missing_status", "unknown_profile", "missing_source", "unknown_field",
    "unknown_token", "unknown_visual_version", "unknown_numeric_version", "duplicate_json", "unknown_visual_field",
    "incomplete_plan", "master_version", "master_hash", "configuration_release", "master_release"])
def test_fail_closed(setup, tmp_path, defect):
    path, request = setup
    if defect == "missing_result":
        request = replace(request, results=())
    elif defect == "missing_mapping":
        request = resign(replace(request, slots=()))
    elif defect == "unknown_mapping_version":
        request = replace(request, mapping_version="UNKNOWN")
    elif defect == "unknown_build":
        request = replace(request, renderer_build="UNKNOWN")
    elif defect in ("missing_target", "protected_formula"):
        request = slot_change(request, name="Absent" if defect == "missing_target" else "FormulaSlot")
    elif defect == "target_type":
        request = slot_change(request, kind="literal")
    elif defect == "undeclared_role":
        request = slot_change(request, role_id="navigation")
    elif defect in ("undeclared_table", "unknown_column", "capacity"):
        request = slot_change(request, name=None, table="Absent" if defect == "undeclared_table" else "CertificationResults",
                              row=99 if defect == "capacity" else 0, column="absent" if defect == "unknown_column" else "value")
    elif defect == "missing_status":
        request = slot_change(request, status_name=None)
    elif defect in ("unknown_profile", "unknown_token"):
        request = spec_change(request, lambda s: s["sections"][0]["visuals"][0].update(
            display_profile_ref="UNKNOWN" if defect == "unknown_profile" else "SIGNIFICANCE_TOKEN"))
    elif defect in ("missing_source", "unknown_field"):
        request = spec_change(request, lambda s: s["sections"][0]["visuals"][0]["source_bindings"][0].update(
            {"record_id": "absent"} if defect == "missing_source" else {"field_name": "expression"}))
    elif defect in ("unknown_visual_version", "unknown_numeric_version"):
        request = spec_change(request, lambda s: s.update({"schema_version": "UNKNOWN"} if defect == "unknown_visual_version"
                                                       else {"numeric_profile_version": "UNKNOWN"}))
    elif defect == "duplicate_json":
        request = resign(replace(request, visual_spec_json='{"schema_version":"A","schema_version":"B"}'))
    elif defect == "unknown_visual_field":
        request = spec_change(request, lambda s: s.update(expression="1/2"))
    elif defect == "incomplete_plan":
        request = spec_change(request, lambda s: s["sections"][0]["visuals"].append(
            {**s["sections"][0]["visuals"][0], "visual_id": "duplicate_target"}))
    elif defect in ("master_version", "master_hash"):
        request = resign(replace(request, master=replace(request.master,
            **({"interface_version": "UNKNOWN"} if defect == "master_version" else {"artifact_sha256": "WRONG"}))))
    elif defect == "configuration_release":
        request = replace(request, configuration_release=release("WRONG"))
    elif defect == "master_release":
        request = replace(request, master_release=release("WRONG"))
    with pytest.raises(ValueError):
        render(request, path, tmp_path / "out.xlsm")
    assert not (tmp_path / "out.xlsm").exists()
    assert not list(tmp_path.glob("m7b_stage_*"))


def test_ambiguous_named_target(setup):
    path, request = setup
    w = load_workbook(path, keep_vba=True)
    w.defined_names["RendererSlot"] = DefinedName("RendererSlot", attr_text="'presentation'!$B$2,'presentation'!$F$1")
    w.save(path)
    w.close()
    w.vba_archive.close()
    request = input_changed(request, path)
    with pytest.raises(RenderError, match="Ambiguous"):
        plan_render(request, path)


@pytest.mark.parametrize("defect", ["slice", "fingerprint", "request", "release", "manifest", "qa"])
def test_canonical_identity_release_failure(setup, defect):
    path, request = setup
    run = request.results[0]
    if defect == "slice":
        run = replace(run, slices=())
    elif defect == "fingerprint":
        run = replace(run, result_fingerprint="WRONG")
    elif defect == "request":
        run = replace(run, request=replace(run.request, request_fingerprint="WRONG"))
    elif defect == "release":
        run = replace(run, release=replace(run.release, releasable=False))
    elif defect == "manifest":
        run = replace(run, manifest=None)
    elif defect == "qa":
        run = replace(run, qa_events=(replace(run.qa_events[0], blocking=True),))
    with pytest.raises(ValueError):
        plan_render(replace(request, results=(run,)), path)


@pytest.mark.parametrize("scalar", [0.0, 0.1234, -0.125, 0.125])
def test_exact_numeric_values(tmp_path, scalar):
    path = tmp_path / "master.xlsm"
    master = build_test_master(path)
    request = request_for(master, source_result(estimate=scalar))
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


def test_exact_text_explicit_mode_and_null(setup, tmp_path):
    path, request = setup
    request = slot_change(request, kind="literal", storage_mode="exact_text", name="LiteralSlot", status_name="TextStatusSlot")
    request = replace(request, results=(source_result(estimate=0.1234567890123456),))
    request = request_for(request.master, request.results[0])
    assert render(request, path, tmp_path / "text.xlsm")["qa"] == "PASS"
    null = request_for(build_test_master(tmp_path / "null_master.xlsm"), source_result(estimate=None))
    assert render(null, tmp_path / "null_master.xlsm", tmp_path / "null.xlsm")["qa"] == "PASS"


def test_unsafe_numeric_precision(setup):
    path, request = setup
    bad = request_for(request.master, source_result(estimate=0.1234567890123456))
    with pytest.raises(RenderError, match="precision"):
        plan_render(bad, path)


def test_tampered_plan_and_incomplete_provenance(setup, tmp_path):
    path, request = setup
    plan = plan_render(request, path)
    for bad in (replace(plan, writes=plan.writes[:-1]), replace(plan, provenance_json="{}")):
        with pytest.raises(RenderError, match="tampered"):
            render(request, path, tmp_path / "out.xlsm", plan=bad)
        assert not (tmp_path / "out.xlsm").exists()


@pytest.mark.parametrize("part", ["xl/vbaProject.bin", "xl/worksheets/sheet1.xml", "xl/styles.xml"])
def test_deliberate_mutation_detected(setup, tmp_path, part):
    path, request = setup
    plan = plan_render(request, path)
    out = tmp_path / "out.xlsm"
    render(request, path, out)
    with ZipFile(out) as z:
        data = z.read(part)
    if part.endswith(".bin"):
        data = data[:-1] + bytes([data[-1] ^ 1])
    elif "sheet1" in part:
        data = data.replace(b"MASTER_OWNED", b"UNDECLARED_CHANGE")
    else:
        data = data.replace(b"Calibri", b"Changed")
    rewrite_zip(out, part, data)
    with pytest.raises(RenderError):
        validate_output(path, out, plan)


def test_writer_failure_does_not_publish(setup, tmp_path, monkeypatch):
    path, request = setup
    original = engine.mutate
    def bad_writer(source, staged, plan):
        original(source, staged, plan)
        with ZipFile(staged) as z:
            data = z.read("xl/vbaProject.bin")
        rewrite_zip(staged, "xl/vbaProject.bin", data[:-1] + bytes([data[-1] ^ 1]))
    monkeypatch.setattr(engine, "mutate", bad_writer)
    with pytest.raises(RenderError, match="VBA"):
        render(request, path, tmp_path / "out.xlsm")
    assert not (tmp_path / "out.xlsm").exists()
    assert not list(tmp_path.glob("m7b_stage_*"))


def test_malformed_xlsm(setup):
    path, request = setup
    path.write_bytes(b"not an OOXML package")
    request = input_changed(request, path)
    with pytest.raises(ValueError):
        plan_render(request, path)


def test_provenance_complete_and_portable(setup, tmp_path):
    path, request = setup
    e = render(request, path, tmp_path / "out.xlsm")
    provenance = json.loads(e["plan"]["provenance_json"])
    assert provenance["mapping"] == engine.MAPPING
    assert provenance["numeric"] == engine.NUMERIC
    assert provenance["renderer"] == engine.BUILD
    assert provenance["master"]["artifact_sha256"] == engine.sha(path)
    assert provenance["configuration_snapshot"] == json.loads(request.visual_spec_json)
    assert provenance["runs"][0]["result_fingerprint"] == request.results[0].result_fingerprint
    assert provenance["runs"][0]["supersedes_result_run_id"] is None
    assert provenance["warnings"] and provenance["errors"] == []
    assert provenance["significance_letters"] == "LETTER_DISPLAY_UNSUPPORTED"
    serialized = stable_json(e)
    assert "C:/Users" not in serialized and "C:\\\\Users" not in serialized
    assert e["output_sha256"] == engine.sha(tmp_path / "out.xlsm")


def test_render_deterministic_normalized_content(setup, tmp_path):
    path, request = setup
    a, b = tmp_path / "a.xlsm", tmp_path / "b.xlsm"
    ea, eb = render(request, path, a), render(request, path, b)
    assert ea == eb
    with ZipFile(a) as za, ZipFile(b) as zb:
        assert all(za.read(n) == zb.read(n) for n in za.namelist())


def test_invariant_half_even_display():
    assert engine.invariant_display(0.1234, "PROPORTION") == "12.3%"
    assert engine.invariant_display(12.345, "SCORE") == "12.34"
    with pytest.raises(RenderError):
        engine.invariant_display(1, "UNKNOWN")


@pytest.mark.parametrize("value", ["a\x00b", "x" * 32768], ids=["invalid_xml", "overlong"])
def test_invalid_or_overlong_text(value):
    with pytest.raises(RenderError):
        engine.literal(value)


def test_customer_and_runtime_dependency_scan():
    root = Path(__file__).parents[1]
    files = list((root / "src" / "excel_renderer").glob("*.py"))
    for path in files:
        source = path.read_text().lower()
        for forbidden in ("mitsubishi", "fun_bht", "c:/users", "c:\\\\users", "win32com", "vbproject"):
            assert forbidden not in source
    assert len(list(FIXTURE.parent.glob("*.xlsm"))) == 1


@pytest.mark.parametrize("status,n", [("NONZERO_BASE", 10), ("VALID_ZERO_BASE", 0)])
def test_real_core_base_statuses(tmp_path, status, n):
    path = tmp_path / "master.xlsm"
    master = build_test_master(path)
    w = load_workbook(path, keep_vba=True)
    w["presentation"]["B2"].number_format = "0"
    w.save(path)
    w.close()
    w.vba_archive.close()
    run = source_result()
    run = replace(run, bases=(replace(run.bases[0], base_status=status, unweighted_n=n),))
    fp = result_fingerprint(run)
    run = replace(run, result_fingerprint=fp, manifest=replace(run.manifest, result_fingerprint=fp))
    master = replace(master, artifact_sha256=engine.sha(path))
    bindings = [{"result_run_id": run.result_run_id, "record_role": "base", "record_id": run.bases[0].base_id,
                 "field_name": "unweighted_n", "slot_id": "official_value"}]
    request = request_for(master, run, bindings, ["unweighted_n"])
    plan = plan_render(request, path)
    assert plan.writes[0].value == n and plan.writes[0].status == status
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


@pytest.mark.parametrize("status", [ValueStatus.NO_VALID_BASE, ValueStatus.UNSUPPORTED, ValueStatus.INELIGIBLE])
def test_nonnumeric_status_annotation(setup, tmp_path, status):
    path, request = setup
    request = request_for(request.master, source_result(status=status))
    plan = plan_render(request, path)
    assert plan.writes[0].value is None
    assert plan.writes[0].status == str(status)
    assert plan.writes[1].value == str(status)
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


@pytest.mark.parametrize("defect", ["schema", "missing_table", "ownership", "unclassified_formula", "user_overlap", "missing_physical", "format"])
def test_incompatible_master_fails_before_mutation(setup, tmp_path, defect, monkeypatch):
    path, request = setup
    w = load_workbook(path, keep_vba=True)
    if defect == "schema":
        w["bases"].tables["Generic_bases"].tableColumns[2].name = "UNKNOWN"
    elif defect == "missing_table":
        del w["bases"].tables["Generic_bases"]
    elif defect == "ownership":
        w["configuration"]["C2"] = "USER"
    elif defect == "unclassified_formula":
        w["presentation"]["F1"] = "=2+2"
    elif defect == "user_overlap":
        from openpyxl.styles import Protection
        w["presentation"]["B2"].protection = Protection(locked=False)
    elif defect == "missing_physical":
        w["presentation"]["F1"] = None
        request = slot_change(request, kind="literal", storage_mode="exact_text", name="LiteralSlot")
    else:
        w["presentation"]["B2"].number_format = "0"
    w.save(path)
    w.close()
    w.vba_archive.close()
    request = input_changed(request, path)
    if defect == "missing_physical":
        request = spec_change(request, lambda s: s["sections"][0]["visuals"][0].update(display_profile_ref="LITERAL"))
        request = spec_change(request, lambda s: s["sections"][0]["visuals"][0]["source_bindings"][0].update(field_name="question_id"))
    called = []
    monkeypatch.setattr(engine, "mutate", lambda *args: called.append(True))
    with pytest.raises(ValueError):
        render(request, path, tmp_path / "out.xlsm")
    assert not called and not (tmp_path / "out.xlsm").exists()


def test_audit_capacity_failure(setup):
    path, request = setup
    run = request.results[0]
    values = tuple(replace(run.values[0], value_id=f"distinct_{i}") for i in range(9))
    run = replace(run, values=values)
    fp = result_fingerprint(run)
    run = replace(run, result_fingerprint=fp, manifest=replace(run.manifest, result_fingerprint=fp))
    request = request_for(request.master, run)
    with pytest.raises(RenderError, match="capacity"):
        plan_render(request, path)


def test_validate_output_rejects_tampered_plan(setup, tmp_path):
    path, request = setup
    out = tmp_path / "out.xlsm"
    render(request, path, out)
    plan = plan_render(request, path)
    with pytest.raises(RenderError, match="integrity"):
        validate_output(path, out, replace(plan, writes=plan.writes[:-1]))


def test_output_destination_never_overwritten(setup, tmp_path):
    path, request = setup
    out = tmp_path / "existing.xlsm"
    out.write_bytes(b"USER_OWNED")
    with pytest.raises(RenderError, match="destination"):
        render(request, path, out)
    assert out.read_bytes() == b"USER_OWNED"


@pytest.mark.parametrize("unit,fmt,value", [(ValueUnit.COUNT, "0", 7), (ValueUnit.COUNT, "0", 7.0),
    (ValueUnit.COUNT, "0.00", 7.5), (ValueUnit.MEAN, "0.00", 12.34),
    (ValueUnit.SCORE, "0.00", 12.34), (ValueUnit.STANDARD_DEVIATION, "0.00", 1.25)])
def test_frozen_profiles_copy_without_calculation(tmp_path, unit, fmt, value):
    path = tmp_path / "master.xlsm"
    master = build_test_master(path)
    w = load_workbook(path, keep_vba=True)
    w["presentation"]["B2"].number_format = fmt
    w.save(path)
    w.close()
    w.vba_archive.close()
    master = replace(master, artifact_sha256=engine.sha(path))
    request = request_for(master, source_result(unit=unit, estimate=value), profiles=[str(unit)])
    plan = plan_render(request, path)
    assert plan.writes[0].value == value and type(plan.writes[0].value) is type(value)
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


@pytest.mark.parametrize("scalar", [5e-324, -0.0, 10**999], ids=["denormal", "negative_zero", "integer_magnitude"])
def test_nonrepresentable_excel_scalar_rejected(setup, tmp_path, scalar):
    path, request = setup
    request = request_for(request.master, source_result(estimate=scalar))
    with pytest.raises(RenderError):
        render(request, path, tmp_path / "out.xlsm")
    assert not (tmp_path / "out.xlsm").exists()


def test_precision_as_displayed_master_rejected(setup):
    path, request = setup
    w = load_workbook(path, keep_vba=True)
    w.calculation.fullPrecision = False
    w.save(path)
    w.close()
    w.vba_archive.close()
    request = input_changed(request, path)
    with pytest.raises(RenderError, match="Precision-as-displayed"):
        plan_render(request, path)


def test_optional_reference_arrays_default_empty(setup):
    path, request = setup
    spec = json.loads(request.visual_spec_json)
    spec.pop("provenance_refs")
    visual = spec["sections"][0]["visuals"][0]
    visual.pop("warning_refs")
    visual.pop("significance_presentation_refs")
    request = resign(replace(request, visual_spec_json=stable_json(spec)))
    plan = plan_render(request, path)
    assert json.loads(plan.provenance_json)["configuration_snapshot"]["provenance_refs"] == []
    assert json.loads(plan.provenance_json)["visual_spec_json"] == request.visual_spec_json


def test_supplied_label_is_literal_and_preserves_identity(setup, tmp_path):
    path, request = setup
    request = spec_change(request, lambda s: s["sections"][0]["visuals"][0].update(
        labels=[{"text": "=HYPERLINK(\"unsafe\")", "language": "es"}]))
    plan = plan_render(request, path)
    p = next(w for w in plan.writes if w.slot_id == "official_value:label")
    assert p.kind == "literal" and p.record_role == "visual_spec"
    assert p.value == '=HYPERLINK("unsafe")'
    assert json.loads(plan.provenance_json)["renderer_warnings"] == []
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


def test_absent_label_uses_technical_id_with_diagnostic(setup):
    path, request = setup
    plan = plan_render(request, path)
    p = next(w for w in plan.writes if w.slot_id == "official_value:label")
    assert p.value == request.results[0].values[0].value_id
    assert json.loads(plan.provenance_json)["renderer_warnings"][0]["code"] == "TECHNICAL_ID_LABEL"
    with pytest.raises(RenderError, match="label target"):
        plan_render(slot_change(request, label_name=None), path)


def test_registry_table_can_move_without_coordinate_inference(setup):
    path, request = setup
    w = load_workbook(path, keep_vba=True)
    sheet = w["configuration"]
    sheet.move_range("A1:G12", rows=3, cols=2)
    sheet.tables[request.master.roles[-2].table].ref = "C4:I15"
    w.defined_names["Slot_configuration"] = DefinedName("Slot_configuration", attr_text="'configuration'!$C$5")
    w.save(path)
    w.close()
    w.vba_archive.close()
    request = input_changed(request, path)
    assert plan_render(request, path).writes


def test_unclassified_target_children_fail_before_mutation(setup, tmp_path, monkeypatch):
    path, request = setup
    with ZipFile(path) as z:
        data = z.read("xl/worksheets/sheet1.xml")
    tree = engine.etree.fromstring(data)
    cell = next(c for c in tree.iter(f"{{{engine.S}}}c") if c.get("r") == "B2")
    engine.etree.SubElement(cell, f"{{{engine.S}}}extLst")
    rewrite_zip(path, "xl/worksheets/sheet1.xml", engine.etree.tostring(tree))
    request = input_changed(request, path)
    called = []
    monkeypatch.setattr(engine, "mutate", lambda *args: called.append(True))
    with pytest.raises(RenderError, match="child structure"):
        render(request, path, tmp_path / "out.xlsm")
    assert not called and not (tmp_path / "out.xlsm").exists()


@pytest.mark.parametrize("status", [ValueStatus.OK, ValueStatus.NO_VALID_BASE, ValueStatus.UNSUPPORTED])
def test_null_count_preserves_declared_integral_profile(setup, tmp_path, status):
    path, request = setup
    w = load_workbook(path, keep_vba=True)
    w["presentation"]["B2"].number_format = "0"
    w.save(path)
    w.close()
    w.vba_archive.close()
    request = input_changed(request, path)
    request = request_for(request.master, source_result(unit=ValueUnit.COUNT, estimate=None, status=status),
                          profiles=["COUNT"])
    plan = plan_render(request, path)
    assert plan.writes[0].value is None and plan.writes[0].number_format == "0"
    assert plan.writes[1].value == ("NULL" if status == ValueStatus.OK else str(status))
    assert render(request, path, tmp_path / "out.xlsm")["qa"] == "PASS"


@pytest.mark.parametrize("reference", [123, "", " "], ids=["nontext", "empty", "whitespace"])
def test_invalid_provenance_reference_fails_closed(setup, reference):
    path, request = setup
    request = spec_change(request, lambda s: s.update(provenance_refs=[reference]))
    with pytest.raises(RenderError, match="provenance reference"):
        plan_render(request, path)
