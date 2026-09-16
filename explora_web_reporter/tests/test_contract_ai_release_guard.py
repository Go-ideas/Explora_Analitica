from __future__ import annotations

import unittest
from dataclasses import replace

from src.contracts.models import ProjectSpec, ReleaseMetadata
from src.contracts.validators import (
    ContractValidationError,
    validate_ai_release_guard,
    validate_project_spec,
)
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.REVIEW,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="B3",
        policy_version="v1",
        source_hash="hash",
    )


def project(release: ReleaseMetadata | None = None) -> ProjectSpec:
    return ProjectSpec(
        spec_id="project-spec-1",
        version="1.0.0",
        release=release or released(),
        project_id="project-1",
        dataset_fingerprint="dataset-hash",
        respondent_id_binding="id_respondente",
        project_universe_ref="universe-true",
    )


class AIReleaseGuardTests(unittest.TestCase):
    def test_only_released_specs_cross_canonical_boundary(self) -> None:
        for state in (
            ReleaseLifecycle.PROPOSED,
            ReleaseLifecycle.REVIEW_REQUIRED,
            ReleaseLifecycle.APPROVED,
            ReleaseLifecycle.REJECTED,
        ):
            with self.subTest(state=state):
                with self.assertRaises(ContractValidationError):
                    validate_ai_release_guard(
                        project(replace(released(), state=state))
                    )

        valid_project = project()
        self.assertIs(validate_ai_release_guard(valid_project), valid_project)

    def test_missing_release_audit_metadata_fails(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate_project_spec(
                project(replace(released(), decided_by=""))
            )


if __name__ == "__main__":
    unittest.main()
