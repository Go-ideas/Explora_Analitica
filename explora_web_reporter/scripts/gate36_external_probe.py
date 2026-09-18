"""Opt-in external stress probe. Never retains a client workbook in Git."""
from __future__ import annotations

import argparse
import json
import shutil
import warnings
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from openpyxl import load_workbook

from gate36_certification import S, compare, digest, inspect_package


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("temporary", type=Path)
    args = parser.parse_args()
    if args.temporary.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("Client derivatives must remain outside repository")
    args.temporary.mkdir(parents=True, exist_ok=True)
    outputs = []
    evidence = {"fixture_id": "EXTERNAL_XLSM_FIXTURE_A", "backends": {}}
    original_hash = digest(args.source.read_bytes())
    try:
        baseline = inspect_package(args.source, ignored_cell="XFD1")
        with ZipFile(args.source) as z:
            # A far-right empty technical cell is chosen; no source cell is overwritten.
            first = "xl/worksheets/sheet1.xml"
            tree = ET.fromstring(z.read(first))
            if any(e.get("r") == "XFD1" for e in tree.iter(f"{{{S}}}c")):
                raise ValueError("Designated technical cell is occupied")
        evidence["baseline"] = baseline
        print("INTAKE_COMPLETE", flush=True)
        output = args.temporary / "openpyxl.xlsm"
        outputs.append(output)
        with ZipFile(args.source) as archive:
            oversized = any(p.file_size > 64 * 1024 * 1024 and p.filename.endswith(".xml") for p in archive.infolist())
        if oversized:
            evidence["backends"]["openpyxl"] = {
                "result": "NOT_APPLICABLE",
                "reason": "Full object-model load exceeds certification XML-part resource bound; complex slicer/pivot preservation unproved"}
        else:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                w = load_workbook(args.source, keep_vba=True, data_only=False, keep_links=True)
                try:
                    w.worksheets[0]["XFD1"] = "CERTIFICATION_ONLY"
                    w.worksheets[0]["XFD1"].data_type = "s"
                    w.save(output)
                finally:
                    w.close()
                    if w.vba_archive is not None:
                        w.vba_archive.close()
            after = inspect_package(output, ignored_cell="XFD1")
            evidence["backends"]["openpyxl"] = {"comparison": compare(baseline, after),
                "after_vba_sha256": after["vba_sha256"],
                "warning_count": len(caught),
                "warning_hashes": [digest(str(x.message).encode()) for x in caught]}
        print("OPENPYXL_TRIAGE_COMPLETE", flush=True)
        # Normal Excel automation only; never touch VBProject or execute macros.
        import win32com.client
        app = None
        book = None
        seed = None
        native_input = args.temporary / "native_input.xlsm"
        native_output = args.temporary / "native_output.xlsm"
        outputs.extend([native_input, native_output])
        shutil.copyfile(args.source, native_input)
        try:
            app = win32com.client.DispatchEx("Excel.Application")
            app.Visible = False
            app.DisplayAlerts = False
            app.EnableEvents = False
            app.AutomationSecurity = 3
            app.AskToUpdateLinks = False
            # Keep a blank workbook active while setting application calculation.
            seed = app.Workbooks.Add()
            app.Calculation = -4135
            app.CalculateBeforeSave = False
            print("NATIVE_OPEN_START", flush=True)
            book = app.Workbooks.Open(str(native_input.resolve()), UpdateLinks=0,
                                      ReadOnly=False, IgnoreReadOnlyRecommended=True)
            app.Calculation = -4135
            app.CalculateBeforeSave = False
            seed.Close(SaveChanges=False)
            seed = None
            if book.Worksheets(1).Range("XFD1").Value2 is not None:
                raise ValueError("Native technical cell is occupied")
            book.Worksheets(1).Range("XFD1").Value2 = "CERTIFICATION_ONLY"
            print("NATIVE_SAVE_START", flush=True)
            book.SaveAs(str(native_output.resolve()), FileFormat=52)
            book.Close(SaveChanges=False)
            book = None
            after = inspect_package(native_output, ignored_cell="XFD1")
            evidence["backends"]["native_excel"] = {"comparison": compare(baseline, after),
                "after_vba_sha256": after["vba_sha256"], "version": app.Version,
                "macros_disabled": True, "manual_calculation": True, "links_update": False}
        finally:
            if book is not None:
                book.Close(SaveChanges=False)
            if seed is not None:
                seed.Close(SaveChanges=False)
            if app is not None:
                app.Quit()
    finally:
        for path in outputs:
            if path.parent.resolve() != args.temporary.resolve():
                raise ValueError("Unsafe cleanup target")
            path.unlink(missing_ok=True)
        evidence["source_unchanged"] = digest(args.source.read_bytes()) == original_hash
        evidence["temporary_derivatives_cleaned"] = all(not p.exists() for p in outputs)
        (args.temporary / "anonymized_evidence.json").write_text(
            json.dumps(evidence, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({"source_sha256": original_hash,
                      "vba_sha256": evidence.get("baseline", {}).get("vba_sha256"),
                      "backends": evidence["backends"],
                      "cleanup": evidence["temporary_derivatives_cleaned"]}, indent=2))


if __name__ == "__main__":
    main()
