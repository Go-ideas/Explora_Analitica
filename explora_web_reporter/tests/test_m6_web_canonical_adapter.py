from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from src.contracts.models import CanonicalValue
from src.contracts.vocabulary import (
    DenominatorUnit,
    StatisticalState,
    ValueStatus,
    ValueUnit,
)
from src.web_canonical.adapter import (
    CANONICAL_WEB_ADAPTER_VERSION,
    CanonicalWebAdapterError,
    project_canonical_result,
)
from src.web_canonical.significance import significance_presentation
from m6_fixtures import canonical_result, result_with_significance


@pytest.mark.parametrize(
    ("status", "estimate", "expected"),
    [
        (ValueStatus.OK, 0.0, "0.0%"),
        (ValueStatus.NO_VALID_BASE, None, "NO_VALID_BASE"),
        (ValueStatus.UNSUPPORTED, None, "UNSUPPORTED"),
        (ValueStatus.INELIGIBLE, None, "INELIGIBLE"),
        (ValueStatus.ERROR, None, "ERROR"),
    ],
)
def test_value_status_rendering_preserves_m5_vocabulary(
    status: ValueStatus,
    estimate: float | None,
    expected: str,
) -> None:
    result = canonical_result(status=status, estimate=estimate)
    projection = project_canonical_result(result)
    assert projection.cells[0].value_status == status.value
    assert projection.cells[0].display_value == expected


@pytest.mark.parametrize(
    ("structure_id", "unit", "denominator_unit"),
    [
        ("RU", ValueUnit.PROPORTION, DenominatorUnit.RESPONDENT),
        ("RU", ValueUnit.MEAN, DenominatorUnit.RESPONDENT),
        ("RM", ValueUnit.PROPORTION, DenominatorUnit.RESPONDENT),
        ("RM", ValueUnit.PROPORTION, DenominatorUnit.MENTION),
        ("GRID_ESCALA", ValueUnit.MEAN, DenominatorUnit.RESPONDENT),
        ("GRID_RM", ValueUnit.PROPORTION, DenominatorUnit.MENTION),
        ("LOOP_RU", ValueUnit.PROPORTION, DenominatorUnit.INSTANCE),
        ("LOOP_RM", ValueUnit.PROPORTION, DenominatorUnit.MENTION),
        ("LOOP_NUMERICO", ValueUnit.MEAN, DenominatorUnit.INSTANCE),
    ],
)
def test_supported_m6_shapes_preserve_base_identity(
    structure_id: str,
    unit: ValueUnit,
    denominator_unit: DenominatorUnit,
) -> None:
    projection = project_canonical_result(
        canonical_result(
            structure_id=structure_id,
            unit=unit,
            denominator_unit=denominator_unit,
        )
    )
    cell = projection.cells[0]
    assert cell.structure_id == structure_id
    assert cell.denominator_unit == denominator_unit.value
    assert cell.base_id == "base_total"
    assert cell.value_id == "value_total"


def test_weight_fields_are_display_only_downstream() -> None:
    projection = project_canonical_result(canonical_result(weighted=True))
    cell = projection.cells[0]
    assert cell.weighted_n_raw == 12.0
    assert cell.weighted_n == 12.0
    assert cell.effective_n == 9.5
    assert cell.active_weight_ref == "weight_main"


def test_total_banner_filter_slice_identity_is_selected_not_rebuilt() -> None:
    projection = project_canonical_result(
        canonical_result(),
        selected_slice_ids=("slice_total",),
    )
    assert {cell.slice_id for cell in projection.cells} == {"slice_total"}
    assert projection.cache_key.startswith("m6-canonical-web-")


def test_unknown_slice_is_explicit_error() -> None:
    with pytest.raises(CanonicalWebAdapterError):
        project_canonical_result(
            canonical_result(),
            selected_slice_ids=("missing_slice",),
        )


def test_schema_mismatch_is_explicit_error() -> None:
    with pytest.raises(CanonicalWebAdapterError):
        project_canonical_result(canonical_result(schema_version="M4_RESULT"))


def test_fingerprint_mismatch_is_explicit_error() -> None:
    result = canonical_result()
    manifest = replace(result.manifest, result_fingerprint="different")
    with pytest.raises(CanonicalWebAdapterError):
        project_canonical_result(replace(result, manifest=manifest))


def test_missing_base_reference_is_explicit_error() -> None:
    result = canonical_result()
    bad_value = replace(result.values[0], base_id="missing_base")
    with pytest.raises(CanonicalWebAdapterError):
        project_canonical_result(replace(result, values=(bad_value,)))


def test_adapter_does_not_accept_or_read_raw_data() -> None:
    signature = inspect.signature(project_canonical_result)
    assert "raw_data" not in signature.parameters
    source = inspect.getsource(project_canonical_result)
    assert "read_table" not in source
    assert "respuestas_long" not in source
    assert "respondentes" not in source


@pytest.mark.parametrize(
    "status",
    [
        StatisticalState.SIGNIFICANT,
        StatisticalState.NOT_SIGNIFICANT,
        StatisticalState.UNSUPPORTED,
    ],
)
def test_significance_relations_are_rendered_without_tests(
    status: StatisticalState,
) -> None:
    result = result_with_significance(status)
    presentation = significance_presentation(result.comparisons, result.slices)
    assert set(presentation.table["status"]) == {status.value}
    if status is StatisticalState.SIGNIFICANT:
        assert presentation.tokens_by_slice_id
    else:
        assert not presentation.tokens_by_slice_id


def test_no_letters_does_not_mean_not_significant() -> None:
    result = result_with_significance(StatisticalState.UNSUPPORTED)
    projection = project_canonical_result(result)
    assert projection.significance.iloc[0]["status"] == "UNSUPPORTED"
    assert projection.table.iloc[0]["Significancia"] == ""
