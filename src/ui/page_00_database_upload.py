from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd
import streamlit as st

from src.database.db_reader import read_table
from src.database.validation import validate_reporter_database
from src.utils.session_paths import session_file


def render() -> None:
    st.subheader("Cargar base del reporteador")
    st.caption(
        "Usa la base SQLite ya generada en la consola de procesamiento."
    )

    current_path = _current_db_path()
    if current_path:
        validation = validate_reporter_database(current_path)
        if validation.ok:
            st.success("Base cargada y compatible con el reporteador.")
            _render_database_summary(current_path, validation.tables)
        else:
            st.warning(validation.message)
            st.session_state.pop("db_path", None)

    uploaded = st.file_uploader(
        "Base analítica",
        type=["db", "sqlite", "sqlite3"],
        accept_multiple_files=False,
        help="Carga el archivo BD_Analitica_Explora.db generado por la consola.",
    )
    if uploaded is None:
        if not current_path:
            st.info("Carga `BD_Analitica_Explora.db` para habilitar el reporteador.")
        return

    destination = session_file("db", "BD_Analitica_Explora.db")
    with destination.open("wb") as output:
        shutil.copyfileobj(uploaded, output)

    validation = validate_reporter_database(destination)
    if not validation.ok:
        st.error(validation.message)
        if validation.missing_tables:
            st.caption(
                "Tablas faltantes: "
                + ", ".join(validation.missing_tables)
            )
        st.session_state.pop("db_path", None)
        return

    _reset_report_state_for_new_database()
    st.session_state.db_path = destination
    st.success("Base cargada correctamente.")
    _render_database_summary(destination, validation.tables)


def _current_db_path() -> Path | None:
    value = st.session_state.get("db_path")
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def _render_database_summary(db_path: Path, tables: list[str]) -> None:
    questions = _safe_table(db_path, "preguntas")
    respondents = _safe_table(db_path, "respondentes")
    config = _safe_table(db_path, "configuracion_dashboard")

    metrics = st.columns(4)
    metrics[0].metric("Preguntas", _row_count(questions))
    metrics[1].metric("Respondentes", _row_count(respondents))
    metrics[2].metric("Variables configuradas", _row_count(config))
    metrics[3].metric("Tablas SQLite", len(tables))

    with st.expander("Tablas detectadas", expanded=False):
        st.dataframe(
            pd.DataFrame({"Tabla": tables}),
            hide_index=True,
            width="stretch",
        )


def _safe_table(db_path: Path, table_name: str) -> pd.DataFrame:
    try:
        return read_table(db_path, table_name)
    except Exception:
        return pd.DataFrame()


def _row_count(frame: pd.DataFrame) -> int:
    return int(len(frame)) if frame is not None else 0


def _reset_report_state_for_new_database() -> None:
    for key in [
        "current_report",
        "saved_reports",
        "analytic_tables",
        "revision_excel_path",
        "datamap_final_path",
        "datamap_path",
        "df_spss",
        "metadata_spss",
        "review_datamap",
        "datamap_import_log",
    ]:
        st.session_state.pop(key, None)
