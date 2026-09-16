from __future__ import annotations

import unittest

from src.contracts.vocabulary import (
    AggregateReleaseState,
    CanonicalBaseMeasure,
    ExecutionMode,
    QAIssueLifecycle,
    QAIssueState,
    ReleaseLifecycle,
    ReleaseMode,
    SampleRelationship,
    StatisticalQAState,
    StatisticalState,
)


class ContractVocabularyTests(unittest.TestCase):
    def test_shared_vocabularies_define_gate1_terms_once(self) -> None:
        self.assertEqual(
            {item.value for item in ReleaseLifecycle},
            {
                "PROPOSED",
                "REVIEW_REQUIRED",
                "APPROVED",
                "REJECTED",
                "RELEASED",
            },
        )
        self.assertEqual(
            {item.value for item in ReleaseMode},
            {"AUTO", "REVIEW", "MANUAL"},
        )
        self.assertEqual(
            {item.value for item in QAIssueState},
            {"PASS", "WARN", "FAIL"},
        )
        self.assertEqual(
            {item.value for item in QAIssueLifecycle},
            {"OPEN", "RESOLVED", "WAIVED"},
        )
        self.assertEqual(
            {item.value for item in StatisticalQAState},
            {"PASS", "WARN", "INELIGIBLE", "UNSUPPORTED", "FAIL"},
        )
        self.assertEqual(
            {item.value for item in StatisticalState},
            {
                "SIGNIFICANT",
                "NOT_SIGNIFICANT",
                "INELIGIBLE",
                "UNSUPPORTED",
                "NOT_TESTED",
                "FAIL",
            },
        )
        self.assertEqual(
            {item.value for item in AggregateReleaseState},
            {
                "PASS",
                "PASS_WITH_WARNINGS",
                "FAIL",
                "REVIEW_REQUIRED",
            },
        )
        self.assertEqual(
            {item.value for item in SampleRelationship},
            {"INDEPENDENT", "PAIRED", "REPEATED", "PANEL", "UNKNOWN"},
        )
        self.assertEqual(
            {item.value for item in ExecutionMode},
            {"LEGACY", "CORE_WRAPPER", "CANONICAL_V1", "DUAL_RUN"},
        )
        self.assertEqual(
            {item.value for item in CanonicalBaseMeasure},
            {
                "unweighted_n",
                "weighted_n_raw",
                "weighted_n",
                "effective_n",
            },
        )

    def test_qa_vocabularies_are_not_interchangeable(self) -> None:
        self.assertIsNot(QAIssueState, StatisticalQAState)
        self.assertIsNot(QAIssueState, AggregateReleaseState)
        self.assertIsNot(StatisticalQAState, StatisticalState)
        self.assertNotIsInstance(QAIssueState.WARN, StatisticalQAState)
        self.assertNotIsInstance(QAIssueState.PASS, AggregateReleaseState)
        self.assertNotIsInstance(StatisticalQAState.FAIL, StatisticalState)
        self.assertFalse(hasattr(AggregateReleaseState, "WARN"))


if __name__ == "__main__":
    unittest.main()
