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
    spec_id: str = "u-corrective",
) -> UniverseSpec:
    return UniverseSpec(
        spec_id=spec_id,
        version="1.0.0",
        release=released(),
        expression=expression,
    )


class UniverseEvaluatorCorrectiveTests(unittest.TestCase):
    def test_incompatible_ordered_comparisons_are_structured_failures(
        self,
    ) -> None:
        for operator in ("gte", "gt", "lt", "lte"):
            with self.subTest(operator=operator):
                spec = universe(UniverseExpression(operator, ("AGE", 18)))
                context = UniverseEvaluationContext(
                    respondent_ids=("r1",),
                    field_values={"AGE": {"r1": "18"}},
                )

                result = UniverseEvaluator().evaluate(spec, context)

                self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
                self.assertEqual(result.respondent_mask, {"r1": False})
                self.assertTrue(result.qa.issues)
                self.assertTrue(
                    any(
                        "incompatible comparison operand types" in reason
                        for reason in result.reasons
                    )
                )

    def test_incompatible_equality_and_membership_do_not_return_false_silently(
        self,
    ) -> None:
        cases = (
            UniverseExpression("eq", ("AGE", 18)),
            UniverseExpression("neq", ("AGE", 18)),
            UniverseExpression("in", ("AGE", [18])),
            UniverseExpression("not_in", ("AGE", [18])),
        )
        for expression in cases:
            with self.subTest(operator=expression.operator):
                context = UniverseEvaluationContext(
                    respondent_ids=("r1",),
                    field_values={"AGE": {"r1": "18"}},
                )

                result = UniverseEvaluator().evaluate(universe(expression), context)

                self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
                self.assertEqual(result.respondent_mask, {"r1": False})
                self.assertTrue(
                    any(
                        "incompatible comparison operand types" in reason
                        for reason in result.reasons
                    )
                )

    def test_valid_typed_comparisons_continue_to_execute(self) -> None:
        cases = (
            (UniverseExpression("eq", ("SEG", "A")), {"SEG": {"r1": "A"}}, True),
            (UniverseExpression("neq", ("SEG", "B")), {"SEG": {"r1": "A"}}, True),
            (UniverseExpression("in", ("SEG", ["A", "B"])), {"SEG": {"r1": "A"}}, True),
            (
                UniverseExpression("not_in", ("SEG", ["B", "C"])),
                {"SEG": {"r1": "A"}},
                True,
            ),
            (UniverseExpression("gt", ("AGE", 17)), {"AGE": {"r1": 18}}, True),
            (UniverseExpression("gte", ("AGE", 18)), {"AGE": {"r1": 18}}, True),
            (UniverseExpression("lt", ("AGE", 19)), {"AGE": {"r1": 18}}, True),
            (UniverseExpression("lte", ("AGE", 18)), {"AGE": {"r1": 18}}, True),
        )
        for expression, field_values, expected in cases:
            with self.subTest(operator=expression.operator):
                result = UniverseEvaluator().evaluate(
                    universe(expression),
                    UniverseEvaluationContext(
                        respondent_ids=("r1",),
                        field_values=field_values,
                    ),
                )

                self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
                self.assertEqual(result.respondent_mask, {"r1": expected})

    def test_unknown_scope_is_rejected_before_explicit_binding_resolution(
        self,
    ) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry={
                "foo-u": universe(UniverseExpression("true"), spec_id="foo-u")
            },
            scope_universe_refs={"foo": UniverseRef("foo-u")},
        )

        result = UniverseEvaluator().evaluate_scope("foo", context)

        self.assertEqual(result.status, UniverseEvaluationStatus.UNSUPPORTED)
        self.assertEqual(result.respondent_mask, {"r1": False})
        self.assertIn("unsupported universe scope: foo", result.reasons)

    def test_frozen_v1_scope_vocabulary_executes_only_with_explicit_refs(
        self,
    ) -> None:
        registry = {}
        scope_refs = {}
        for scope in ("project", "question", "row/entity", "column", "cell"):
            spec_id = f"{scope}-u"
            registry[spec_id] = universe(
                UniverseExpression("true"),
                spec_id=spec_id,
            )
            scope_refs[scope] = UniverseRef(spec_id)
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            universe_registry=registry,
            scope_universe_refs=scope_refs,
        )

        for scope in ("project", "question", "row/entity", "column", "cell"):
            with self.subTest(scope=scope):
                result = UniverseEvaluator().evaluate_scope(scope, context)

                self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
                self.assertEqual(result.respondent_mask, {"r1": True})

    def test_numeric_variable_ref_is_not_silently_coerced(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            field_values={"123": {"r1": "A"}},
        )

        result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("eq", (123, "A"))),
            context,
        )

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn(
            "variable_ref must be a non-empty string reference",
            result.reasons,
        )

    def test_numeric_question_ref_is_not_silently_coerced(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "123": {"r1": ResponseState(applicable=True, answered=True)}
            },
        )

        result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("answered", (123,))),
            context,
        )

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn(
            "question_ref must be a non-empty string reference",
            result.reasons,
        )

    def test_numeric_category_ref_is_not_silently_coerced(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=True,
                        answered=True,
                        selected_categories=frozenset({"123"}),
                    )
                }
            },
        )

        result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("selected", ("Q1", 123))),
            context,
        )

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn(
            "category_ref must be a non-empty string reference",
            result.reasons,
        )

    def test_string_refs_continue_to_execute_exactly(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            field_values={"123": {"r1": "A"}},
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=True,
                        answered=True,
                        selected_categories=frozenset({"123"}),
                    )
                }
            },
        )

        field_result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("eq", ("123", "A"))),
            context,
        )
        response_result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("selected", ("Q1", "123"))),
            context,
        )

        self.assertEqual(field_result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(field_result.respondent_mask, {"r1": True})
        self.assertEqual(response_result.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(response_result.respondent_mask, {"r1": True})

    def test_full_v1_operator_runtime_semantics_are_covered(self) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1", "r2"),
            field_values={
                "SEG": {"r1": "A", "r2": "B"},
                "AGE": {"r1": 18, "r2": 17},
                "MISS": {"r1": None, "r2": "value"},
            },
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=True,
                        answered=True,
                        selected_categories=frozenset({"C1"}),
                    ),
                    "r2": ResponseState(
                        applicable=True,
                        answered=False,
                        explicitly_not_selected_categories=frozenset({"C1"}),
                    ),
                }
            },
            universe_registry={
                "all": universe(UniverseExpression("true"), spec_id="all")
            },
        )
        cases = (
            (UniverseExpression("true"), {"r1": True, "r2": True}),
            (UniverseExpression("false"), {"r1": False, "r2": False}),
            (
                UniverseExpression(
                    "and",
                    (
                        UniverseExpression("eq", ("SEG", "A")),
                        UniverseExpression("gte", ("AGE", 18)),
                    ),
                ),
                {"r1": True, "r2": False},
            ),
            (
                UniverseExpression(
                    "or",
                    (
                        UniverseExpression("eq", ("SEG", "A")),
                        UniverseExpression("eq", ("SEG", "B")),
                    ),
                ),
                {"r1": True, "r2": True},
            ),
            (
                UniverseExpression("not", (UniverseExpression("eq", ("SEG", "A")),)),
                {"r1": False, "r2": True},
            ),
            (UniverseExpression("eq", ("SEG", "A")), {"r1": True, "r2": False}),
            (UniverseExpression("neq", ("SEG", "A")), {"r1": False, "r2": True}),
            (UniverseExpression("in", ("SEG", ["A"])), {"r1": True, "r2": False}),
            (
                UniverseExpression("not_in", ("SEG", ["A"])),
                {"r1": False, "r2": True},
            ),
            (UniverseExpression("gt", ("AGE", 17)), {"r1": True, "r2": False}),
            (UniverseExpression("gte", ("AGE", 18)), {"r1": True, "r2": False}),
            (UniverseExpression("lt", ("AGE", 18)), {"r1": False, "r2": True}),
            (UniverseExpression("lte", ("AGE", 17)), {"r1": False, "r2": True}),
            (
                UniverseExpression("is_missing", ("MISS",)),
                {"r1": True, "r2": False},
            ),
            (
                UniverseExpression("not_missing", ("MISS",)),
                {"r1": False, "r2": True},
            ),
            (
                UniverseExpression("selected", ("Q1", "C1")),
                {"r1": True, "r2": False},
            ),
            (
                UniverseExpression("not_selected", ("Q1", "C1")),
                {"r1": False, "r2": True},
            ),
            (
                UniverseExpression("answered", ("Q1",)),
                {"r1": True, "r2": False},
            ),
            (
                UniverseExpression("not_answered", ("Q1",)),
                {"r1": False, "r2": True},
            ),
            (
                UniverseExpression("universe_ref", (UniverseRef("all"),)),
                {"r1": True, "r2": True},
            ),
        )

        for expression, expected in cases:
            with self.subTest(operator=expression.operator):
                result = UniverseEvaluator().evaluate(universe(expression), context)

                self.assertEqual(result.status, UniverseEvaluationStatus.PASS)
                self.assertEqual(result.respondent_mask, expected)

    def test_unknown_operator_at_evaluator_boundary_is_structured(self) -> None:
        result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("mystery", ())),
            UniverseEvaluationContext(respondent_ids=("r1",)),
        )

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertEqual(result.respondent_mask, {"r1": False})
        self.assertIn("unknown universe operator: mystery", result.reasons)

    def test_contradictory_response_state_is_local_structured_failure(
        self,
    ) -> None:
        context = UniverseEvaluationContext(
            respondent_ids=("r1",),
            response_states={
                "Q1": {
                    "r1": ResponseState(
                        applicable=True,
                        answered=True,
                        selected_categories=frozenset({"C1"}),
                        explicitly_not_selected_categories=frozenset({"C1"}),
                    )
                }
            },
        )

        result = UniverseEvaluator().evaluate(
            universe(UniverseExpression("selected", ("Q1", "C1"))),
            context,
        )

        self.assertEqual(result.status, UniverseEvaluationStatus.FAIL)
        self.assertIn(
            "contradictory selection state for respondent/question/category: "
            "r1/Q1/C1",
            result.reasons,
        )


if __name__ == "__main__":
    unittest.main()
