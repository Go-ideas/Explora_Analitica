from __future__ import annotations

import sqlite3
from pathlib import Path

from src.database.validation import validate_reporter_database


def _create_minimal_reporter_database(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        for table_name in [
            "preguntas",
            "variables",
            "respondentes",
            "opciones",
            "configuracion_dashboard",
            "respuestas_long",
        ]:
            conn.execute(f'CREATE TABLE "{table_name}" (id INTEGER)')


def test_validate_reporter_database_accepts_builder_database(tmp_path) -> None:
    db_path = tmp_path / "synthetic_reporter.db"
    _create_minimal_reporter_database(db_path)

    result = validate_reporter_database(db_path)

    assert result.ok
    assert result.missing_tables == []


def test_validate_reporter_database_rejects_missing_schema(tmp_path) -> None:
    db_path = tmp_path / "incompleta.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE preguntas (pregunta_id TEXT)")

    result = validate_reporter_database(db_path)

    assert not result.ok
    assert "variables" in result.missing_tables


def test_validate_reporter_database_rejects_non_sqlite(tmp_path) -> None:
    db_path = tmp_path / "archivo.db"
    db_path.write_text("no soy sqlite", encoding="utf-8")

    result = validate_reporter_database(db_path)

    assert not result.ok
    assert "SQLite" in result.message
