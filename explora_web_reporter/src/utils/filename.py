from __future__ import annotations

import re


def safe_filename(base: str, suffix: str, max_len: int = 40) -> str:
    """Build a short cross-platform filename from a stable id and suffix."""
    clean_base = re.sub(r'[<>:"/\\|?*]+', "_", str(base or "")).strip(" ._")
    clean_base = re.sub(r"\s+", "_", clean_base)

    clean_suffix = re.sub(r'[<>:"/\\|?*]+', "_", str(suffix or "")).strip(" ._")
    clean_suffix = re.sub(r"\s+", "_", clean_suffix)

    if "." in clean_suffix:
        stem, extension = clean_suffix.rsplit(".", 1)
        extension = f".{extension}"
    else:
        stem, extension = clean_suffix, ""

    clean_base = clean_base[:max_len] or "Explora"
    stem = stem[:max_len] if len(stem) > max_len else stem
    return f"{clean_base}_{stem}{extension}" if stem else f"{clean_base}{extension}"
