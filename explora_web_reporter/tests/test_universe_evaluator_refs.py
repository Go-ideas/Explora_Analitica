from __future__ import annotations

import unittest
from dataclasses import replace

from src.analytics_core.universe import (
    UniverseEvaluationContext,
    UniverseEvaluationStatus,
    UniverseEvaluator,
)
from src.contracts.models import (
    ReleaseMetadata,
    UniverseExpression,
    UniverseRef,
    UniverseSpec,
)
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.REVIEW,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="UNIVERSE",
        policy_version="v1",
        source_hash="hash",
    )


def universe(spec_id: str, expression: UniverseExpression) -> UniverseSpec:
    return UniverseSpec(
        spec_id=spec_id,
        version="1.0.0",
        release=released(),
        expression=expression,
    )


class UniverseEvaluatorRefTests(unittest.TestCase):
    def test_unknown_universe_ref_fails(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={},
        )

        result = UniverseEvaluator().evaluate(UniverseRef("missing"), context)

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn("unknown universe_ref: missing", result.reasons)

    def test_universe_ref_must_be_released_for_runtime_authority(self) -> None:
        spec = universe("draft", UniverseExpression("true"))
        spec = replace(
            spec,
            release=replace(released(), state=ReleaseLifecycle.APPROVED),
        )
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={"draft": spec},
        )

        result = UniverseEvaluator().evaluate(UniverseRef("draft"), context)

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn("universe draft is not RELEASED: APPROVED", result.reasons)

    def test_direct_cycle_fails(self) -> None:
        spec = universe(
            "u1",
            UniverseExpression("universe_ref", (UniverseRef("u1"),)),
        )
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={"u1": spec},
        )

        result = UniverseEvaluator().evaluate(UniverseRef("u1"), context)

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertTrue(
            any("circular universe_ref detected" in reason for reason in result.reasons)
        )

    def test_indirect_cycle_fails(self) -> None:
        first = universe(
            "u1",
            UniverseExpression("universe_ref", (UniverseRef("u2"),)),
        )
        second = universe(
            "u2",
            UniverseExpression("universe_ref", (UniverseRef("u1"),)),
        )
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={"u1": first, "u2": second},
        )

        result = UniverseEvaluator().evaluate(UniverseRef("u1"), context)

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertTrue(
            any("circular universe_ref detected" in reason for reason in result.reasons)
        )

    def test_nested_universe_ref_uses_exact_registry_id(self) -> None:
        adult = universe("adult", UniverseExpression("gte", ("AGE", 18)))
        target = universe(
            "target",
            UniverseExpression(
                "and",
                (
                    UniverseExpression("universe_ref", (UniverseRef("adult"),)),
                    UniverseExpression("eq", ("SEG", "A")),
                ),
            ),
        )
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            field_values={
                "AGE": {"r1": 21, "r2": 17},
                "SEG": {"r1": "A", "r2": "A"},
            },
            universe_registry={"adult": adult, "target": target},
        )

        result = UniverseEvaluator().evaluate(UniverseRef("target"), context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": True, "r2": False})


if __name__ == "__main__":
    unittest.main()
