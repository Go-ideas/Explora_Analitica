from dataclasses import asdict, replace
from pathlib import Path
import ast
import inspect

import pytest

from src.analytics_core.mode import ANALYTICS_ENGINE_ENV_VAR, ExecutionModeError, resolve_execution_mode
from src.analytics_core.runner import CanonicalResultRequiredError, DualRunExecution, generate_report
from src.contracts.vocabulary import ExecutionMode
from src.web_canonical.request_binding import CanonicalRequestBindingError, request_observability, web_request_from_settings
from src.web_canonical.session import analysis_session_binding
from test_m6_execution_modes import _canonical_binding_options
from test_m6_v3_request_slice_and_legacy_projection import _db, _total_result, _options
from m6_fixtures import canonical_result


@pytest.fixture(autouse=True)
def clean_runtime_environment(monkeypatch):
    monkeypatch.delenv(ANALYTICS_ENGINE_ENV_VAR, raising=False)


def test_cds_001_missing_selector():
    assert resolve_execution_mode(environ={}) is ExecutionMode.CANONICAL_V1


def test_cds_002_explicit_canonical():
    assert resolve_execution_mode("CANONICAL") is ExecutionMode.CANONICAL_V1
    assert resolve_execution_mode("canonical_v1") is ExecutionMode.CANONICAL_V1


def test_cds_003_explicit_legacy():
    assert resolve_execution_mode("LEGACY") is ExecutionMode.LEGACY


def test_cds_004_dual_run_preserves_real_comparison(tmp_path):
    db = _db(str(tmp_path), [1, 2, 1, 2], "Frecuencia")
    output = generate_report(db, "Q1", mode="DUAL_RUN", canonical_result=_total_result(), **_options())
    assert isinstance(output, DualRunExecution)
    assert output.aggregate_comparison_status == "PASS"
    assert len(output.comparison.items) == 1
    assert output.comparison.items[0].legacy_value.value == .5
    assert output.comparison.items[0].canonical_value.value == .5


def test_cds_005_invalid_selector():
    for selector in ("", "unknown", "canonical_with_fallback"):
        with pytest.raises(ExecutionModeError):
            resolve_execution_mode(selector, environ={})


def test_cds_006_canonical_failure_never_calls_legacy(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Legacy was invoked during canonical failure")
    monkeypatch.setattr("src.analytics_core.runner.LegacyAdapter.generate", forbidden)
    for selector in (None, "CANONICAL", "CANONICAL_V1"):
        with pytest.raises(CanonicalResultRequiredError):
            generate_report(Path("unused.db"), "Q1", mode=selector)
        with pytest.raises(CanonicalRequestBindingError):
            generate_report(Path("unused.db"), "different-question", mode=selector, canonical_result=canonical_result(), **_canonical_binding_options())


def test_cds_007_explicit_legacy_output(tmp_path):
    db = _db(str(tmp_path), [1, 2, 1, 2], "Frecuencia")
    result = generate_report(db, "Q1", mode="LEGACY")
    assert result.question_id == "Q1"
    assert result.base == 4
    assert list(result.summary["n"]) == [2, 2]
    assert list(result.summary["porcentaje"]) == [.5, .5]


def test_cds_008_default_equals_explicit_canonical():
    result = canonical_result()
    implicit = generate_report(Path("unused.db"), "Q1", canonical_result=result, **_canonical_binding_options())
    explicit = generate_report(Path("unused.db"), "Q1", mode="CANONICAL", canonical_result=result, **_canonical_binding_options())
    assert implicit is explicit is result


def test_cds_009_deterministic_resolution():
    inputs = (None, "CANONICAL", "CANONICAL_V1", "LEGACY", "CORE_WRAPPER", "DUAL_RUN")
    first = tuple(resolve_execution_mode(v, environ={}) for v in inputs)
    assert all(tuple(resolve_execution_mode(v, environ={}) for v in inputs) == first for _ in range(10))


def test_cds_010_existing_metadata_records_resolved_mode():
    result = canonical_result()
    request = web_request_from_settings("Q1", _canonical_binding_options())
    observability = request_observability(request, result)
    binding = analysis_session_binding(execution_mode=resolve_execution_mode(None), request_identity=observability["request_identity"], request=request, result_run_id=result.result_run_id, result_fingerprint=result.result_fingerprint)
    assert binding.execution_mode == "CANONICAL_V1"
    assert binding.result_run_id == result.result_run_id
    assert binding.result_fingerprint == result.result_fingerprint
    assert result.project_id and result.dataset_fingerprint and result.request


def test_cds_011_resolution_is_project_independent():
    assert tuple(inspect.signature(resolve_execution_mode).parameters) == ("value", "environ")
    for project in ("synthetic-one", "unrelated-project"):
        result = replace(canonical_result(), project_id=project)
        assert generate_report(Path("unused.db"), "Q1", canonical_result=result, **_canonical_binding_options()) is result


def test_cds_012_canonical_snapshot_unchanged():
    result = canonical_result()
    before = asdict(result)
    assert generate_report(Path("unused.db"), "Q1", canonical_result=result, **_canonical_binding_options()) is result
    assert asdict(result) == before
    assert tuple(mode.value for mode in ExecutionMode) == ("LEGACY", "CORE_WRAPPER", "CANONICAL_V1", "DUAL_RUN")


def test_environment_override_and_explicit_precedence(monkeypatch):
    monkeypatch.setenv(ANALYTICS_ENGINE_ENV_VAR, "LEGACY")
    assert resolve_execution_mode() is ExecutionMode.LEGACY
    assert resolve_execution_mode("CANONICAL") is ExecutionMode.CANONICAL_V1
    monkeypatch.setenv(ANALYTICS_ENGINE_ENV_VAR, "CANONICAL")
    assert resolve_execution_mode() is ExecutionMode.CANONICAL_V1
    assert resolve_execution_mode("LEGACY") is ExecutionMode.LEGACY


def test_empty_environment_remains_invalid(monkeypatch):
    monkeypatch.setenv(ANALYTICS_ENGINE_ENV_VAR, "")
    with pytest.raises(ExecutionModeError):
        generate_report(Path("unused.db"), "Q1")


def test_all_existing_explicit_modes_survive_environment_override():
    for mode in ExecutionMode:
        assert resolve_execution_mode(mode, environ={ANALYTICS_ENGINE_ENV_VAR: "invalid"}) is mode


@pytest.mark.parametrize("filename", ["page_04_reporter.py", "page_05_significance.py"])
def test_web_defaults_use_authoritative_resolver(filename):
    path = Path(__file__).resolve().parents[1] / "src" / "ui" / filename
    tree = ast.parse(path.read_text(encoding="utf-8"))
    render = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "render")
    assignment = next(n for n in ast.walk(render) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "execution_mode" for t in n.targets))
    assert isinstance(assignment.value, ast.Attribute)
    assert assignment.value.value.func.id == "resolve_execution_mode"
