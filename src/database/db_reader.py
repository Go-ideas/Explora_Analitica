from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd


def list_tables(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    with closing(sqlite3.connect(db_path)) as conn:
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        return pd.read_sql_query(query, conn)["name"].tolist()


def read_table(db_path: Path, table_name: str) -> pd.DataFrame:
    with closing(sqlite3.connect(db_path)) as conn:
        return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)


def read_sql(db_path: Path, query: str, params: tuple | None = None) -> pd.DataFrame:
    with closing(sqlite3.connect(db_path)) as conn:
        return pd.read_sql_query(query, conn, params=params or ())
