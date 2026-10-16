from __future__ import annotations

import pandas as pd
import math

from src.utils.text_utils import normalize_text


def scale_bounds(item: pd.Series, labels: dict) -> tuple[float | None, float | None]:
    """Use the declared scale, never the extrema observed in this sample."""
    low = pd.to_numeric(item.get("escala_min"), errors="coerce")
    high = pd.to_numeric(item.get("escala_max"), errors="coerce")
    declared = any(
        pd.notna(item.get(field)) and str(item.get(field)).strip() != ''
        for field in ('escala_min', 'escala_max')
    )
    if declared:
        if pd.isna(low) or pd.isna(high) or not math.isfinite(low) or not math.isfinite(high) or low >= high:
            raise ValueError(f"Límites de escala incompletos o inválidos para {item.get('variable')}.")
        return float(low), float(high)
    if "nps" in normalize_text(f"{item.get('tipo_pregunta', '')} {item.get('tipo_calculo', '')}"):
        return 0.0, 10.0
    codes = pd.to_numeric(pd.Series(list(labels), dtype=object), errors="coerce")
    if len(codes) >= 2 and codes.notna().all():
        ordered = sorted(set(codes.astype(float)))
        if all(b - a == 1 for a, b in zip(ordered, ordered[1:])):
            return ordered[0], ordered[-1]
    # A mean can still be computed; boxes remain unavailable without a scale.
    return None, None
