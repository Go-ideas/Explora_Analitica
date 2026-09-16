from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import streamlit as st

from src.utils.constants import DATA_DIR


def session_root() -> Path:
    session_id = st.session_state.get("explora_session_id")
    if not session_id:
        session_id = uuid4().hex
        st.session_state.explora_session_id = session_id
    root = DATA_DIR / "sessions" / str(session_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def session_dir(name: str) -> Path:
    path = session_root() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def session_file(folder: str, filename: str) -> Path:
    return session_dir(folder) / filename
