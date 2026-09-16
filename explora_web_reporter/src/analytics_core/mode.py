from __future__ import annotations

import os
from collections.abc import Mapping

from src.contracts.vocabulary import ExecutionMode


ANALYTICS_ENGINE_ENV_VAR = "EXPLORA_ANALYTICS_ENGINE"


class ExecutionModeError(ValueError):
    pass


def resolve_execution_mode(
    value: str | ExecutionMode | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> ExecutionMode:
    if isinstance(value, ExecutionMode):
        return value
    raw = value
    if raw is None:
        source = os.environ if environ is None else environ
        raw = source.get(ANALYTICS_ENGINE_ENV_VAR)
    if raw is None:
        return ExecutionMode.LEGACY
    normalized = str(raw).strip().upper()
    try:
        return ExecutionMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in ExecutionMode)
        raise ExecutionModeError(
            f"Invalid {ANALYTICS_ENGINE_ENV_VAR}: {raw!r}. "
            f"Allowed values: {allowed}."
        ) from exc
