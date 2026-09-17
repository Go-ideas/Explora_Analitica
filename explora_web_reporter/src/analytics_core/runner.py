from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.analytics_core.interface import AnalyticsRequest
from src.analytics_core.legacy_adapter import LegacyAdapter
from src.analytics_core.mode import resolve_execution_mode
from src.contracts.models import CanonicalResult
from src.contracts.vocabulary import (
    ExecutionMode,
    LegacyCanonicalComparisonStatus,
)
from src.web_canonical.comparison import (
    DualRunComparisonResult,
    canonical_comparison_records_from_result,
    compare_dual_run_records,
)
from src.web_canonical.legacy_projection import legacy_comparison_records_from_report
from src.web_canonical.request_binding import (
    request_observability,
    validate_request_binding,
    web_request_from_settings,
)


class CanonicalResultRequiredError(RuntimeError):
    pass


@dataclass(frozen=True)
class DualRunExecution:
    legacy_result: Any
    canonical_result: CanonicalResult
    comparison: DualRunComparisonResult
    aggregate_comparison_status: str
    potential_regression: bool
    limitations: tuple[str, ...]
    observability: dict[str, Any]


def generate_report(
    db_path: Path,
    question_id: str,
    *,
    mode: str | ExecutionMode | None = None,
    **options: Any,
) -> Any:
    selected_mode = resolve_execution_mode(mode)
    legacy_options = _legacy_options(options)
    request = AnalyticsRequest(
        db_path=db_path,
        question_id=question_id,
        options=legacy_options,
    )
    if selected_mode in {ExecutionMode.LEGACY, ExecutionMode.CORE_WRAPPER}:
        return LegacyAdapter().generate(request)
    if selected_mode is ExecutionMode.CANONICAL_V1:
        return _canonical_result_from_options(question_id, options)
    if selected_mode is ExecutionMode.DUAL_RUN:
        legacy_result = LegacyAdapter().generate(request)
        canonical_result = _canonical_result_from_options(question_id, options)
        comparison, limitations = _dual_run_comparison(
            legacy_result,
            canonical_result,
            options,
            request_identity=str(
                request_observability(
                    web_request_from_settings(question_id, options),
                    canonical_result,
                )["request_identity"]
            ),
        )
        return DualRunExecution(
            legacy_result=legacy_result,
            canonical_result=canonical_result,
            comparison=comparison,
            aggregate_comparison_status=_aggregate_comparison_status(
                comparison,
                limitations,
            ),
            potential_regression=comparison.blocks_migration,
            limitations=limitations,
            observability={
                **request_observability(
                    web_request_from_settings(question_id, options),
                    canonical_result,
                ),
                "execution_mode": ExecutionMode.DUAL_RUN.value,
                "dual_run_comparison_count": len(comparison.items),
                "potential_regression_count": sum(
                    1
                    for item in comparison.items
                    if item.classification
                    is LegacyCanonicalComparisonStatus.POTENTIAL_REGRESSION
                ),
            },
        )
    raise AssertionError(f"Unhandled execution mode: {selected_mode}")


def _canonical_result_from_options(
    question_id: str,
    options: dict[str, Any],
) -> CanonicalResult:
    candidate = options.get("canonical_result")
    if not isinstance(candidate, CanonicalResult):
        raise CanonicalResultRequiredError(
            "CANONICAL_V1 requires an explicit CanonicalResult. "
            "Legacy fallback is prohibited."
        )
    request = web_request_from_settings(question_id, options)
    return validate_request_binding(candidate, request)


def _dual_run_comparison(
    legacy_result: Any,
    canonical_result: CanonicalResult,
    options: dict[str, Any],
    *,
    request_identity: str,
) -> tuple[DualRunComparisonResult, tuple[str, ...]]:
    canonical_records = canonical_comparison_records_from_result(
        canonical_result,
        request_identity=request_identity,
    )
    legacy_records, limitations = legacy_comparison_records_from_report(
        legacy_result,
        canonical_result,
        request_identity=request_identity,
        identity_bridge=options.get("legacy_identity_bridge"),
    )
    if limitations and not legacy_records:
        canonical_records = {}
    comparison = compare_dual_run_records(
        canonical_records,
        legacy_records,
        classifications=options.get("dual_run_classifications"),
    )
    if limitations:
        comparison = DualRunComparisonResult(
            items=comparison.items,
            limitations=limitations,
        )
    return comparison, limitations


def _aggregate_comparison_status(
    comparison: DualRunComparisonResult,
    limitations: tuple[str, ...],
) -> str:
    if comparison.blocks_migration:
        return "BLOCKED_POTENTIAL_REGRESSION"
    if limitations:
        return "REVIEW_REQUIRED"
    return "PASS"


def _legacy_options(options: dict[str, Any]) -> dict[str, Any]:
    legacy = {
        key: value
        for key, value in options.items()
        if key
        not in {
            "canonical_result",
            "legacy_identity_bridge",
            "canonical_projection",
            "execution_mode",
            "dual_run_classifications",
            "legacy_comparison_records",
            "canonical_comparison_records",
            "m6_comparison_records",
            "canonical_metric_refs",
            "canonical_filters",
            "canonical_banner_config",
            "canonical_execution_options",
            "requested_slice_ids",
            "selected_slice_ids",
            "request_fingerprint",
        }
    }
    if "filters" not in legacy and "canonical_filters" in options:
        legacy["filters"] = dict(options.get("canonical_filters") or {})
    if "banner" not in legacy and "canonical_banner_config" in options:
        banner_config = dict(options.get("canonical_banner_config") or {})
        banner = banner_config.get("banner") or tuple(
            key
            for key, value in banner_config.items()
            if key not in {"banner", "banners", "banner_mode", "mode"} and value
        )
        if banner:
            legacy["banner"] = banner
        mode = banner_config.get("banner_mode") or banner_config.get("mode")
        if mode and "banner_mode" not in legacy:
            legacy["banner_mode"] = mode
    return legacy
