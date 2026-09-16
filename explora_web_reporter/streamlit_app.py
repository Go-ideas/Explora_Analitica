from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import streamlit as st

from src.database.validation import validate_reporter_database
from src.ui import page_04_reporter, page_06_export
from src.utils.constants import DATA_DIR
from src.utils.file_utils import ensure_data_dirs, safe_filename


SESSION_DB_DIR = DATA_DIR / "sessions"


st.set_page_config(
    page_title="EXPLORA REPORTER",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    ensure_data_dirs()
    SESSION_DB_DIR.mkdir(parents=True, exist_ok=True)
    _apply_styles()

    with st.sidebar:
        st.markdown("## EXPLORA")
        st.caption("REPORTER")
        uploaded_db = st.file_uploader(
            "Base analítica SQLite",
            type=["db", "sqlite", "sqlite3"],
            accept_multiple_files=False,
        )
        if uploaded_db is not None:
            _activate_uploaded_database(uploaded_db)
        _render_database_status()

    st.title("EXPLORA REPORTER")
    db_path = _current_db_path()
    if db_path is None:
        _render_upload_state()
        return

    validation = validate_reporter_database(db_path)
    if not validation.ok:
        st.error(validation.message)
        if validation.missing_tables:
            st.caption(
                "Tablas faltantes: "
                + ", ".join(validation.missing_tables)
            )
        return

    analysis_tab, export_tab = st.tabs(["Análisis", "Exportar"])
    with analysis_tab:
        page_04_reporter.render()
    with export_tab:
        page_06_export.render()


def _activate_uploaded_database(uploaded_db) -> None:
    content = uploaded_db.getvalue()
    fingerprint = sha256(content).hexdigest()
    if (
        st.session_state.get("uploaded_db_fingerprint")
        == fingerprint
        and _current_db_path() is not None
    ):
        return

    _discard_session_database()
    file_stem = Path(safe_filename(uploaded_db.name)).stem or "base"
    db_path = SESSION_DB_DIR / f"{file_stem}_{uuid4().hex}.db"
    db_path.write_bytes(content)

    validation = validate_reporter_database(db_path)
    if not validation.ok:
        db_path.unlink(missing_ok=True)
        st.session_state.upload_error = validation.message
        st.session_state.pop("db_path", None)
        st.session_state.pop("uploaded_db_name", None)
        st.session_state.pop("uploaded_db_fingerprint", None)
        return

    _reset_analysis_state()
    st.session_state.db_path = db_path
    st.session_state.uploaded_db_name = uploaded_db.name
    st.session_state.uploaded_db_fingerprint = fingerprint
    st.session_state.upload_error = None


def _current_db_path() -> Path | None:
    value = st.session_state.get("db_path")
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def _discard_session_database() -> None:
    path = _current_db_path()
    if path is not None and path.parent == SESSION_DB_DIR:
        path.unlink(missing_ok=True)


def _reset_analysis_state() -> None:
    for key in [
        "current_report",
        "saved_reports",
        "analytic_tables",
        "revision_excel_path",
        "datamap_final_path",
        "datamap_path",
        "df_spss",
        "meta_spss",
    ]:
        st.session_state.pop(key, None)


def _render_database_status() -> None:
    error = st.session_state.get("upload_error")
    if error:
        st.error(error)
    db_path = _current_db_path()
    st.divider()
    if db_path is None:
        st.caption("Base pendiente")
        return

    validation = validate_reporter_database(db_path)
    if validation.ok:
        st.success("Base cargada")
        st.caption(st.session_state.get("uploaded_db_name", db_path.name))
        st.metric("Tablas disponibles", len(validation.tables))
    else:
        st.warning("Base no compatible")
    if st.button("Quitar base", width="stretch"):
        _discard_session_database()
        _reset_analysis_state()
        for key in [
            "db_path",
            "uploaded_db_name",
            "uploaded_db_fingerprint",
            "upload_error",
        ]:
            st.session_state.pop(key, None)
        st.rerun()


def _render_upload_state() -> None:
    st.info(
        "Sube el archivo BD_Analitica_Explora.db generado por "
        "EXPLORA BUILDER para iniciar el análisis."
    )


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1500px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }
        h1 {
            color: #17324d;
            font-size: 1.75rem !important;
            letter-spacing: 0 !important;
            margin-bottom: 1rem !important;
        }
        h2, h3 {
            color: #17324d;
            letter-spacing: 0 !important;
        }
        [data-testid="stMetric"] {
            border: 1px solid #dfe7eb;
            border-top: 3px solid #176b87;
            border-radius: 6px;
            padding: 0.75rem;
            background: #ffffff;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid #dfe7eb;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #dfe7eb;
        }
        .stButton > button[kind="primary"]:not(:disabled) {
            background-color: #176b87;
            border-color: #176b87;
        }
        div[data-testid="stExpander"] {
            border-color: #dfe7eb;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
