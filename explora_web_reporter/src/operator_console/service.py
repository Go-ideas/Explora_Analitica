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
from xml.etree import ElementTree
from uuid import uuid4
import zipfile

from src.package_authoring.builder import BuildEvidence, build_released_package
from src.package_authoring.contract import PackageAuthoringError, validate_execution_release
from src.project_intake.contract import IntakeResult, project_spec_fingerprint, validate_project
from src.project_intake.generic_productive import GenericRuntimeError, run_generic_productive
from src.readers.spss_reader import read_spss


OPERATOR_CONSOLE_VERSION = "EXPLORA_OPERATOR_CONSOLE_V1_3"
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


def _normalise_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _questionnaire_docx_lines(path: str | Path | None) -> list[str]:
    if path is None:
        return []
    source = Path(path)
    if source.suffix.lower() != ".docx":
        return []
    try:
        with zipfile.ZipFile(source) as archive:
            xml = archive.read("word/document.xml")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise OperatorConsoleError(f"No se pudo leer el cuestionario DOCX: {exc}") from exc
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise OperatorConsoleError("El cuestionario DOCX contiene XML inválido") from exc
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    lines: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        text = "".join(node.text or "" for node in paragraph.iter(namespace + "t"))
        text = _normalise_text(text)
        if text:
            lines.append(text)
    return lines


def _variable_type(series) -> str:
    import pandas as pd
    if pd.api.types.is_bool_dtype(series.dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(series.dtype):
        return "INTEGER"
    if pd.api.types.is_numeric_dtype(series.dtype):
        return "NUMBER"
    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return "DATE"
    return "STRING"


def _numbered_prefix(variable: str) -> str | None:
    match = re.fullmatch(r"(.+?)[_.](\d{1,3})", variable)
    if not match:
        return None
    prefix = match.group(1).rstrip("_.")
    return prefix if len(prefix) >= 2 else None


def _grid_prefix(variable: str) -> str | None:
    match = re.fullmatch(r"(.+?)_r(\d{1,3})", variable, flags=re.IGNORECASE)
    if not match:
        return None
    prefix = match.group(1).rstrip("_")
    return prefix if len(prefix) >= 2 else None


def _has_explicit_loop_marker(label: str) -> bool:
    lowered = label.lower()
    return "looplabel" in lowered or "looptime" in lowered


def analyze_source_inputs(
    dataset_path: str | Path,
    *,
    questionnaire_path: str | Path | None = None,
    datamap_path: str | Path | None = None,
) -> dict[str, Any]:
    """Create non-authoritative source evidence without producing analytical results."""
    source = Path(dataset_path)
    if source.suffix.lower() != ".sav":
        raise OperatorConsoleError("El análisis de fuentes V1 requiere una base .sav")
    try:
        df, meta, summary = read_spss(source)
    except RuntimeError as exc:
        raise OperatorConsoleError(str(exc)) from exc

    questionnaire_lines = _questionnaire_docx_lines(questionnaire_path)
    questionnaire_text = "\n".join(questionnaire_lines)
    labels = summary.get("variable_labels", {}) or {}
    value_labels = summary.get("value_labels", {}) or {}
    missing_user = summary.get("missing_user_values", {}) or {}
    missing_ranges = summary.get("missing_ranges", {}) or {}

    rm_groups: dict[str, list[str]] = {}
    loop_groups: dict[str, list[str]] = {}
    grid_groups: dict[str, list[str]] = {}
    for raw_variable in summary["variables"]:
        variable = str(raw_variable)
        label = _normalise_text(labels.get(variable, ""))
        grid_prefix = _grid_prefix(variable)
        numbered_prefix = _numbered_prefix(variable)
        if grid_prefix:
            grid_groups.setdefault(grid_prefix, []).append(variable)
        elif numbered_prefix and _has_explicit_loop_marker(label):
            loop_groups.setdefault(numbered_prefix, []).append(variable)
        elif numbered_prefix:
            rm_groups.setdefault(numbered_prefix, []).append(variable)

    def qualified_groups(groups: dict[str, list[str]]) -> dict[str, list[str]]:
        return {
            key: values for key, values in groups.items()
            if len(values) >= 2
        }

    rm_groups = qualified_groups(rm_groups)
    loop_groups = qualified_groups(loop_groups)
    grid_groups = qualified_groups(grid_groups)
    rm_members = {variable for values in rm_groups.values() for variable in values}
    loop_members = {variable for values in loop_groups.values() for variable in values}
    grid_members = {variable for values in grid_groups.values() for variable in values}

    id_candidates: list[str] = []
    id_signal_candidates: list[dict[str, Any]] = []
    weight_candidates: list[str] = []
    variables: list[dict[str, Any]] = []
    weight_pattern = re.compile(r"(^|[_])(pond|ponder|peso|weight|wgt|factor)([_]|$)", re.IGNORECASE)
    id_pattern = re.compile(r"(?<![A-Za-z0-9])(id|folio|case|record|respondent|respondiente|entrevista)(?![A-Za-z0-9])", re.IGNORECASE)

    for variable in summary["variables"]:
        variable = str(variable)
        series = df[variable]
        label = _normalise_text(labels.get(variable, ""))
        combined = f"{variable} {label}"
        is_weight = bool(weight_pattern.search(combined))
        if is_weight:
            weight_candidates.append(variable)

        unique_non_missing = int(series.nunique(dropna=True))
        has_id_signal = bool(id_pattern.search(combined))
        uniqueness_ratio = 0.0 if len(df) == 0 else unique_non_missing / len(df)
        is_id = len(df) > 0 and unique_non_missing == len(df) and has_id_signal
        if has_id_signal:
            id_signal_candidates.append(
                {
                    "variable": variable,
                    "unique_non_missing": unique_non_missing,
                    "n_cases": len(df),
                    "uniqueness_ratio": uniqueness_ratio,
                    "authority": "CANDIDATE_ONLY",
                }
            )
        if is_id:
            id_candidates.append(variable)

        exact_pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(variable)}(?![A-Za-z0-9_])", re.IGNORECASE)
        matched_lines = [line for line in questionnaire_lines if exact_pattern.search(line)]
        role = (
            "WEIGHT_CANDIDATE"
            if is_weight
            else "ID_CANDIDATE"
            if is_id
            else "LOOP_MEMBER_CANDIDATE"
            if variable in loop_members
            else "GRID_ROW_CANDIDATE"
            if variable in grid_members
            else "RM_MEMBER_CANDIDATE"
            if variable in rm_members
            else "RU_CANDIDATE"
            if bool(value_labels.get(variable))
            else "UNCLASSIFIED"
        )
        variables.append(
            {
                "variable": variable,
                "label": label,
                "data_type": _variable_type(series),
                "value_label_count": len(value_labels.get(variable, {}) or {}),
                "missing_user_values": list(missing_user.get(variable, []) or []),
                "missing_range_count": len(missing_ranges.get(variable, []) or []),
                "unique_non_missing": unique_non_missing,
                "uniqueness_ratio": uniqueness_ratio,
                "questionnaire_exact_matches": len(matched_lines),
                "questionnaire_evidence": matched_lines[:3],
                "candidate_role": role,
                "authority": "CANDIDATE_ONLY",
            }
        )

    datamap = None
    if datamap_path is not None:
        path = Path(datamap_path)
        datamap = {
            "filename": path.name,
            "sha256": sha256(path.read_bytes()).hexdigest().upper(),
            "status": "EVIDENCE_PRESENT_NOT_INTERPRETED",
        }

    return {
        "schema_version": "EXPLORA_SOURCE_ANALYSIS_V1",
        "authority": "SOURCE_EVIDENCE_ONLY",
        "dataset": {
            "filename": source.name,
            "sha256": sha256(source.read_bytes()).hexdigest().upper(),
            "n_cases": int(summary["n_casos"]),
            "n_variables": int(summary["n_variables"]),
        },
        "questionnaire": {
            "filename": None if questionnaire_path is None else Path(questionnaire_path).name,
            "sha256": None if questionnaire_path is None else sha256(Path(questionnaire_path).read_bytes()).hexdigest().upper(),
            "format_supported_for_text_evidence": bool(
                questionnaire_path is not None and Path(questionnaire_path).suffix.lower() == ".docx"
            ),
            "paragraphs_extracted": len(questionnaire_lines),
            "variables_with_exact_questionnaire_match": sum(
                1 for item in variables if item["questionnaire_exact_matches"] > 0
            ),
        },
        "datamap": datamap,
        "id_candidates": sorted(id_candidates),
        "id_signal_candidates": sorted(id_signal_candidates, key=lambda item: item["variable"]),
        "weight_candidates": sorted(weight_candidates),
        "rm_group_candidates": [
            {"group": key, "variables": values, "authority": "CANDIDATE_ONLY"}
            for key, values in sorted(rm_groups.items())
        ],
        "loop_group_candidates": [
            {"group": key, "variables": values, "authority": "CANDIDATE_ONLY"}
            for key, values in sorted(loop_groups.items())
        ],
        "grid_group_candidates": [
            {"group": key, "variables": values, "authority": "CANDIDATE_ONLY"}
            for key, values in sorted(grid_groups.items())
        ],
        "variables": variables,
        "next_state": (
            "REVIEW_SOURCE_CANDIDATES"
            if variables
            else "BLOCKED_NO_VARIABLES"
        ),
        "limitations": [
            "No question type is promoted to Project Spec authority automatically.",
            "RM groups are naming-pattern candidates only and require review.",
            "Explicit LoopLabel/Looptime metadata separates loop repetitions from RM candidates.",
            "Variables using _rN row notation are surfaced as grid-row candidates.",
            "Weight and respondent-ID candidates require review.",
            "Questionnaire matching is lexical evidence, not semantic authority.",
            "No percentages, bases, weights, significance or Canonical Results are calculated.",
        ],
    }



CAPABILITY_MATRIX = {
    "RU": {"status": "QUALIFIED", "authority": "GATE47"},
    "RM": {"status": "QUALIFIED", "authority": "GATE47"},
    "LOOP_RU": {"status": "QUALIFIED", "authority": "GATE49"},
    "LOOP_NUMERICO": {"status": "QUALIFIED", "authority": "GATE49"},
    "LOOP_RM": {"status": "NOT_YET_QUALIFIED", "authority": "GATE49_FAIL_CLOSED"},
    "GRID_ESCALA": {"status": "NOT_YET_QUALIFIED", "authority": "UNQUALIFIED"},
    "GRID_RM": {"status": "NOT_YET_QUALIFIED", "authority": "UNQUALIFIED"},
    "SCALE": {"status": "NOT_YET_QUALIFIED", "authority": "UNQUALIFIED"},
    "NUMERIC": {"status": "NOT_YET_QUALIFIED", "authority": "UNQUALIFIED"},
}
QUALIFIED_QUESTION_TYPES = {
    final_type for final_type, capability in CAPABILITY_MATRIX.items()
    if capability["status"] == "QUALIFIED"
}
NOT_YET_QUALIFIED_QUESTION_TYPES = {
    final_type for final_type, capability in CAPABILITY_MATRIX.items()
    if capability["status"] == "NOT_YET_QUALIFIED"
}
CONFIG_REVIEW_TYPES = {"RESPONDENT_ID", "WEIGHT", "META_CONTROL"}
STRUCTURE_REVIEW_FINAL_TYPES = tuple(sorted(
    QUALIFIED_QUESTION_TYPES
    | NOT_YET_QUALIFIED_QUESTION_TYPES
    | CONFIG_REVIEW_TYPES
    | {"UNCLASSIFIED"}
))


def _control_candidate(item: Mapping[str, Any]) -> bool:
    text = f"{item.get('variable', '')} {item.get('label', '')}"
    pattern = re.compile(
        r"(^|[_\s.-])("
        r"sys|system|rotation|rotacion|rotación|cell|celda|key|clave|"
        r"product|producto|lot|lote|classification|clasificacion|clasificación|"
        r"quota|cuota|sample|muestra|usuario"
        r")([_\s.-]|$)",
        re.IGNORECASE,
    )
    return bool(pattern.search(text))


def _questionnaire_marker(item: Mapping[str, Any]) -> str | None:
    evidence = " ".join(item.get("questionnaire_evidence", []) or [])
    markers = []
    for marker_name in ("RM", "RU", "RN"):
        if re.search(rf"(?<![A-Za-z0-9_]){marker_name}(?![A-Za-z0-9_])", evidence, re.IGNORECASE):
            markers.append(marker_name)
    if len(markers) != 1:
        return None
    return {"RM": "RM", "RU": "RU", "RN": "NUMERIC"}[markers[0]]


def _capability_status(final_type: str) -> str:
    if final_type in CAPABILITY_MATRIX:
        return CAPABILITY_MATRIX[final_type]["status"]
    if final_type in CONFIG_REVIEW_TYPES:
        return "CONFIG_ROLE"
    return "UNRESOLVED"


def _review_item(
    *,
    item_id: str,
    source_kind: str,
    variables: list[str],
    proposed_type: str,
    confidence: str,
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "source_kind": source_kind,
        "variables": variables,
        "proposed_type": proposed_type,
        "proposal_confidence": confidence,
        "evidence": evidence,
        "capability_status": _capability_status(proposed_type),
        "review_state": "PENDING",
        "final_type": proposed_type,
        "human_note": "",
        "authority": "HUMAN_REVIEW_REQUIRED",
    }


def build_structure_review(source_analysis: Mapping[str, Any]) -> dict[str, Any]:
    if source_analysis.get("schema_version") != "EXPLORA_SOURCE_ANALYSIS_V1":
        raise OperatorConsoleError("Structure Review requires EXPLORA_SOURCE_ANALYSIS_V1")
    variable_lookup = {
        item["variable"]: item
        for item in source_analysis.get("variables", [])
        if isinstance(item, dict) and item.get("variable")
    }
    items: list[dict[str, Any]] = []
    grouped_variables: set[str] = set()

    for group in source_analysis.get("loop_group_candidates", []):
        variables = list(group.get("variables", []))
        if not variables:
            continue
        grouped_variables.update(variables)
        member_rows = [variable_lookup.get(variable, {}) for variable in variables]
        proposed = (
            "LOOP_RU"
            if member_rows and all(int(row.get("value_label_count", 0)) > 0 for row in member_rows)
            else "LOOP_NUMERICO"
        )
        items.append(_review_item(
            item_id=f"LOOP::{group['group']}",
            source_kind="GROUP",
            variables=variables,
            proposed_type=proposed,
            confidence="HIGH",
            evidence=[
                "Variables share a numbered repeated-measure stem.",
                "SPSS labels contain explicit LoopLabel/Looptime metadata.",
                "Loop candidates are intentionally excluded from RM grouping.",
            ],
        ))

    for group in source_analysis.get("grid_group_candidates", []):
        variables = list(group.get("variables", []))
        if not variables:
            continue
        grouped_variables.update(variables)
        member_rows = [variable_lookup.get(variable, {}) for variable in variables]
        proposed = (
            "GRID_ESCALA"
            if member_rows and all(int(row.get("value_label_count", 0)) > 0 for row in member_rows)
            else "UNCLASSIFIED"
        )
        items.append(_review_item(
            item_id=f"GRID::{group['group']}",
            source_kind="GROUP",
            variables=variables,
            proposed_type=proposed,
            confidence="MEDIUM",
            evidence=[
                "Variables share _rN row notation.",
                "The proposal is structural only; questionnaire semantics still require review.",
            ],
        ))

    for group in source_analysis.get("rm_group_candidates", []):
        variables = list(group.get("variables", []))
        if not variables:
            continue
        grouped_variables.update(variables)
        items.append(_review_item(
            item_id=f"RM::{group['group']}",
            source_kind="GROUP",
            variables=variables,
            proposed_type="RM",
            confidence="MEDIUM",
            evidence=[
                "Variables share a numbered option stem without explicit loop metadata.",
                "RM proposal remains naming-pattern evidence and requires human confirmation.",
            ],
        ))

    id_unique = set(source_analysis.get("id_candidates", []))
    id_signals = {
        item.get("variable")
        for item in source_analysis.get("id_signal_candidates", [])
        if item.get("variable")
    }
    weight_candidates = set(source_analysis.get("weight_candidates", []))

    for variable, row in variable_lookup.items():
        if variable in grouped_variables:
            continue
        marker = _questionnaire_marker(row)
        if variable in weight_candidates:
            proposed = "WEIGHT"
            confidence = "MEDIUM"
            evidence = ["Variable name/label matches generic weight terminology."]
        elif variable in id_unique:
            proposed = "RESPONDENT_ID"
            confidence = "HIGH"
            evidence = [
                "Variable has respondent-identity naming evidence.",
                "Non-missing values are unique across all source rows.",
            ]
        elif variable in id_signals:
            proposed = "RESPONDENT_ID"
            confidence = "MEDIUM"
            evidence = [
                "Variable has respondent-identity naming evidence.",
                f"Observed uniqueness ratio: {float(row.get('uniqueness_ratio', 0.0)):.1%}.",
                "Identity authority requires human selection.",
            ]
        elif _control_candidate(row):
            proposed = "META_CONTROL"
            confidence = "MEDIUM"
            evidence = ["Variable name/label matches generic survey-control metadata terminology."]
        elif marker is not None:
            proposed = marker
            confidence = "HIGH"
            evidence = [
                f"Questionnaire evidence contains explicit {marker if marker != 'NUMERIC' else 'RN'} marker.",
                *list(row.get("questionnaire_evidence", []) or [])[:2],
            ]
        elif row.get("candidate_role") == "RU_CANDIDATE":
            proposed = "RU"
            confidence = "MEDIUM"
            evidence = [
                f"SPSS metadata contains {int(row.get('value_label_count', 0))} value labels.",
                "No stronger LOOP/GRID/RM/control pattern was detected.",
            ]
        elif (
            row.get("data_type") in {"INTEGER", "NUMBER"}
            and int(row.get("value_label_count", 0)) == 0
            and (row.get("label") or row.get("questionnaire_evidence"))
        ):
            proposed = "NUMERIC"
            confidence = "MEDIUM"
            evidence = [
                "Numeric SPSS variable has no value-label domain.",
                "Question/label evidence exists but requires human confirmation.",
            ]
        else:
            proposed = "UNCLASSIFIED"
            confidence = "LOW"
            evidence = ["Insufficient deterministic evidence for a question/configuration role."]

        items.append(_review_item(
            item_id=f"VAR::{variable}",
            source_kind="VARIABLE",
            variables=[variable],
            proposed_type=proposed,
            confidence=confidence,
            evidence=evidence,
        ))

    type_counts: dict[str, int] = {}
    for item in items:
        type_counts[item["proposed_type"]] = type_counts.get(item["proposed_type"], 0) + 1

    return {
        "schema_version": "EXPLORA_STRUCTURE_REVIEW_V1",
        "source_analysis_sha256": sha256(
            json.dumps(source_analysis, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest().upper(),
        "authority": "HUMAN_REVIEW_REQUIRED",
        "status": "NEEDS_HUMAN_DECISION",
        "items": items,
        "proposal_type_counts": dict(sorted(type_counts.items())),
        "capability_matrix": deepcopy(CAPABILITY_MATRIX),
        "qualified_question_types": sorted(QUALIFIED_QUESTION_TYPES),
        "not_yet_qualified_question_types": sorted(NOT_YET_QUALIFIED_QUESTION_TYPES),
        "loop_significance": "NOT_YET_QUALIFIED",
        "summary": {
            "total_items": len(items),
            "pending_items": len(items),
            "approved_items": 0,
            "excluded_items": 0,
            "capability_gaps": [],
        },
    }


def finalize_structure_review(
    review: Mapping[str, Any],
    decisions: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if review.get("schema_version") != "EXPLORA_STRUCTURE_REVIEW_V1":
        raise OperatorConsoleError("Unsupported Structure Review schema")
    items = deepcopy(list(review.get("items", [])))
    decision_by_id = {
        str(item.get("item_id")): item
        for item in decisions
        if item.get("item_id")
    }
    allowed_states = {"PENDING", "APPROVED", "EXCLUDED"}
    allowed_types = set(STRUCTURE_REVIEW_FINAL_TYPES)

    for item in items:
        decision = decision_by_id.get(item["item_id"])
        if decision is None:
            continue
        state = str(decision.get("review_state", "PENDING"))
        final_type = str(decision.get("final_type", item["proposed_type"]))
        note = str(decision.get("human_note", "") or "")
        if state not in allowed_states:
            raise OperatorConsoleError(f"Invalid review state for {item['item_id']}: {state}")
        if final_type not in allowed_types:
            raise OperatorConsoleError(f"Invalid final type for {item['item_id']}: {final_type}")
        if state == "APPROVED" and final_type == "UNCLASSIFIED":
            raise OperatorConsoleError(
                f"{item['item_id']} cannot be approved as UNCLASSIFIED"
            )
        item["review_state"] = state
        item["final_type"] = final_type
        item["human_note"] = note
        item["capability_status"] = _capability_status(final_type)
        item["authority"] = (
            "HUMAN_APPROVED"
            if state == "APPROVED"
            else "HUMAN_EXCLUDED"
            if state == "EXCLUDED"
            else "HUMAN_REVIEW_REQUIRED"
        )

    pending = [item for item in items if item["review_state"] == "PENDING"]
    approved = [item for item in items if item["review_state"] == "APPROVED"]
    excluded = [item for item in items if item["review_state"] == "EXCLUDED"]
    capability_gaps = [
        {
            "item_id": item["item_id"],
            "final_type": item["final_type"],
            "variables": item["variables"],
        }
        for item in approved
        if item["final_type"] in NOT_YET_QUALIFIED_QUESTION_TYPES
    ]
    if pending:
        status = "NEEDS_HUMAN_DECISION"
    elif capability_gaps:
        status = "CAPABILITY_GAP"
    else:
        status = "READY_FOR_PROJECT_SPEC_DRAFT"

    output = deepcopy(dict(review))
    output["items"] = items
    output["status"] = status
    output["authority"] = (
        "HUMAN_REVIEWED"
        if not pending
        else "HUMAN_REVIEW_REQUIRED"
    )
    output["summary"] = {
        "total_items": len(items),
        "pending_items": len(pending),
        "approved_items": len(approved),
        "excluded_items": len(excluded),
        "capability_gaps": capability_gaps,
    }
    return output


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
