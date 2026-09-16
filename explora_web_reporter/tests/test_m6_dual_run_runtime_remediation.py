from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path
import tempfile

import pandas as pd
import pytest

from src.analytics_core.runner import DualRunExecution, generate_report
from src.builder.analytic_db_builder import build_analytic_database
from src.contracts.vocabulary import LegacyCanonicalComparisonStatus, ValueUnit
from src.web_canonical.comparison import legacy_semantic_key
from m6_fixtures import canonical_result


def _canonical_binding_options() -> dict:
    return {
        "canonical_metric_refs": ("metric_1",),
        "canonical_filters": {"region": ("north",)},
        "canonical_banner_config": {"segment": ("segment_a",)},
        "canonical_execution_options": {"structure_id": "RU"},
    }


def _comparison_key() -> tuple[tuple[str, str], ...]:
    return legacy_semantic_key(
        {
            "question_id": "Q1",
            "metric_id": "metric_1",
            "formula_id": "formula_1",
            "formula_version": "v1",
            "slice_identity": "slice_total",
            "banner_identity": "",
            "filter_identity": "",
            "row_id": "",
            "entity_id": "",
            "column_id": "",
            "option_id": "",
            "category_id": "",
            "loop_instance_id": "",
            "denominator_unit": "respondent",
            "denominator_scope_id": "scope_resp",
            "weight_identity": "",
            "structure_type": "RU",
            "value_unit": "PROPORTION",
            "value_status": "OK",
        }
    )


def _canonical_result_for_legacy_total(
    *,
    estimate: float,
    unit: ValueUnit = ValueUnit.PROPORTION,
    option_id: str | None = "1",
) -> object:
    result = canonical_result(estimate=estimate, unit=unit)
    total = replace(result.slices[0], filter_refs=())
    base = replace(result.bases[0], slice_id=total.slice_id)
    value = replace(
        result.values[0],
        slice_id=total.slice_id,
        base_id=base.base_id,
        option_id=option_id,
        unit=unit,
        estimate=estimate,
    )
    request = replace(
        result.request,
        filters={},
        banner_config={},
        execution_options={"structure_id": "RU"},
    )
    return replace(
        result,
        request=request,
        slices=(total,),
        bases=(base,),
        values=(value,),
    )


class Metadata:
    variable_value_labels = {}
    variable_labels = {"Q1": "Pregunta principal"}


def _ru_db(temp_dir: str, values: list[float | int], calculation: str) -> Path:
    db_path = Path(temp_dir) / "m6_dual.db"
    datamap = pd.DataFrame(
        [
            {
                "variable": "Q1",
                "pregunta_id": "Q1",
                "texto_pregunta": "Pregunta principal",
                "tipo_pregunta": (
                    "Escala" if calculation == "Media" else "RU"
                ),
                "clasificacion_analitica": "Pregunta analizable",
                "tipo_calculo": calculation,
                "usar_en_dashboard": True,
                "es_banner": False,
                "es_filtro": False,
                "es_ponderador": False,
            },
        ]
    )
    build_analytic_database(
        pd.DataFrame({"Q1": values}),
        Metadata(),
        datamap,
        {},
        db_path=db_path,
        export_revision=False,
    )
    return db_path


def _unfiltered_binding_options() -> dict:
    return {
        "canonical_metric_refs": ("metric_1",),
        "canonical_filters": {},
        "canonical_banner_config": {},
        "canonical_execution_options": {"structure_id": "RU"},
    }


def test_dual_run_runtime_ignores_side_channel_comparison_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.analytics_core.runner.LegacyAdapter.generate",
        lambda self, request: SimpleNamespace(
            m6_comparison_records={
                _comparison_key(): 0.5
            }
        ),
    )
    result = generate_report(
        Path("fake.db"),
        "Q1",
        mode="DUAL_RUN",
        canonical_result=canonical_result(),
        legacy_comparison_records={_comparison_key(): 0.5},
        canonical_comparison_records={_comparison_key(): 0.5},
        **_canonical_binding_options(),
    )
    assert isinstance(result, DualRunExecution)
    assert result.aggregate_comparison_status == "REVIEW_REQUIRED"
    assert result.comparison.items == ()
    assert result.observability["dual_run_comparison_count"] == 0


def test_dual_run_reports_legacy_identity_limitation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.analytics_core.runner.LegacyAdapter.generate",
        lambda self, request: "legacy",
    )
    result = generate_report(
        Path("fake.db"),
        "Q1",
        mode="DUAL_RUN",
        canonical_result=canonical_result(),
        **_canonical_binding_options(),
    )
    assert result.aggregate_comparison_status == "REVIEW_REQUIRED"
    assert result.limitations


def test_real_legacy_adapter_dual_run_sanitizes_m6_options() -> None:
    df_spss = pd.DataFrame({"Q1": [1, 2, 1, 2]})
    datamap = pd.DataFrame(
        [
            {
                "variable": "Q1",
                "pregunta_id": "Q1",
                "texto_pregunta": "Pregunta principal",
                "tipo_pregunta": "RU",
                "clasificacion_analitica": "Pregunta analizable",
                "tipo_calculo": "Frecuencia",
                "usar_en_dashboard": True,
                "es_banner": False,
                "es_filtro": False,
                "es_ponderador": False,
            },
        ]
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "m6_dual.db"
        build_analytic_database(
            df_spss,
            Metadata(),
            datamap,
            {},
            db_path=db_path,
            export_revision=False,
        )
        result = canonical_result()
        request = type(result.request)(
            request_id=result.request.request_id,
            request_fingerprint=result.request.request_fingerprint,
            question_ids=("Q1",),
            metric_refs=("metric_1",),
            banner_config={"segment": ("segment_a",)},
            filters={"region": ("north",)},
            execution_options={"structure_id": "RU"},
        )
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=replace(result, request=request),
            canonical_comparison_records={_comparison_key(): 0.5},
            legacy_comparison_records={_comparison_key(): 0.5},
            canonical_metric_refs=("metric_1",),
            canonical_filters={"region": ("north",)},
            canonical_banner_config={"segment": ("segment_a",)},
            canonical_execution_options={"structure_id": "RU"},
            requested_slice_ids=("slice_total",),
        )
    assert isinstance(output, DualRunExecution)
    assert output.aggregate_comparison_status == "REVIEW_REQUIRED"


def test_real_legacy_adapter_dual_run_produces_comparisons() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _ru_db(temp_dir, [1, 2, 1, 2], "Frecuencia")
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=_canonical_result_for_legacy_total(estimate=0.5),
            display_mode="%",
            **_unfiltered_binding_options(),
        )
    assert isinstance(output, DualRunExecution)
    assert output.comparison.items
    assert output.observability["dual_run_comparison_count"] > 0
    assert output.comparison.items[0].legacy_value.source == "LEGACY"
    assert output.comparison.items[0].canonical_value.source == "CANONICAL"


def test_actual_legacy_and_canonical_equal_values_classify_parity() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _ru_db(temp_dir, [1, 2, 1, 2], "Frecuencia")
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=_canonical_result_for_legacy_total(estimate=0.5),
            display_mode="%",
            **_unfiltered_binding_options(),
        )
    item = output.comparison.items[0]
    assert item.classification is LegacyCanonicalComparisonStatus.PARITY
    assert item.blocking is False
    assert output.aggregate_comparison_status == "PASS"


def test_actual_legacy_delta_is_potential_regression_and_blocks() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _ru_db(temp_dir, [999, 999, 999], "Media")
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=_canonical_result_for_legacy_total(
                estimate=0.5,
                unit=ValueUnit.MEAN,
                option_id=None,
            ),
            calculation="Media",
            **_unfiltered_binding_options(),
        )
    item = output.comparison.items[0]
    assert item.legacy_value.value == 999
    assert item.canonical_value.value == 0.5
    assert item.classification is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
    assert item.blocking is True
    assert output.potential_regression is True
    assert output.aggregate_comparison_status == "BLOCKED_POTENTIAL_REGRESSION"


def test_actual_potential_regression_rejects_false_parity_override() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _ru_db(temp_dir, [999, 999, 999], "Media")
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=_canonical_result_for_legacy_total(
                estimate=0.5,
                unit=ValueUnit.MEAN,
                option_id=None,
            ),
            calculation="Media",
            dual_run_classifications={
                tuple(): LegacyCanonicalComparisonStatus.PARITY
            },
            **_unfiltered_binding_options(),
        )
    assert (
        output.comparison.items[0].classification
        is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
    )
