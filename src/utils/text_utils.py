from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import pandas as pd


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalized = {normalize_text(col): col for col in columns}
    candidate_norms = [normalize_text(candidate) for candidate in candidates]
    for candidate in candidate_norms:
        if candidate in normalized:
            return normalized[candidate]
    for candidate in candidate_norms:
        for norm, original in normalized.items():
            if candidate and (candidate in norm or norm in candidate):
                return original
    return None


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = normalize_text(value)
    return text in {
        "1",
        "si",
        "s",
        "yes",
        "y",
        "true",
        "verdadero",
        "x",
        "usar",
        "incluir",
        "incluido",
        "recomendado",
        "recomendada",
        "dashboard",
        "aplica",
    }


def clean_open_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def first_existing(columns: Iterable[str], names: Iterable[str]) -> str | None:
    lookup = {normalize_text(col): col for col in columns}
    for name in names:
        found = lookup.get(normalize_text(name))
        if found:
            return found
    return None
