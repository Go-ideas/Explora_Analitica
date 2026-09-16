from __future__ import annotations

import ast
import unittest
from pathlib import Path


FORBIDDEN_IMPORT_ROOTS = {
    "plotly",
    "streamlit",
    "openpyxl",
    "xlsxwriter",
    "pywin32",
}
FORBIDDEN_SRC_IMPORTS = {
    "src.ui",
    "src.export",
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class ContractRendererNeutralityTests(unittest.TestCase):
    def test_contracts_and_core_interface_are_renderer_neutral(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src"
        files = [
            *(root / "contracts").glob("*.py"),
            root / "analytics_core" / "interface.py",
            root / "analytics_core" / "mode.py",
            root / "analytics_core" / "runner.py",
            root / "analytics_core" / "universe.py",
            root / "analytics_core" / "weights.py",
        ]
        for path in files:
            with self.subTest(path=path.name):
                imports = imported_modules(path)
                roots = {module.split(".")[0] for module in imports}
                self.assertFalse(roots & FORBIDDEN_IMPORT_ROOTS)
                self.assertFalse(
                    any(
                        module == forbidden
                        or module.startswith(f"{forbidden}.")
                        for module in imports
                        for forbidden in FORBIDDEN_SRC_IMPORTS
                    )
                )

    def test_legacy_adapter_is_the_only_core_module_importing_reporter(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "analytics_core"
        reporter_importers = [
            path.name
            for path in root.glob("*.py")
            if any(
                module == "src.reporter.tabulator"
                or module.startswith("src.reporter")
                for module in imported_modules(path)
            )
        ]
        self.assertEqual(reporter_importers, ["legacy_adapter.py"])


if __name__ == "__main__":
    unittest.main()
