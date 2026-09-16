from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from src.database.db_reader import list_tables


REQUIRED_REPORTER_TABLES = [
    "preguntas",
    "variables",
    "respondentes",
    "opciones",
    "configuracion_dashboard",
]

ANALYTIC_RESPONSE_TABLES = [
    "respuestas_long",
    "multirrespuesta_long",
    "escalas_long",
    "abiertas",
]


@dataclass(frozen=True)
class DatabaseValidation:
    ok: bool
    tables: list[str]
    missing_tables: list[str]
    message: str


def validate_reporter_database(db_path: Path) -> DatabaseValidation:
    """Validate that a SQLite file has the minimum reporter schema."""
    if not db_path.exists():
        return DatabaseValidation(
            ok=False,
            tables=[],
            missing_tables=[],
            message="El archivo no existe.",
        )
    try:
        with sqlite3.connect(db_path) as conn:
            quick_check = conn.execute("PRAGMA quick_check").fetchone()
    except sqlite3.Error as exc:
        return DatabaseValidation(
            ok=False,
            tables=[],
            missing_tables=[],
            message=f"No es una base SQLite válida: {exc}",
        )

    if not quick_check or quick_check[0] != "ok":
        return DatabaseValidation(
            ok=False,
            tables=[],
            missing_tables=[],
            message="SQLite reportó inconsistencias internas.",
        )

    tables = list_tables(db_path)
    table_set = set(tables)
    missing = [
        table
        for table in REQUIRED_REPORTER_TABLES
        if table not in table_set
    ]
    if missing:
        return DatabaseValidation(
            ok=False,
            tables=tables,
            missing_tables=missing,
            message=(
                "La base no contiene las tablas mínimas del "
                "reporteador."
            ),
        )

    if not any(table in table_set for table in ANALYTIC_RESPONSE_TABLES):
        return DatabaseValidation(
            ok=False,
            tables=tables,
            missing_tables=ANALYTIC_RESPONSE_TABLES,
            message=(
                "La base no contiene tablas de respuestas analizables."
            ),
        )

    return DatabaseValidation(
        ok=True,
        tables=tables,
        missing_tables=[],
        message="Base compatible con EXPLORA WEB REPORTER.",
    )
