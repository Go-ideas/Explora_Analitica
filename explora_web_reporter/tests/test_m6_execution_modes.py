from __future__ import annotations

from pathlib import Path

import pytest

from src.analytics_core.runner import (
    CanonicalResultRequiredError,
    DualRunExecution,
    generate_report,
)
from src.contracts.models import CanonicalResult
from src.contracts.vocabulary import ExecutionMode
from m6_fixtures import canonical_result


def _canonical_binding_options() -> dict:
    return {
        "canonical_metric_refs": ("metric_1",),
        "canonical_filters": {"region": ("north",)},
        "canonical_banner_config": {"segment": ("segment_a",)},
        "canonical_execution_options": {"structure_id": "RU"},
    }


def test_explicit_legacy_remains_available(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    def fake_generate(self, request):
        calls["options"] = request.options
        return "legacy"

    monkeypatch.setattr(
        "src.analytics_core.runner.LegacyAdapter.generate",
        fake_generate,
    )
    assert generate_report(Path("fake.db"), "Q1", mode="LEGACY") == "legacy"
    assert calls["options"] == {}


def test_explicit_canonical_v1_returns_canonical_result() -> None:
    result = canonical_result()
    output = generate_report(
        Path("fake.db"),
        "Q1",
        mode=ExecutionMode.CANONICAL_V1,
        canonical_result=result,
        **_canonical_binding_options(),
    )
    assert isinstance(output, CanonicalResult)
    assert output is result


def test_canonical_v1_never_silently_falls_back() -> None:
    with pytest.raises(CanonicalResultRequiredError):
        generate_report(Path("fake.db"), "Q1", mode="CANONICAL_V1")


def test_dual_run_executes_separate_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_calls = []

    def fake_generate(self, request):
        legacy_calls.append(request)
        return "legacy-result"

    monkeypatch.setattr(
        "src.analytics_core.runner.LegacyAdapter.generate",
        fake_generate,
    )
    result = generate_report(
        Path("fake.db"),
        "Q1",
        mode=ExecutionMode.DUAL_RUN,
        canonical_result=canonical_result(),
        **_canonical_binding_options(),
    )
    assert isinstance(result, DualRunExecution)
    assert result.legacy_result == "legacy-result"
    assert result.canonical_result.result_run_id == "run_m6_fixture"
    assert len(legacy_calls) == 1
    assert "canonical_result" not in legacy_calls[0].options
