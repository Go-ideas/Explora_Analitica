from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class AnalyticsRequest:
    db_path: Path
    question_id: str
    options: dict[str, Any] = field(default_factory=dict)


class AnalyticsCore(Protocol):
    def generate(self, request: AnalyticsRequest) -> Any:
        ...
