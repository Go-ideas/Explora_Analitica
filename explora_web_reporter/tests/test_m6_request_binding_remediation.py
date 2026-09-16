from __future__ import annotations

from dataclasses import replace

import pytest

from src.web_canonical.request_binding import (
    CanonicalRequestBindingError,
    validate_request_binding,
    web_request_from_settings,
)
from m6_fixtures import canonical_result


def _settings(**overrides):
    values = {
        "metric_refs": ("metric_1",),
        "canonical_filters": {"region": ("north",)},
        "canonical_banner_config": {"segment": ("segment_a",)},
        "weight_override": None,
        "canonical_execution_options": {"structure_id": "RU"},
        "requested_slice_ids": ("slice_total",),
    }
    values.update(overrides)
    return values


def test_same_request_binding_is_accepted() -> None:
    result = canonical_result()
    request = web_request_from_settings("Q1", _settings())
    assert validate_request_binding(result, request) is result


def test_different_question_binding_is_rejected() -> None:
    result = canonical_result()
    request = web_request_from_settings("Q_DIFFERENT", _settings())
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "question identity mismatch" in exc.value.reasons


def test_different_metric_binding_is_rejected() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(metric_refs=("metric_other",)),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "metric identity mismatch" in exc.value.reasons


def test_different_filter_binding_requires_new_execution() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_filters={"region": ("south",)}),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "filter identity mismatch" in exc.value.reasons


def test_different_banner_binding_requires_new_execution() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_banner_config={"segment": ("segment_b",)}),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "banner identity mismatch" in exc.value.reasons


def test_different_weight_binding_requires_new_execution() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(weight_override="weight_other"),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "weight identity mismatch" in exc.value.reasons


def test_requested_slice_missing_requires_new_execution() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(requested_slice_ids=("slice_missing",)),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert exc.value.code == "NEW_CORE_EXECUTION_REQUIRED"
    assert any("requested slice missing" in item for item in exc.value.reasons)


def test_request_fingerprint_binding_is_checked() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(request_fingerprint="different_fingerprint"),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "request fingerprint mismatch" in exc.value.reasons


def test_non_semantic_label_changes_do_not_break_binding() -> None:
    result = canonical_result()
    changed_slices = tuple(
        replace(item, label=f"{item.label} Display")
        for item in result.slices
    )
    request = web_request_from_settings("Q1", _settings())
    assert validate_request_binding(
        replace(result, slices=changed_slices),
        request,
    ).slices[0].label == "Total Display"


def test_filter_absence_vs_presence_is_rejected() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_filters={}),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "filter identity mismatch" in exc.value.reasons


def test_filter_presence_vs_absence_is_rejected() -> None:
    result = canonical_result()
    canonical_request = replace(result.request, filters={})
    request = web_request_from_settings("Q1", _settings())
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request),
            request,
        )
    assert "filter identity mismatch" in exc.value.reasons


def test_equivalent_filter_ordering_matches() -> None:
    result = canonical_result()
    canonical_request = replace(
        result.request,
        filters={"region": ("north", "center")},
    )
    slices = tuple(
        replace(
            item,
            filter_refs=("filter_region_center", "filter_region_north"),
        )
        if item.slice_id == "slice_total" or item.member_id == "segment_a"
        else item
        for item in result.slices
    )
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_filters={"region": ("center", "north")}),
    )
    assert validate_request_binding(
        replace(result, request=canonical_request, slices=slices),
        request,
    )


def test_banner_absence_vs_presence_is_rejected() -> None:
    result = canonical_result()
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_banner_config={}),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(result, request)
    assert "banner identity mismatch" in exc.value.reasons


def test_banner_presence_vs_absence_is_rejected() -> None:
    result = canonical_result()
    canonical_request = replace(result.request, banner_config={})
    request = web_request_from_settings("Q1", _settings())
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request),
            request,
        )
    assert "banner identity mismatch" in exc.value.reasons


def test_required_banner_slice_missing_is_derived_from_request() -> None:
    result = canonical_result()
    slices = tuple(item for item in result.slices if item.member_id != "segment_a")
    request = web_request_from_settings("Q1", _settings(requested_slice_ids=()))
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(replace(result, slices=slices), request)
    assert any(
        "required banner/filter slice missing" in item
        for item in exc.value.reasons
    )


def test_total_only_request_with_total_slice_is_accepted() -> None:
    result = canonical_result()
    canonical_request = replace(
        result.request,
        filters={},
        banner_config={},
    )
    slices = tuple(
        replace(item, filter_refs=())
        if item.slice_id == "slice_total"
        else item
        for item in result.slices
    )
    request = web_request_from_settings(
        "Q1",
        _settings(
            canonical_filters={},
            canonical_banner_config={},
            requested_slice_ids=(),
        ),
    )
    assert validate_request_binding(
        replace(result, request=canonical_request, slices=slices),
        request,
    )


def test_filtered_request_rejects_unfiltered_total_slice() -> None:
    result = canonical_result()
    canonical_request = replace(result.request, banner_config={})
    slices = (
        replace(result.slices[0], filter_refs=()),
    )
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_banner_config={}, requested_slice_ids=()),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request, slices=slices),
            request,
        )
    assert any("required total slice missing" in item for item in exc.value.reasons)


def test_filtered_request_accepts_total_with_exact_filter_identity() -> None:
    result = canonical_result()
    canonical_request = replace(result.request, banner_config={})
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_banner_config={}, requested_slice_ids=()),
    )
    assert validate_request_binding(
        replace(result, request=canonical_request, slices=(result.slices[0],)),
        request,
    )


def test_slice_with_extra_filter_is_rejected() -> None:
    result = canonical_result()
    canonical_request = replace(result.request, banner_config={})
    slices = (
        replace(
            result.slices[0],
            filter_refs=("filter_region_north", "filter_age_18"),
        ),
    )
    request = web_request_from_settings(
        "Q1",
        _settings(canonical_banner_config={}, requested_slice_ids=()),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request, slices=slices),
            request,
        )
    assert any("slice filter identity mismatch" in item for item in exc.value.reasons)


def test_slice_with_missing_filter_is_rejected() -> None:
    result = canonical_result()
    canonical_request = replace(
        result.request,
        banner_config={},
        filters={"region": ("north",), "age": ("18",)},
    )
    request = web_request_from_settings(
        "Q1",
        _settings(
            canonical_filters={"region": ("north",), "age": ("18",)},
            canonical_banner_config={},
            requested_slice_ids=(),
        ),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request, slices=(result.slices[0],)),
            request,
        )
    assert any("required total slice missing" in item for item in exc.value.reasons)


def test_actual_web_banner_shape_requires_banner_slice() -> None:
    result = canonical_result()
    canonical_request = replace(
        result.request,
        banner_config={"banner": ("segment",), "banner_mode": "nested"},
    )
    request = web_request_from_settings(
        "Q1",
        _settings(
            canonical_banner_config=None,
            banner=("segment",),
            banner_mode="nested",
            requested_slice_ids=(),
        ),
    )
    with pytest.raises(CanonicalRequestBindingError) as exc:
        validate_request_binding(
            replace(result, request=canonical_request, slices=(result.slices[0],)),
            request,
        )
    assert any(
        "required banner/filter slice missing" in item
        for item in exc.value.reasons
    )


def test_actual_web_banner_shape_accepts_available_banner_slice() -> None:
    result = canonical_result()
    canonical_request = replace(
        result.request,
        banner_config={"banner": ("segment",), "banner_mode": "nested"},
    )
    request = web_request_from_settings(
        "Q1",
        _settings(
            canonical_banner_config=None,
            banner=("segment",),
            banner_mode="nested",
            requested_slice_ids=(),
        ),
    )
    assert validate_request_binding(
        replace(
            result,
            request=canonical_request,
            slices=(result.slices[0], result.slices[1]),
        ),
        request,
    )
