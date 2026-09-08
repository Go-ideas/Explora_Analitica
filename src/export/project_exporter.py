from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from src.export.report_exporter import (
    report_to_excel_bytes,
    reports_to_excel_bytes,
)
from src.reporter.tabulator import ReportResult


def executive_export_bytes(report: ReportResult) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{report.question_id}_Analisis_Explora.xlsx",
            report_to_excel_bytes(report),
        )
        if report.figure is not None:
            archive.writestr(
                f"{report.question_id}_Grafico.html",
                report.figure.to_html(
                    full_html=True,
                    include_plotlyjs=True,
                ).encode("utf-8"),
            )
        archive.writestr(
            "LEEME.txt",
            (
                "Exportación ejecutiva de Explora.\n"
                "Incluye tabla, configuración, notas metodológicas"
                " y gráfico interactivo cuando está disponible.\n"
            ).encode("utf-8"),
        )
    return output.getvalue()


def technical_export_bytes(
    files: list[tuple[str, Path]],
) -> bytes:
    output = BytesIO()
    included = []
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for export_name, path in files:
            if not path.exists():
                continue
            archive.write(path, arcname=export_name)
            included.append(export_name)
        archive.writestr(
            "CONTENIDO.txt",
            (
                "Exportación técnica de Explora.\n"
                "Archivos incluidos:\n- "
                + "\n- ".join(included)
            ).encode("utf-8"),
        )
    return output.getvalue()


def saved_reports_export_bytes(
    saved_reports: list[dict[str, Any]],
) -> bytes:
    output = BytesIO()
    reports = [
        entry["report"]
        for entry in saved_reports
        if entry.get("report") is not None
    ]
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "Todas_las_tablas.xlsx",
            reports_to_excel_bytes(reports),
        )
        for index, entry in enumerate(saved_reports, start=1):
            report = entry.get("report")
            if report is None:
                continue
            stem = _safe_export_name(
                entry.get("name")
                or f"{report.question_id}_Analisis"
            )
            prefix = f"{index:02d}_{stem}"
            archive.writestr(
                f"{prefix}_Tabla.xlsx",
                report_to_excel_bytes(report),
            )
            if report.figure is not None:
                archive.writestr(
                    f"{prefix}_Grafico.html",
                    report.figure.to_html(
                        full_html=True,
                        include_plotlyjs=True,
                    ).encode("utf-8"),
                )
        archive.writestr(
            "CONTENIDO.txt",
            (
                f"Análisis guardados: {len(reports)}\n"
                "Cada análisis incluye su tabla en Excel y su "
                "gráfico interactivo cuando está disponible.\n"
            ).encode("utf-8"),
        )
    return output.getvalue()


def saved_reports_tables_excel_bytes(
    saved_reports: list[dict[str, Any]],
) -> bytes:
    reports = [
        entry["report"]
        for entry in saved_reports
        if entry.get("report") is not None
    ]
    return reports_to_excel_bytes(reports)


def _safe_export_name(value: object) -> str:
    text = re.sub(
        r'[<>:"/\\|?*]+', "_", str(value or "")
    ).strip(" ._")
    text = re.sub(r"\s+", "_", text)
    return (text[:90] or "Analisis")
