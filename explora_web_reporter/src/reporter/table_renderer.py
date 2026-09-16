from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src.utils.formatting import (
    format_display_header,
    is_count_column,
    is_mean_column,
    is_percentage_column,
    is_significance_column,
)


def estimate_column_widths(df: pd.DataFrame) -> dict[str, int]:
    widths = {}
    for index, column in enumerate(df.columns):
        name = str(column)
        if index == 0 or name.lower() in {"respuesta", "indicador"}:
            content_length = _max_length(df[column], name)
            widths[name] = max(280, min(480, content_length * 8))
        elif is_significance_column(name):
            widths[name] = 70
        elif is_count_column(name) or is_percentage_column(name) or is_mean_column(name):
            widths[name] = max(90, min(120, len(name) * 7))
        else:
            widths[name] = max(140, min(220, _max_length(df[column], name) * 7))
    return widths


def detect_column_alignment(df: pd.DataFrame) -> dict[str, str]:
    alignments = {}
    for index, column in enumerate(df.columns):
        name = str(column)
        if is_significance_column(name):
            alignments[name] = "center"
        elif (
            is_count_column(name)
            or is_percentage_column(name)
            or is_mean_column(name)
            or _is_metric_value_column(name)
            or pd.api.types.is_numeric_dtype(df[column])
        ):
            alignments[name] = "right"
        elif index == 0:
            alignments[name] = "left"
        else:
            alignments[name] = "left"
    return alignments


def format_report_values(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in result.columns:
        if not pd.api.types.is_numeric_dtype(result[column]):
            continue
        if is_percentage_column(column):
            result[column] = result[column].round(1)
        elif is_count_column(column):
            result[column] = result[column].round(0)
        elif is_mean_column(column):
            result[column] = result[column].round(2)
        else:
            result[column] = result[column].round(2)
    return result


def render_report_table(
    df: pd.DataFrame,
    title: str | None = None,
    notes: list[str] | None = None,
    column_letters: dict[str, str] | None = None,
) -> None:
    if title:
        st.markdown(f"**{title}**")
    formatted = format_report_values(df)
    widths = estimate_column_widths(formatted)
    alignments = detect_column_alignment(formatted)
    st.markdown(
        _table_html(
            formatted,
            widths,
            alignments,
            column_letters=column_letters,
        ),
        unsafe_allow_html=True,
    )
    if notes:
        for note in notes:
            st.caption(note)


def _max_length(series: pd.Series, column_name: str) -> int:
    if series.empty:
        return len(column_name)
    content = series.fillna("").astype(str).str.len().max()
    return max(len(column_name), int(content or 0))


def _table_html(
    df: pd.DataFrame,
    widths: dict[str, int],
    alignments: dict[str, str],
    column_letters: dict[str, str] | None = None,
) -> str:
    style = """
    <style>
    .explora-table-wrap {
        width: 100%;
        max-height: 650px;
        overflow-x: scroll;
        overflow-y: auto;
        scrollbar-gutter: stable;
        scrollbar-color: #9fb3bd #eef3f6;
        scrollbar-width: thin;
        border: 1px solid #dfe7eb;
        background: #ffffff;
    }
    .explora-table-wrap::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    .explora-table-wrap::-webkit-scrollbar-track {
        background: #eef3f6;
    }
    .explora-table-wrap::-webkit-scrollbar-thumb {
        background: #9fb3bd;
        border: 2px solid #eef3f6;
    }
    .explora-table-wrap::-webkit-scrollbar-thumb:hover {
        background: #6f8d9b;
    }
    .explora-table {
        width: max-content;
        min-width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: #17324d;
        font-size: 13px;
    }
    .explora-table th {
        position: sticky;
        top: 0;
        z-index: 2;
        padding: 10px 9px;
        border-right: 1px solid #dfe7eb;
        border-bottom: 1px solid #ccd9df;
        background: #eef3f6;
        color: #425466;
        font-weight: 600;
        line-height: 1.25;
        text-align: center;
        vertical-align: middle;
        white-space: normal;
    }
    .explora-table td {
        padding: 8px 9px;
        border-right: 1px solid #e5ecef;
        border-bottom: 1px solid #e5ecef;
        background: #ffffff;
        line-height: 1.35;
        vertical-align: top;
    }
    .explora-table tbody tr:hover td {
        background: #f7fafb;
    }
    .explora-table th:first-child,
    .explora-table td:first-child {
        position: sticky;
        left: 0;
        z-index: 1;
        background: #ffffff;
        text-align: left;
    }
    .explora-table th:first-child {
        z-index: 3;
        background: #eef3f6;
    }
    .explora-table .sig-cell {
        color: #c62828;
        font-size: 11px;
        font-weight: 700;
        text-align: center;
    }
    .explora-table .column-letter-row th {
        top: 66px;
        padding: 4px 9px;
        background: #f7fafb;
        color: #c62828;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.1;
        text-align: center;
    }
    </style>
    """
    header_cells = []
    for column in df.columns:
        name = str(column)
        label = escape(format_display_header(name)).replace("\n", "<br>")
        header_cells.append(
            f'<th style="min-width:{widths[name]}px;'
            f'max-width:{widths[name]}px">{label}</th>'
        )
    letter_cells = _column_letter_cells(
        df, widths, column_letters or {}
    )

    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for column in df.columns:
            name = str(column)
            value = _format_cell(
                row[column],
                name,
                row.iloc[0] if len(row) else "",
            )
            css_class = (
                ' class="sig-cell"'
                if is_significance_column(name)
                else ""
            )
            cells.append(
                f'<td{css_class} style="min-width:{widths[name]}px;'
                f'max-width:{widths[name]}px;'
                f'text-align:{alignments[name]}">{value}</td>'
            )
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return (
        f"{style}<div class=\"explora-table-wrap\">"
        f"<table class=\"explora-table\"><thead><tr>"
        f"{''.join(header_cells)}</tr>{letter_cells}</thead><tbody>"
        f"{''.join(body_rows)}</tbody></table></div>"
    )


def _format_cell(
    value: object,
    column: str,
    row_metric: object = "",
) -> str:
    if pd.isna(value) or value == "":
        return ""
    if is_percentage_column(column):
        try:
            return f"{float(value):.1f}%"
        except (TypeError, ValueError):
            pass
    if is_count_column(column):
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            pass
    if is_mean_column(column):
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            pass
    if _is_metric_value_column(column):
        metric = str(row_metric).lower()
        try:
            numeric = float(value)
            if "top2box" in metric or "bottombox" in metric:
                return f"{numeric:.1f}%"
            return f"{numeric:.2f}"
        except (TypeError, ValueError):
            pass
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return escape(str(value))


def _is_metric_value_column(column: object) -> bool:
    name = str(column).lower()
    return name.endswith(" | valor") or name == "valor"


def _column_letter_cells(
    df: pd.DataFrame,
    widths: dict[str, int],
    column_letters: dict[str, str],
) -> str:
    if not column_letters:
        return ""
    category_columns = {}
    for column in df.columns[1:]:
        name = str(column)
        category = (
            name.rsplit(" | ", 1)[0]
            if " | " in name
            else name
        )
        category_columns.setdefault(category, []).append(name)
    target_columns = {}
    for category, columns in category_columns.items():
        preferred = [
            column
            for column in columns
            if "%" in column.rsplit(" | ", 1)[-1]
        ]
        target_columns[category] = (
            preferred[0] if preferred else columns[0]
        )

    cells = []
    for index, column in enumerate(df.columns):
        name = str(column)
        category = (
            name.rsplit(" | ", 1)[0]
            if " | " in name
            else name
        )
        letter = ""
        if (
            index > 0
            and category in column_letters
            and target_columns.get(category) == name
        ):
            letter = escape(str(column_letters[category]))
        cells.append(
            f'<th style="min-width:{widths[name]}px;'
            f'max-width:{widths[name]}px">{letter}</th>'
        )
    return (
        '<tr class="column-letter-row">'
        f"{''.join(cells)}</tr>"
    )
