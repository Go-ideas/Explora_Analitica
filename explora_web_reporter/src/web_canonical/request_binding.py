from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.analytics_core.result_identity import stable_json
from src.contracts.models import CanonicalResult, CanonicalSlice


NEW_CORE_EXECUTION_REQUIRED = "NEW_CORE_EXECUTION_REQUIRED"


class CanonicalRequestBindingError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = NEW_CORE_EXECUTION_REQUIRED,
        reasons: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.reasons = reasons


@dataclass(frozen=True)
class WebCanonicalRequest:
    question_ids: tuple[str, ...]
    metric_refs: tuple[str, ...] = field(default_factory=tuple)
    filters: dict[str, Any] = field(default_factory=dict)
    banner_config: dict[str, Any] = field(default_factory=dict)
    weight_override: str | None = None
    execution_options: dict[str, Any] = field(default_factory=dict)
    request_fingerprint: str | None = None
    requested_slice_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RequiredSliceDescriptor:
    is_total: bool
    filter_refs: tuple[str, ...]
    banner_dimension_id: str = ""
    member_id: str = ""
    requires_any_member: bool = False

    @property
    def label(self) -> str:
        filters = ",".join(self.filter_refs) or "no_filter"
        if self.is_total:
            return f"total[{filters}]"
        member = self.member_id if self.member_id else "*"
        return f"banner[{self.banner_dimension_id}={member};{filters}]"


def web_request_from_settings(
    question_id: str,
    settings: Mapping[str, Any] | None = None,
) -> WebCanonicalRequest:
    payload = dict(settings or {})
    return WebCanonicalRequest(
        question_ids=_tuple_text(payload.get("question_ids") or (question_id,)),
        metric_refs=_tuple_text(
            payload.get("metric_refs")
            or payload.get("canonical_metric_refs")
            or payload.get("calculations")
            or ()
        ),
        filters=dict(
            payload.get("canonical_filters")
            if payload.get("canonical_filters") is not None
            else payload.get("filters") or {}
        ),
        banner_config=dict(
            payload.get("canonical_banner_config")
            if payload.get("canonical_banner_config") is not None
            else _banner_config_from_settings(payload)
        ),
        weight_override=_optional_text(
            payload.get("weight_override")
            if payload.get("weight_override") is not None
            else payload.get("ponderador")
        ),
        execution_options=dict(
            payload.get("canonical_execution_options")
            if payload.get("canonical_execution_options") is not None
            else payload.get("execution_options") or {}
        ),
        request_fingerprint=_optional_text(payload.get("request_fingerprint")),
        requested_slice_ids=_tuple_text(
            payload.get("requested_slice_ids")
            or payload.get("selected_slice_ids")
            or ()
        ),
    )


def validate_request_binding(
    result: CanonicalResult,
    request: WebCanonicalRequest,
) -> CanonicalResult:
    canonical_request = result.request
    reasons: list[str] = []
    if canonical_request is None:
        reasons.append("canonical result has no request snapshot")
    else:
        if request.question_ids or canonical_request.question_ids:
            if _normalize(request.question_ids) != _normalize(
                canonical_request.question_ids
            ):
                reasons.append("question identity mismatch")
        if request.metric_refs or canonical_request.metric_refs:
            if _normalize(request.metric_refs) != _normalize(
                canonical_request.metric_refs
            ):
                reasons.append("metric identity mismatch")
        if not _mapping_equal(request.filters, canonical_request.filters):
            reasons.append("filter identity mismatch")
        if not _mapping_equal(
            request.banner_config, canonical_request.banner_config
        ):
            reasons.append("banner identity mismatch")
        if request.weight_override != _optional_text(
            canonical_request.weight_override
        ):
            reasons.append("weight identity mismatch")
        if not _mapping_equal(
            request.execution_options,
            canonical_request.execution_options,
        ):
            reasons.append("execution option mismatch")
        if (
            request.request_fingerprint
            and request.request_fingerprint
            != canonical_request.request_fingerprint
        ):
            reasons.append("request fingerprint mismatch")
    available_slice_ids = {item.slice_id for item in result.slices}
    derived_required = _derive_required_slice_ids(result.slices, request)
    missing_slices = sorted(
        (set(request.requested_slice_ids) | derived_required) - available_slice_ids
    )
    if missing_slices:
        reasons.append("requested slice missing: " + ", ".join(missing_slices))
    reasons.extend(_slice_coverage_reasons(result.slices, request))
    value_questions = {item.question_id for item in result.values}
    if request.question_ids and not set(request.question_ids).issubset(
        value_questions or set(request.question_ids)
    ):
        reasons.append("canonical values do not cover requested question")
    if reasons:
        raise CanonicalRequestBindingError(
            "CanonicalResult does not cover current Web request: "
            + "; ".join(reasons),
            reasons=tuple(reasons),
        )
    return result


def request_observability(
    request: WebCanonicalRequest,
    result: CanonicalResult | None = None,
) -> dict[str, Any]:
    return {
        "request_identity": stable_json(request),
        "request_fingerprint": request.request_fingerprint
        or (
            result.request.request_fingerprint
            if result is not None and result.request is not None
            else None
        ),
        "result_run_id": result.result_run_id if result is not None else None,
        "result_fingerprint": (
            result.result_fingerprint if result is not None else None
        ),
        "schema_version": (
            result.result_schema_version if result is not None else None
        ),
        "requested_slice_ids": request.requested_slice_ids,
        "derived_required_slice_ids": tuple(
            sorted(_derive_required_slice_ids(result.slices, request))
        )
        if result is not None
        else (),
        "derived_required_slice_descriptors": tuple(
            item.label for item in _required_slice_descriptors(request)
        ),
    }


def _banner_config_from_settings(payload: Mapping[str, Any]) -> dict[str, Any]:
    banner = payload.get("banner")
    if not banner:
        return {}
    return {
        "banner": _tuple_text(banner),
        "banner_mode": str(payload.get("banner_mode") or "nested"),
    }


def _derive_required_slice_ids(
    slices: tuple[CanonicalSlice, ...],
    request: WebCanonicalRequest,
) -> set[str]:
    required = {
        item.slice_id
        for descriptor in _required_slice_descriptors(request)
        for item in slices
        if _slice_matches_descriptor(item, descriptor)
    }
    return required | set(request.requested_slice_ids)


def _slice_coverage_reasons(
    slices: tuple[CanonicalSlice, ...],
    request: WebCanonicalRequest,
) -> tuple[str, ...]:
    reasons = []
    required = _required_slice_descriptors(request)
    for descriptor in required:
        if not any(_slice_matches_descriptor(item, descriptor) for item in slices):
            if descriptor.is_total:
                reasons.append(f"required total slice missing: {descriptor.label}")
            else:
                reasons.append(
                    f"required banner/filter slice missing: {descriptor.label}"
                )
    rendered = [
        item.slice_id
        for item in slices
        if _slice_participates_in_request(item, request)
        and not _slice_filter_refs_match_request(item, request)
    ]
    if rendered:
        reasons.append(
            "slice filter identity mismatch: " + ", ".join(sorted(rendered))
        )
    return tuple(reasons)


def _required_slice_descriptors(
    request: WebCanonicalRequest,
) -> tuple[RequiredSliceDescriptor, ...]:
    filters = _filter_tokens_from_request(request)
    descriptors = [RequiredSliceDescriptor(is_total=True, filter_refs=filters)]
    banner_members = _banner_member_pairs(request.banner_config)
    if banner_members:
        descriptors.extend(
            RequiredSliceDescriptor(
                is_total=False,
                banner_dimension_id=dimension,
                member_id=member,
                filter_refs=filters,
            )
            for dimension, member in banner_members
        )
        return tuple(descriptors)
    for dimension in _banner_dimensions(request.banner_config):
        descriptors.append(
            RequiredSliceDescriptor(
                is_total=False,
                banner_dimension_id=dimension,
                filter_refs=filters,
                requires_any_member=True,
            )
        )
    return tuple(descriptors)


def _slice_matches_descriptor(
    slice_item: CanonicalSlice,
    descriptor: RequiredSliceDescriptor,
) -> bool:
    if slice_item.is_total != descriptor.is_total:
        return False
    if not _slice_filter_refs_equal(slice_item.filter_refs, descriptor.filter_refs):
        return False
    if descriptor.is_total:
        return True
    if str(slice_item.banner_dimension_id or "") != descriptor.banner_dimension_id:
        return False
    if descriptor.requires_any_member:
        return bool(str(slice_item.member_id or ""))
    return str(slice_item.member_id or "") == descriptor.member_id


def _slice_participates_in_request(
    slice_item: CanonicalSlice,
    request: WebCanonicalRequest,
) -> bool:
    if slice_item.is_total:
        return True
    banner_members = _banner_member_pairs(request.banner_config)
    if banner_members:
        return (
            str(slice_item.banner_dimension_id or ""),
            str(slice_item.member_id or ""),
        ) in set(banner_members)
    return str(slice_item.banner_dimension_id or "") in set(
        _banner_dimensions(request.banner_config)
    )


def _banner_member_pairs(banner_config: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    pairs = []
    for key, value in (banner_config or {}).items():
        dimension = str(key)
        if dimension in {"banner", "banner_mode", "mode"}:
            continue
        values = _tuple_text(value)
        for member in values:
            pairs.append((dimension, member))
    return tuple(sorted(pairs))


def _banner_dimensions(banner_config: Mapping[str, Any]) -> tuple[str, ...]:
    values = []
    if not banner_config:
        return ()
    values.extend(_tuple_text(banner_config.get("banner")))
    values.extend(_tuple_text(banner_config.get("banners")))
    for key, value in banner_config.items():
        dimension = str(key)
        if dimension in {"banner", "banners", "banner_mode", "mode"}:
            continue
        if _tuple_text(value):
            values.append(dimension)
    return tuple(sorted(dict.fromkeys(values)))


def _slice_filter_refs_match_request(
    slice_item: CanonicalSlice,
    request: WebCanonicalRequest,
) -> bool:
    return _slice_filter_refs_equal(
        slice_item.filter_refs,
        _filter_tokens_from_request(request),
    )


def _slice_filter_refs_equal(
    actual: tuple[str, ...],
    expected: tuple[str, ...],
) -> bool:
    return tuple(sorted(str(item) for item in actual)) == tuple(
        sorted(str(item) for item in expected)
    )


def _filter_tokens_from_request(request: WebCanonicalRequest) -> tuple[str, ...]:
    return tuple(
        sorted(
            f"filter_{field}_{value}"
            for field, values in sorted((request.filters or {}).items())
            for value in sorted(_tuple_text(values))
        )
    )


def _mapping_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _normalize(left or {}) == _normalize(right or {})


def _tuple_text(value: Any) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item) != "")
    return (str(value),)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted(str(item) for item in value))
    return str(getattr(value, "value", value))
