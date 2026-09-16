from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import Any, Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class FrequencySummary:
    total: int
    valid: int
    missing: int
    observed_categories: int
    unlabeled_codes: int
    unlabeled_observations: int
    zero_frequency_labels: int


def build_frequency_profile(
    series: pd.Series,
    value_labels: Mapping[Any, str] | None = None,
    missing_values: Iterable[Any] | None = None,
    missing_ranges: Iterable[Mapping[str, Any]] | None = None,
) -> tuple[pd.DataFrame, FrequencySummary]:
    """Build a simple frequency table, including labels without observations."""
    labels = value_labels or {}
    user_missing = list(missing_values or [])
    user_missing_ranges = list(missing_ranges or [])

    observed: dict[tuple[str, Any], dict[str, Any]] = {}
    for value, frequency in series.value_counts(
        dropna=False, sort=False
    ).items():
        key = _value_key(value)
        observed[key] = {
            "raw_value": value,
            "frequency": int(frequency),
        }

    normalized_labels = {
        _value_key(code): (code, str(label))
        for code, label in labels.items()
    }
    rows: list[dict[str, Any]] = []

    for key, (code, label) in normalized_labels.items():
        item = observed.pop(
            key, {"raw_value": code, "frequency": 0}
        )
        rows.append(
            _frequency_row(
                raw_value=item["raw_value"],
                frequency=item["frequency"],
                label=label,
                has_label=bool(label.strip()),
                missing_values=user_missing,
                missing_ranges=user_missing_ranges,
            )
        )

    for item in observed.values():
        rows.append(
            _frequency_row(
                raw_value=item["raw_value"],
                frequency=item["frequency"],
                label="",
                has_label=False,
                missing_values=user_missing,
                missing_ranges=user_missing_ranges,
            )
        )

    valid = sum(
        row["Frecuencia"]
        for row in rows
        if not row["_es_perdido"]
    )
    for row in rows:
        if row["_es_perdido"]:
            row["% válido"] = None
        else:
            row["% válido"] = (
                row["Frecuencia"] / valid * 100 if valid else 0.0
            )

    table = pd.DataFrame(
        [
            {
                "Código": row["Código"],
                "Value Label": row["Value Label"],
                "Frecuencia": row["Frecuencia"],
                "% válido": row["% válido"],
                "Estado": row["Estado"],
            }
            for row in rows
        ]
    )

    summary = FrequencySummary(
        total=int(len(series)),
        valid=int(valid),
        missing=int(
            sum(
                row["Frecuencia"]
                for row in rows
                if row["_es_perdido"]
            )
        ),
        observed_categories=sum(
            1
            for row in rows
            if row["Frecuencia"] > 0 and not row["_es_perdido"]
        ),
        unlabeled_codes=sum(
            1
            for row in rows
            if row["Frecuencia"] > 0
            and not row["_es_perdido"]
            and not row["_tiene_etiqueta"]
        ),
        unlabeled_observations=sum(
            row["Frecuencia"]
            for row in rows
            if row["Frecuencia"] > 0
            and not row["_es_perdido"]
            and not row["_tiene_etiqueta"]
        ),
        zero_frequency_labels=sum(
            1
            for row in rows
            if row["Frecuencia"] == 0 and row["_tiene_etiqueta"]
        ),
    )
    return table, summary


def _frequency_row(
    raw_value: Any,
    frequency: int,
    label: str,
    has_label: bool,
    missing_values: list[Any],
    missing_ranges: list[Mapping[str, Any]],
) -> dict[str, Any]:
    system_missing = _is_missing(raw_value)
    defined_missing = (
        not system_missing
        and _is_defined_missing(
            raw_value, missing_values, missing_ranges
        )
    )
    is_missing = system_missing or defined_missing

    if system_missing:
        status = "Perdido del sistema"
        display_label = "(Sin respuesta)"
    elif defined_missing:
        status = "Perdido definido"
        display_label = label or "(Valor perdido)"
    elif not has_label and frequency > 0:
        status = "Sin Value Label"
        display_label = "(Sin etiqueta)"
    elif frequency == 0:
        status = "Sin casos"
        display_label = label
    else:
        status = ""
        display_label = label

    return {
        "Código": _format_code(raw_value),
        "Value Label": display_label,
        "Frecuencia": int(frequency),
        "% válido": None,
        "Estado": status,
        "_es_perdido": is_missing,
        "_tiene_etiqueta": has_label,
    }


def _is_defined_missing(
    value: Any,
    missing_values: list[Any],
    missing_ranges: list[Mapping[str, Any]],
) -> bool:
    key = _value_key(value)
    if any(key == _value_key(item) for item in missing_values):
        return True

    for item in missing_ranges:
        if not isinstance(item, Mapping):
            continue
        lower = item.get("lo")
        upper = item.get("hi")
        if lower is None or upper is None:
            continue
        try:
            if lower <= value <= upper:
                return True
        except TypeError:
            continue
    return False


def _value_key(value: Any) -> tuple[str, Any]:
    if _is_missing(value):
        return ("missing", None)
    if isinstance(value, Number) and not isinstance(value, bool):
        return ("number", float(value))
    return ("text", str(value).strip())


def _format_code(value: Any) -> str:
    if _is_missing(value):
        return "(vacío)"
    if isinstance(value, Number) and not isinstance(value, bool):
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:g}"
    return str(value)


def _is_missing(value: Any) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
