from __future__ import annotations

import re
from typing import Any, Iterable

import pandas as pd


FACTOR_CALCULATION_ORDER = [
    "n",
    "%",
    "n ponderado",
    "% ponderado",
    "Media",
    "Desviación estándar",
    "Top2Box",
    "BottomBox",
    "NPS",
    "RM % Respondentes",
    "RM % Menciones",
]


def recommended_factor_calculations(
    question_type: str,
    base_calculations: list[str],
    recommendations: pd.DataFrame | None,
) -> list[str]:
    if recommendations is None or recommendations.empty:
        return list(dict.fromkeys(base_calculations))
    text = " ".join(
        " ".join(
            recommendations[column]
            .fillna("")
            .astype(str)
            .tolist()
        )
        for column in (
            "Tipo_Factor_Recomendado",
            "Regla_Factor_Sugerida",
        )
        if column in recommendations
    ).lower()
    question = str(question_type or "").lower()

    if "nps" in text:
        selected = ["NPS"]
    elif question == "rm" or "multirrespuesta" in question:
        selected = ["n", "RM % Respondentes"]
        if "menciones" in text:
            selected.append("RM % Menciones")
    elif question in {"escala", "nps"} or "escala" in question:
        selected = []
        if any(token in text for token in ("media", "promedio", "score", "índice", "indice")):
            selected.append("Media")
        if "desvi" in text:
            selected.append("Desviación estándar")
        if "top2" in text or "top 2" in text:
            selected.append("Top2Box")
        if "bottom" in text:
            selected.append("BottomBox")
        if not selected:
            selected = list(base_calculations)
    elif "rango" in text:
        selected = ["n", "%"]
    else:
        selected = list(base_calculations)

    return [
        calculation
        for calculation in FACTOR_CALCULATION_ORDER
        if calculation in set(selected)
    ]


def parse_recommended_ranges(rule: object) -> list[dict[str, Any]]:
    text = str(rule or "")
    rows = []
    for segment in re.split(r"[,;]", text):
        interval = re.search(
            r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)",
            segment,
        )
        if interval:
            lower = float(interval.group(1))
            upper = float(interval.group(2))
            rows.append(
                {
                    "Incluir": True,
                    "Etiqueta": _range_label(lower, upper),
                    "Mínimo": lower,
                    "Máximo": upper,
                }
            )
            continue
        open_ended = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:\+|o\s+m[aá]s)",
            segment,
            flags=re.IGNORECASE,
        )
        if open_ended:
            lower = float(open_ended.group(1))
            rows.append(
                {
                    "Incluir": True,
                    "Etiqueta": f"{_number_text(lower)}+",
                    "Mínimo": lower,
                    "Máximo": None,
                }
            )
    return rows


def validate_ranges(
    rows: pd.DataFrame | Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    frame = (
        rows.copy()
        if isinstance(rows, pd.DataFrame)
        else pd.DataFrame(list(rows))
    )
    if frame.empty:
        raise ValueError("Agrega al menos un rango.")
    if "Incluir" in frame:
        frame = frame[frame["Incluir"].fillna(False).astype(bool)]
    normalized = []
    for _, row in frame.iterrows():
        label = str(row.get("Etiqueta") or "").strip()
        lower = _optional_number(row.get("Mínimo"))
        upper = _optional_number(row.get("Máximo"))
        if not label:
            raise ValueError("Todos los rangos necesitan etiqueta.")
        if lower is None and upper is None:
            raise ValueError(
                f"El rango {label} necesita un límite."
            )
        if (
            lower is not None
            and upper is not None
            and lower > upper
        ):
            raise ValueError(
                f"El mínimo supera al máximo en {label}."
            )
        normalized.append(
            {
                "Incluir": True,
                "Etiqueta": label,
                "Mínimo": lower,
                "Máximo": upper,
            }
        )
    if not normalized:
        raise ValueError("Activa al menos un rango.")
    labels = [row["Etiqueta"] for row in normalized]
    if len(labels) != len(set(labels)):
        raise ValueError("Las etiquetas de rango deben ser únicas.")

    normalized.sort(
        key=lambda row: (
            float("-inf")
            if row["Mínimo"] is None
            else row["Mínimo"]
        )
    )
    previous_upper = None
    previous_label = ""
    for index, row in enumerate(normalized):
        lower = row["Mínimo"]
        if index and (
            previous_upper is None
            or lower is None
            or lower <= previous_upper
        ):
            raise ValueError(
                f"Los rangos {previous_label} y "
                f"{row['Etiqueta']} se traslapan."
            )
        previous_upper = row["Máximo"]
        previous_label = row["Etiqueta"]
    return normalized


def apply_numeric_ranges(
    series: pd.Series,
    ranges: pd.DataFrame | Iterable[dict[str, Any]],
) -> pd.Series:
    validated = validate_ranges(ranges)
    numeric = pd.to_numeric(series, errors="coerce")
    result = pd.Series(pd.NA, index=series.index, dtype="object")
    for row in validated:
        mask = numeric.notna()
        if row["Mínimo"] is not None:
            mask &= numeric >= row["Mínimo"]
        if row["Máximo"] is not None:
            mask &= numeric <= row["Máximo"]
        result.loc[mask] = row["Etiqueta"]
    return result


def range_preview(
    series: pd.Series,
    ranges: pd.DataFrame | Iterable[dict[str, Any]],
) -> pd.DataFrame:
    derived = apply_numeric_ranges(series, ranges)
    display = derived.fillna("(Sin dato o fuera de rango)")
    counts = display.value_counts(dropna=False)
    total = len(display)
    return pd.DataFrame(
        {
            "Rango": counts.index.astype(str),
            "Frecuencia": counts.values.astype(int),
            "%": (
                counts.values / total * 100
                if total
                else counts.values.astype(float)
            ),
        }
    )


def _optional_number(value: object) -> float | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)


def _range_label(lower: float, upper: float) -> str:
    return f"{_number_text(lower)}-{_number_text(upper)}"


def _number_text(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"
