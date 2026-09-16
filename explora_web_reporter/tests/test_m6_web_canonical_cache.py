from __future__ import annotations

from dataclasses import replace

from src.web_canonical.cache import canonical_cache_key
from m6_fixtures import canonical_result


def test_cache_key_includes_result_run_identity() -> None:
    left = canonical_result(result_run_id="run_a")
    right = canonical_result(result_run_id="run_b")
    assert canonical_cache_key(left) != canonical_cache_key(right)


def test_cache_key_includes_request_fingerprint() -> None:
    left = canonical_result()
    request = replace(left.request, request_fingerprint="different_request")
    right = replace(left, request=request)
    assert canonical_cache_key(left) != canonical_cache_key(right)


def test_cache_key_includes_selected_slices_and_presentation() -> None:
    result = canonical_result()
    assert canonical_cache_key(
        result,
        slice_ids=("slice_total",),
        presentation_identity="table",
    ) != canonical_cache_key(
        result,
        slice_ids=("slice_banner_a",),
        presentation_identity="chart",
    )
