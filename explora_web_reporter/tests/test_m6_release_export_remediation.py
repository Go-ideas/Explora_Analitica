from __future__ import annotations

import pytest

from src.web_canonical.adapter import project_canonical_result
from src.web_canonical.export import (
    CanonicalExportReleaseError,
    internal_qa_export_bytes,
    official_released_export_bytes,
)
from m6_fixtures import canonical_result


def test_releasable_true_allows_official_export() -> None:
    projection = project_canonical_result(canonical_result(releasable=True))
    data = official_released_export_bytes(projection).decode("utf-8")
    assert "OFFICIAL_RELEASED_EXPORT" in data
    assert "value_total" in data
    assert "base_total" in data


def test_releasable_false_blocks_official_export() -> None:
    projection = project_canonical_result(canonical_result(releasable=False))
    with pytest.raises(CanonicalExportReleaseError):
        official_released_export_bytes(projection)


def test_releasable_false_allows_explicit_internal_qa_export() -> None:
    projection = project_canonical_result(canonical_result(releasable=False))
    data = internal_qa_export_bytes(projection).decode("utf-8")
    assert "INTERNAL_QA_EXPORT" in data
    assert "REVIEW_REQUIRED" in data


def test_export_does_not_mutate_value_status_or_qa() -> None:
    projection = project_canonical_result(canonical_result(releasable=False))
    before = (
        projection.cells[0].value_status,
        projection.qa[0].state,
        projection.release["qa_release_status"],
    )
    internal_qa_export_bytes(projection)
    after = (
        projection.cells[0].value_status,
        projection.qa[0].state,
        projection.release["qa_release_status"],
    )
    assert after == before
