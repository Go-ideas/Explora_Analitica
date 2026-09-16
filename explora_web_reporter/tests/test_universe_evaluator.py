from __future__ import annotations

import unittest

from src.analytics_core.universe import (
    LegacyUniverseComparisonStatus,
    ResponseState,
    UniverseEvaluationContext,
    UniverseEvaluationStatus,
    UniverseEvaluator,
    compare_legacy_universe,
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


def universe(
    expression: UniverseExpression,
    spec_id: str = "u1",
) -> UniverseSpec:
    return UniverseSpec(
        spec_id=spec_id,
        version="1.0.0",
        release=released(),
        expression=expression,
    )


class UniverseEvaluatorTests(unittest.TestCase):
    def test_boolean_and_comparison_operators_evaluate(self) -> None:
        spec = universe(
            UniverseExpression(
                "and",
                (
                    UniverseExpression("eq", ("SEG", "A")),
                    UniverseExpression("gte", ("AGE", 18)),
                ),
            )
        )
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2", "r3"),
            field_values={
                "SEG": {"r1": "A", "r2": "B", "r3": "A"},
                "AGE": {"r1": 18, "r2": 21, "r3": 17},
            },
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(
            result.respondent_mask, {"r1": True, "r2": False, "r3": False}
        )
        self.assertEqual(result.input_n, 3)
        self.assertEqual(result.eligible_n, 1)
        self.assertEqual(result.excluded_n, 2)

    def test_zero_eligible_is_valid_when_spec_executes(self) -> None:
        spec = universe(UniverseExpression("false"))
        context = UniverseEvaluationContext(respondent_ids=("r1", "r2"))

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.eligible_n, 0)
        self.assertEqual(result.excluded_n, 2)
        self.assertEqual(result.reasons, ())

    def test_missing_value_differs_from_missing_field(self) -> None:
        evaluator = UniverseEvaluator()
        missing_value = universe(UniverseExpression("is_missing", ("AGE",)))
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            field_values={"AGE": {"r1": None, "r2": 21}},
        )

        result = evaluator.evaluate(missing_value, context)

        self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(result.respondent_mask, {"r1": True, "r2": False})

        missing_field = universe(UniverseExpression("is_missing", ("NOPE",)))
        result = evaluator.evaluate(missing_field, context)
        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn("unknown variable_ref: NOPE", result.reasons)

    def test_result_is_renderer_neutral_and_traceable(self) -> None:
        spec = universe(UniverseExpression("true"))
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            traceability={"dataset_fingerprint": "dataset-hash"},
        )

        result = UniverseEvaluator().evaluate(spec, context)

        self.assertEqual(result.universe_ref, UniverseRef("u1"))
        self.assertEqual(result.universe_spec_version, "1.0.0")
        self.assertEqual(result.evaluator_rules_version, "M2_UNIVERSE_V1")
        self.assertEqual(result.traceability["dataset_fingerprint"], "dataset-hash")
        self.assertNotIn("weighted_n", result.__dataclass_fields__)
        self.assertNotIn("figure", result.__dataclass_fields__)

    def test_legacy_comparison_classifies_without_forcing_match(self) -> None:
        spec = universe(UniverseExpression("eq", ("SEG", "A")))
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            field_values={"SEG": {"r1": "A", "r2": "B"}},
        )
        canonical = UniverseEvaluator().evaluate(spec, context)

        match = compare_legacy_universe(canonical, {"r1": True, "r2": False})
        unknown = compare_legacy_universe(canonical, {"r1": False, "r2": False})
        expected = compare_legacy_universe(
            canonical,
            {"r1": False, "r2": False},
            declared_difference=(
                LegacyUniverseComparisonStatus.EXPECTED_METHODOLOGICAL_CHANGE
            ),
            reason="legacy used response-presence base",
        )

        self.assertEqual(match.status, LegacyUniverseComparisonStatus.MATCH)
        self.assertEqual(
            unknown.status,
            LegacyUniverseComparisonStatus.UNKNOWN_REQUIRES_REVIEW,
        )
        self.assertEqual(
            expected.status,
            LegacyUniverseComparisonStatus.EXPECTED_METHODOLOGICAL_CHANGE,
        )
        self.assertEqual(canonical.respondent_mask, {"r1": True, "r2": False})


if __name__ == "__main__":
    unittest.main()
