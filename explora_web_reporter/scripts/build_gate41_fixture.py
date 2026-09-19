"""Build the deterministic, non-customer Gate 41 XLSM qualification fixture."""
from pathlib import Path
import json

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.workbook.defined_name import DefinedName

import hashlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/m7b/generic_macro_renderer_fixture.xlsm"
TARGET_DIR = ROOT / "tests/fixtures/gate41"
TARGET = TARGET_DIR / "dynamic_region_runtime_fixture.xlsm"


def build():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    workbook = load_workbook(SOURCE, keep_vba=True)
    try:
        for name in ("dynamic_table", "dynamic_range", "collision_fixture"):
            if name in workbook.sheetnames:
                del workbook[name]
        table_sheet = workbook.create_sheet("dynamic_table")
        table_sheet.append(["estimate", "status", "display"])
        table_sheet.append([None, None, "=IF(A2=\"\",\"\",TEXT(A2,\"0.0%\"))"])
        table = Table(displayName="Gate41DynamicTable", ref="A1:A2")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        table_sheet.add_table(table)
        range_sheet = workbook.create_sheet("dynamic_range")
        for row in range(1, 7):
            for col in range(1, 5):
                cell = range_sheet.cell(row, col)
                cell.font = Font(name="Calibri", size=11, color="FF1F1F1F")
                cell.fill = PatternFill("solid", fgColor="FFD9EAF7")
                cell.alignment = Alignment(horizontal="center")
                cell.protection = Protection(locked=True)
                cell.number_format = "0.0%" if col == 1 else "General"
        workbook.defined_names.add(DefinedName("Gate41RangeAnchor", attr_text="'dynamic_range'!$A$1"))
        collision = workbook.create_sheet("collision_fixture")
        collision.merge_cells("A1:B1")
        collision["A1"] = "MERGED_PROTECTED"
        collision["D1"] = "MASTER_OWNED"
        collision["F1"] = "=1+1"
        workbook.defined_names.add(DefinedName("Gate41MergedAnchor", attr_text="'collision_fixture'!$A$1"))
        workbook.defined_names.add(DefinedName("Gate41ProtectedName", attr_text="'collision_fixture'!$D$1"))
        workbook.defined_names.add(DefinedName("Gate41FormulaAnchor", attr_text="'collision_fixture'!$F$1"))
        workbook.save(TARGET)
    finally:
        workbook.close()
        if workbook.vba_archive:
            workbook.vba_archive.close()
    evidence = {"schema_version": "GATE41_SYNTHETIC_FIXTURE_PROVENANCE_V1",
                "source_fixture": SOURCE.name, "customer_workbook_used": False,
                "customer_data_used": False, "fixture_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
                "builder": "scripts/build_gate41_fixture.py"}
    (TARGET_DIR / "dynamic_region_runtime_fixture_provenance.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="ascii")


if __name__ == "__main__":
    build()
