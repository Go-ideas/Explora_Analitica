from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from .constants import DB_DIR, EXPORTS_DIR, PROCESSED_DIR, RAW_DIR


def ensure_data_dirs() -> None:
    for folder in (RAW_DIR, PROCESSED_DIR, DB_DIR, EXPORTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    allowed = []
    for char in filename:
        allowed.append(char if char.isalnum() or char in "._- " else "_")
    clean = "".join(allowed).strip()
    return clean or "archivo"


def save_uploaded_file(uploaded_file: BinaryIO, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    name = safe_filename(getattr(uploaded_file, "name", "archivo"))
    destination = destination_dir / name
    with destination.open("wb") as output:
        shutil.copyfileobj(uploaded_file, output)
    return destination


def file_bytes(path: Path) -> bytes:
    return path.read_bytes()
