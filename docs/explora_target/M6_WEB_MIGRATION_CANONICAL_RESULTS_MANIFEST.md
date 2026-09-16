# M6 - Web Migration to Canonical Results Manifest

Date: 2026-09-14

## Status

M6 implementation package prepared for human implementation review.

## Baseline

- Pre-change full suite: 309 PASS / 0 FAIL / 0 SKIP
- Pre-change M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Pre-change Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## Final Verification

- Focused M6: 46 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 355 PASS / 0 FAIL / 0 SKIP

## Files Created

- `src/web_canonical/__init__.py`
- `src/web_canonical/models.py`
- `src/web_canonical/adapter.py`
- `src/web_canonical/significance.py`
- `src/web_canonical/cache.py`
- `src/web_canonical/comparison.py`
- `tests/m6_fixtures.py`
- `tests/test_m6_execution_modes.py`
- `tests/test_m6_web_canonical_adapter.py`
- `tests/test_m6_web_canonical_cache.py`
- `tests/test_m6_dual_run_comparison.py`
- `tests/test_m6_boundaries.py`
- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_IMPLEMENTATION.md`
- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_MANIFEST.md`

## Files Modified

- `src/contracts/vocabulary.py`
- `src/analytics_core/runner.py`
- `src/ui/page_04_reporter.py`
- `src/ui/page_05_significance.py`
- `src/ui/page_06_export.py`
- `tests/test_core_execution_mode.py`
- `tests/test_contract_vocabularies.py`

## Contract Extension

Model/field:

- `ExecutionMode.CANONICAL_V1`
- `ExecutionMode.DUAL_RUN`

Additive: YES

Backward compatible: YES

Existing frozen analytical semantics changed: NO

## Execution Default

`LEGACY` remains default.

## Protected Areas

No functional changes were made to:

- M2 `src/analytics_core/universe.py`
- M3 `src/analytics_core/weights.py`
- M4 `src/analytics_core/structure.py`
- M5 `src/analytics_core/results.py`
- M5 `src/analytics_core/result_identity.py`
- M5 `src/analytics_core/serialization.py`
- M5 `src/analytics_core/formula_registry.py`
- Legacy analytical reporter files:
  - `src/reporter/tabulator.py`
  - `src/reporter/calculations.py`
  - `src/reporter/filters.py`
  - `src/reporter/banners.py`
  - `src/reporter/significance.py`

## Database / Excel / M7

- SQLite schema changed: NO
- Productive SQLite migration: NO
- Excel dashboard migration started: NO
- M7 started: NO

## Checkpoint

Checkpoint filename:

- `checkpoints/M6_WEB_MIGRATION_CANONICAL_RESULTS_2026-09-14.zip`

Checkpoint SHA-256:

- Recorded in final response after ZIP freeze.

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

## Known Warnings

- Canonical Web mode requires an upstream/supplied `CanonicalResult`.
- This milestone does not switch the production default.
- Productive Grid/Loop benchmark remains pending by human-accepted warning.
