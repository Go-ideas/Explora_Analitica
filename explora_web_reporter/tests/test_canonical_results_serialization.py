from __future__ import annotations

from dataclasses import replace
import json
import math

import pytest

from src.analytics_core.serialization import (
    from_canonical_json,
    to_canonical_data,
    to_canonical_json,
)
from src.analytics_core.results import assemble_canonical_result, make_request_snapshot, make_slice
from src.contracts.models import CanonicalBase, CanonicalValue, QAEnvelope, UniverseRef
from src.contracts.validators import ContractValidationError, validate_canonical_result
from src.contracts.vocabulary import AggregateReleaseState, DenominatorUnit, ValueStatus, ValueUnit


def _minimal_result():
    return assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=make_request_snapshot(question_ids=("q1",)),
        slices=(make_slice(is_total=True),),
        bases=(),
        values=(),
        result_run_id="run-1",
    )


def _with_release_reasons(reasons: tuple[str, ...]):
    result = _minimal_result()
    return replace(
        result,
        release=replace(result.release, reasons=reasons),
        result_fingerprint=None,
        manifest=None,
    )


def test_canonical_serialization_is_deterministic_and_json_compatible() -> None:
    result = _minimal_result()
    first = to_canonical_json(result)
    second = to_canonical_json(result)

    assert first == second
    assert json.loads(first)["result_schema_version"] == "M5_CANONICAL_RESULT_V1"


def test_serialization_round_trip_preserves_analytical_semantics() -> None:
    result = _minimal_result()
    restored = from_canonical_json(to_canonical_json(result))

    assert to_canonical_data(restored) == to_canonical_data(result)


def test_canonical_serialization_rejects_nan_and_infinity() -> None:
    result = _minimal_result()
    bad = replace(
        result,
        base_records=({"bad": math.nan},),
        qa=QAEnvelope(aggregate_state=AggregateReleaseState.PASS),
    )

    with pytest.raises(ContractValidationError):
        validate_canonical_result(bad)


def test_typed_values_cannot_expose_non_finite_estimates() -> None:
    base = CanonicalBase(
        base_id="base-1",
        question_id="q1",
        structure_id="s1",
        slice_id="slice-1",
        universe_ref=UniverseRef("u1"),
        denominator_unit=DenominatorUnit.RESPONDENT,
        denominator_ref="respondent",
        denominator_scope_id="structure",
        unweighted_n=1,
    )
    value = CanonicalValue(
        value_id="value-1",
        question_id="q1",
        structure_id="s1",
        slice_id="slice-1",
        metric_id="m1",
        formula_id="MEAN",
        formula_version="v1",
        base_id="base-1",
        value_status=ValueStatus.OK,
        unit=ValueUnit.MEAN,
        estimate=math.inf,
    )
    result = replace(_minimal_result(), bases=(base,), values=(value,))

    with pytest.raises(ContractValidationError):
        validate_canonical_result(result)


def test_renderer_specific_modules_are_not_imported_by_m5_modules() -> None:
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src" / "analytics_core"
    forbidden = {"streamlit", "plotly", "openpyxl", "xlsxwriter", "src.ui"}
    for module in ("results.py", "serialization.py", "formula_registry.py", "result_identity.py"):
        tree = ast.parse((root / module).read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        direct = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert forbidden.isdisjoint(imports | direct)


def test_serialization_orders_permuted_canonical_collections_deterministically() -> None:
    slice_a = make_slice(is_total=False, banner_dimension_id="age", member_id="a")
    slice_b = make_slice(is_total=False, banner_dimension_id="age", member_id="b")
    first = assemble_canonical_result(
        project_id="project",
        dataset_fingerprint="dataset",
        project_spec_ref="project_spec",
        core_version="m5",
        request=make_request_snapshot(question_ids=("q1",)),
        slices=(slice_a, slice_b),
        bases=(),
        values=(),
        result_run_id="run",
    )
    second = replace(first, slices=(slice_b, slice_a))

    first_data = to_canonical_data(first)
    second_data = to_canonical_data(second)

    assert [item["slice_id"] for item in first_data["slices"]] == [
        item["slice_id"] for item in second_data["slices"]
    ]


def test_release_reasons_are_serialized_in_deterministic_order() -> None:
    first = _with_release_reasons(("R1", "R2"))
    second = _with_release_reasons(("R2", "R1"))

    assert to_canonical_json(first) == to_canonical_json(second)
    assert to_canonical_data(first)["release"]["reasons"] == ["R1", "R2"]


def test_three_plus_release_reason_permutations_share_canonical_output() -> None:
    expected = to_canonical_json(_with_release_reasons(("R1", "R2", "R3")))

    for reasons in (
        ("R3", "R2", "R1"),
        ("R2", "R1", "R3"),
        ("R1", "R3", "R2"),
    ):
        result = _with_release_reasons(reasons)

        assert to_canonical_json(result) == expected
        assert to_canonical_data(result)["release"]["reasons"] == [
            "R1",
            "R2",
            "R3",
        ]


def test_duplicate_release_reasons_preserve_multiplicity() -> None:
    first = _with_release_reasons(("R1", "R1", "R2"))
    second = _with_release_reasons(("R2", "R1", "R1"))
    data = to_canonical_data(first)

    assert to_canonical_json(first) == to_canonical_json(second)
    assert data["release"]["reasons"] == ["R1", "R1", "R2"]
    assert data["release"]["reasons"].count("R1") == 2


def test_release_reason_round_trip_remains_lossless_after_ordering() -> None:
    result = _with_release_reasons(("R2", "R1", "R1"))
    restored = from_canonical_json(to_canonical_json(result))

    assert to_canonical_data(restored)["release"]["reasons"] == ["R1", "R1", "R2"]
    assert to_canonical_data(restored) == to_canonical_data(result)
