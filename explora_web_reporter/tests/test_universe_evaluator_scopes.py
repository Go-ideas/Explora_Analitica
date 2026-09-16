from __future__ import annotations

import unittest

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


class UniverseEvaluatorScopeTests(unittest.TestCase):
    def test_scope_without_explicit_composition_is_not_inferred(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={
                "project": universe("project", UniverseExpression("true"))
            },
            scope_universe_refs={},
        )

        result = UniverseEvaluator().evaluate_scope("cell", context)

        self.assertEqual(result.status, UniverseEvaluationStatus.UNSUPPORTED)
        self.assertEqual(result.respondent_mask, {"r1": False})
        self.assertIn(
            "scope has no explicit universe composition: cell",
            result.reasons,
        )

    def test_scope_uses_explicit_universe_ref_only(self) -> None:
        spec = universe("question-u", UniverseExpression("eq", ("SEG", "A")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            field_values={"SEG": {"r1": "A", "r2": "B"}},
            universe_registry={"question-u": spec},
            scope_universe_refs={"question": UniverseRef("question-u")},
        )

        result = UniverseEvaluator().evaluate_scope("question", context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": True, "r2": False})

    def test_weights_do_not_alter_universe_result(self) -> None:
        spec = universe("project-u", UniverseExpression("not_missing", ("SEG",)))
        base_context = {
            "respondent_ids": ("r1", "r2"),
            "field_values": {"SEG": {"r1": "A", "r2": "B"}},
            "universe_registry": {"project-u": spec},
        }
        light_weights = UniverseEvaluationContext(
            **base_context,
            weights={"POND": {"r1": 1.0, "r2": 1.0}},
        )
        heavy_weights = UniverseEvaluationContext(
            **base_context,
            weights={"POND": {"r1": 0.0, "r2": 999.0}},
        )

        evaluator = UniverseEvaluator()
        left = evaluator.evaluate(UniverseRef("project-u"), light_weights)
        right = evaluator.evaluate(UniverseRef("project-u"), heavy_weights)

        self.assertEqual(left.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(left.respondent_mask, right.respondent_mask)
        self.assertEqual(left.eligible_n, right.eligible_n)


if __name__ == "__main__":
    unittest.main()
