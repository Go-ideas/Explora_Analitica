from __future__ import annotations

import unittest

from src.contracts.models import ReleaseMetadata, SignificanceSpec
from src.contracts.validators import (
    ContractValidationError,
    validate_significance_spec,
)
from src.contracts.vocabulary import (
    ReleaseLifecycle,
    ReleaseMode,
    SampleRelationship,
)


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.REVIEW,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="B2",
        policy_version="v1",
        source_hash="hash",
    )


def significance(**overrides: object) -> SignificanceSpec:
    values = {
        "spec_id": "sig-spec-1",
        "version": "1.0.0",
        "release": released(),
        "test_id": "b2-v1",
    }
    values.update(overrides)
    return SignificanceSpec(**values)


class SignificancePolicyContractTests(unittest.TestCase):
    def test_valid_b2_significance_spec_passes(self) -> None:
        spec = validate_significance_spec(significance())
        self.assertEqual(spec.adjustment, "HOLM")
        self.assertEqual(spec.test_version, "B2_V1")
        self.assertEqual(spec.policy_version, "B2_V1")
        self.assertEqual(spec.adjustment_version, "B2_V1")
        self.assertEqual(spec.alpha, 0.05)

    def test_unsupported_confidence_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(confidence=0.97))

    def test_one_sided_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(sidedness="one_sided"))

    def test_alpha_must_match_confidence(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(alpha=0.10))

    def test_invalid_base_rule_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(
                significance(minimum_base_rule="weighted_n>=30")
            )

    def test_no_multiplicity_adjustment_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(adjustment="NONE"))

    def test_total_must_be_excluded(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(total_excluded=False))

    def test_weighted_inference_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(significance(weighted_inference=True))

    def test_missing_sample_relationship_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_significance_spec(
                significance(sample_relationship="independent")
            )

    def test_unknown_sample_relationship_is_explicit_not_guessed(self) -> None:
        spec = validate_significance_spec(
            significance(sample_relationship=SampleRelationship.UNKNOWN)
        )
        self.assertEqual(spec.sample_relationship, SampleRelationship.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
