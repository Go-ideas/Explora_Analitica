from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.constants import PROCESSED_DIR, RAW_DIR
from src.utils.text_utils import find_column, normalize_text


ADDITIONAL_SECTION = (
    "Variables adicionales / no documentadas en cuestionario"
)


def resolve_datamap_paths(
    paths: Path | str | Iterable[Path | str] | None = None,
) -> list[Path]:
    requested: list[Path | str] = []
    if paths is None:
        requested.extend(
            [
                PROCESSED_DIR / "Datamap_Final.xlsx",
                RAW_DIR / "Datamap_Validado.xlsx",
            ]
        )
    else:
        if isinstance(paths, (str, Path)):
            requested.append(paths)
        else:
            requested.extend(paths)
    result = []
    seen = set()
    for value in requested:
        path = Path(value)
        key = str(path.resolve()) if path.exists() else str(path)
        if path.exists() and key not in seen:
            result.append(path)
            seen.add(key)
    return result


def order_question_catalog(
    questions: pd.DataFrame,
    datamap_paths: Path
    | str
    | Iterable[Path | str]
    | None = None,
) -> pd.DataFrame:
    if questions is None or questions.empty:
        return questions.copy()

    work = questions.copy().reset_index(drop=True)
    work["_original_order"] = range(len(work))
    metadata, documented = _question_metadata(
        resolve_datamap_paths(datamap_paths)
    )

    rows = []
    for _, row in work.iterrows():
        question_id = str(row.get("pregunta_id", "")).strip()
        info = metadata.get(question_id, {})
        documented_question = (
            question_id in documented if documented else True
        )
        additional = not documented_question
        if _explicit_no(
            info.get("mostrar_en_menu_reporter")
            or _row_value(
                row,
                [
                    "Mostrar_En_Menu_Reporteador",
                    "mostrar_en_menu_reporter",
                ],
            )
        ):
            continue
        if _looks_technical(row, question_id):
            continue

        section = (
            info.get("seccion")
            or info.get("grupo")
            or _clean_value(row.get("seccion_reporter"))
            or "Sin sección"
        )
        if additional:
            section = ADDITIONAL_SECTION

        number = (
            info.get("numero")
            or _clean_value(row.get("numero_pregunta"))
            or question_id
        )
        text = (
            info.get("texto")
            or _clean_value(row.get("texto_pregunta"))
            or question_id
        )
        order = _row_priority_order(row)
        if order is None:
            order = info.get("orden")
        if order is None:
            order = float(row["_original_order"])

        enriched = row.to_dict()
        enriched.update(
            {
                "seccion_reporter": section,
                "numero_pregunta_reporter": number,
                "orden_reporter": float(order),
                "es_variable_adicional": additional,
                "menu_label": (
                    f"{section} | {number} | {_short_text(text)}"
                ),
            }
        )
        rows.append(enriched)

    if not rows:
        return work.drop(columns=["_original_order"])
    result = pd.DataFrame(rows)
    return (
        result.sort_values(
            [
                "es_variable_adicional",
                "orden_reporter",
                "_original_order",
            ],
            kind="stable",
        )
        .drop(columns=["_original_order"])
        .reset_index(drop=True)
    )


def _question_metadata(
    paths: list[Path],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    candidates: list[tuple[int, int, pd.Series, bool]] = []
    position = 0
    for path in paths:
        try:
            sheets = pd.read_excel(
                path, sheet_name=None, engine="openpyxl"
            )
        except Exception:
            continue
        for rank, names, documented in [
            (
                1,
                ["13_Orden_Menu_Reporteador"],
                True,
            ),
            (
                2,
                ["10_Datamap_Corregido"],
                True,
            ),
            (
                3,
                ["08_Clasificacion_Analitica"],
                False,
            ),
        ]:
            for name in names:
                frame = sheets.get(name)
                if frame is None or frame.empty:
                    continue
                frame_is_questionnaire = documented and (
                    rank == 1
                    or find_column(
                        frame.columns,
                        [
                            "Seccion_Cuestionario",
                            "Sección",
                            "Seccion",
                            "Bloque",
                        ],
                    )
                    is not None
                )
                for _, row in frame.iterrows():
                    candidates.append(
                        (
                            rank,
                            position,
                            row,
                            frame_is_questionnaire,
                        )
                    )
                    position += 1

    metadata: dict[str, dict[str, Any]] = {}
    documented_ids: set[str] = set()
    for rank, position, row, is_documented in sorted(candidates):
        question_id = _question_id(row)
        if not question_id:
            continue
        if is_documented:
            documented_ids.add(question_id)
        info = metadata.setdefault(question_id, {})
        values = {
            "orden": _first_numeric(
                row,
                [
                    "Orden_Cuestionario",
                    "orden_cuestionario",
                    "orden_reporte",
                    "Orden_Reporte",
                    "Orden",
                ],
            ),
            "seccion": _row_value(
                row,
                [
                    "Seccion_Cuestionario",
                    "Sección_Cuestionario",
                    "Sección",
                    "Seccion",
                    "Bloque",
                ],
            ),
            "grupo": _row_value(
                row,
                [
                    "Grupo_Menu_Reporteador",
                    "grupo_menu_reporter",
                ],
            ),
            "numero": _row_value(
                row,
                [
                    "Numero_Pregunta",
                    "Número_Pregunta",
                    "Pregunta_ID",
                    "pregunta_id",
                    "Pregunta asociada",
                ],
            ),
            "texto": _row_value(
                row,
                [
                    "Texto_Pregunta",
                    "texto_pregunta",
                    "Variable label",
                    "label",
                ],
            ),
            "mostrar_en_menu_reporter": _row_value(
                row,
                [
                    "Mostrar_En_Menu_Reporteador",
                    "mostrar_en_menu_reporter",
                ],
            ),
        }
        if values["orden"] is None:
            values["orden"] = float(position)
        for key, value in values.items():
            if key not in info and _clean_value(value):
                info[key] = value
        info["_rank"] = min(rank, info.get("_rank", rank))
    return metadata, documented_ids


def _question_id(row: pd.Series) -> str:
    value = _row_value(
        row,
        [
            "Pregunta_ID",
            "pregunta_id",
            "Numero_Pregunta",
            "Pregunta asociada",
            "question_id",
        ],
    )
    if not value:
        value = _row_value(
            row,
            ["Variable", "variable", "Variable_SPSS"],
        )
    return _clean_value(value)


def _row_priority_order(row: pd.Series) -> float | None:
    return _first_numeric(
        row,
        [
            "Orden_Cuestionario",
            "orden_cuestionario",
            "orden_reporte",
        ],
    )


def _first_numeric(
    row: pd.Series, candidates: list[str]
) -> float | None:
    value = _row_value(row, candidates)
    if not _clean_value(value):
        return None
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(numeric) if pd.notna(numeric) else None


def _row_value(row: pd.Series, candidates: list[str]) -> Any:
    column = find_column(row.index, candidates)
    return row.get(column) if column else None


def _looks_technical(row: pd.Series, question_id: str) -> bool:
    classification = normalize_text(
        row.get("clasificacion_analitica", "")
    )
    if any(
        token in classification
        for token in (
            "variable_tecnica",
            "control_de_calidad",
            "no_usar",
        )
    ):
        return True
    text = normalize_text(
        " ".join(
            [
                question_id,
                str(row.get("texto_pregunta", "")),
            ]
        )
    )
    question_name = normalize_text(question_id)
    operational_names = {
        "base",
        "total",
        "checa",
        "check",
        "final",
        "nombre",
        "name",
    }
    if (
        question_name in operational_names
        or question_name.startswith(("fil_", "rev_", "status_"))
    ):
        return True
    return any(
        token in text
        for token in (
            "folio",
            "duracion",
            "duration",
            "fecha",
            "token",
            "registro",
            "identificador",
            "nombre",
            "telefono",
            "phone",
            "email",
            "correo",
        )
    )


def _explicit_no(value: Any) -> bool:
    return normalize_text(value) in {
        "0",
        "no",
        "false",
        "falso",
        "excluir",
        "no_mostrar",
    }


def _clean_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text


def _short_text(value: Any, limit: int = 120) -> str:
    text = " ".join(_clean_value(value).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"
