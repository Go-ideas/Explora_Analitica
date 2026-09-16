from __future__ import annotations

import string

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from statsmodels.stats.proportion import proportions_ztest

from src.reporter.banners import banner_order


def combine_significance_tables(
    tables: list[pd.DataFrame],
) -> pd.DataFrame:
    normalized = []
    for table in tables:
        if table is None or table.empty:
            continue
        item = table.copy()
        if "Indicador" in item.columns and "Respuesta" not in item.columns:
            item = item.rename(columns={"Indicador": "Respuesta"})
        if "Respuesta" in item.columns:
            normalized.append(item)
    if not normalized:
        return pd.DataFrame()
    return (
        pd.concat(normalized, ignore_index=True, sort=False)
        .fillna("")
        .drop_duplicates("Respuesta", keep="first")
    )


def percentage_significance(
    summary: pd.DataFrame,
    confidence: float = 0.95,
    min_base: int = 30,
    count_column: str = "n",
    proportion_column: str = "porcentaje",
    comparison_groups: list[list[str]] | None = None,
) -> pd.DataFrame:
    required = {
        "banner",
        "respuesta",
        count_column,
        "base",
        proportion_column,
    }
    if summary.empty or not required.issubset(summary.columns):
        return pd.DataFrame()

    categories = [
        value
        for value in banner_order(summary["banner"])
        if value != "Total"
    ]
    if len(categories) < 2:
        return pd.DataFrame()
    letters = _column_letters(categories)
    alpha = 1.0 - confidence
    rows = []

    for response, response_data in summary.groupby(
        "respuesta", dropna=False
    ):
        indexed = response_data.set_index("banner")
        marks = {category: "" for category in categories}
        for left, right in _comparison_pairs(
            categories, comparison_groups
        ):
            if left not in indexed.index or right not in indexed.index:
                continue
            left_row = indexed.loc[left]
            right_row = indexed.loc[right]
            left_base = float(left_row["base"])
            right_base = float(right_row["base"])
            if left_base < min_base or right_base < min_base:
                continue
            counts = np.array(
                [
                    float(left_row[count_column]),
                    float(right_row[count_column]),
                ]
            )
            bases = np.array([left_base, right_base])
            if (
                np.all(counts == 0)
                or np.all(counts == bases)
            ):
                continue
            try:
                _, p_value = proportions_ztest(counts, bases)
            except (ValueError, ZeroDivisionError):
                continue
            if not np.isfinite(p_value) or p_value >= alpha:
                continue
            left_pct = float(left_row[proportion_column])
            right_pct = float(right_row[proportion_column])
            if left_pct > right_pct:
                marks[left] += letters[right]
            elif right_pct > left_pct:
                marks[right] += letters[left]
        row = {"Respuesta": str(response)}
        row.update(marks)
        rows.append(row)
    return pd.DataFrame(rows)


def mean_significance(
    data: pd.DataFrame,
    confidence: float = 0.95,
    min_base: int = 30,
    comparison_groups: list[list[str]] | None = None,
) -> pd.DataFrame:
    required = {"banner", "valor"}
    if data.empty or not required.issubset(data.columns):
        return pd.DataFrame()
    categories = [
        value for value in banner_order(data["banner"]) if value != "Total"
    ]
    if len(categories) < 2:
        return pd.DataFrame()
    letters = _column_letters(categories)
    marks = {category: "" for category in categories}
    alpha = 1.0 - confidence

    for left, right in _comparison_pairs(
        categories, comparison_groups
    ):
        left_values = pd.to_numeric(
            data.loc[data["banner"] == left, "valor"], errors="coerce"
        ).dropna()
        right_values = pd.to_numeric(
            data.loc[data["banner"] == right, "valor"], errors="coerce"
        ).dropna()
        if len(left_values) < min_base or len(right_values) < min_base:
            continue
        if left_values.var() == 0 and right_values.var() == 0:
            p_value = (
                0.0
                if left_values.mean() != right_values.mean()
                else 1.0
            )
        else:
            test = ttest_ind(
                left_values,
                right_values,
                equal_var=False,
                nan_policy="omit",
            )
            p_value = test.pvalue
        if not np.isfinite(p_value) or p_value >= alpha:
            continue
        if left_values.mean() > right_values.mean():
            marks[left] += letters[right]
        elif right_values.mean() > left_values.mean():
            marks[right] += letters[left]
    row = {"Indicador": "Media"}
    row.update(marks)
    return pd.DataFrame([row])


def column_legend(columns: list[str]) -> pd.DataFrame:
    letters = _column_letters(columns)
    return pd.DataFrame(
        [
            {"Letra": letter, "Columna": column}
            for column, letter in letters.items()
        ]
    )


def insufficient_bases(
    summary: pd.DataFrame, min_base: int
) -> list[str]:
    if summary.empty or "base" not in summary.columns:
        return []
    bases = (
        summary[summary["banner"] != "Total"]
        .groupby("banner")["base"]
        .max()
    )
    return [
        str(banner)
        for banner, base in bases.items()
        if float(base) < min_base
    ]


def _column_letters(columns: list[str]) -> dict[str, str]:
    alphabet = list(string.ascii_uppercase)
    return {
        column: (
            alphabet[index]
            if index < len(alphabet)
            else f"A{index - len(alphabet) + 1}"
        )
        for index, column in enumerate(columns)
    }


def _comparison_pairs(
    categories: list[str],
    groups: list[list[str]] | None,
):
    selected_groups = groups or [categories]
    valid = set(categories)
    for group in selected_groups:
        members = [item for item in group if item in valid]
        for left_index, left in enumerate(members):
            for right in members[left_index + 1 :]:
                yield left, right
