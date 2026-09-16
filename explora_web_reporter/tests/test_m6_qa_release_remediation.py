from __future__ import annotations

from src.contracts.vocabulary import QAReleaseStatus
from src.web_canonical.adapter import project_canonical_result
from m6_fixtures import canonical_result


def test_qa_projection_preserves_domain_state_blocking_and_code() -> None:
    projection = project_canonical_result(canonical_result())
    item = projection.qa[0]
    assert item.domain == "RESULT"
    assert item.code == "M6_FIXTURE"
    assert item.state == "PASS_WITH_WARNINGS"
    assert item.blocking is False


def test_release_state_review_required_is_preserved() -> None:
    projection = project_canonical_result(canonical_result(releasable=False))
    assert projection.release["qa_release_status"] == "REVIEW_REQUIRED"
    assert projection.release["releasable"] is False


def test_release_state_fail_with_blocking_qa_is_preserved() -> None:
    result = canonical_result(releasable=False)
    event = result.qa_events[0]
    blocking_event = type(event)(
        qa_id=event.qa_id,
        qa_domain=event.qa_domain,
        code=event.code,
        state=QAReleaseStatus.FAIL,
        blocking=True,
        scope_type=event.scope_type,
        message=event.message,
        related_ids=event.related_ids,
        details=event.details,
        source_component=event.source_component,
        policy_version=event.policy_version,
    )
    release = type(result.release)(
        computation_status=result.release.computation_status,
        qa_release_status=QAReleaseStatus.FAIL,
        releasable=False,
        reasons=("qa_warning",),
    )
    result = type(result)(
        result_schema_version=result.result_schema_version,
        result_run_id=result.result_run_id,
        project_id=result.project_id,
        dataset_fingerprint=result.dataset_fingerprint,
        project_spec_ref=result.project_spec_ref,
        core_version=result.core_version,
        qa=result.qa,
        result_fingerprint=result.result_fingerprint,
        manifest=result.manifest,
        request=result.request,
        slices=result.slices,
        bases=result.bases,
        values=result.values,
        comparisons=result.comparisons,
        qa_events=(blocking_event,),
        release=release,
    )
    projection = project_canonical_result(result)
    assert projection.qa[0].blocking is True
    assert projection.release["qa_release_status"] == "FAIL"
