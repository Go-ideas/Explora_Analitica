from __future__ import annotations

import unittest

from src.contracts.models import MetricSpec, ReleaseMetadata
from src.contracts.validators import (
    ContractValidationError,
    validate_metric_spec,
)
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.REVIEW,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="METRIC",
        policy_version="v1",
        source_hash="hash",
    )


def metric(**overrides: object) -> MetricSpec:
    values = {
        "spec_id": "metric-spec-1",
        "version": "1.0.0",
        "release": released(),
        "metric_id": "pct",
        "formula_id": "frequency_pct_v1",
        "question_ref": "Q1",
        "universe_ref": "u1",
        "denominator_policy": "eligible_respondents",
        "missing_behavior": "exclude_missing",
        "significance_family": "proportion",
        "significance_supported": True,
    }
    values.update(overrides)
    return MetricSpec(**values)


class MetricSchemaContractTests(unittest.TestCase):
    def test_metric_with_explicit_denominator_passes(self) -> None:
        self.assertEqual(validate_metric_spec(metric()).metric_id, "pct")
        self.assertNotIn("denominator", MetricSpec.__dataclass_fields__)

    def test_missing_denominator_policy_fails(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_metric_spec(metric(denominator_policy=""))

    def test_display_label_alone_cannot_select_formula(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_metric_spec(metric(formula_id=""))

    def test_significance_requires_denominator(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_metric_spec(
                metric(denominator_policy="NOT_APPLICABLE")
            )

    def test_derived_denominator_policy_ref_is_distinct_from_policy(self) -> None:
        spec = validate_metric_spec(
            metric(
                denominator_policy="derived_denominator",
                denominator_policy_ref="denom-policy-1",
            )
        )
        self.assertEqual(spec.denominator_policy, "derived_denominator")
        self.assertEqual(spec.denominator_policy_ref, "denom-policy-1")


if __name__ == "__main__":
    unittest.main()
