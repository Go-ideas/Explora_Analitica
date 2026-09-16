from __future__ import annotations

import unittest
from dataclasses import replace

from src.contracts.models import ReleaseMetadata, WeightSpec
from src.contracts.validators import (
    ContractValidationError,
    validate_weight_override,
    validate_weight_spec,
)
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="B1",
        policy_version="v1",
        source_hash="hash",
    )


def weight(**overrides: object) -> WeightSpec:
    values = {
        "spec_id": "weight-spec-1",
        "version": "1.0.0",
        "release": released(),
        "weight_id": "weight-total",
        "variable_ref": "Pond_Total",
        "provenance": "client-supplied",
    }
    values.update(overrides)
    return WeightSpec(**values)


class WeightPolicyContractTests(unittest.TestCase):
    def test_valid_b1_weight_spec_passes(self) -> None:
        self.assertEqual(validate_weight_spec(weight()).weight_id, "weight-total")

    def test_impute_one_is_rejected_in_canonical_b1(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(missing_policy="IMPUTE_ONE"))

    def test_negative_allowed_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(negative_policy="VALID"))

    def test_normalization_or_trimming_are_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(normalization="NORMALIZE_TO_N"))
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(trimming="WINSORIZE"))

    def test_weighted_significance_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(weighted_significance=True))

    def test_missing_to_one_is_not_a_canonical_policy_value(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(weight(non_numeric_policy="FILLNA_ONE"))

    def test_multiple_project_default_weights_are_rejected(self) -> None:
        first = weight(is_project_default=True)
        second = replace(
            weight(is_project_default=True),
            spec_id="weight-spec-2",
            weight_id="weight-alt",
            variable_ref="Pond_Alt",
        )
        with self.assertRaises(ContractValidationError):
            validate_weight_spec(first, [first, second])

    def test_unknown_weight_override_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_weight_override("unknown", [weight()])

    def test_ambiguous_weight_override_is_rejected(self) -> None:
        duplicate = replace(
            weight(),
            spec_id="weight-spec-2",
            variable_ref="Pond_Duplicate",
        )
        with self.assertRaises(ContractValidationError):
            validate_weight_override("weight-total", [weight(), duplicate])

    def test_out_of_scope_weight_override_is_rejected(self) -> None:
        restricted = weight(permitted_analysis_overrides=("other-weight",))
        with self.assertRaises(ContractValidationError):
            validate_weight_override("weight-total", [restricted])


if __name__ == "__main__":
    unittest.main()
