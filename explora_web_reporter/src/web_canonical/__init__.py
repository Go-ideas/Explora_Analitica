from __future__ import annotations

from src.web_canonical.adapter import (
    CANONICAL_WEB_ADAPTER_VERSION,
    CanonicalWebAdapterError,
    project_canonical_result,
)
from src.web_canonical.cache import canonical_cache_key
from src.web_canonical.comparison import (
    ComparisonRecord,
    DualRunComparisonItem,
    DualRunComparisonResult,
    canonical_comparison_records_from_result,
    compare_dual_run_records,
)
from src.web_canonical.export import (
    CanonicalExportReleaseError,
    internal_qa_export_bytes,
    official_released_export_bytes,
)
from src.web_canonical.models import (
    CanonicalWebCell,
    CanonicalWebProjection,
    CanonicalWebQAItem,
)
from src.web_canonical.legacy_projection import legacy_comparison_records_from_report
from src.web_canonical.request_binding import (
    CanonicalRequestBindingError,
    NEW_CORE_EXECUTION_REQUIRED,
    validate_request_binding,
    web_request_from_settings,
)

__all__ = [
    "CANONICAL_WEB_ADAPTER_VERSION",
    "CanonicalWebAdapterError",
    "CanonicalExportReleaseError",
    "CanonicalRequestBindingError",
    "CanonicalWebCell",
    "CanonicalWebProjection",
    "CanonicalWebQAItem",
    "ComparisonRecord",
    "DualRunComparisonItem",
    "DualRunComparisonResult",
    "NEW_CORE_EXECUTION_REQUIRED",
    "canonical_cache_key",
    "canonical_comparison_records_from_result",
    "compare_dual_run_records",
    "internal_qa_export_bytes",
    "legacy_comparison_records_from_report",
    "official_released_export_bytes",
    "project_canonical_result",
    "validate_request_binding",
    "web_request_from_settings",
]
