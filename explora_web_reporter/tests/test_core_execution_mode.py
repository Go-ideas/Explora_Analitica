from __future__ import annotations

import unittest

from src.analytics_core.mode import (
    ANALYTICS_ENGINE_ENV_VAR,
    ExecutionModeError,
    resolve_execution_mode,
)
from src.contracts.vocabulary import ExecutionMode


class CoreExecutionModeTests(unittest.TestCase):
    def test_missing_config_defaults_to_legacy(self) -> None:
        self.assertEqual(
            resolve_execution_mode(environ={}), ExecutionMode.LEGACY
        )

    def test_explicit_legacy_and_core_wrapper_are_supported(self) -> None:
        self.assertEqual(
            resolve_execution_mode("LEGACY"), ExecutionMode.LEGACY
        )
        self.assertEqual(
            resolve_execution_mode("core_wrapper"),
            ExecutionMode.CORE_WRAPPER,
        )
        self.assertEqual(
            resolve_execution_mode(environ={ANALYTICS_ENGINE_ENV_VAR: "LEGACY"}),
            ExecutionMode.LEGACY,
        )
        self.assertEqual(
            resolve_execution_mode("CANONICAL_V1"),
            ExecutionMode.CANONICAL_V1,
        )
        self.assertEqual(
            resolve_execution_mode("dual_run"),
            ExecutionMode.DUAL_RUN,
        )

    def test_invalid_mode_fails_explicitly(self) -> None:
        with self.assertRaises(ExecutionModeError):
            resolve_execution_mode("CANONICAL")
        with self.assertRaises(ExecutionModeError):
            resolve_execution_mode(environ={ANALYTICS_ENGINE_ENV_VAR: ""})


if __name__ == "__main__":
    unittest.main()
