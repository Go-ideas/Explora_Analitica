# EXPLORA - M4 RM / GRID AUTHORITY REMEDIATION

**Milestone:** M4 - RM / GRID AUTHORITY
**Corrective pass:** B-M4-IMPL-01 through B-M4-IMPL-05
**Date:** 2026-09-14
**Authority:** `M4_RM_GRID_AUTHORITY_IMPLEMENTATION_CONTRACT.md`
**Runtime default:** `LEGACY` / `legacy_inference`

## Status

M4 corrective remediation is complete and isolated. M5 was not started.

## Pre-Change Baseline

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_corrective_pre
```

Result: 216 PASS / 0 FAIL / 0 SKIP

```powershell
python -m pytest -q tests/test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_corrective_pre_parity
```

Result: 2 PASS / 0 FAIL / 0 SKIP

## B-M4-IMPL-01 - RM Duplicate Keep

Root cause: respondent selected counts reused duplicate-policy mention
semantics, allowing `duplicate_policy=keep` to count two selected events for
the same respondent-option.

Source change: respondent counts now deduplicate by analytical
respondent-option identity. `duplicate_policy=keep` is retained only for
mention-event ledgers.

Tests changed/added:

- corrected `test_duplicate_policy_keep_vs_deduplicate_vs_error`;
- added `test_duplicate_keep_separates_respondent_and_mention_counts`.

Final behavior: respondent selected count is unique per respondent-option;
mention count can retain duplicate mention events when explicitly scoped.

## B-M4-IMPL-02 - Separate Denominator Ledgers

Root cause: one ledger mixed respondent-option and mention semantics.

Source change: M4 now emits separate respondent and mention ledgers for
RM/GRID_RM/LOOP_RM when a released mention denominator scope is explicit.

Tests changed/added:

- added explicit respondent vs mention ledger assertions in
  `test_duplicate_keep_separates_respondent_and_mention_counts`.

Final behavior: respondent denominator uses `respondent-option`; mention
denominator uses `mention`; the two are auditable independently.

## B-M4-IMPL-03 - Grid Applicability

Root cause: optional row/column/cell applicability scopes were treated as
mandatory generic refs.

Source change: question applicability remains mandatory; optional
row/column/cell applicability is applied only when declared. Missing optional
scope means no additional restriction. Member-specific `StructureMember`
UniverseRefs and cell-specific applicability refs are consumed.

Tests changed/added:

- corrected missing optional Grid scope expectation;
- added `test_grid_member_specific_and_cell_applicability_compose`;
- added `test_grid_missing_optional_row_column_cell_rules_add_no_restriction`.

Final behavior: effective Grid applicability is question AND declared member
row AND declared member column AND declared cell restriction, with absent
optional rules treated as TRUE.

## B-M4-IMPL-04 - Loop Duplicate Scope

Root cause: duplicate and exclusivity keys collapsed loop records by
respondent-option, ignoring loop instance/entity scope.

Source change: duplicate identity now uses analytical scope:

- RM: respondent + option;
- GRID_RM: respondent + row/entity + option;
- LOOP_RM: respondent + entity when present + loop_instance + option.

Exclusive option checks use the same scoped analytical unit without crossing
rows, entities or loop instances.

Tests changed/added:

- corrected loop repeated-dependency expectation;
- added `test_loop_duplicate_identity_includes_loop_instance`;
- added `test_loop_duplicate_policy_applies_inside_same_loop_instance`;
- added `test_exclusive_scope_respects_loop_instance`.

Final behavior: repeated loop instances are preserved as separate normalized
records, are not false duplicates, and keep repeated-dependency metadata.

## B-M4-IMPL-05 - Released Reference Integrity

Root cause: runtime checked RELEASED state but did not verify internal
Question -> Structure -> Universe reference consistency.

Source change: M4 validates:

- `QuestionSpec.structure_ref` matches the executed `StructureSpec.structure_id`
  or canonical `StructureSpec.spec_id`;
- `StructureSpec.parent_question_ref` matches `QuestionSpec.question_id`;
- `QuestionSpec.universe_ref` matches StructureSpec question-level
  applicability UniverseRef when both are present.

Tests changed/added:

- added `test_released_question_structure_reference_integrity`;
- added `test_released_question_universe_consistency`;
- added `test_detector_disagreement_loses_to_consistent_released_chain`.

Final behavior: contradictory RELEASED chains fail; detector disagreement does
not override a consistent RELEASED chain.

## RU Response-State Reconciliation

Root cause: RU valid category records used generic `ANSWERED`.

Source change: added additive `ResponseStateValue.VALID_CATEGORY` and M4 RU /
category-mapped structures now emit `VALID_CATEGORY` for mapped valid
categories. M2 response semantics are unchanged.

Tests changed/added:

- updated RU category mapping assertions;
- added `test_ru_response_states_use_valid_category_and_distinct_missing_states`.

Final behavior: RU emits `VALID_CATEGORY`, `ORDINARY_MISSING`,
`STRUCTURAL_MISSING` and `INVALID_OUT_OF_DOMAIN` as distinct M4 analytical
states.

## Test Evidence

Focused M4 corrective:

```powershell
python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_structure_authority_corrective.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_corrective_focus
```

Result: 50 PASS / 0 FAIL / 0 SKIP

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_corrective_full
```

Result: 226 PASS / 0 FAIL / 0 SKIP

Legacy parity:

```powershell
python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_corrective_parity
```

Result: 2 PASS / 0 FAIL / 0 SKIP

## Guardrails

- M2 Universe runtime was not modified.
- M3 Weight runtime was not modified.
- Productive Legacy reporter behavior was not modified.
- Legacy RM/Grid/Scale builders were not modified.
- Grid loop detector behavior was not modified.
- Web/UI was not modified.
- SQLite/database behavior was not modified.
- Excel/VBA was not modified.
- NG was not modified.
- Significance runtime was not modified.
- No dependencies changed.
- No M5 work was started.

## Productive Grid / Loop Benchmark

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

No actual traced real Grid/Loop benchmark was executed during the corrective
pass. Synthetic/unit fixtures are not claimed as a productive benchmark.
