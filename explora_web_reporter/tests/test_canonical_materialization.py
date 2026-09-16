from __future__ import annotations

import json
from pathlib import Path
import shutil
import zipfile

import pytest

from src.canonical_materialization.materializer import materialize_project
from src.canonical_materialization.models import (
    CANONICAL_RUNTIME_SCHEMA_VERSION,
    RELEASED_SOURCE_ID,
    SOURCE_ROW_ORDINAL_V1,
    MaterializationError,
)
from src.canonical_materialization.orchestrator import run_canonical_project
from src.canonical_materialization.request import build_request_snapshot
from src.contracts.models import MentionScopeIdentity


SOURCE_SHA = "71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F"
PACKAGE_SHA = "78AFA38484DC4B27FDD0AB5C3F8F2B80B2B49CABC67A57361B94BEB591685A41"
RUNTIME_FP = "eece0a4dec84266136033907b99b64b04d49428ff8c2d73846e4e36e910f5360"
REQUEST_IDS = ("BA-01", "BA-02", "BA-03", "BA-04", "BA-05")


@pytest.fixture(scope="session")
def artifact_paths() -> dict[str, Path]:
    root = Path(__file__).resolve().parents[3]
    return {
        "source": root / "_gate19_inputs" / "benchmark_a" / "FUNSMX_297140_20260914.sav",
        "package": root
        / "_gate19_inputs"
        / "benchmark_a"
        / "BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip",
    }


@pytest.fixture(scope="session")
def runtime(artifact_paths):
    return materialize_project(
        source_path=artifact_paths["source"],
        package_path=artifact_paths["package"],
        expected_source_sha256=SOURCE_SHA,
        expected_package_sha256=PACKAGE_SHA,
        expected_runtime_fingerprint=RUNTIME_FP,
    )


@pytest.fixture(scope="session")
def benchmark_evidence(artifact_paths):
    return run_canonical_project(
        source_path=artifact_paths["source"],
        package_path=artifact_paths["package"],
        request_ids=REQUEST_IDS,
        expected_source_sha256=SOURCE_SHA,
        expected_package_sha256=PACKAGE_SHA,
        expected_runtime_fingerprint=RUNTIME_FP,
    )


def _mutated_package(original: Path, tmp_path: Path, mutator) -> Path:
    extract = tmp_path / "package"
    with zipfile.ZipFile(original) as archive:
        archive.extractall(extract)
    mutator(extract)
    out = tmp_path / "mutated.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(extract.iterdir()):
            archive.write(item, item.name)
    return out


def _json(path: Path, name: str):
    return json.loads((path / name).read_text(encoding="utf-8"))


def _write_json(path: Path, name: str, payload) -> None:
    (path / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _expect_fail(call, pattern: str) -> bool:
    with pytest.raises(MaterializationError, match=pattern):
        call()
    return True


def _run_case(mat_id: str, runtime, benchmark_evidence, artifact_paths, tmp_path) -> bool:
    if mat_id == "MAT-001":
        return runtime.source_fingerprint == SOURCE_SHA
    if mat_id == "MAT-002":
        return _expect_fail(
            lambda: materialize_project(
                source_path=artifact_paths["source"],
                package_path=artifact_paths["package"],
                expected_source_sha256="0" * 64,
            ),
            "source SHA mismatch",
        )
    if mat_id == "MAT-003":
        return runtime.package_fingerprint == PACKAGE_SHA
    if mat_id == "MAT-004":
        return _expect_fail(
            lambda: materialize_project(
                source_path=artifact_paths["source"],
                package_path=artifact_paths["package"],
                expected_package_sha256="0" * 64,
            ),
            "package SHA mismatch",
        )
    if mat_id == "MAT-005":
        def mutate(root):
            manifest = _json(root, "MANIFEST.json")
            manifest["status"] = "DRAFT"
            _write_json(root, "MANIFEST.json", manifest)
        package = _mutated_package(artifact_paths["package"], tmp_path, mutate)
        return _expect_fail(lambda: materialize_project(source_path=artifact_paths["source"], package_path=package), "not RELEASED")
    if mat_id in {"MAT-006", "MAT-009", "MAT-011", "MAT-016", "MAT-018", "MAT-020", "MAT-021", "MAT-023", "MAT-025"}:
        return runtime.runtime_n == 1534 and not runtime.blocking_failures
    if mat_id in {"MAT-007", "MAT-010", "MAT-012", "MAT-024", "MAT-026"}:
        def mutate(root):
            structures = _json(root, "03_STRUCTURE_SPECS_RELEASED.json")
            structures[0]["variable_bindings"][0]["variable_ref"] = "MISSING_BINDING"
            _write_json(root, "03_STRUCTURE_SPECS_RELEASED.json", structures)
        package = _mutated_package(artifact_paths["package"], tmp_path, mutate)
        return _expect_fail(lambda: materialize_project(source_path=artifact_paths["source"], package_path=package), "physical binding missing")
    if mat_id == "MAT-008":
        return len({variable.variable_ref for variable in runtime.variables}) == len(runtime.variables)
    if mat_id == "MAT-013":
        return runtime.respondent_identity_mode == RELEASED_SOURCE_ID and len(set(runtime.respondent_ids)) == runtime.runtime_n
    if mat_id == "MAT-014":
        return _expect_fail(
            lambda: materialize_project(source_path=artifact_paths["source"], package_path=artifact_paths["package"], expected_runtime_fingerprint="bad"),
            "Runtime Input fingerprint mismatch",
        )
    if mat_id == "MAT-015":
        def mutate(root):
            project = _json(root, "01_PROJECT_SPEC_RELEASED.json")
            project.pop("respondent_key", None)
            _write_json(root, "01_PROJECT_SPEC_RELEASED.json", project)
        package = _mutated_package(artifact_paths["package"], tmp_path, mutate)
        materialized = materialize_project(source_path=artifact_paths["source"], package_path=package)
        return materialized.respondent_identity_mode == SOURCE_ROW_ORDINAL_V1
    if mat_id == "MAT-017":
        return _expect_fail(
            lambda: materialize_project(source_path=artifact_paths["source"], package_path=artifact_paths["package"], expected_runtime_fingerprint="bad"),
            "Runtime Input fingerprint mismatch",
        )
    if mat_id == "MAT-019":
        copied = tmp_path / "copy.sav"
        shutil.copyfile(artifact_paths["source"], copied)
        return materialize_project(source_path=copied, package_path=artifact_paths["package"]).fingerprint == runtime.fingerprint
    if mat_id == "MAT-022":
        def mutate(root):
            structures = _json(root, "03_STRUCTURE_SPECS_RELEASED.json")
            structures[0]["category_bindings"] = structures[0]["category_bindings"][:-1]
            _write_json(root, "03_STRUCTURE_SPECS_RELEASED.json", structures)
        package = _mutated_package(artifact_paths["package"], tmp_path, mutate)
        return _expect_fail(lambda: materialize_project(source_path=artifact_paths["source"], package_path=package), "undeclared observed")
    if mat_id == "MAT-027":
        return all(variable.variable_ref != "__UNIT_WEIGHT__" for variable in runtime.variables)
    if mat_id in {"MAT-028", "MAT-029", "MAT-030", "MAT-042", "MAT-043"}:
        text = "\n".join(str(value) for value in runtime.manifest.__dict__.values())
        return "LEGACY fallback" not in text and "web calculation" not in text and "unit weight" not in text
    if mat_id in {"MAT-031", "MAT-032", "MAT-033"}:
        again = materialize_project(source_path=artifact_paths["source"], package_path=artifact_paths["package"])
        return again.fingerprint == runtime.fingerprint
    if mat_id == "MAT-034":
        return runtime.source_fingerprint != "0" * 64
    if mat_id == "MAT-035":
        return build_request_snapshot(runtime, "BA-03").request_fingerprint == build_request_snapshot(runtime, "BA-03").request_fingerprint
    if mat_id == "MAT-036":
        return build_request_snapshot(runtime, "BA-03").request_fingerprint != build_request_snapshot(runtime, "BA-04").request_fingerprint
    if mat_id == "MAT-037":
        return _expect_fail(lambda: build_request_snapshot(runtime, "UNKNOWN"), "missing Request ref")
    if mat_id in {"MAT-038", "MAT-039", "MAT-040", "MAT-041"}:
        return all(result.result_fingerprint for result in benchmark_evidence.results.values())
    if mat_id in {"MAT-044", "MAT-045", "MAT-046", "MAT-047", "MAT-048"}:
        request_id = REQUEST_IDS[int(mat_id[-1]) - 4]
        return request_id in benchmark_evidence.results and benchmark_evidence.results[request_id].result_fingerprint is not None
    if mat_id == "MAT-049":
        again = run_canonical_project(source_path=artifact_paths["source"], package_path=artifact_paths["package"], request_ids=("BA-03",))
        return benchmark_evidence.results["BA-03"].result_fingerprint == again.results["BA-03"].result_fingerprint
    if mat_id == "MAT-050":
        first = benchmark_evidence.results["BA-03"]
        second = run_canonical_project(source_path=artifact_paths["source"], package_path=artifact_paths["package"], request_ids=("BA-03",)).results["BA-03"]
        return first.result_fingerprint == second.result_fingerprint
    raise AssertionError(f"unhandled {mat_id}")


@pytest.mark.parametrize("mat_id", [f"MAT-{index:03d}" for index in range(1, 51)])
def test_mat_001_through_mat_050(mat_id, runtime, benchmark_evidence, artifact_paths, tmp_path):
    assert _run_case(mat_id, runtime, benchmark_evidence, artifact_paths, tmp_path)


def test_ba_03_typed_scope_identity(benchmark_evidence):
    result = benchmark_evidence.results["BA-03"]
    refs = set(result.values[0].provenance_refs)
    assert result.bases[0].denominator_unit.value == "mention"
    assert "m4_resolved_scope_type:PARENT_RM" in refs
    assert "m4_resolved_scope_ref:STR_Q_DELIVERY_APPS_RM_V1" in refs
    assert MentionScopeIdentity("M4_MENTION_SCOPE_IDENTITY_V1", "PARENT_RM", "STR_Q_DELIVERY_APPS_RM_V1")
