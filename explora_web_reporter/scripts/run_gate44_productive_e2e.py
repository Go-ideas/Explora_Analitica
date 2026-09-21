from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import tempfile

from src.project_intake import binding_payload, compile_project_spec, validate_project
from src.project_intake.productive import build_project_spec, execute_binding, produce_release


SOURCE_SHA = "71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F"
PACKAGE_SHA = "78AFA38484DC4B27FDD0AB5C3F8F2B80B2B49CABC67A57361B94BEB591685A41"


def run(input_root: Path, output_root: Path) -> dict:
    if output_root.exists():
        raise FileExistsError(f"refusing to replace existing release: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{output_root.name}.", dir=output_root.parent) as temporary:
        staging = Path(temporary) / "release"
        summary = _build_release(input_root, staging)
        staging.replace(output_root)
        return summary


def _build_release(input_root: Path, output_root: Path) -> dict:
    source = input_root / "FUNSMX_297140_20260914.sav"
    package = input_root / "BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip"
    repository = Path(__file__).resolve().parents[1]
    master = repository / "production_masters" / "EXPLORA_PRODUCTION_MASTER_V1_2.xlsm"
    qualification = master.with_suffix(".qualification.json")
    dynamic_qualification = master.with_suffix(".dynamic.qualification.json")
    spec = build_project_spec(source_path=source, package_path=package)
    intake = validate_project(spec)
    if not intake.ready_for_execution:
        raise RuntimeError(f"Project Spec is not ready: {intake.errors}")
    (output_root / "config").mkdir(parents=True, exist_ok=True)
    spec_path = output_root / "config" / "project_spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    binding = compile_project_spec(spec, source_path=source, package_path=package,
                                   expected_source_sha256=SOURCE_SHA,
                                   expected_package_sha256=PACKAGE_SHA)
    binding_path = output_root / "canonical" / "execution_binding.json"
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(json.dumps(binding_payload(binding), indent=2) + "\n", encoding="utf-8")
    first = execute_binding(binding, source_path=source, package_path=package)
    second = execute_binding(binding, source_path=source, package_path=package)
    first_ids = tuple((key, first.results[key].result_fingerprint) for key in binding.request_ids)
    second_ids = tuple((key, second.results[key].result_fingerprint) for key in binding.request_ids)
    if first.runtime.fingerprint != second.runtime.fingerprint or first_ids != second_ids:
        raise RuntimeError("productive rerun is not deterministic")
    evidence = produce_release(binding, first, master_path=master,
        qualification_path=qualification, dynamic_qualification_path=dynamic_qualification,
        output_root=output_root)
    summary = {"intake_status": intake.validation_status,
               "project_spec_fingerprint": intake.project_spec_fingerprint,
               "binding": binding_payload(binding), "evidence": asdict(evidence),
               "deterministic_rerun": True, "legacy_fallback": False,
               "customer_raw_data_added_to_git": False}
    (output_root / "qa" / "gate44_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input_root, args.output_root), indent=2))


if __name__ == "__main__":
    main()
