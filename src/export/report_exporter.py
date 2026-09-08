from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd

from src.builder.recommendations_builder import (
    is_distribution_text,
)
from src.export.excel_exporter import (
    export_report_table_to_excel,
    write_executive_report_sheet,
)
from src.reporter.tabulator import ReportResult


def report_to_excel_bytes(report: ReportResult) -> bytes:
    output = BytesIO()
    config = _report_config(report)
    separate_significance = (
        report.significance
        if report.significance_display == "separate"
        else None
    )
    column_letters = {
        str(row["Columna"]): str(row["Letra"])
        for _, row in report.significance_legend.iterrows()
    }
    export_report_table_to_excel(
        report.table,
        config,
        output,
        significance=separate_significance,
        column_letters=column_letters,
        notes=report.notes,
    )
    return output.getvalue()


def _report_config(
    report: ReportResult,
) -> dict[str, object]:
    return {
        "Pregunta": f"{report.question_id} | {report.title}",
        "Sección": report.section,
        "Orden": report.question_order,
        "Tipo de pregunta": report.question_type,
        "Base válida": report.base,
        "Base antes de filtros": (
            report.base_before_filters or report.base
        ),
        "Banners": report.banners or ["Total"],
        "Tipo de banner": (
            "No anidados"
            if report.banner_mode == "separate"
            else "Anidados"
        ),
        "Banners recomendados": (
            report.recommended_banners or "Ninguno"
        ),
        "Justificación de banners": _recommendation_text(
            report, report.banners
        ),
        "Filtros aplicados": report.filter_summary,
        "Filtros recomendados": (
            report.recommended_filters or "Ninguno"
        ),
        "Justificación de filtros": _recommendation_text(
            report, list(report.filters)
        ),
        "Base por categoría": _distribution_text(
            report,
            list(dict.fromkeys(
                [*report.banners, *report.filters]
            )),
        ),
        "Ponderador": report.ponderador or "Sin ponderación",
        "Cálculos": report.calculations,
        "Orden de respuestas": report.response_order,
        "Nivel de confianza": (
            f"{report.confidence:.0%}"
            if report.confidence is not None
            else "No aplica"
        ),
        "Significancia": report.significance_display,
        "Base mínima": report.min_base or "No aplica",
        "Fecha de exportación": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
    }


def reports_to_excel_bytes(reports: list[ReportResult]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        if not reports:
            pd.DataFrame(
                {"Mensaje": ["No hay tablas generadas."]}
            ).to_excel(writer, sheet_name="Resumen", index=False)
        for index, report in enumerate(reports, start=1):
            sheet = _safe_sheet_name(
                f"{index:02d}_{report.question_id}"
            )
            _write_report_sheet(writer, report, sheet)
            if (
                report.significance_display == "separate"
                and not report.significance.empty
            ):
                significance_sheet = _safe_sheet_name(
                    f"{index:02d}_{report.question_id}_Sig"
                )
                config = _report_config(report)
                config["Pregunta"] = (
                    "Diferencias significativas · "
                    f"{report.question_id} | {report.title}"
                )
                write_executive_report_sheet(
                    writer,
                    significance_sheet,
                    report.significance,
                    config,
                )
    return output.getvalue()


def _write_report_sheet(
    writer: pd.ExcelWriter, report: ReportResult, sheet_name: str
) -> None:
    column_letters = {
        str(row["Columna"]): str(row["Letra"])
        for _, row in report.significance_legend.iterrows()
    }
    next_row = write_executive_report_sheet(
        writer,
        sheet_name,
        report.table,
        _report_config(report),
        column_letters=column_letters,
    )
    if not report.notes:
        return
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    section = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#665191",
            "border": 1,
            "align": "left",
        }
    )
    note_format = workbook.add_format(
        {
            "font_color": "#425466",
            "text_wrap": True,
            "valign": "top",
            "border": 1,
            "border_color": "#D9E2E7",
        }
    )
    notes_row = next_row + 2
    last_column = max(len(report.table.columns) - 1, 0)
    _write_or_merge_range(
        worksheet,
        notes_row,
        last_column,
        "Notas metodológicas",
        section,
    )
    for offset, note in enumerate(report.notes, start=1):
        row = notes_row + offset
        _write_or_merge_range(
            worksheet,
            row,
            last_column,
            str(note),
            note_format,
        )
        worksheet.set_row(
            row,
            min(72, max(24, 15 * (1 + len(str(note)) // 120))),
        )


def _safe_sheet_name(value: str) -> str:
    invalid = set("[]:*?/\\")
    cleaned = "".join("_" if char in invalid else char for char in value)
    return cleaned[:31] or "Reporte"


def _write_or_merge_range(
    worksheet,
    row: int,
    last_column: int,
    value: object,
    cell_format,
) -> None:
    if last_column <= 0:
        worksheet.write(row, 0, value, cell_format)
    else:
        worksheet.merge_range(
            row,
            0,
            row,
            last_column,
            value,
            cell_format,
        )


def _recommendation_text(
    report: ReportResult, variables: list[str]
) -> str:
    parts = []
    for variable in variables:
        details = report.recommendation_details.get(variable, {})
        justification = str(
            details.get("justificacion") or ""
        ).strip()
        if justification and not is_distribution_text(
            justification
        ):
            parts.append(f"{variable}: {justification}")
    return " | ".join(parts) or "Sin justificación registrada"


def _distribution_text(
    report: ReportResult, variables: list[str]
) -> str:
    parts = []
    for variable in variables:
        details = report.recommendation_details.get(variable, {})
        distribution = str(
            details.get("distribucion_base") or ""
        ).strip()
        if distribution:
            parts.append(f"{variable}: {distribution}")
    return " | ".join(parts) or "Sin distribución registrada"
