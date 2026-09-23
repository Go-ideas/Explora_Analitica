from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Mapping
from uuid import uuid4
import zipfile

from src.package_authoring.builder import BuildEvidence, build_released_package
from src.package_authoring.contract import PackageAuthoringError, validate_execution_release
from src.project_intake.contract import IntakeResult, project_spec_fingerprint, validate_project
from src.project_intake.generic_productive import GenericRuntimeError, run_generic_productive


OPERATOR_CONSOLE_VERSION = "EXPLORA_OPERATOR_CONSOLE_V1"
SESSION_ROOT = Path(tempfile.gettempdir()) / "explora_operator_console"
SUPPORTED_DATASET_SUFFIXES = {".sav"}


class OperatorConsoleError(ValueError):
    pass


@dataclass(frozen=True)
class Workspace:
    session_id: str
    root: Path
    uploads: Path
    generated: Path
    releases: Path


@dataclass(frozen=True)
class UploadedArtifact:
    role: str
    original_name: str
    stored_path: Path
    sha256: str
    size_bytes: int


def create_workspace(session_id: str | None = None) -> Workspace:
    session_id = session_id or uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", session_id):
        raise OperatorConsoleError("invalid session identity")
    root = SESSION_ROOT / session_id
    uploads = root / "uploads"
    generated = root / "generated"
    releases = root / "releases"
    for path in (uploads, generated, releases):
        path.mkdir(parents=True, exist_ok=True)
    return Workspace(session_id, root, uploads, generated, releases)


def cleanup_workspace(workspace: Workspace) -> None:
    if workspace.root.exists() and workspace.root.parent == SESSION_ROOT:
        shutil.rmtree(workspace.root)


def safe_upload_name(name: str) -> str:
    candidate = Path(name).name
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate).strip("._")
    return candidate or "upload.bin"


def save_upload(
    workspace: Workspace,
    *,
    role: str,
    filename: str,
    content: bytes,
    allowed_suffixes: set[str] | None = None,
) -> UploadedArtifact:
    if not content:
        raise OperatorConsoleError(f"{role} upload is empty")
    safe_name = safe_upload_name(filename)
    suffix = Path(safe_name).suffix.lower()
    if allowed_suffixes is not None and suffix not in allowed_suffixes:
        raise OperatorConsoleError(
            f"{role} requires one of: {', '.join(sorted(allowed_suffixes))}"
        )
    digest = sha256(content).hexdigest().upper()
    target_dir = workspace.uploads / safe_upload_name(role)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{digest[:12]}__{safe_name}"
    if not target.exists():
        target.write_bytes(content)
    return UploadedArtifact(role, filename, target, digest, len(content))


def parse_json_upload(content: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OperatorConsoleError(f"{label} must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise OperatorConsoleError(f"{label} root must be an object")
    return payload


def intake_summary(project_spec: Mapping[str, Any]) -> dict[str, Any]:
    result = validate_project(project_spec)
    return {
        "status": result.validation_status,
        "ready": result.ready_for_execution,
        "project_id": result.project_id,
        "spec_version": result.spec_version,
        "fingerprint": result.project_spec_fingerprint,
        "source_fingerprints": list(result.source_fingerprints),
        "errors": [asdict(item) for item in result.errors],
        "warnings": [asdict(item) for item in result.warnings],
        "ambiguity_decisions": list(result.ambiguity_decisions),
        "unsupported_capabilities": list(result.unsupported_capabilities),
    }


def release_summary(
    project_spec: Mapping[str, Any],
    execution_release: Mapping[str, Any],
) -> dict[str, Any]:
    decision = execution_release.get("release_decision")
    approved = isinstance(decision, dict) and decision.get("approved") is True
    if not approved:
        return {
            "status": "PENDING_HUMAN_RELEASE",
            "ready": False,
            "approved": False,
            "error": None,
        }
    try:
        validated = validate_execution_release(project_spec, execution_release)
    except (PackageAuthoringError, ValueError, KeyError, TypeError) as exc:
        return {
            "status": "VALIDATION_FAILED",
            "ready": False,
            "approved": True,
            "error": str(exc),
        }
    return {
        "status": "READY_FOR_PACKAGE",
        "ready": True,
        "approved": True,
        "error": None,
        "project_spec_fingerprint": validated.project_spec_fingerprint,
    }


def approve_execution_release(
    execution_release: Mapping[str, Any],
    *,
    decision_id: str,
    decision_basis: str,
    released_at: str | None = None,
) -> dict[str, Any]:
    if not decision_id.strip() or not decision_basis.strip():
        raise OperatorConsoleError("human decision id and basis are required")
    payload = deepcopy(dict(execution_release))
    decision = payload.get("release_decision")
    if not isinstance(decision, dict):
        raise OperatorConsoleError("Execution Release has no release_decision object")
    timestamp = released_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    decision.update(
        {
            "human_decision_id": decision_id.strip(),
            "human_decision_basis": decision_basis.strip(),
            "release_mode": "MANUAL",
            "released_at": timestamp,
            "approved": True,
        }
    )
    payload["release_decision"] = decision
    return payload


def execution_targets(project_spec: Mapping[str, Any]) -> tuple[str, ...]:
    targets: set[str] = set()
    for request in project_spec.get("output_requests", []):
        if request.get("web_included"):
            targets.add("WEB")
        if request.get("excel_included"):
            targets.add("EXCEL")
    return tuple(target for target in ("WEB", "EXCEL") if target in targets)


def web_execution_readiness(
    project_spec: Mapping[str, Any],
    execution_release: Mapping[str, Any],
    *,
    package_present: bool,
) -> tuple[bool, str]:
    intake = intake_summary(project_spec)
    if not intake["ready"]:
        return False, "Project Spec is not READY_FOR_EXECUTION"
    release = release_summary(project_spec, execution_release)
    if not release["ready"]:
        return False, "Execution Release is not human-approved and valid"
    if not package_present:
        return False, "RELEASED package has not been built"
    targets = execution_targets(project_spec)
    if "EXCEL" in targets:
        return False, (
            "Operator Console V1 executes WEB-only projects. "
            "Excel requires explicit M7 QualifiedMaster integration."
        )
    if "WEB" not in targets:
        return False, "Project has no WEB output intent"
    return True, "READY_FOR_CANONICAL_WEB_EXECUTION"


def build_package(
    workspace: Workspace,
    *,
    project_spec: Mapping[str, Any],
    execution_release: Mapping[str, Any],
    source_path: str | Path,
) -> BuildEvidence:
    package_id = str(execution_release.get("package", {}).get("package_id", "package"))
    safe_id = safe_upload_name(package_id)
    destination = workspace.generated / f"{safe_id}_{uuid4().hex[:8]}.zip"
    return build_released_package(
        project_spec,
        execution_release,
        destination=destination,
        source_path=source_path,
    )


def run_web_project(
    workspace: Workspace,
    *,
    project_spec: Mapping[str, Any],
    execution_release: Mapping[str, Any],
    source_path: str | Path,
    package_path: str | Path,
) -> tuple[Path, dict[str, Any]]:
    ready, reason = web_execution_readiness(
        project_spec,
        execution_release,
        package_present=Path(package_path).exists(),
    )
    if not ready:
        raise OperatorConsoleError(reason)
    destination = workspace.releases / f"release_{uuid4().hex[:10]}"
    try:
        summary = run_generic_productive(
            project_spec,
            source_path=source_path,
            package_path=package_path,
            output_root=destination,
        )
    except (GenericRuntimeError, ValueError, KeyError, FileNotFoundError) as exc:
        raise OperatorConsoleError(str(exc)) from exc
    return destination, summary


def archive_directory(root: str | Path) -> bytes:
    base = Path(root)
    if not base.is_dir():
        raise OperatorConsoleError("release directory does not exist")
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in base.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(base).as_posix())
    return output.getvalue()


def decision_rows(
    project_spec: Mapping[str, Any],
    execution_release: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in project_spec.get("ambiguities", []):
        rows.append(
            {
                "source": "Project Spec ambiguity",
                "id": item.get("ambiguity_id"),
                "state": item.get("state"),
                "approval_required": item.get("classification") in {"BLOCKING", "HUMAN_DECISION_REQUIRED"},
                "detail": item.get("description") or item.get("source_evidence") or "",
            }
        )
    for item in project_spec.get("ai_interpretations", []):
        rows.append(
            {
                "source": "AI interpretation",
                "id": item.get("decision_id"),
                "state": item.get("release_state"),
                "approval_required": bool(item.get("human_approval_required")),
                "detail": item.get("proposed_interpretation") or "",
            }
        )
    if execution_release is not None:
        decision = execution_release.get("release_decision", {})
        rows.append(
            {
                "source": "B3 release",
                "id": decision.get("human_decision_id"),
                "state": "APPROVED" if decision.get("approved") is True else "PENDING",
                "approval_required": True,
                "detail": decision.get("human_decision_basis") or "",
            }
        )
    return rows
