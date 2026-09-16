import pytest

from src.contracts.models import (
    CategoryOptionBinding,
    ReleaseMetadata,
    StructureAxis,
    StructureMember,
    StructureSpec,
    UniverseRef,
    VariableBinding,
)
from src.contracts.validators import (
    ContractValidationError,
    validate_structure_spec,
)
from src.contracts.vocabulary import (
    AxisRole,
    CompletionPolicy,
    DuplicatePolicy,
    ReleaseLifecycle,
    ReleaseMode,
    StorageEncoding,
)


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="human",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="M4",
        policy_version="V1",
        source_hash="hash",
    )


def rm_spec(**overrides) -> StructureSpec:
    base = dict(
        spec_id="structure_rm",
        version="1.0",
        release=released(),
        structure_id="rm",
        structure_type="RM",
        parent_question_ref="q1",
        axes=(
            StructureAxis(
                axis_id="options",
                role=AxisRole.OPTION,
                members=(
                    StructureMember("a", "A"),
                    StructureMember("b", "B"),
                ),
            ),
        ),
        variable_bindings=(
            VariableBinding("b_a", "q1_a", option_id="a"),
            VariableBinding("b_b", "q1_b", option_id="b"),
        ),
        applicability_refs={"question": UniverseRef("u_q1")},
        selected_values=(1,),
        not_selected_values=(0,),
        completion_policy=CompletionPolicy.EXPLICIT_RESPONSE,
        duplicate_policy=DuplicatePolicy.ERROR,
        storage_encoding=StorageEncoding.ONE_COLUMN_PER_OPTION,
    )
    base.update(overrides)
    return StructureSpec(**base)


def test_m4_structure_spec_accepts_explicit_released_authority() -> None:
    spec = rm_spec()

    assert (
        validate_structure_spec(
            spec,
            available_variables={"q1_a", "q1_b"},
            universe_ids={"u_q1"},
            enforce_m4=True,
        )
        is spec
    )


def test_legacy_shape_remains_constructible_without_m4_enforcement() -> None:
    spec = StructureSpec(
        spec_id="legacy_shape",
        version="1.0",
        release=released(),
        structure_id="legacy",
        structure_type="SOMETHING_LEGACY",
        parent_question_ref="q1",
    )

    assert validate_structure_spec(spec) is spec


@pytest.mark.parametrize(
    "override, message",
    [
        (
            {
                "axes": (
                    StructureAxis(axis_id="dup", role=AxisRole.OPTION),
                    StructureAxis(axis_id="dup", role=AxisRole.OPTION),
                )
            },
            "duplicate axis_id",
        ),
        (
            {
                "variable_bindings": (
                    VariableBinding("b_a", "q1_a", option_id="a"),
                    VariableBinding("b_a", "q1_b", option_id="b"),
                )
            },
            "duplicate variable binding_id",
        ),
        (
            {
                "category_bindings": (
                    CategoryOptionBinding("c1", "cat_a", raw_values=(1,)),
                    CategoryOptionBinding("c2", "cat_b", raw_values=(1,)),
                ),
            },
            "duplicate raw category value",
        ),
        ({"duplicate_policy": "invented"}, "duplicate_policy"),
        ({"storage_encoding": "invented"}, "storage_encoding"),
        ({"completion_policy": "invented"}, "completion_policy"),
        ({"exclusive_option_ids": ("missing",)}, "unknown exclusive"),
        ({"applicability_refs": {"row/entity": UniverseRef("u_q1")}}, "unsupported"),
    ],
)
def test_m4_structure_spec_rejects_ambiguous_authority(
    override, message
) -> None:
    with pytest.raises(ContractValidationError, match=message):
        validate_structure_spec(rm_spec(**override), enforce_m4=True)


def test_m4_structure_spec_rejects_unknown_variable_when_registry_given() -> None:
    with pytest.raises(ContractValidationError, match="unknown variable_ref"):
        validate_structure_spec(
            rm_spec(),
            available_variables={"q1_a"},
            enforce_m4=True,
        )


def test_m4_structure_spec_rejects_unknown_universe_ref() -> None:
    with pytest.raises(ContractValidationError, match="unknown universe_ref"):
        validate_structure_spec(
            rm_spec(),
            universe_ids={"other"},
            enforce_m4=True,
        )


def test_m4_structure_spec_rejects_loop_without_identity() -> None:
    with pytest.raises(ContractValidationError, match="loop instance identity"):
        validate_structure_spec(
            rm_spec(
                structure_type="LOOP_RU",
                category_bindings=(
                    CategoryOptionBinding("c1", "cat_a", raw_values=(1,)),
                ),
            ),
            enforce_m4=True,
        )


def test_m4_structure_spec_rejects_unsupported_loop_rango() -> None:
    with pytest.raises(ContractValidationError, match="unsupported"):
        validate_structure_spec(
            rm_spec(structure_type="LOOP_RANGO"),
            enforce_m4=True,
        )
