from __future__ import annotations

import pandas as pd

from src.utils.constants import ID_CANDIDATES
from src.utils.text_utils import normalize_text


INVALID_TEXT_VALUES = {"", "nan", "none", "null", "na", "n/a"}
MAX_BANNER_FILTER_CATEGORIES = 50


def banner_filter_exclusion_reason(
    df_spss: pd.DataFrame,
    variable: object,
) -> str:
    """Return why a variable should not be used as banner/filter."""
    name = str(variable or "").strip()
    if not name:
        return "Variable vacía"
    if name not in df_spss.columns:
        return "Variable inexistente en la base SPSS"

    values = _valid_values(df_spss[name])
    valid_count = len(values)
    if valid_count == 0:
        return "Sin datos válidos"

    unique_count = int(values.nunique(dropna=True))
    if unique_count <= 1:
        return "Sin variación"
    if _looks_like_id(name):
        return "Variable tipo ID/folio"
    if unique_count > MAX_BANNER_FILTER_CATEGORIES:
        return "Alta cardinalidad"
    return ""


def is_safe_banner_filter_variable(
    df_spss: pd.DataFrame,
    variable: object,
) -> bool:
    return not banner_filter_exclusion_reason(df_spss, variable)


def _valid_values(series: pd.Series) -> pd.Series:
    values = series.dropna()
    if values.empty:
        return values
    text = values.astype(str).str.strip().str.casefold()
    return values.loc[~text.isin(INVALID_TEXT_VALUES)]


def _looks_like_id(variable: str) -> bool:
    normalized = normalize_text(variable)
    return any(candidate in normalized for candidate in ID_CANDIDATES)
