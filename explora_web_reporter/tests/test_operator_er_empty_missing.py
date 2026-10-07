from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from test_gate51_execution_release_draft_authoring import _inputs, _structure
import src.operator_console as console


@pytest.mark.parametrize("missing,confirmed,valid", [
    ("[]", True, True), ("[99]", True, True),
    ("", True, False), ("[", True, False), ("[]", False, False),
])
def test_rm_form_requires_explicit_json_and_confirmation(monkeypatch, missing, confirmed, valid):
    calls = []
    original = console.author_execution_release_draft
    def capture(*args, **kwargs):
        calls.append(args[3])
        return original(*args, **kwargs)
    monkeypatch.setattr(console, "author_execution_release_draft", capture)
    project, _, _ = _inputs()
    app = AppTest.from_file(str(Path("operator_console.py").resolve()), default_timeout=30)
    app.session_state["project_spec"] = project
    app.session_state["dataset_artifact"] = SimpleNamespace(original_name="source.sav", sha256="A"*64, size_bytes=0)
    app.session_state["questionnaire_artifact"] = SimpleNamespace(original_name="questionnaire.docx", sha256="B"*64, size_bytes=0)
    app.run()
    assert not app.exception
    def text(label): return next(item for item in app.text_input if item.label == label)
    missing_input = text("Ordinary missing value(s)")
    assert missing_input.value == ""
    assert missing_input.proto.placeholder == "[]"
    assert "Usa []" in missing_input.proto.help
    for label, value in (("Release Spec ID", "ER"), ("Package ID", "PKG"), ("Internal project name", "SYNTH"), ("Selected value(s)", "[1]"), ("Not-selected value(s)", "[0]"), ("Ordinary missing value(s)", missing)):
        text(label).set_value(value)
    checkbox = next(item for item in app.checkbox if item.label == "Confirmo esta decisión explícita de estados físicos RM")
    assert checkbox.value is False
    checkbox.set_value(confirmed)
    next(item for item in app.button if item.label == "Generar Execution Release Draft").click().run()
    assert not app.exception
    if valid:
        expected = [] if missing == "[]" else [99]
        assert calls == [{"RM": {"selected_values": [1], "not_selected_values": [0], "ordinary_missing_values": expected}}]
        result = app.session_state["execution_release_draft_result"]
        assert result.status == "ER_DRAFT_VALID"
        assert _structure(result.execution_release, "RM")["ordinary_missing_values"] == expected
    else:
        assert calls == []
        assert app.error
