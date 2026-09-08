from __future__ import annotations

from pathlib import Path
from numbers import Number
import re
from typing import BinaryIO

import pandas as pd

from src.export.pivot_exporter import build_pivot_table
from src.reporter.table_renderer import estimate_column_widths
from src.utils.formatting import (
    format_display_header,
    is_count_column,
    is_mean_column,
    is_percentage_column,
    is_significance_column,
)
from src.utils.text_utils import first_existing


def export_revision_excel(
    path: Path,
    tables: dict[str, pd.DataFrame],
    datamap_sheets: dict[str, pd.DataFrame] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pivot = build_pivot_table(tables)
    summary = _summary_table(tables, pivot)
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        summary.to_excel(writer, sheet_name="Resumen_Base_Analitica", index=False)
        pivot.to_excel(writer, sheet_name="BD_Pivot", index=False)
        _write(writer, tables, "respondentes", "Respondentes")
        _write(writer, tables, "preguntas", "Preguntas")
        _write(writer, tables, "variables", "Variables")
        _write(writer, tables, "opciones", "Opciones")
        _write(writer, tables, "respuestas_long", "Respuestas_Long_Muestra", sample=True)
        _write(writer, tables, "multirrespuesta_long", "RM_Long_Muestra", sample=True)
        _write(writer, tables, "escalas_long", "Escalas_Long_Muestra", sample=True)
        _write(writer, tables, "abiertas", "Abiertas_Muestra", sample=True)
        _write(writer, tables, "riesgos", "Riesgos_Aplicados")
        _write(
            writer,
            tables,
            "configuracion_dashboard",
            "Configuracion_Dashboard",
        )
        _write(
            writer,
            tables,
            "recomendaciones_reporteador",
            "Recomendaciones_Reporter",
        )
        _write(
            writer,
            tables,
            "recomendaciones_reporteador",
            "Recomendaciones_Reporteador",
        )
        _write(
            writer,
            tables,
            "factores_configurados",
            "Factores_Configurados",
        )
        _write_datamap_recommendations(
            writer, datamap_sheets or {}, tables
        )
    return path


def _write_datamap_recommendations(
    writer: pd.ExcelWriter,
    datamap_sheets: dict[str, pd.DataFrame],
    tables: dict[str, pd.DataFrame],
) -> None:
    mappings = {
        "11_Banners_Filtros_Recomendados": (
            "Banners_Filtros_Recomendados"
        ),
        "12_Factores_Scores_Recomendados": (
            "Factores_Scores_Recomendados"
        ),
        "13_Orden_Menu_Reporteador": "Orden_Menu_Reporteador",
    }
    for source_name, export_name in mappings.items():
        frame = datamap_sheets.get(source_name)
        if frame is not None:
            if source_name == (
                "11_Banners_Filtros_Recomendados"
            ):
                frame = _sanitized_banner_sheet(
                    frame,
                    tables.get(
                        "recomendaciones_reporteador",
                        pd.DataFrame(),
                    ),
                )
            frame.to_excel(
                writer, sheet_name=export_name, index=False
            )


def _sanitized_banner_sheet(
    frame: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    if frame.empty or recommendations.empty:
        return frame.copy()
    variable_column = first_existing(
        frame.columns, ["Variable", "variable"]
    )
    if not variable_column or "variable" not in recommendations:
        return frame.copy()
    source = recommendations.copy()
    if "tipo_recomendacion" in source:
        source = source[
            source["tipo_recomendacion"].astype(str).eq(
                "banner_filtro"
            )
        ]
    source = source.drop_duplicates("variable").set_index(
        "variable"
    )
    result = frame.copy()
    result["Justificacion_Banner_Filtro"] = (
        result[variable_column]
        .astype(str)
        .map(source.get("justificacion", pd.Series(dtype=str)))
        .fillna("")
    )
    result["Distribucion_Base"] = (
        result[variable_column]
        .astype(str)
        .map(
            source.get(
                "distribucion_base", pd.Series(dtype=str)
            )
        )
        .fillna("")
    )
    original_justification = first_existing(
        result.columns, ["Justificacion"]
    )
    if original_justification:
        result[original_justification] = result[
            "Justificacion_Banner_Filtro"
        ]
    base_column = first_existing(
        result.columns, ["Base_Categorias_Obs"]
    )
    if base_column:
        result[base_column] = result["Distribucion_Base"]
    return result


def _write(writer: pd.ExcelWriter, tables: dict[str, pd.DataFrame], key: str, sheet_name: str, sample: bool = False) -> None:
    df = tables.get(key, pd.DataFrame())
    if sample and len(df) > 5000:
        df = df.head(5000)
    df.to_excel(writer, sheet_name=sheet_name, index=False)


def _summary_table(tables: dict[str, pd.DataFrame], pivot: pd.DataFrame) -> pd.DataFrame:
    rows = [{"elemento": "BD_Pivot", "filas": len(pivot)}]
    for name, df in tables.items():
        rows.append({"elemento": name, "filas": len(df) if df is not None else 0})
    return pd.DataFrame(rows)


def export_report_table_to_excel(
    df: pd.DataFrame,
    config: dict[str, object],
    output_path: Path | BinaryIO,
    significance: pd.DataFrame | None = None,
    column_letters: dict[str, str] | None = None,
    notes: list[str] | None = None,
) -> Path | BinaryIO:
    config_table = pd.DataFrame(
        [
            {
                "Configuración": key,
                "Valor": _config_value(value),
            }
            for key, value in config.items()
        ]
    )
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        write_executive_report_sheet(
            writer,
            "Tabla",
            df,
            config,
            column_letters=column_letters,
        )
        config_table.to_excel(
            writer,
            sheet_name="Configuracion",
            index=False,
            startrow=2,
        )
        _format_config_sheet(writer, config_table)
        if significance is not None and not significance.empty:
            significance.to_excel(
                writer,
                sheet_name="Significancia",
                index=False,
                startrow=2,
            )
            _format_report_sheet(
                writer,
                "Significancia",
                significance,
                header_row=2,
                sheet_title="Diferencias significativas",
            )
        if notes:
            notes_table = pd.DataFrame(
                {
                    "Notas metodológicas": [
                        str(note) for note in notes
                    ]
                }
            )
            notes_table.to_excel(
                writer,
                sheet_name="Notas_Metodologicas",
                index=False,
                startrow=2,
            )
            _format_notes_sheet(writer, notes_table)
    return output_path


def write_executive_report_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    df: pd.DataFrame,
    config: dict[str, object],
    column_letters: dict[str, str] | None = None,
) -> int:
    """Write one report using the same executive visual contract."""
    export_table = _excel_percentage_values(df)
    grouped_headers = _grouped_header_spec(
        export_table.columns
    )
    letter_columns = _excel_letter_columns(
        export_table, column_letters or {}
    )
    export_table = export_table.rename(
        columns={
            column: format_display_header(column)
            for column in export_table.columns
        }
    )
    letter_columns = {
        format_display_header(column): letter
        for column, letter in letter_columns.items()
    }
    header_row = 4
    data_start_row = (
        header_row + 2 + (1 if letter_columns else 0)
    )
    export_table.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        header=False,
        startrow=data_start_row,
    )
    _format_report_sheet(
        writer,
        sheet_name,
        export_table,
        letter_columns=letter_columns,
        header_row=header_row,
        grouped_headers=grouped_headers,
    )
    _write_report_heading(
        writer,
        config,
        max(len(export_table.columns), 1),
        sheet_name=sheet_name,
    )
    return data_start_row + len(export_table)


def _format_report_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    df: pd.DataFrame,
    letter_columns: dict[str, str] | None = None,
    header_row: int = 0,
    sheet_title: str | None = None,
    grouped_headers: list[tuple[str, str]] | None = None,
) -> None:
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    header = workbook.add_format(
        {
            "bold": True,
            "font_color": "#17324D",
            "bg_color": "#DCE8EE",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    group_header = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#176B87",
            "border": 1,
            "border_color": "#FFFFFF",
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    text = workbook.add_format(
        {
            "border": 1,
            "border_color": "#D9E2E7",
            "align": "left",
            "valign": "top",
        }
    )
    integer = workbook.add_format(
        {
            "border": 1,
            "border_color": "#D9E2E7",
            "align": "right",
            "num_format": "#,##0",
        }
    )
    percentage = workbook.add_format(
        {
            "border": 1,
            "border_color": "#D9E2E7",
            "align": "right",
            "num_format": "0.0%",
        }
    )
    decimal = workbook.add_format(
        {
            "border": 1,
            "border_color": "#D9E2E7",
            "align": "right",
            "num_format": "0.00",
        }
    )
    significance_format = workbook.add_format(
        {
            "border": 1,
            "border_color": "#D9E2E7",
            "align": "center",
            "font_size": 9,
            "font_color": "#C62828",
        }
    )
    letter_format = workbook.add_format(
        {
            "border": 1,
            "align": "center",
            "font_color": "#C62828",
            "bold": True,
            "font_size": 10,
            "bg_color": "#F7FAFB",
        }
    )
    zebra = workbook.add_format({"bg_color": "#F7FAFB"})
    widths = estimate_column_widths(df)

    for index, column in enumerate(df.columns):
        excel_width = max(10, min(55, widths[str(column)] / 7))
        # Solo definimos ancho: aplicar un formato a la columna
        # completa marca también todas las celdas vacías de Excel.
        worksheet.set_column(index, index, excel_width)
    if grouped_headers:
        data_start_row = _write_grouped_headers(
            worksheet,
            grouped_headers,
            list(df.columns),
            header_row,
            group_header,
            header,
            letter_format,
            letter_columns or {},
        )
    else:
        for index, column in enumerate(df.columns):
            worksheet.write(
                header_row, index, str(column), header
            )
        header_lines = max(
            (
                str(column).count("\n") + 1
                for column in df.columns
            ),
            default=1,
        )
        worksheet.set_row(
            header_row,
            min(90, max(34, header_lines * 18)),
        )
        data_start_row = header_row + 1
    _write_report_cells(
        worksheet,
        df,
        data_start_row,
        text,
        integer,
        percentage,
        decimal,
        significance_format,
    )
    worksheet.freeze_panes(data_start_row, 1)
    worksheet.hide_gridlines(2)
    worksheet.set_tab_color("#176B87")
    if len(df):
        last_data_row = data_start_row + len(df) - 1
        if not grouped_headers:
            worksheet.autofilter(
                header_row,
                0,
                last_data_row,
                len(df.columns) - 1,
            )
        worksheet.conditional_format(
            data_start_row,
            0,
            last_data_row,
            len(df.columns) - 1,
            {
                "type": "formula",
                "criteria": "=MOD(ROW(),2)=0",
                "format": zebra,
            },
        )
    if sheet_title:
        title = workbook.add_format(
            {
                "bold": True,
                "font_size": 16,
                "font_color": "#17324D",
            }
        )
        _write_or_merge(
            worksheet,
            0,
            0,
            0,
            max(len(df.columns) - 1, 0),
            sheet_title,
            title,
        )


def _write_report_cells(
    worksheet,
    df: pd.DataFrame,
    data_start_row: int,
    text_format,
    integer_format,
    percentage_format,
    decimal_format,
    significance_format,
) -> None:
    if df.empty:
        return
    response_column = df.columns[0]
    for row_offset, (_, row) in enumerate(df.iterrows()):
        metric = str(row[response_column]).lower()
        for column_index, column in enumerate(df.columns):
            value = row[column]
            if value is None or pd.isna(value) or value == "":
                continue
            row_index = data_start_row + row_offset
            if column_index == 0:
                worksheet.write(
                    row_index,
                    column_index,
                    str(value),
                    text_format,
                )
            elif is_significance_column(column):
                worksheet.write(
                    row_index,
                    column_index,
                    str(value),
                    significance_format,
                )
            elif _is_metric_value_column(column):
                numeric = pd.to_numeric(
                    pd.Series([value]), errors="coerce"
                ).iloc[0]
                if pd.isna(numeric):
                    worksheet.write(
                        row_index,
                        column_index,
                        str(value),
                        text_format,
                    )
                elif (
                    "top2box" in metric
                    or "bottombox" in metric
                ):
                    worksheet.write_number(
                        row_index,
                        column_index,
                        float(numeric) / 100,
                        percentage_format,
                    )
                else:
                    worksheet.write_number(
                        row_index,
                        column_index,
                        float(numeric),
                        decimal_format,
                    )
            elif is_percentage_column(column):
                worksheet.write_number(
                    row_index,
                    column_index,
                    float(value),
                    percentage_format,
                )
            elif is_count_column(column):
                worksheet.write_number(
                    row_index,
                    column_index,
                    float(value),
                    integer_format,
                )
            elif is_mean_column(column) or isinstance(
                value, Number
            ):
                worksheet.write_number(
                    row_index,
                    column_index,
                    float(value),
                    decimal_format,
                )
            else:
                worksheet.write(
                    row_index,
                    column_index,
                    str(value),
                    text_format,
                )


def _grouped_header_spec(
    columns,
) -> list[tuple[str, str]]:
    result = []
    for index, column in enumerate(columns):
        name = str(column)
        if index == 0 or " | " not in name:
            result.append((name, ""))
            continue
        group, metric = name.rsplit(" | ", 1)
        result.append(
            (_clean_excel_group_label(group), metric)
        )
    return result


def _clean_excel_group_label(value: str) -> str:
    parts = []
    for part in str(value).split(" / "):
        cleaned = re.sub(
            r"^\s*(?:código\s+)?-?\d+(?:\.0+)?\s*\|\s*",
            "",
            part,
            flags=re.IGNORECASE,
        ).strip()
        parts.append(cleaned or part.strip())
    return " / ".join(parts)


def _write_grouped_headers(
    worksheet,
    grouped_headers: list[tuple[str, str]],
    columns: list[object],
    header_row: int,
    group_format,
    metric_format,
    letter_format,
    letter_columns: dict[str, str],
) -> int:
    has_letters = bool(letter_columns)
    metric_row = header_row + 1
    letter_row = metric_row + 1 if has_letters else None
    last_header_row = (
        letter_row if letter_row is not None else metric_row
    )

    _write_or_merge(
        worksheet,
        header_row,
        0,
        last_header_row,
        0,
        grouped_headers[0][0],
        group_format,
    )

    index = 1
    while index < len(grouped_headers):
        group = grouped_headers[index][0]
        end = index
        while (
            end + 1 < len(grouped_headers)
            and grouped_headers[end + 1][0] == group
        ):
            end += 1
        _write_or_merge(
            worksheet,
            header_row,
            index,
            header_row,
            end,
            group,
            group_format,
        )
        for column_index in range(index, end + 1):
            metric = grouped_headers[column_index][1]
            worksheet.write(
                metric_row,
                column_index,
                metric,
                metric_format,
            )
            if letter_row is not None:
                worksheet.write(
                    letter_row,
                    column_index,
                    letter_columns.get(
                        str(columns[column_index]), ""
                    ),
                    letter_format,
                )
        index = end + 1

    worksheet.set_row(header_row, 26)
    worksheet.set_row(metric_row, 42)
    if letter_row is not None:
        worksheet.set_row(letter_row, 20)
    return last_header_row + 1


def _write_report_heading(
    writer: pd.ExcelWriter,
    config: dict[str, object],
    column_count: int,
    sheet_name: str = "Tabla",
) -> None:
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    last_column = max(column_count - 1, 0)
    brand = workbook.add_format(
        {
            "bold": True,
            "font_size": 11,
            "font_color": "#FFFFFF",
            "bg_color": "#176B87",
            "align": "left",
            "valign": "vcenter",
        }
    )
    title = workbook.add_format(
        {
            "bold": True,
            "font_size": 16,
            "font_color": "#17324D",
            "text_wrap": True,
            "valign": "vcenter",
        }
    )
    summary = workbook.add_format(
        {
            "font_size": 10,
            "font_color": "#425466",
            "bg_color": "#EAF1F4",
            "text_wrap": True,
            "valign": "vcenter",
        }
    )
    _write_or_merge(
        worksheet,
        0,
        0,
        0,
        last_column,
        "EXPLORA · REPORTE EJECUTIVO",
        brand,
    )
    question = str(
        config.get("Pregunta") or "Análisis de resultados"
    )
    _write_or_merge(
        worksheet,
        1,
        0,
        1,
        last_column,
        question,
        title,
    )
    context = "   |   ".join(
        [
            f"Base válida: {config.get('Base válida', '—')}",
            f"Comparar por: {_config_value(config.get('Banners', 'Total'))}",
            f"Filtros: {config.get('Filtros aplicados', 'Sin filtros')}",
            f"Cálculos: {_config_value(config.get('Cálculos', '—'))}",
        ]
    )
    _write_or_merge(
        worksheet,
        2,
        0,
        2,
        last_column,
        context,
        summary,
    )
    worksheet.set_row(0, 24)
    worksheet.set_row(1, 42)
    worksheet.set_row(2, 32)
    worksheet.set_row(3, 8)


def _write_or_merge(
    worksheet,
    first_row: int,
    first_col: int,
    last_row: int,
    last_col: int,
    value: object,
    cell_format,
) -> None:
    if first_row == last_row and first_col == last_col:
        worksheet.write(
            first_row, first_col, value, cell_format
        )
    else:
        worksheet.merge_range(
            first_row,
            first_col,
            last_row,
            last_col,
            value,
            cell_format,
        )


def _format_config_sheet(
    writer: pd.ExcelWriter, config_table: pd.DataFrame
) -> None:
    workbook = writer.book
    worksheet = writer.sheets["Configuracion"]
    header = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#176B87",
            "border": 1,
            "border_color": "#176B87",
            "align": "left",
            "valign": "vcenter",
        }
    )
    title = workbook.add_format(
        {
            "bold": True,
            "font_size": 16,
            "font_color": "#17324D",
        }
    )
    label_format = workbook.add_format(
        {
            "bold": True,
            "font_color": "#17324D",
            "bg_color": "#EAF1F4",
            "border": 1,
            "border_color": "#D9E2E7",
            "valign": "top",
        }
    )
    value_format = workbook.add_format(
        {
            "font_color": "#425466",
            "text_wrap": True,
            "border": 1,
            "border_color": "#D9E2E7",
            "valign": "top",
        }
    )
    worksheet.write(0, 0, "Configuración del análisis", title)
    for index, column in enumerate(config_table.columns):
        worksheet.write(2, index, column, header)
    for row_offset, (_, row) in enumerate(
        config_table.iterrows(), start=3
    ):
        worksheet.write(
            row_offset, 0, str(row.iloc[0]), label_format
        )
        worksheet.write(
            row_offset, 1, str(row.iloc[1]), value_format
        )
        length = len(str(row.iloc[1]))
        worksheet.set_row(
            row_offset, min(72, max(20, 15 * (1 + length // 85)))
        )
    worksheet.set_column(0, 0, 24)
    worksheet.set_column(1, 1, 80)
    worksheet.set_row(2, 26)
    worksheet.freeze_panes(3, 0)
    worksheet.autofilter(2, 0, 2 + len(config_table), 1)
    worksheet.hide_gridlines(2)
    worksheet.set_tab_color("#EDA33B")


def _format_notes_sheet(
    writer: pd.ExcelWriter, notes_table: pd.DataFrame
) -> None:
    workbook = writer.book
    worksheet = writer.sheets["Notas_Metodologicas"]
    header = workbook.add_format(
        {
            "bold": True,
            "font_color": "#17324D",
            "bg_color": "#DCE8EE",
            "border": 1,
        }
    )
    wrapped = workbook.add_format(
        {
            "text_wrap": True,
            "valign": "top",
            "border": 1,
            "border_color": "#D9E2E7",
            "font_color": "#425466",
        }
    )
    title = workbook.add_format(
        {
            "bold": True,
            "font_size": 16,
            "font_color": "#17324D",
        }
    )
    worksheet.write(0, 0, "Notas metodológicas", title)
    worksheet.write(2, 0, notes_table.columns[0], header)
    for row_offset, value in enumerate(
        notes_table.iloc[:, 0], start=3
    ):
        worksheet.write(
            row_offset, 0, str(value), wrapped
        )
        worksheet.set_row(
            row_offset,
            min(90, max(24, 15 * (1 + len(str(value)) // 110))),
        )
    worksheet.set_column(0, 0, 100)
    worksheet.freeze_panes(3, 0)
    worksheet.hide_gridlines(2)
    worksheet.set_tab_color("#665191")


def _excel_percentage_values(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if is_percentage_column(column):
            result[column] = (
                pd.to_numeric(result[column], errors="coerce") / 100
            )
    return result


def _config_value(value: object) -> str:
    if isinstance(value, dict):
        return " | ".join(
            f"{key}: {', '.join(map(str, values))}"
            for key, values in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return ", ".join(map(str, value))
    return str(value)


def _excel_letter_columns(
    df: pd.DataFrame,
    column_letters: dict[str, str],
) -> dict[str, str]:
    if not column_letters:
        return {}
    grouped = {}
    for column in df.columns[1:]:
        name = str(column)
        category = (
            name.rsplit(" | ", 1)[0]
            if " | " in name
            else name
        )
        grouped.setdefault(category, []).append(name)
    result = {}
    for category, columns in grouped.items():
        if category not in column_letters:
            continue
        preferred = [
            column
            for column in columns
            if "%" in column.rsplit(" | ", 1)[-1]
        ]
        target = preferred[0] if preferred else columns[0]
        result[target] = column_letters[category]
    return result


def _is_metric_value_column(column: object) -> bool:
    name = str(column).lower().replace("\n", " | ")
    return name.endswith(" | valor") or name == "valor"
