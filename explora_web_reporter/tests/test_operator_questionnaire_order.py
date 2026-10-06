from copy import deepcopy
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

import pandas as pd
import pytest

from src.operator_console.questionnaire_order import questionnaire_sequence, review_editor_items
from src.operator_console.service import analyze_source_inputs
from test_operator_review_safe_preselection import _app, _analysis, _click


def _item(item_id, kind="RU"):
    return {"item_id": item_id, "variables": [item_id.split("::")[1]], "final_type": kind, "review_state": "PENDING", "authority": "HUMAN_REVIEW_REQUIRED"}


def _source(texts, variables=()):
    return {"questionnaire": {"question_sequence": questionnaire_sequence(texts)}, "variables": list(variables)}


def _ids(items):
    return [item["item_id"] for item in items]


def test_sequence_preserves_source_order_and_bounded_text():
    texts = ["Introduction 2026", "X2. First", "", "X10. " + "long " * 100, "Y.1: Next", "123 narrative", "There are 12 participants and X99 references", "ZX-7 Last"]
    sequence = questionnaire_sequence(texts)
    assert [(x["question_ref"], x["paragraph_index"]) for x in sequence] == [("X2", 1), ("X10", 3), ("Y1", 4), ("ZX7", 7)]
    assert all(len(x["source_text"]) <= 240 for x in sequence)
    assert sequence == questionnaire_sequence(texts)


def test_question_order_is_neither_alphabetical_nor_numeric():
    review = {"items": [_item("VAR::X10"), _item("VAR::X2"), _item("VAR::X1")]}
    source = _source(["X2. First", "X10. Second", "X1. Last"], [{"variable": name, "label": name} for name in ["X1", "X2", "X10"]])
    assert _ids(review_editor_items(review, source)) == ["VAR::X2", "VAR::X10", "VAR::X1"]


@pytest.mark.parametrize("family,kind", [("LOOP", "LOOP_RU"), ("RM", "RM"), ("GRID", "GRID_ESCALA")])
def test_group_uses_normalized_parent_and_earliest_stable_position(family, kind):
    source = _source(["X.7 Parent", "X7 repeated heading", "X2 Later"])
    item = _item(f"{family}::x7", kind)
    item["variables"] = ["x7_1", "x7_2"]
    ordered = review_editor_items({"items": [item]}, source)
    assert ordered[0]["questionnaire_order_key"] == 0
    assert ordered[0]["questionnaire_question_ref"] == "X7"


def test_exact_variable_match_has_priority_over_label_candidates():
    row = {"variable": "X2b", "label": "X10 unrelated label", "questionnaire_exact_positions": [{"question_ref": "X2B", "paragraph_index": 3}]}
    ordered = review_editor_items({"items": [_item("VAR::X2b")]}, _source(["X10 Early", "X2 Second"], [row]))
    assert ordered[0]["questionnaire_order_key"] == 3


def test_label_identity_can_map_but_never_changes_control_classification():
    item = _item("VAR::X2b", "META_CONTROL")
    before = deepcopy(item)
    ordered = review_editor_items({"items": [item]}, _source(["X.2 Text"], [{"variable": "X2b", "label": "X.2 Source label"}]))
    assert ordered[0]["questionnaire_order_key"] == 0
    for field in ["final_type", "review_state", "authority"]:
        assert ordered[0][field] == before[field]
    assert item == before


@pytest.mark.parametrize("row", [
    {"variable": "support", "label": "X2 and X10"},
    {"variable": "support", "questionnaire_exact_positions": [{"question_ref": "X2", "paragraph_index": 0}, {"question_ref": "X10", "paragraph_index": 1}]},
])
def test_multiple_distinct_identities_fail_safe(row):
    ordered = review_editor_items({"items": [_item("VAR::support")]}, _source(["X2 Text", "X10 Text"], [row]))
    assert ordered[0]["questionnaire_order_key"] is None
    assert ordered[0]["questionnaire_order_status"] == "UNRESOLVED"


def test_shared_position_group_first_then_detection_order():
    review = {"items": [_item("VAR::Z9b", "META_CONTROL"), _item("VAR::Z9a"), _item("RM::Z9", "RM")]}
    source = _source(["Z9 Parent"], [{"variable": x, "label": "Z9"} for x in ["Z9a", "Z9b"]])
    assert _ids(review_editor_items(review, source)) == ["RM::Z9", "VAR::Z9b", "VAR::Z9a"]


def test_unmapped_block_and_no_questionnaire_fallback_preserve_detection_order():
    review = {"items": [_item("VAR::technical_z", "RESPONDENT_ID"), _item("RM::unknown", "RM"), _item("VAR::technical_a", "WEIGHT"), _item("VAR::X2")]}
    source = _source(["X2 Question"], [{"variable": "X2", "label": "X2"}])
    assert _ids(review_editor_items(review, source)) == ["VAR::X2", "VAR::technical_z", "RM::unknown", "VAR::technical_a"]
    before = deepcopy(review)
    assert review_editor_items(review, source) == review_editor_items(review, source)
    assert review == before
    assert _ids(review_editor_items(review, {})) == _ids(review["items"])
    source["questionnaire"]["format_supported_for_text_evidence"] = False
    assert _ids(review_editor_items(review, source)) == _ids(review["items"])


def test_docx_source_analysis_evidence_and_exact_positions(tmp_path, monkeypatch):
    from src.operator_console import service
    frame = pd.DataFrame({"X2": [1, 2], "alias": [1, 2]})
    summary = {"variables": ["X2", "alias"], "n_casos": 2, "n_variables": 2, "variable_labels": {"alias": "X10 source"}}
    monkeypatch.setattr(service, "read_spss", lambda _: (frame, None, summary))
    sav = tmp_path / "synthetic.sav"; sav.write_bytes(b"synthetic")
    paragraphs = ["Title", "X2. First", "", "X10. Second"]
    docx = tmp_path / "synthetic.docx"
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + ''.join(f'<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>' for text in paragraphs) + '</w:body></w:document>'
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("word/document.xml", xml)
    result = analyze_source_inputs(sav, questionnaire_path=docx)
    assert result["questionnaire"]["question_sequence"] == questionnaire_sequence(paragraphs)
    assert result["questionnaire"]["paragraph_index_base"] == 0
    assert result["questionnaire"]["question_sequence_authority"] == "SOURCE_PRESENTATION_EVIDENCE_ONLY"
    assert result["variables"][0]["questionnaire_exact_positions"] == [{"question_ref": "X2", "paragraph_index": 1}]
    for path in [None, tmp_path / "synthetic.pdf"]:
        if path: path.write_bytes(b"synthetic")
        assert analyze_source_inputs(sav, questionnaire_path=path)["questionnaire"]["question_sequence"] == []


def test_ui_default_order_disabled_evidence_and_saved_identity(monkeypatch):
    from src.operator_console.service import build_structure_review
    app, captured = _app(monkeypatch)
    analysis = _analysis()
    analysis["questionnaire"]["question_sequence"] = questionnaire_sequence(["Q1 First", "Q2 Second", "Q3 Third", "G1 Last"])
    for row in analysis["variables"]:
        if row["variable"] == "Q1": row["questionnaire_exact_matches"] = 1
    app.session_state["source_analysis"] = analysis
    review = build_structure_review(analysis); before = deepcopy(review)
    app.session_state["structure_review"] = review
    app.run()
    assert not app.exception
    assert captured[-1]["item_id"].tolist()[:4] == ["VAR::Q1", "RM::Q2", "LOOP::Q3", "GRID::G1"]
    assert captured[-1].iloc[-1]["bloque"].startswith("Roles")
    assert app.session_state["structure_review"] == before
    _click(app, "Guardar revisión humana")
    assert _ids(app.session_state["structure_review"]["items"]) == _ids(before["items"])
    assert next(x for x in app.session_state["structure_review"]["items"] if x["item_id"] == "VAR::Q1")["authority"] == "HUMAN_APPROVED"
    source = Path("operator_console.py").read_text(encoding="utf-8")
    assert '"orden_cuestionario", "pregunta_ref", "bloque"' in source

def test_new_source_analysis_resets_editor_and_old_review(monkeypatch):
    from types import SimpleNamespace
    import src.operator_console as console
    from src.operator_console.service import build_structure_review
    fresh = _analysis()
    fresh["dataset"]["n_cases"] = 20
    monkeypatch.setattr(console, "analyze_source_inputs", lambda *args, **kwargs: fresh)
    app, _ = _app(monkeypatch)
    app.session_state["dataset_artifact"] = SimpleNamespace(stored_path=Path("synthetic.sav"), original_name="synthetic.sav", sha256="A" * 64, size_bytes=10)
    app.session_state["structure_review"] = build_structure_review(_analysis())
    app.run()
    assert not app.exception
    app.session_state["structure_review_editor"] = {"edited_rows": {0: {"estado": "EXCLUDED"}}, "added_rows": [], "deleted_rows": []}
    _click(app, "Analizar archivos cargados")
    assert app.session_state["source_analysis"]["dataset"]["n_cases"] == 20
    assert "structure_review" not in app.session_state.filtered_state
    assert "structure_review_editor" not in app.session_state.filtered_state
