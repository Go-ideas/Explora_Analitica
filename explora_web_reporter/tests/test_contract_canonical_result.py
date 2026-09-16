from __future__ import annotations

import unittest

from src.contracts.models import CanonicalResult, QAEnvelope, QAIssue
from src.contracts.validators import (
    ContractValidationError,
    validate_canonical_result,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    QAIssueLifecycle,
    QAIssueState,
)
from src.reporter.tabulator import ReportResult


def result(**overrides: object) -> CanonicalResult:
    values = {
        "result_schema_version": "1.0.0",
        "result_run_id": "run-1",
        "project_id": "project-1",
        "dataset_fingerprint": "dataset-hash",
        "project_spec_ref": "project-spec-1",
        "core_version": "m0.1",
        "qa": QAEnvelope(
            aggregate_state=AggregateReleaseState.PASS,
            issues=(
                QAIssue(
                    issue_id="issue-1",
                    state=QAIssueState.PASS,
                    lifecycle=QAIssueLifecycle.RESOLVED,
                    layer="contract",
                    message="ok",
                ),
            ),
        ),
    }
    values.update(overrides)
    return CanonicalResult(**values)


class CanonicalResultContractTests(unittest.TestCase):
    def test_canonical_result_schema_skeleton_validates(self) -> None:
        validated = validate_canonical_result(result())
        self.assertEqual(validated.result_run_id, "run-1")

    def test_canonical_result_is_not_report_result_shaped(self) -> None:
        fields = set(CanonicalResult.__dataclass_fields__)
        self.assertNotIn("figure", fields)
        self.assertNotIn("table", fields)
        self.assertNotIn("significance_legend", fields)
        self.assertIsNot(CanonicalResult, ReportResult)
        self.assertFalse(issubclass(CanonicalResult, ReportResult))

    def test_aggregate_fail_state_fails_validation(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_canonical_result(
                result(
                    qa=QAEnvelope(
                        aggregate_state=AggregateReleaseState.FAIL
                    )
                )
            )


if __name__ == "__main__":
    unittest.main()
