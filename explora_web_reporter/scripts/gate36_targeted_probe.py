"""Opt-in narrowly scoped OOXML preservation stress probe."""
import argparse
import json
from pathlib import Path

from gate36_certification import compare, digest, inspect_package, targeted_write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("temporary", type=Path)
    args = parser.parse_args()
    if args.temporary.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("Client derivatives must remain outside repository")
    args.temporary.mkdir(parents=True, exist_ok=True)
    destination = args.temporary / "targeted_output.xlsm"
    before = inspect_package(args.source, ignored_cell="XFD1")
    evidence = {"fixture_id": "EXTERNAL_XLSM_FIXTURE_A", "baseline": before}
    try:
        targeted_write(args.source, destination, "XFD1", "CERTIFICATION_ONLY",
                       require_interface=False)
        after = inspect_package(destination, ignored_cell="XFD1")
        evidence["comparison"] = compare(before, after)
        evidence["after_vba_sha256"] = after["vba_sha256"]
        evidence["untouched_part_hashes_equal"] = all(
            after["parts"][name]["sha256"] == part["sha256"]
            for name, part in before["parts"].items()
            if name != "xl/worksheets/sheet1.xml")
    finally:
        if destination.parent.resolve() != args.temporary.resolve():
            raise ValueError("Unsafe cleanup target")
        destination.unlink(missing_ok=True)
        destination.with_name(destination.name + ".stage").unlink(missing_ok=True)
        evidence["cleanup"] = not destination.exists()
        evidence["source_unchanged"] = digest(args.source.read_bytes()) == before["whole_sha256"]
        (args.temporary / "anonymized_evidence.json").write_text(
            json.dumps(evidence, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items() if k != "baseline"}, indent=2))


if __name__ == "__main__":
    main()
