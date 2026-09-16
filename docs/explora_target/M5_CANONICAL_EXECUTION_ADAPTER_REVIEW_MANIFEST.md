# M5 Canonical Execution Adapter Review Manifest

Checkpoint identity: `M5_CANONICAL_EXECUTION_ADAPTER_REVIEW_CHECKPOINT_2026-09-15`

Created at: `2026-09-15T14:21:59-06:00`

Repository root: `C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica`

Git status availability: NOT AVAILABLE. No `.git` metadata is present at repository root.

## Packaged Files

- `explora_web_reporter/src/analytics_core/execution_adapter.py` SHA-256 `BD1546E8E0B309B7ABA26E67972184D9DA04E79061CD16C6D81CD95D475E9FD8`
- `explora_web_reporter/tests/test_m5_execution_adapter.py` SHA-256 `AECDFED3439E0218A2C863B73A006A12AA0A58AF421E08A9C36C94A49671DE81`
- `docs/explora_target/M5_CANONICAL_EXECUTION_ADAPTER_IMPLEMENTATION.md` SHA-256 `3FBB5F38D218A308AA373B02719BAA200E23C0FED1C173EB891D25554ABF1D96`
- `docs/explora_target/M5_CANONICAL_EXECUTION_ADAPTER_MANIFEST.md` SHA-256 `CEEC78BFB659BA4065875AEFC6D3BD006E9DBA03583BADFC96E1969083B25930`
- `docs/explora_target/M5_CANONICAL_EXECUTION_ADAPTER_REVIEW_MANIFEST.md` SHA-256 reported after creation.
- `evidence/m5_execution_adapter_review/hashes/protected_source_hash_inventory.json` SHA-256 `0AE19D9D60929AE68F071576FCB6A64BC7DE66828458F03D770C9B2A7A4956C2`
- `evidence/m5_execution_adapter_review/logs/focused_adapter_tests.log` SHA-256 `0F0E88A0667D6B1EDD48B5A0665DEF3499C53016EC184291DF325A369DC33848`
- `evidence/m5_execution_adapter_review/logs/m2_regression.log` SHA-256 `B50BFFD53725AC7FCC625D1CDDB3178049A30E6A392AB1A82EFD9B550BE2ABC9`
- `evidence/m5_execution_adapter_review/logs/m3_regression.log` SHA-256 `C6362D78F121AD04783305C6C3667EE2EE3648B68CBBBE59AC4B0FF7500F2B7E`
- `evidence/m5_execution_adapter_review/logs/m4_regression.log` SHA-256 `ED1C455A14D04581F1B54B8F9F3A21F1C97582D6E3DE24373F8808611CCEB16C`
- `evidence/m5_execution_adapter_review/logs/m5_regression.log` SHA-256 `97750AE6774A7E3CEB69B717487A212B5F2831146C9D2AA8F5D950211583E266`
- `evidence/m5_execution_adapter_review/logs/m6_regression.log` SHA-256 `DD14BA560A7DCE34D891FB7AF836BA963A73D3EB8C8CBFF9B4C017EE4480062F`
- `evidence/m5_execution_adapter_review/logs/legacy_parity.log` SHA-256 `83DD46AB23618D148ED0F1B06BB9E1C7801D40C0E71A05B8530CDB77A2F88048`
- `evidence/m5_execution_adapter_review/logs/full_regression.log` SHA-256 `BC504D3BD616A9437DF4277929ADDCDE2490CB7AC1448E84B9BE2E82C84F2287`

## Adapter Source Audit

Adapter source exists: YES

SHA-256: `BD1546E8E0B309B7ABA26E67972184D9DA04E79061CD16C6D81CD95D475E9FD8`

Line count: `639`

Public symbols:

- `ExecutionAdapterError`
- `SliceExecutionAuthority`
- `CanonicalExecutionContext`
- `execute_canonical_request`
- `metric_universe`

Imports:

- `dataclasses`
- `math`
- `typing`
- `src.analytics_core.results`
- `src.analytics_core.result_identity`
- `src.analytics_core.structure`
- `src.analytics_core.universe`
- `src.analytics_core.weights`
- `src.contracts.models`
- `src.contracts.validators`
- `src.contracts.vocabulary`

Forbidden import/reference audit:

- Legacy: NO
- Web: NO
- reporter: NO
- raw SAV reader: NO
- pandas/raw dataframe: NO
- z-test: NO
- t-test: NO
- Holm: NO
- p-value implementation: NO
- letter-assignment implementation: NO
- Python eval: NO

Public interface evidence:

- Import: `from src.analytics_core.execution_adapter import execute_canonical_request`
- Signature: `(context: 'CanonicalExecutionContext | None' = None, **kwargs: 'Any') -> 'CanonicalResult'`

## Formula Authority Audit

The adapter uses existing M5 helpers:

- `base_from_ledger`
- `value_from_formula`
- `assemble_canonical_result`

The adapter performs primitive derivation from authoritative M2/M3/M4 outputs only. It does not independently implement mean, standard deviation, z-test, t-test, Holm correction, p-values, or significance letters.

The adapter derives counts required as primitive formula inputs for existing M5 formulas:

- RU category numerator from M4 `VALID_CATEGORY` records.
- RU valid denominator from M4-valid category records inside M2 slice mask.
- RM respondent numerator/denominator from M4 `SELECTED`/`NOT_SELECTED` states.
- RM mention numerator/denominator from M4 selected records and required M4 mention ledger.

## M4 Authority Audit

Relevant source lines:

- `_execute_ru_metric`: starts at line 192.
- RU uses `_valid_category`, which excludes `ordinary_missing`, `structural_missing`, and `invalid`: lines 478-483.
- `_execute_rm_respondent_metric`: starts at line 255.
- RM respondent uses M4 `record.selected` / `record.not_selected`: lines 277 and 280.
- `_execute_rm_mention_metric`: starts at line 324.
- RM mention requires M4 `DenominatorUnit.MENTION` ledger: line 334.
- M5 helpers are called via `base_from_ledger` and `value_from_formula`: lines 219/229, 290/300, 353/363.

There is no independent interpretation of physical raw `0`, `1`, missing values, or source variables.

## Respondent vs Mention Audit

Respondent path:

- `_execute_rm_respondent_metric`
- Requires M4 respondent-option ledger.
- Emits bases with `DenominatorUnit.RESPONDENT`.

Mention path:

- `_execute_rm_mention_metric`
- Requires M4 mention ledger.
- Emits bases with `DenominatorUnit.MENTION`.

Fail-closed evidence:

- `test_m5a_011_missing_mention_scope_fails_closed` asserts `ExecutionAdapterError` when the M4 mention ledger is absent.

## Test Commands and Results

- Focused adapter: `$env:PYTHONPATH='.'; pytest -q tests\test_m5_execution_adapter.py --basetemp .pytest_tmp_review_adapter` -> `28 passed`
- M2 regression: `$env:PYTHONPATH='.'; pytest -q tests\test_universe_evaluator.py tests\test_universe_evaluator_corrective.py tests\test_universe_evaluator_refs.py tests\test_universe_evaluator_response_states.py tests\test_universe_evaluator_scopes.py tests\test_contract_universe_schema.py --basetemp .pytest_tmp_review_m2` -> `38 passed`
- M3 regression: `$env:PYTHONPATH='.'; pytest -q tests\test_weight_runtime.py tests\test_contract_weight_policy.py --basetemp .pytest_tmp_review_m3` -> `45 passed`
- M4 regression: `$env:PYTHONPATH='.'; pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_structure_authority_corrective.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_review_m4` -> `61 passed`
- M5 regression: `$env:PYTHONPATH='.'; pytest -q tests\test_canonical_results_identity.py tests\test_canonical_results_formulas.py tests\test_canonical_results_bases_values.py tests\test_canonical_results_legacy_comparison.py tests\test_canonical_results_qa_release.py tests\test_canonical_results_serialization.py tests\test_canonical_results_significance_transport.py tests\test_canonical_results_upstream_integration.py tests\test_contract_canonical_result.py tests\test_contract_metric_schema.py tests\test_m5_execution_adapter.py --basetemp .pytest_tmp_review_m5` -> `108 passed`
- M6 regression: `$env:PYTHONPATH='.'; pytest -q tests\test_m6_boundaries.py tests\test_m6_dual_run_comparison.py tests\test_m6_dual_run_runtime_remediation.py tests\test_m6_execution_modes.py tests\test_m6_qa_release_remediation.py tests\test_m6_release_export_remediation.py tests\test_m6_request_binding_remediation.py tests\test_m6_session_remediation.py tests\test_m6_significance_grain_remediation.py tests\test_m6_v3_request_slice_and_legacy_projection.py tests\test_m6_web_canonical_adapter.py tests\test_m6_web_canonical_cache.py --basetemp .pytest_tmp_review_m6` -> `97 passed`
- Legacy parity: `$env:PYTHONPATH='.'; pytest -q tests\test_core_wrapper_parity.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_review_legacy` -> `3 passed`
- Full regression: `$env:PYTHONPATH='.'; pytest -q --basetemp .pytest_tmp_review_full` -> `434 passed`

## M5A Assertion Mapping

| ID | Test function | Contract condition | Key assertions | Fixture/input nature | Expected result |
| --- | --- | --- | --- | --- | --- |
| M5A-001 | `test_m5a_001_ru_count_derivation` | RU COUNT derivation | Category A count estimate equals 1 | Synthetic M4 RU records | PASS |
| M5A-002 | `test_m5a_002_ru_proportion_derivation` | RU PROPORTION derivation | Category A proportion estimate equals 0.5 | Synthetic M4 RU records | PASS |
| M5A-003 | `test_m5a_003_ru_invalid_missing_follows_m4` | RU invalid/missing follows M4 | Denominator 2, numerator 1 | Synthetic M4 RU records with ordinary missing and invalid | PASS |
| M5A-004 | `test_m5a_004_rm_respondent_selected_numerator` | RM respondent selected numerator | Option A numerator equals 1 | Synthetic M4 RM records | PASS |
| M5A-005 | `test_m5a_005_rm_respondent_valid_denominator` | RM respondent valid denominator | Option A denominator equals 2 | Synthetic M4 RM records | PASS |
| M5A-006 | `test_m5a_006_all_zero_valid_respondent_remains_denominator` | All-zero valid respondent remains denominator | Numerator 0, denominator 2, status OK | Synthetic M4 `NOT_SELECTED` records | PASS |
| M5A-007 | `test_m5a_007_structural_ordinary_missing_excluded` | Structural/ordinary missing excluded | Denominator remains 2 | Synthetic M4 records with structural and ordinary missing | PASS |
| M5A-008 | `test_m5a_008_rm_mention_numerator` | RM mention numerator | Option A mention numerator equals 1 | Synthetic M4 RM selected records | PASS |
| M5A-009 | `test_m5a_009_rm_mention_denominator` | RM mention denominator | Option A mention denominator equals 2 | Synthetic M4 mention ledger | PASS |
| M5A-010 | `test_m5a_010_respondent_vs_mention_separation` | Respondent vs mention separation | Respondent base unit differs from mention base unit | Synthetic M4 ledgers | PASS |
| M5A-011 | `test_m5a_011_missing_mention_scope_fails_closed` | Missing mention scope fails closed | Raises `ExecutionAdapterError` | Synthetic M4 result lacking mention ledger | PASS |
| M5A-012 | `test_m5a_012_event_category_proportion` | Event/category proportion | Single category B value, estimate 0.5 | Synthetic RU records, released category param | PASS |
| M5A-013 | `test_m5a_013_filtered_slice_uses_m2_authority` | Filtered slice uses M2 authority | Denominator 1, estimate 1 | Synthetic M2 slice mask | PASS |
| M5A-014 | `test_m5a_014_banner_slices_remain_separate` | Banner slices remain separate | Two slices, estimates [1, 0] | Synthetic M2 banner slice masks | PASS |
| M5A-015 | `test_m5a_015_unweighted_execution` | Unweighted execution | No active weight, weighted_n null | Synthetic unweighted context | PASS |
| M5A-016 | `test_m5a_016_weighted_request_without_m3_fails_closed` | Weighted request without M3 fails closed | Raises `ExecutionAdapterError` | Synthetic weighted metric without M3 result | PASS |
| M5A-017 | `test_m5a_017_unsupported_metric_fails_closed` | Unsupported metric fails closed | Raises `ExecutionAdapterError` | Synthetic unknown formula ID | PASS |
| M5A-018 | `test_m5a_018_metric_structure_incompatibility_fails_closed` | Metric/structure incompatibility fails closed | Raises `ExecutionAdapterError` | Synthetic RM metric against RU structure | PASS |
| M5A-019 | `test_m5a_019_missing_upstream_authority_fails_closed` | Missing/incompatible upstream authority fails closed | Raises `ExecutionAdapterError` on M2 FAIL | Synthetic failing M2 result | PASS |
| M5A-020 | `test_m5a_020_no_legacy_fallback` | Legacy fallback unavailable | Adapter imports do not include `src.reporter` | AST source audit | PASS |
| M5A-021 | `test_m5a_021_no_web_calculation_dependency` | Web dependency unavailable | Adapter imports do not include `src.web_canonical` | AST source audit | PASS |
| M5A-022 | `test_m5a_022_deterministic_execution_input` | Deterministic execution input | Result fingerprints match | Repeated synthetic execution | PASS |
| M5A-023 | `test_m5a_023_complete_provenance` | Complete provenance | Runtime/request/metric refs present | Synthetic execution with provenance refs | PASS |
| M5A-024 | `test_m5a_024_ba_01_adapter_path` | BA-01 adapter path | Request id BA-01, 4 values | Synthetic BA-named adapter fixture | PASS |
| M5A-025 | `test_m5a_025_ba_02_adapter_path` | BA-02 adapter path | Request id BA-02, formula RM_RESPONDENT_PROPORTION | Synthetic BA-named adapter fixture | PASS |
| M5A-026 | `test_m5a_026_ba_03_adapter_path` | BA-03 adapter path | Request id BA-03, formula RM_MENTION_PROPORTION | Synthetic BA-named adapter fixture | PASS |
| M5A-027 | `test_m5a_027_ba_04_adapter_path` | BA-04 adapter path | Request id BA-04, filter ref preserved | Synthetic BA-named adapter fixture | PASS |
| M5A-028 | `test_m5a_028_ba_05_adapter_path` | BA-05 adapter path | Request id BA-05, banner members SEG_1/SEG_2 preserved | Synthetic BA-named adapter fixture | PASS |

## Critical Assertion Review

- M5A-003: line 219 asserts denominator `2`; line 220 asserts numerator `1`.
- M5A-006: lines 248-250 assert numerator `0`, denominator `2`, ValueStatus `OK`.
- M5A-007: line 256 asserts denominator `2`, excluding structural/ordinary missing records.
- M5A-010: lines 275-276 assert separate `RESPONDENT` and `MENTION` denominator units.
- M5A-011: line 280 asserts fail-closed `ExecutionAdapterError`.
- M5A-013: lines 303-304 assert filtered slice denominator `1` and estimate `1`.
- M5A-014: lines 316-317 assert two slices and separate estimates `[1, 0]`.
- M5A-016: line 328 asserts weighted-without-M3 fail closed.
- M5A-018: line 338 asserts metric/structure incompatibility fail closed.
- M5A-020: line 365 asserts no `src.reporter` import.
- M5A-021: line 375 asserts no `src.web_canonical` import.
- M5A-024: lines 398-399 assert BA-01 request id and value count.
- M5A-025: lines 405-406 assert BA-02 id and respondent formula.
- M5A-026: lines 412-413 assert BA-03 id and mention formula.
- M5A-027: lines 420-421 assert BA-04 id and filter ref.
- M5A-028: lines 434-435 assert BA-05 id and banner members.

## BA Test Nature

- BA-01 adapter test nature: SYNTHETIC
- BA-02 adapter test nature: SYNTHETIC
- BA-03 adapter test nature: SYNTHETIC
- BA-04 adapter test nature: SYNTHETIC
- BA-05 adapter test nature: SYNTHETIC

These tests do not use the frozen physical Benchmark A SAV or RELEASED package. They validate adapter paths only.

## Fail-Closed Audit

Directly tested:

- Missing/incompatible M2 status: M5A-019.
- Missing required M3 for weighted request: M5A-016.
- Missing mention ledger/scope: M5A-011.
- Metric/structure incompatibility: M5A-018.
- Unknown/unsupported formula: M5A-017.
- No Legacy fallback/import: M5A-020.
- No Web fallback/import: M5A-021.

Source-supported but not separately directly tested:

- Missing M2 object: `_require_universe`.
- Missing M4 result: `_validate_context`.
- Missing respondent ledger: `_require_ledger`.
- Denominator unit mismatch: `_require_ledger`.
- Non-finite analytical input: `_require_finite`.
- Ambiguous mention authority: `_require_ledger`.

Partially tested:

- Incomplete provenance: M5A-023 checks positive provenance presence, but no negative fail-closed provenance test exists.

## Protected Source Audit

Protected source inventory: `evidence/m5_execution_adapter_review/hashes/protected_source_hash_inventory.json`

Protected inventory count: `36`

Changed against physically available prior protected hashes: `0`

Files with current hash only and no prior physical baseline: `28`

For those files, status is `CURRENT HASH RECORDED / PRIOR PHYSICAL BASELINE NOT AVAILABLE`.

## Test Inventory Reconciliation

Reported prior full suite before adapter implementation: `406 passed`.

Focused adapter tests: `28 passed`.

Current full suite: `434 passed`.

Arithmetic reconciliation: `406 + 28 = 434`.

Pre-existing test removals, renames, disablements, or weakenings: UNVERIFIED because no Git metadata or prior physical test inventory for the exact pre-adapter state is available in this workspace.

## Warnings

- `PYTHONPATH=.` is required for test collection.
- Local `--basetemp` is required to avoid a Windows permission issue in the default pytest temp root.
- BA-01..BA-05 adapter tests are SYNTHETIC, not PRODUCTIVE.
- No Git metadata is available.
- Materialization implementation has not resumed.
- Gate 19 remains BLOCKED.
