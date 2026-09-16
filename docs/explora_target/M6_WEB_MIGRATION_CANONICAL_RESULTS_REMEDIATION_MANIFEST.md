# M6 - Web Migration to Canonical Results Remediation Manifest

Date: 2026-09-15

## Status

M6 targeted corrective remediation prepared for human re-gate.

## Pre-Change Baseline

- Focused M6: 46 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Reported full baseline: 355 PASS / 0 FAIL / 0 SKIP

## Final Verification

- Focused M6: 80 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 389 PASS / 0 FAIL / 0 SKIP

## Files Created

- `src/web_canonical/request_binding.py`
- `src/web_canonical/session.py`
- `src/web_canonical/export.py`
- `tests/test_m6_request_binding_remediation.py`
- `tests/test_m6_dual_run_runtime_remediation.py`
- `tests/test_m6_significance_grain_remediation.py`
- `tests/test_m6_release_export_remediation.py`
- `tests/test_m6_session_remediation.py`
- `tests/test_m6_qa_release_remediation.py`
- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATION.md`
- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATION_MANIFEST.md`

## Files Modified

- `src/analytics_core/runner.py`
- `src/ui/page_04_reporter.py`
- `src/ui/page_05_significance.py`
- `src/ui/page_06_export.py`
- `src/web_canonical/__init__.py`
- `src/web_canonical/adapter.py`
- `src/web_canonical/significance.py`
- M6 remediation tests

## Contract Files

Contract files modified in corrective remediation: NO.

The prior additive M6 execution-mode extension remains unchanged.

## Corrective Status

- B-M6-IMPL-01: CLOSED
- B-M6-IMPL-02: CLOSED
- B-M6-IMPL-03: CLOSED
- B-M6-IMPL-04: CLOSED
- B-M6-IMPL-05: CLOSED
- B-M6-IMPL-06: CLOSED

## Protected Areas

No functional changes were made to:

- `src/analytics_core/universe.py`
- `src/analytics_core/weights.py`
- `src/analytics_core/structure.py`
- `src/analytics_core/results.py`
- `src/analytics_core/result_identity.py`
- `src/analytics_core/serialization.py`
- `src/analytics_core/formula_registry.py`
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

- `checkpoints/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATED_2026-09-15.zip`

Checkpoint SHA-256:

- Recorded in final response after archive freeze.

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

## Open Warnings

- Production default remains `LEGACY`.
- Productive Grid/Loop benchmark remains pending by human-accepted warning.
- Canonical productive execution still requires upstream `CanonicalResult`.
