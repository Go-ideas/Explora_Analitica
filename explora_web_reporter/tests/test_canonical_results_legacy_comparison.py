from __future__ import annotations

from src.analytics_core.results import compare_legacy_canonical_result
from src.contracts.vocabulary import LegacyCanonicalComparisonStatus


def test_all_legacy_comparison_classifications_are_allowed() -> None:
    for classification in LegacyCanonicalComparisonStatus:
        comparison = compare_legacy_canonical_result(
            {"estimate": 1},
            {"estimate": 1},
            classification=classification,
        )

        assert comparison.classification is classification


def test_unexplained_delta_is_potential_regression_and_blocks_release() -> None:
    comparison = compare_legacy_canonical_result(
        {"estimate": 0.52},
        {"estimate": 52},
        classification=LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION,
        reason="unexplained scale mismatch",
    )

    assert comparison.blocking is True
    assert comparison.deltas == {"estimate": (0.52, 52)}


def test_presentation_only_delta_does_not_block_release() -> None:
    comparison = compare_legacy_canonical_result(
        {"label": "52%"},
        {"label": "52.0%"},
        classification=LegacyCanonicalComparisonStatus.PRESENTATION_ONLY,
    )

    assert comparison.blocking is False
    assert "label" in comparison.deltas


def test_rounding_only_is_not_a_core_classification() -> None:
    assert "ROUNDING_ONLY" not in {
        item.value for item in LegacyCanonicalComparisonStatus
    }
