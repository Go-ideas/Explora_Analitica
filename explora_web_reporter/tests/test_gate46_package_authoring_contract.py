from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
DOCS = ROOT / "docs" / "explora_target"
CHECKPOINT = json.loads(
    (DOCS / "GATE46_PACKAGE_AUTHORING_CHECKPOINT.json").read_text(encoding="utf-8")
)
CROSSWALK = (DOCS / "GATE46_PROJECT_SPEC_PACKAGE_CROSSWALK.md").read_text(
    encoding="utf-8"
)
CONTRACT = (DOCS / "GATE46_PACKAGE_AUTHORING_CONTRACT_V1.md").read_text(
    encoding="utf-8"
)


EXPECTED_PACKAGE_FILES = {
    "01_PROJECT_SPEC_RELEASED.json",
    "02_QUESTION_SPECS_RELEASED.json",
    "03_STRUCTURE_SPECS_RELEASED.json",
    "04_UNIVERSE_SPECS_RELEASED.json",
    "05_WEIGHT_REGISTRY_RELEASED.json",
    "06_METRIC_SPECS_RELEASED.json",
    "07_SIGNIFICANCE_SPECS_RELEASED.json",
    "08_BANNER_FILTER_SPECS_RELEASED.json",
    "09_REQUEST_MATRIX_RELEASED.json",
    "MANIFEST.json",
}


def test_g46_01_all_package_files_are_covered() -> None:
    assert set(CHECKPOINT["package_files"]) == EXPECTED_PACKAGE_FILES
    assert CHECKPOINT["package_files_covered"] == 10
    assert all(name in CROSSWALK for name in EXPECTED_PACKAGE_FILES)


def test_g46_02_required_fields_are_classified() -> None:
    assert CHECKPOINT["required_fields_classified"] is True
    assert CHECKPOINT["source_classifications"] == ["A", "B", "C", "D", "E", "F"]


def test_g46_03_no_field_is_unclassified() -> None:
    assert CHECKPOINT["unclassified_fields"] == []


def test_g46_04_authoring_performs_no_statistical_calculation() -> None:
    assert CHECKPOINT["statistical_calculation_in_authoring"] is False
    for forbidden in ("percentages", "weighted bases", "effective n", "means", "significance"):
        assert forbidden in CONTRACT


def test_g46_05_no_benchmark_specific_generic_rule() -> None:
    assert CHECKPOINT["generic_rule_specific_ids"] == []


def test_g46_06_no_atlas_specific_generic_rule() -> None:
    assert CHECKPOINT["generic_rule_specific_ids"] == []
    assert "do not create generic defaults" in (
        DOCS / "GATE46_PACKAGE_AUTHORING_DECISION_REGISTER.md"
    ).read_text(encoding="utf-8")


def test_g46_07_b1_authority_is_preserved() -> None:
    assert CHECKPOINT["b1_authority"] == "PRESERVED"
    assert "never becomes silently unweighted" in CONTRACT


def test_g46_08_b2_authority_is_preserved() -> None:
    assert CHECKPOINT["b2_authority"] == "PRESERVED"
    assert "B2 remains sole significance methodology authority" in CONTRACT


def test_g46_09_b3_release_authority_is_preserved() -> None:
    assert CHECKPOINT["b3_authority"] == "PRESERVED"
    assert "Only a B3-authorized `RELEASED` package" in CONTRACT


def test_g46_10_project_spec_is_not_result_authority() -> None:
    assert CHECKPOINT["project_spec_alone_sufficient"] is False
    assert CHECKPOINT["target_authoring_architecture"] == "EXECUTION_RELEASE_SPEC"


def test_g46_11_backward_compatibility_is_preserved() -> None:
    assert CHECKPOINT["gate44_backward_compatibility"] == "PRESERVED_BY_NO_RUNTIME_CHANGE"
    assert CHECKPOINT["gate45_backward_compatibility"] == "PRESERVED_BY_NO_RUNTIME_CHANGE"


def test_g46_12_missing_information_fails_closed() -> None:
    assert "## Fail-closed conditions" in CONTRACT
    assert CHECKPOINT["implementation_ready"] is True
    assert CHECKPOINT["next_milestone_authorized"] is False
