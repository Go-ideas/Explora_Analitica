from __future__ import annotations

import re


def normalize_metric_name(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("ponderado", "pond.").replace("ponderada", "pond.")
    aliases = {
        "frecuencia": "n",
        "porcentaje": "%",
        "n pond": "n ponderado",
        "n pond.": "n ponderado",
        "% pond": "% ponderado",
        "% pond.": "% ponderado",
        "desviacion estandar": "Desviación estándar",
        "desviación estándar": "Desviación estándar",
        "media": "Media",
        "top2box": "Top2Box",
        "bottom2box": "BottomBox",
        "nps": "NPS",
        "rm % respondentes": "RM % Respondentes",
        "rm % menciones": "RM % Menciones",
    }
    return aliases.get(text, str(value).strip())


def format_display_header(column: object) -> str:
    name = str(column)
    if " | " not in name:
        return name
    category, metric = name.rsplit(" | ", 1)
    if " / " in category or ": " in category:
        parts = []
        for part in category.split(" / "):
            parts.append(part.replace(" | ", " - "))
        category_display = "\n".join(parts)
    else:
        category_display = category.replace(" | ", "\n")
    return f"{category_display}\n{metric}"


def is_percentage_column(column: object) -> bool:
    name = str(column).lower()
    return (
        "%" in name
        or "porcentaje" in name
        or "top2box" in name
        or "bottombox" in name
    )


def is_count_column(column: object) -> bool:
    name = str(column).lower().replace("\n", " | ")
    return bool(
        re.search(r"(^|\|\s*)(n|base|frecuencia)(\s|$)", name)
    ) or "menciones" in name


def is_mean_column(column: object) -> bool:
    name = str(column).lower()
    return "media" in name or "desviación" in name or "desviacion" in name


def is_significance_column(column: object) -> bool:
    return "sig." in str(column).lower() or str(column).lower().endswith("sig")
