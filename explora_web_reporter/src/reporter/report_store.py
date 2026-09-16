from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.reporter.tabulator import ReportResult


def save_report_snapshot(
    saved_reports: list[dict[str, Any]] | None,
    report: ReportResult,
    name: str,
) -> list[dict[str, Any]]:
    clean_name = str(name or "").strip()
    if not clean_name:
        clean_name = f"{report.question_id} · {report.title}"
    entry = {
        "id": uuid4().hex,
        "name": clean_name[:160],
        "question_id": report.question_id,
        "title": report.title,
        "section": report.section,
        "saved_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "report": deepcopy(report),
    }
    return [*(saved_reports or []), entry]


def delete_report_snapshots(
    saved_reports: list[dict[str, Any]] | None,
    report_ids: list[str] | set[str],
) -> list[dict[str, Any]]:
    selected = {str(value) for value in report_ids}
    return [
        entry
        for entry in (saved_reports or [])
        if str(entry.get("id")) not in selected
    ]


def saved_reports_summary(
    saved_reports: list[dict[str, Any]] | None,
) -> list[dict[str, object]]:
    return [
        {
            "Eliminar": False,
            "Nombre": entry.get("name", ""),
            "Pregunta": entry.get("question_id", ""),
            "Sección": entry.get("section", ""),
            "Guardado": entry.get("saved_at", ""),
            "_id": entry.get("id", ""),
        }
        for entry in (saved_reports or [])
    ]
