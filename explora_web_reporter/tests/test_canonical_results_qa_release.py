from __future__ import annotations

import pytest

from src.analytics_core.results import (
    assemble_canonical_result,
    derive_release_state,
    make_request_snapshot,
    make_slice,
    qa_event,
)
from src.contracts.models import CanonicalReleaseState, CanonicalResult, QAEnvelope
from src.contracts.validators import ContractValidationError, validate_canonical_result
from src.contracts.vocabulary import (
    AggregateReleaseState,
    ComputationStatus,
    QADomain,
    QAIssueState,
    QAReleaseStatus,
    QAScopeType,
)


def test_warnings_are_structured_qa_events_and_release_passes_with_warnings() -> None:
    event = qa_event(
        qa_domain=QADomain.METRIC,
        code="SUPPORTED_WITH_WARNING",
        state=QAReleaseStatus.PASS_WITH_WARNINGS,
        blocking=False,
        scope_type=QAScopeType.VALUE,
        message="metric warning",
    )

    release = derive_release_state((event,), b3_release_evidence=True)

    assert release.qa_release_status is QAReleaseStatus.PASS_WITH_WARNINGS
    assert release.releasable is True


def test_blocking_qa_event_blocks_release() -> None:
    event = qa_event(
        qa_domain=QADomain.RESULT,
        code="POTENTIAL_REGRESSION",
        state=QAReleaseStatus.FAIL,
        blocking=True,
        scope_type=QAScopeType.RESULT,
        message="unexplained delta",
    )

    release = derive_release_state((event,))

    assert release.qa_release_status is QAReleaseStatus.FAIL
    assert release.releasable is False


def test_blocking_qa_overrides_positive_b3_evidence() -> None:
    event = qa_event(
        qa_domain=QADomain.RESULT,
        code="POTENTIAL_REGRESSION",
        state=QAReleaseStatus.FAIL,
        blocking=True,
        scope_type=QAScopeType.RESULT,
        message="unexplained delta",
    )

    release = derive_release_state((event,), b3_release_evidence=True)

    assert release.qa_release_status is QAReleaseStatus.FAIL
    assert release.releasable is False


def test_failed_computation_is_not_releasable_even_without_numbers() -> None:
    release = derive_release_state((), computation_status=ComputationStatus.FAILED)

    assert release.computation_status is ComputationStatus.FAILED
    assert release.qa_release_status is QAReleaseStatus.FAIL
    assert release.releasable is False


def test_empty_qa_without_b3_evidence_is_not_auto_releasable() -> None:
    release = derive_release_state(())

    assert release.qa_release_status is QAReleaseStatus.REVIEW_REQUIRED
    assert release.releasable is False


def test_positive_b3_evidence_allows_clean_release() -> None:
    release = derive_release_state((), b3_release_evidence=True)

    assert release.qa_release_status is QAReleaseStatus.PASS
    assert release.releasable is True


def test_review_required_event_is_not_releasable() -> None:
    event = qa_event(
        qa_domain=QADomain.RELEASE,
        code="HUMAN_REVIEW_REQUIRED",
        state=QAReleaseStatus.REVIEW_REQUIRED,
        blocking=False,
        scope_type=QAScopeType.RESULT,
        message="release evidence incomplete",
    )

    release = derive_release_state((event,), b3_release_evidence=True)

    assert release.qa_release_status is QAReleaseStatus.REVIEW_REQUIRED
    assert release.releasable is False


def test_fail_event_is_not_releasable() -> None:
    event = qa_event(
        qa_domain=QADomain.RELEASE,
        code="FAIL",
        state=QAReleaseStatus.FAIL,
        blocking=True,
        scope_type=QAScopeType.RESULT,
        message="release fail",
    )

    release = derive_release_state((event,), b3_release_evidence=True)

    assert release.qa_release_status is QAReleaseStatus.FAIL
    assert release.releasable is False


def test_release_validation_rejects_releasable_blocking_events() -> None:
    event = qa_event(
        qa_domain=QADomain.RELEASE,
        code="BLOCKING",
        state=QAIssueState.FAIL,
        blocking=True,
        scope_type=QAScopeType.RESULT,
        message="blocking",
    )
    result = CanonicalResult(
        result_schema_version="M5",
        result_run_id="run",
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        qa=QAEnvelope(AggregateReleaseState.PASS),
        qa_events=(event,),
        release=CanonicalReleaseState(
            ComputationStatus.COMPLETE,
            QAReleaseStatus.PASS,
            True,
        ),
    )

    with pytest.raises(ContractValidationError):
        validate_canonical_result(result)


def test_structured_failed_release_result_can_be_validated() -> None:
    event = qa_event(
        qa_domain=QADomain.RESULT,
        code="POTENTIAL_REGRESSION",
        state=QAReleaseStatus.FAIL,
        blocking=True,
        scope_type=QAScopeType.RESULT,
        message="unexplained numerical delta",
    )
    result = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=make_request_snapshot(question_ids=("q1",)),
        slices=(make_slice(is_total=True),),
        bases=(),
        values=(),
        qa_events=(event,),
        result_run_id="run",
    )

    assert result.release.qa_release_status is QAReleaseStatus.FAIL
    assert result.release.releasable is False
    assert validate_canonical_result(result) is result
