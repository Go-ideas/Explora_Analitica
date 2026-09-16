from __future__ import annotations

import unittest
from dataclasses import replace

from src.contracts.models import (
    ReleaseMetadata,
    UniverseExpression,
    UniverseRef,
    UniverseSpec,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_universe_expression,
    validate_universe_spec,
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
    spec_id: str,
    expression: UniverseExpression,
) -> UniverseSpec:
    return UniverseSpec(
        spec_id=spec_id,
        version="1.0.0",
        release=released(),
        expression=expression,
    )


class UniverseSchemaContractTests(unittest.TestCase):
    def test_v1_operator_signatures_validate(self) -> None:
        expressions = [
            UniverseExpression("true"),
            UniverseExpression("false"),
            UniverseExpression(
                "and",
                (
                    UniverseExpression("eq", ("SEG", 1)),
                    UniverseExpression("not_missing", ("AGE",)),
                ),
            ),
            UniverseExpression(
                "or",
                (
                    UniverseExpression("answered", ("Q1",)),
                    UniverseExpression("selected", ("Q2", "Q2_1")),
                ),
            ),
            UniverseExpression(
                "not", (UniverseExpression("is_missing", ("AGE",)),)
            ),
            UniverseExpression("neq", ("SEG", 9)),
            UniverseExpression("in", ("SEG", [1, 2])),
            UniverseExpression("not_in", ("SEG", [8, 9])),
            UniverseExpression("gt", ("AGE", 17)),
            UniverseExpression("gte", ("AGE", 18)),
            UniverseExpression("lt", ("AGE", 65)),
            UniverseExpression("lte", ("AGE", 64)),
            UniverseExpression("not_selected", ("Q2", "Q2_2")),
            UniverseExpression("not_answered", ("Q3",)),
            UniverseExpression("universe_ref", (UniverseRef("adultos"),)),
        ]
        for expression in expressions:
            with self.subTest(operator=expression.operator):
                validate_universe_expression(
                    expression,
                    universes={
                        "adultos": universe(
                            "adultos", UniverseExpression("true")
                        )
                    },
                )

    def test_unknown_operator_and_alias_are_rejected(self) -> None:
        for operator in ("python_eval", "contains_selected"):
            with self.subTest(operator=operator):
                with self.assertRaises(ContractValidationError):
                    validate_universe_expression(
                        UniverseExpression(operator, ("Q1", "Q1_1"))
                    )

    def test_malformed_arity_and_operand_types_fail(self) -> None:
        invalid = [
            UniverseExpression("and", (UniverseExpression("true"),)),
            UniverseExpression("not", ("not-an-expression",)),
            UniverseExpression("eq", ("SEG", {"not": "scalar"})),
            UniverseExpression("in", ("SEG", [])),
            UniverseExpression("selected", ("Q1",)),
        ]
        for expression in invalid:
            with self.subTest(expression=expression):
                with self.assertRaises(ContractValidationError):
                    validate_universe_expression(expression)

    def test_universe_ref_must_be_structured(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_universe_expression(
                UniverseExpression("universe_ref", ("adultos",))
            )

    def test_unresolved_refs_fail_when_registries_are_supplied(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_universe_expression(
                UniverseExpression("eq", ("UNKNOWN", 1)),
                variables={"SEG"},
            )
        with self.assertRaises(ContractValidationError):
            validate_universe_expression(
                UniverseExpression("selected", ("Q1", "UNKNOWN")),
                questions={"Q1"},
                categories={"Q1_1"},
            )

    def test_circular_universe_ref_fails(self) -> None:
        first = universe(
            "u1", UniverseExpression("universe_ref", (UniverseRef("u2"),))
        )
        second = universe(
            "u2", UniverseExpression("universe_ref", (UniverseRef("u1"),))
        )
        with self.assertRaises(ContractValidationError):
            validate_universe_spec(first, universes={"u1": first, "u2": second})

    def test_non_released_universe_spec_fails(self) -> None:
        spec = universe("u1", UniverseExpression("true"))
        with self.assertRaises(ContractValidationError):
            validate_universe_spec(
                replace(
                    spec,
                    release=replace(
                        released(), state=ReleaseLifecycle.PROPOSED
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
