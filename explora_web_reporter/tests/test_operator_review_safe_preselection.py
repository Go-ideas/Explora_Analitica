from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.operator_console.service import build_structure_review, finalize_structure_review, review_editor_state
from test_gate48_operator_console import _source_analysis_fixture_for_review


@pytest.mark.parametrize("kind", ["RU", "RM", "LOOP_RU", "LOOP_NUMERICO"])
def test_qualified_analytical_preselection(kind):
    item = {"review_state": "PENDING", "final_type": kind, "capability_status": "QUALIFIED", "authority": "HUMAN_REVIEW_REQUIRED"}
    before = deepcopy(item)
    assert review_editor_state(item) == "APPROVED"
    assert item == before


@pytest.mark.parametrize("kind", ["RESPONDENT_ID", "WEIGHT", "META_CONTROL", "UNCLASSIFIED", "GRID_ESCALA", "GRID_RM", "LOOP_RM", "NUMERIC", "SCALE", "FUTURE_TYPE"])
@pytest.mark.parametrize("capability", ["QUALIFIED", "CONFIG_ROLE", "NOT_YET_QUALIFIED", "UNRESOLVED"])
def test_other_types_never_preapprove(kind, capability):
    assert review_editor_state({"review_state": "PENDING", "final_type": kind, "capability_status": capability}) == "PENDING"


@pytest.mark.parametrize("kind", ["RU", "RM", "LOOP_RU", "LOOP_NUMERICO"])
@pytest.mark.parametrize("capability", ["NOT_YET_QUALIFIED", "UNRESOLVED", "CONFIG_ROLE"])
def test_unqualified_analytical_types_never_preapprove(kind, capability):
    assert review_editor_state({"review_state": "PENDING", "final_type": kind, "capability_status": capability}) == "PENDING"


@pytest.mark.parametrize("state", ["APPROVED", "EXCLUDED"])
@pytest.mark.parametrize("kind,capability", [("RU", "QUALIFIED"), ("GRID_RM", "NOT_YET_QUALIFIED")])
def test_existing_human_decisions_preserved(state, kind, capability):
    item = {"review_state": state, "final_type": kind, "capability_status": capability}
    assert review_editor_state(item) == state


def _analysis():
    analysis = _source_analysis_fixture_for_review()
    analysis["questionnaire"] = {"filename": None}
    for item in analysis["variables"]:
        item.update(questionnaire_exact_matches=0, authority="CANDIDATE_ONLY")
    return analysis


def _app(monkeypatch):
    import streamlit as st
    captured = []
    original = st.data_editor
    def capture(data, **kwargs):
        captured.append(data.copy(deep=True))
        return original(data, **kwargs)
    monkeypatch.setattr(st, "data_editor", capture)
    app = AppTest.from_file(str(Path("operator_console.py").resolve()), default_timeout=30)
    app.session_state["source_analysis"] = _analysis()
    return app, captured


def _click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_render_does_not_grant_authority_and_save_uses_editor_values(monkeypatch):
    app, captured = _app(monkeypatch)
    review = build_structure_review(_analysis())
    app.session_state["structure_review"] = review
    before = deepcopy(review)
    app.run()
    assert not app.exception
    assert app.session_state["structure_review"] == before
    rows = captured[-1].set_index("item_id")
    assert rows.loc["VAR::Q1", "estado"] == "APPROVED"
    assert rows.loc["GRID::G1", "estado"] == "PENDING"
    assert all(item["review_state"] == "PENDING" and item["authority"] == "HUMAN_REVIEW_REQUIRED" for item in review["items"])
    assert any("ninguna preselección constituye aprobación humana" in caption.value for caption in app.caption)
    _click(app, "Guardar revisión humana")
    saved = app.session_state["structure_review"]
    approved = next(item for item in saved["items"] if item["item_id"] == "VAR::Q1")
    assert approved["review_state"] == "APPROVED" and approved["authority"] == "HUMAN_APPROVED"
    assert review == before
    app.run()
    assert app.session_state["structure_review"] == saved


@pytest.mark.parametrize("label", ["Preparar revisión de estructuras", "Preparar revisión"])
def test_fresh_review_resets_stale_widget_edits(monkeypatch, label):
    app, captured = _app(monkeypatch)
    if label == "Preparar revisión de estructuras":
        app.session_state["structure_review"] = build_structure_review(_analysis())
    app.run()
    assert not app.exception
    app.session_state["structure_review_editor"] = {"edited_rows": {0: {"estado": "EXCLUDED", "tipo_final": "WEIGHT", "nota_humana": "stale prior review"}}, "added_rows": [], "deleted_rows": []}
    _click(app, label)
    assert app.session_state["structure_review_editor"]["edited_rows"] == {}
    assert all(item["review_state"] == "PENDING" for item in app.session_state["structure_review"]["items"])
    assert "stale prior review" not in captured[-1]["nota_humana"].tolist()
    _click(app, "Guardar revisión humana")
    assert not any(item["final_type"] == "WEIGHT" or item.get("human_note") == "stale prior review" for item in app.session_state["structure_review"]["items"])


def test_saved_exclusion_survives_render_and_save(monkeypatch):
    app, captured = _app(monkeypatch)
    review = finalize_structure_review(build_structure_review(_analysis()), [{"item_id": "VAR::Q1", "review_state": "EXCLUDED", "final_type": "RU", "human_note": "explicit exclusion"}])
    app.session_state["structure_review"] = review
    app.run()
    assert not app.exception
    assert captured[-1].set_index("item_id").loc["VAR::Q1", "estado"] == "EXCLUDED"
    assert app.session_state["structure_review"] == review
    _click(app, "Guardar revisión humana")
    item = next(item for item in app.session_state["structure_review"]["items"] if item["item_id"] == "VAR::Q1")
    assert item["review_state"] == "EXCLUDED" and item["authority"] == "HUMAN_EXCLUDED"

def test_operator_can_override_suggestions_before_save(monkeypatch):
    app, captured = _app(monkeypatch)
    review = build_structure_review(_analysis())
    app.session_state["structure_review"] = review
    app.run()
    assert not app.exception
    rows = captured[-1]
    qualified_index = rows.index[rows["item_id"] == "VAR::Q1"][0]
    control_index = rows.index[rows["item_id"] == "VAR::rotation_code"][0]
    app.session_state["structure_review_editor"] = {"edited_rows": {int(qualified_index): {"estado": "PENDING"}, int(control_index): {"tipo_final": "RU", "estado": "APPROVED"}}, "added_rows": [], "deleted_rows": []}
    _click(app, "Guardar revisión humana")
    by_id = {item["item_id"]: item for item in app.session_state["structure_review"]["items"]}
    assert by_id["VAR::Q1"]["review_state"] == "PENDING"
    assert by_id["VAR::Q1"]["authority"] == "HUMAN_REVIEW_REQUIRED"
    assert by_id["VAR::rotation_code"]["final_type"] == "RU"
    assert by_id["VAR::rotation_code"]["authority"] == "HUMAN_APPROVED"
