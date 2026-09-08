from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def write_tables(db_path: Path, tables: dict[str, pd.DataFrame]) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with closing(sqlite3.connect(db_path)) as conn:
        for table_name, df in tables.items():
            safe_df = df.copy() if df is not None else pd.DataFrame()
            if len(safe_df.columns) == 0:
                conn.execute(
                    f'CREATE TABLE IF NOT EXISTS "{table_name}" '
                    "(_empty INTEGER)"
                )
            else:
                safe_df.to_sql(
                    table_name, conn, if_exists="replace", index=False
                )
        _create_indexes(conn)
        conn.commit()
    return db_path


def _create_indexes(conn: sqlite3.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_resp_long_pregunta ON respuestas_long(pregunta_id)",
        "CREATE INDEX IF NOT EXISTS idx_resp_long_pregunta_id ON respuestas_long(pregunta_id, id_respondente)",
        "CREATE INDEX IF NOT EXISTS idx_rm_pregunta ON multirrespuesta_long(pregunta_id)",
        "CREATE INDEX IF NOT EXISTS idx_rm_pregunta_id ON multirrespuesta_long(pregunta_id, id_respondente)",
        "CREATE INDEX IF NOT EXISTS idx_escala_pregunta ON escalas_long(pregunta_id)",
        "CREATE INDEX IF NOT EXISTS idx_escala_pregunta_id ON escalas_long(pregunta_id, id_respondente)",
        "CREATE INDEX IF NOT EXISTS idx_abiertas_pregunta ON abiertas(pregunta_id)",
        "CREATE INDEX IF NOT EXISTS idx_abiertas_pregunta_id ON abiertas(pregunta_id, id_respondente)",
    ]
    for statement in indexes:
        try:
            conn.execute(statement)
        except sqlite3.Error:
            pass
