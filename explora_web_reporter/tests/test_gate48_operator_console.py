from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

import pytest

from src.operator_console.service import (
    OperatorConsoleError,
    approve_execution_release,
    cleanup_workspace,
    create_workspace,
    execution_targets,
    release_summary,
    safe_upload_name,
    save_upload,
    web_execution_readiness,
)


def test_g48_01_workspace_upload_is_session_local_and_hashed(tmp_path, monkeypatch) -> None:
    from src.operator_console import service
    monkeypatch.setattr(service, "SESSION_ROOT", tmp_path / "sessions")
    workspace = create_workspace("gate48session")
    artifact = save_upload(
        workspace,
        role="dataset",
        filename="../../customer.sav",
        content=b"synthetic-not-customer",
        allowed_suffixes={".sav"},
    )
    assert artifact.stored_path.is_relative_to(workspace.root)
    assert artifact.original_name == "../../customer.sav"
    assert artifact.sha256 == sha256(b"synthetic-not-customer").hexdigest().upper()
    assert ".." not in artifact.stored_path.name
    cleanup_workspace(workspace)
    assert not workspace.root.exists()


def test_g48_02_safe_upload_name_removes_path_components() -> None:
    assert safe_upload_name("../../secret/client.sav") == "client.sav"


def test_g48_03_release_stays_pending_without_human_b3() -> None:
    project = {"schema_version": "not-evaluated-because-b3-is-pending"}
    release = {"release_decision": {"approved": False}}
    result = release_summary(project, release)
    assert result["status"] == "PENDING_HUMAN_RELEASE"
    assert result["ready"] is False


def test_g48_04_human_approval_changes_only_release_decision() -> None:
    original = {
        "package": {"package_id": "P"},
        "requests": [{"request_id": "R"}],
        "release_decision": {
            "human_decision_id": "",
            "human_decision_basis": "",
            "release_mode": "MANUAL",
            "released_at": "",
            "approved": False,
        },
    }
    before = deepcopy(original)
    approved = approve_execution_release(
        original,
        decision_id="HUMAN-01",
        decision_basis="Reviewed configuration",
        released_at="2026-09-22T12:00:00Z",
    )
    assert original == before
    assert approved["package"] == before["package"]
    assert approved["requests"] == before["requests"]
    assert approved["release_decision"] == {
        "human_decision_id": "HUMAN-01",
        "human_decision_basis": "Reviewed configuration",
        "release_mode": "MANUAL",
        "released_at": "2026-09-22T12:00:00Z",
        "approved": True,
    }


def test_g48_05_human_approval_requires_id_and_basis() -> None:
    release = {"release_decision": {}}
    with pytest.raises(OperatorConsoleError):
        approve_execution_release(release, decision_id="", decision_basis="reviewed")
    with pytest.raises(OperatorConsoleError):
        approve_execution_release(release, decision_id="H1", decision_basis="")


def test_g48_06_output_target_detection() -> None:
    project = {
        "output_requests": [
            {"web_included": True, "excel_included": False},
            {"web_included": True, "excel_included": True},
        ]
    }
    assert execution_targets(project) == ("WEB", "EXCEL")


def test_g48_07_web_console_does_not_silently_execute_excel(monkeypatch) -> None:
    from src.operator_console import service

    monkeypatch.setattr(
        service,
        "intake_summary",
        lambda _: {"ready": True, "status": "READY_FOR_EXECUTION"},
    )
    monkeypatch.setattr(
        service,
        "release_summary",
        lambda *_: {"ready": True, "status": "READY_FOR_PACKAGE"},
    )
    project = {"output_requests": [{"web_included": True, "excel_included": True}]}
    ready, reason = web_execution_readiness(project, {}, package_present=True)
    assert ready is False
    assert "QualifiedMaster" in reason


def test_g48_08_web_console_requires_released_package(monkeypatch) -> None:
    from src.operator_console import service

    monkeypatch.setattr(
        service,
        "intake_summary",
        lambda _: {"ready": True, "status": "READY_FOR_EXECUTION"},
    )
    monkeypatch.setattr(
        service,
        "release_summary",
        lambda *_: {"ready": True, "status": "READY_FOR_PACKAGE"},
    )
    project = {"output_requests": [{"web_included": True, "excel_included": False}]}
    ready, reason = web_execution_readiness(project, {}, package_present=False)
    assert ready is False
    assert "package" in reason.lower()


def test_g48_09_web_console_readiness(monkeypatch) -> None:
    from src.operator_console import service

    monkeypatch.setattr(
        service,
        "intake_summary",
        lambda _: {"ready": True, "status": "READY_FOR_EXECUTION"},
    )
    monkeypatch.setattr(
        service,
        "release_summary",
        lambda *_: {"ready": True, "status": "READY_FOR_PACKAGE"},
    )
    project = {"output_requests": [{"web_included": True, "excel_included": False}]}
    assert web_execution_readiness(project, {}, package_present=True) == (
        True,
        "READY_FOR_CANONICAL_WEB_EXECUTION",
    )
