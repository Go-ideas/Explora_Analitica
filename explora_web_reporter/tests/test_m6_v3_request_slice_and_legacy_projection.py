from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile

import pandas as pd
import pytest

from src.analytics_core.interface import AnalyticsRequest
from src.analytics_core.legacy_adapter import LegacyAdapter
from src.analytics_core.runner import DualRunExecution, generate_report
from src.builder.analytic_db_builder import build_analytic_database
from src.contracts.vocabulary import LegacyCanonicalComparisonStatus, ValueUnit
from src.web_canonical.legacy_projection import legacy_comparison_records_from_report
from src.web_canonical.request_binding import CanonicalRequestBindingError
from m6_fixtures import canonical_result


class Metadata:
    variable_value_labels = {}
    variable_labels = {"Q1": "Pregunta principal"}


def _db(temp_dir: str, values: list[int | float], calculation: str) -> Path:
    db_path = Path(temp_dir) / "m6_v3.db"
    build_analytic_database(
        pd.DataFrame({"Q1": values}),
        Metadata(),
        pd.DataFrame(
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
                }
            ]
        ),
        {},
        db_path=db_path,
        export_revision=False,
    )
    return db_path


def _total_result(
    *,
    filters: dict | None = None,
    banner_config: dict | None = None,
    slice_filter_refs: tuple[str, ...] = (),
    with_banner_slice: bool = False,
    estimate: float = 0.5,
    unit: ValueUnit = ValueUnit.PROPORTION,
    option_id: str | None = "1",
):
    result = canonical_result(estimate=estimate, unit=unit)
    total = replace(result.slices[0], filter_refs=slice_filter_refs)
    slices = [total]
    if with_banner_slice:
        slices.append(
            replace(
                result.slices[1],
                member_id="1",
                filter_refs=slice_filter_refs,
            )
        )
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
        filters=filters or {},
        banner_config=banner_config or {},
        execution_options={"structure_id": "RU"},
    )
    return replace(
        result,
        request=request,
        slices=tuple(slices),
        bases=(base,),
        values=(value,),
    )


def _options(filters: dict | None = None, banner_config: dict | None = None) -> dict:
    return {
        "canonical_metric_refs": ("metric_1",),
        "canonical_filters": filters or {},
        "canonical_banner_config": banner_config or {},
        "canonical_execution_options": {"structure_id": "RU"},
    }


def test_runner_rejects_filtered_request_with_unfiltered_total_slice() -> None:
    with pytest.raises(CanonicalRequestBindingError):
        generate_report(
            Path("fake.db"),
            "Q1",
            mode="CANONICAL_V1",
            canonical_result=_total_result(
                filters={"region": ("north",)},
                slice_filter_refs=(),
            ),
            **_options(filters={"region": ("north",)}),
        )


def test_runner_rejects_extra_slice_filter_restriction() -> None:
    with pytest.raises(CanonicalRequestBindingError):
        generate_report(
            Path("fake.db"),
            "Q1",
            mode="CANONICAL_V1",
            canonical_result=_total_result(
                filters={"region": ("north",)},
                slice_filter_refs=("filter_region_north", "filter_age_18"),
            ),
            **_options(filters={"region": ("north",)}),
        )


def test_runner_accepts_equivalent_filter_order_without_requested_slice_ids() -> None:
    result = _total_result(
        filters={"sex": ("male",), "region": ("north",)},
        slice_filter_refs=("filter_region_north", "filter_sex_male"),
    )
    output = generate_report(
        Path("fake.db"),
        "Q1",
        mode="CANONICAL_V1",
        canonical_result=result,
        **_options(filters={"region": ("north",), "sex": ("male",)}),
    )
    assert output is result


def test_runner_rejects_real_web_banner_shape_without_banner_slice() -> None:
    banner_config = {"banner": ("segment",), "banner_mode": "nested"}
    with pytest.raises(CanonicalRequestBindingError):
        generate_report(
            Path("fake.db"),
            "Q1",
            mode="CANONICAL_V1",
            canonical_result=_total_result(banner_config=banner_config),
            canonical_metric_refs=("metric_1",),
            canonical_filters={},
            canonical_banner_config=None,
            banner=("segment",),
            banner_mode="nested",
            canonical_execution_options={"structure_id": "RU"},
        )


def test_runner_accepts_real_web_banner_shape_with_banner_slice() -> None:
    banner_config = {"banner": ("segment",), "banner_mode": "nested"}
    result = _total_result(
        banner_config=banner_config,
        with_banner_slice=True,
    )
    output = generate_report(
        Path("fake.db"),
        "Q1",
        mode="CANONICAL_V1",
        canonical_result=result,
        canonical_metric_refs=("metric_1",),
        canonical_filters={},
        canonical_banner_config=None,
        banner=("segment",),
        banner_mode="nested",
        canonical_execution_options={"structure_id": "RU"},
    )
    assert output is result


def test_real_legacy_projection_keeps_mappable_records_and_limits_gaps() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _db(temp_dir, [1, 2, 1, 2], "Frecuencia")
        legacy = LegacyAdapter().generate(
            AnalyticsRequest(db_path, "Q1", {"display_mode": "%"})
        )
    result = _total_result()
    extra_value = replace(result.values[0], value_id="value_missing", option_id="99")
    records, limitations = legacy_comparison_records_from_report(
        legacy,
        replace(result, values=(result.values[0], extra_value)),
        request_identity="request",
    )
    assert len(records) == 1
    assert limitations
    assert "99" in limitations[0]


def test_real_dual_run_side_channel_records_do_not_control_delta() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = _db(temp_dir, [999, 999, 999], "Media")
        output = generate_report(
            db_path,
            "Q1",
            mode="DUAL_RUN",
            canonical_result=_total_result(
                estimate=0.5,
                unit=ValueUnit.MEAN,
                option_id=None,
            ),
            calculation="Media",
            legacy_comparison_records={tuple(): 0.5},
            canonical_comparison_records={tuple(): 0.5},
            **_options(),
        )
    assert isinstance(output, DualRunExecution)
    assert output.comparison.items[0].legacy_value.value == 999
    assert output.comparison.items[0].canonical_value.value == 0.5
    assert (
        output.comparison.items[0].classification
        is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
    )
    assert output.potential_regression is True
