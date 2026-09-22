from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.excel_renderer import load_qualified_master
from src.project_intake.generic_productive import output_intent, run_generic_productive


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an accepted EXPLORA Project Spec")
    parser.add_argument("--project-spec", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--presentation-config", type=Path)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--master-qualification", type=Path)
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--expected-package-sha256")
    args = parser.parse_args()

    project_spec = json.loads(args.project_spec.read_text(encoding="utf-8"))
    _, targets = output_intent(project_spec)
    qualified = None
    if "EXCEL" in targets:
        if not (args.presentation_config and args.master and args.master_qualification):
            parser.error("EXCEL output requires presentation config, Master and qualification")
        qualified = load_qualified_master(args.master_qualification, args.master)
    summary = run_generic_productive(
        project_spec, source_path=args.source, package_path=args.package,
        output_root=args.output_root, presentation_configuration=args.presentation_config,
        qualified_master=qualified, master_path=args.master,
        expected_source_sha256=args.expected_source_sha256,
        expected_package_sha256=args.expected_package_sha256,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
