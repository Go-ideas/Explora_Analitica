"""Add the generic Gate 39 significance surface to the qualified Master."""
from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.workbook.defined_name import DefinedName


def build(seed: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("Production Master destination must not exist")
    workbook = load_workbook(seed, keep_vba=True, keep_links=True)
    try:
        sheet = workbook["presentation"]
        sheet["E2"] = "SIGNIFICANCE_MARKER"
        sheet["H2"] = "SIGNIFICANCE_STATUS"
        names = {
            "ProductionSignificanceSlot": "'presentation'!$E$2",
            "ProductionSignificanceStatus": "'presentation'!$H$2",
        }
        for name, target in names.items():
            if name in workbook.defined_names:
                del workbook.defined_names[name]
            workbook.defined_names.add(DefinedName(name, attr_text=target))
        workbook.properties.title = "EXPLORA Production Master V1.1"
        workbook.properties.subject = "Generic canonical result and significance presentation"
        workbook.save(output)
    finally:
        workbook.close()
        workbook.vba_archive.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.seed, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
