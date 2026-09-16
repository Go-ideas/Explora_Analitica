from __future__ import annotations

import unittest

from src.analytics_core.universe import (
    ResponseState,
    UniverseEvaluationContext,
    UniverseEvaluationStatus,
    UniverseEvaluator,
)
from src.contracts.models import (
    ReleaseMetadata,
    UniverseExpression,
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


def universe(expression: UniverseExpression) -> UniverseSpec:
    return UniverseSpec(
        spec_id="u-response",
        version="1.0.0",
        release=released(),
        expression=expression,
    )


class UniverseEvaluatorResponseStateTests(unittest.TestCase):
    def test_not_selected_requires_applicable_and_explicit_not_selected(
        self,
    ) -> None:
        spec = universe(UniverseExpression("not_selected", ("Q1", "C1")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=True,
                        answered=True,
                        explicitly_not_selected_categories=frozenset({"C1"}),
                    ),
                    "r2": ResponseState(
                        applicable=True,
                        answered=True,
                        selected_categories=frozenset({"C1"}),
                    ),
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": True, "r2": False})

    def test_not_selected_is_false_when_applicable_false(self) -> None:
        spec = universe(UniverseExpression("not_selected", ("Q1", "C1")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=False,
                        answered=None,
                    )
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": False})

    def test_not_selected_with_unknown_applicability_is_unsupported(self) -> None:
        spec = universe(UniverseExpression("not_selected", ("Q1", "C1")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=None,
                        answered=None,
                    )
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.UNSUPPORTED)
        self.assertEqual(result.respondent_mask, {"r1": False})
        self.assertIn(
            "unknown applicability for respondent/question: r1/Q1",
            result.reasons,
        )

    def test_not_answered_requires_in_scope_explicit_answer_state(self) -> None:
        spec = universe(UniverseExpression("not_answered", ("Q1",)))
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            response_states={
                "Q1": {
                    "r1": ResponseState(applicable=True, answered=False),
                    "r2": ResponseState(applicable=True, answered=True),
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": True, "r2": False})

    def test_not_answered_is_false_for_out_of_universe_respondent(self) -> None:
        spec = universe(UniverseExpression("not_answered", ("Q1",)))
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(applicable=False, answered=None),
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": False})

    def test_selected_unknown_state_is_unsupported_not_inferred(self) -> None:
        spec = universe(UniverseExpression("selected", ("Q1", "C1")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(applicable=True, answered=True),
                }
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.UNSUPPORTED)
        self.assertEqual(result.respondent_mask, {"r1": False})
        self.assertIn(
            "unknown selection state for respondent/question/category: r1/Q1/C1",
            result.reasons,
        )


if __name__ == "__main__":
    unittest.main()
