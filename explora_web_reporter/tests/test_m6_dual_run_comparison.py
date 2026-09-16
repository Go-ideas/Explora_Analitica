from __future__ import annotations

import pytest

from src.contracts.vocabulary import LegacyCanonicalComparisonStatus
from src.web_canonical.comparison import (
    compare_dual_run_records,
    legacy_semantic_key,
)


def _key() -> tuple[tuple[str, str], ...]:
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
            "option_id": "opt_1",
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


@pytest.mark.parametrize(
    "classification",
    list(LegacyCanonicalComparisonStatus),
)
def test_dual_run_uses_only_frozen_classifications(
    classification: LegacyCanonicalComparisonStatus,
) -> None:
    key = _key()
    legacy_value = (
        0.5
        if classification is LegacyCanonicalComparisonStatus.PARITY
        else 0.4
    )
    result = compare_dual_run_records(
        {key: 0.5},
        {key: legacy_value},
        classifications={key: classification},
    )
    assert result.items[0].classification is classification


def test_unexplained_delta_is_potential_regression_and_blocks() -> None:
    key = _key()
    result = compare_dual_run_records({key: 0.5}, {key: 0.4})
    assert (
        result.items[0].classification
        is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
    )
    assert result.items[0].blocking is True
    assert result.blocks_migration is True


def test_parity_does_not_block_migration() -> None:
    key = _key()
    result = compare_dual_run_records({key: 0.5}, {key: 0.5})
    assert (
        result.items[0].classification
        is LegacyCanonicalComparisonStatus.PARITY
    )
    assert result.blocks_migration is False


def test_legacy_identity_gap_is_review_condition() -> None:
    with pytest.raises(ValueError):
        legacy_semantic_key({"label": "Total"})
