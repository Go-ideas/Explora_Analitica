from __future__ import annotations

from typing import Any

from src.analytics_core.interface import AnalyticsRequest
from src.reporter.tabulator import generate_report


class LegacyAdapter:
    engine_name = "legacy_adapter"

    def generate(self, request: AnalyticsRequest) -> Any:
        return generate_report(
            request.db_path,
            request.question_id,
            **request.options,
        )
