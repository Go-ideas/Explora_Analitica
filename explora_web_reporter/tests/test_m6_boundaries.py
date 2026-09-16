from __future__ import annotations

from pathlib import Path


def test_m5_modules_remain_renderer_neutral() -> None:
    for path in [
        Path("src/analytics_core/results.py"),
        Path("src/analytics_core/result_identity.py"),
        Path("src/analytics_core/serialization.py"),
        Path("src/analytics_core/formula_registry.py"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "streamlit" not in text.lower()
        assert "plotly" not in text.lower()
        assert "web_canonical" not in text


def test_web_canonical_adapter_does_not_import_legacy_analytics() -> None:
    text = Path("src/web_canonical/adapter.py").read_text(encoding="utf-8")
    forbidden = [
        "src.reporter.tabulator",
        "src.reporter.calculations",
        "src.reporter.filters",
        "src.reporter.banners",
        "src.reporter.significance",
        "src.database.db_reader",
    ]
    for item in forbidden:
        assert item not in text


def test_no_sqlite_or_excel_migration_in_m6_modules() -> None:
    for path in Path("src/web_canonical").glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "sqlite" not in text
        assert "openpyxl" not in text
        assert "xlsxwriter" not in text
