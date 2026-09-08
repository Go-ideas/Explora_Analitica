from __future__ import annotations

import streamlit as st

from src.ui import (
    page_00_database_upload,
    page_04_reporter,
    page_06_export,
)
from src.utils.file_utils import ensure_data_dirs


st.set_page_config(
    page_title="EXPLORA WEB REPORTER",
    layout="wide",
    initial_sidebar_state="auto",
)
ensure_data_dirs()


PAGES = {
    "1. Cargar base": page_00_database_upload.render,
    "2. Reporteador": page_04_reporter.render,
    "3. Exportar": page_06_export.render,
}


def main() -> None:
    _apply_styles()
    with st.sidebar:
        st.markdown("## EXPLORA")
        st.caption("WEB REPORTER")
        db_ready = bool(st.session_state.get("db_path"))
        page = st.radio(
            "Navegación",
            list(PAGES),
            index=1 if db_ready else 0,
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(
            "Base del reporteador disponible"
            if db_ready
            else "Carga la base generada"
        )
        if st.button("Limpiar sesión", width="stretch"):
            _clear_session()
            st.rerun()

    st.title("EXPLORA WEB REPORTER")
    PAGES[page]()


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1500px;
            padding-top: 1.6rem;
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


def _clear_session() -> None:
    for key in list(st.session_state):
        del st.session_state[key]


if __name__ == "__main__":
    main()
