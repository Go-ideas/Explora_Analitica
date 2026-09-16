from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat


def read_spss(path: Path) -> tuple[pd.DataFrame, Any, dict[str, Any]]:
    """Read an SPSS .sav file and return data, metadata and a compact summary."""
    try:
        df, meta = pyreadstat.read_sav(str(path), apply_value_formats=False)
    except Exception as exc:
        raise RuntimeError(f"No se pudo leer el archivo SPSS: {exc}") from exc

    variable_labels = getattr(meta, "column_names_to_labels", {}) or {}
    value_labels = getattr(meta, "variable_value_labels", {}) or {}
    missing_ranges = getattr(meta, "missing_ranges", {}) or {}
    missing_user_values = getattr(meta, "missing_user_values", {}) or {}

    summary = {
        "n_casos": int(len(df)),
        "n_variables": int(len(df.columns)),
        "variables": list(df.columns),
        "variable_labels": variable_labels,
        "value_labels": value_labels,
        "missing_ranges": missing_ranges,
        "missing_user_values": missing_user_values,
    }
    return df, meta, summary


def get_variable_label(meta: Any, variable: str) -> str:
    labels = getattr(meta, "column_names_to_labels", {}) or {}
    return labels.get(variable, "")


def get_value_labels(meta: Any, variable: str) -> dict[Any, str]:
    labels = getattr(meta, "variable_value_labels", {}) or {}
    return labels.get(variable, {}) or {}


def get_missing_values(meta: Any, variable: str) -> set[Any]:
    user_values = getattr(meta, "missing_user_values", {}) or {}
    values = user_values.get(variable, []) or []
    return set(values)


def get_missing_ranges(
    meta: Any, variable: str
) -> list[dict[str, Any]]:
    ranges = getattr(meta, "missing_ranges", {}) or {}
    return ranges.get(variable, []) or []
