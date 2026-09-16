# M6 - Web Migration to Canonical Results Remediation V3 Manifest

Date: 2026-09-15

## Status

M6 V3 corrective remediation prepared for final human re-gate.

## Pre-Change Baseline

- Focused M6: 90 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Reported full suite: 399 PASS / 0 FAIL / 0 SKIP

## Final Verification

- Focused M6: 97 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 406 PASS / 0 FAIL / 0 SKIP

## Files Created

- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATION_V3.md`
- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATION_V3_MANIFEST.md`
- `explora_web_reporter/src/web_canonical/legacy_projection.py`
- `explora_web_reporter/tests/test_m6_v3_request_slice_and_legacy_projection.py`

## Files Modified

- `explora_web_reporter/src/analytics_core/runner.py`
- `explora_web_reporter/src/web_canonical/request_binding.py`
- `explora_web_reporter/src/web_canonical/comparison.py`
- `explora_web_reporter/src/web_canonical/__init__.py`
- `explora_web_reporter/tests/m6_fixtures.py`
- `explora_web_reporter/tests/test_m6_request_binding_remediation.py`
- `explora_web_reporter/tests/test_m6_dual_run_runtime_remediation.py`

## Contract Files

Contract files modified in V3 remediation: NO.

## Corrective Status

- B-M6-IMPL-01: CLOSED
- B-M6-IMPL-02: CLOSED
- B-M6-IMPL-03: REGRESSION PASS
- B-M6-IMPL-04: REGRESSION PASS
- B-M6-IMPL-05: REGRESSION PASS
- B-M6-IMPL-06: CLOSED

## Binding Evidence

- Filtered request cannot use unfiltered Total slice.
- Total slice filter identity must exactly equal requested filter identity.
- Extra analytical filters on a selected slice are rejected.
- Equivalent filter order is accepted after deterministic normalization.
- Actual Web banner shape `banner=("segment",)` requires banner slice coverage.
- Required slice coverage is derived from normalized Web request, not from
  manual `requested_slice_ids`.

## DUAL_RUN Evidence

- Productive DUAL_RUN uses actual `LegacyAdapter.generate()` output.
- Legacy comparison records are projected from actual `ReportResult.summary`.
- Canonical comparison records are projected from actual `CanonicalResult`.
- Side-channel comparison records do not control productive DUAL_RUN.
- Actual equal values classify PARITY.
- Actual unexplained deltas classify POTENTIAL_REGRESSION and block readiness.
- Unmappable Legacy records emit structured limitations without fabricated IDs.

## Protected Hashes

- `src/analytics_core/universe.py`:
  `D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E`
- `src/analytics_core/weights.py`:
  `AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B`
- `src/analytics_core/structure.py`:
  `CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56`
- `src/analytics_core/results.py`:
  `17B7D6BE6DD9408AC1673F743D7BC34D174E7CA38949FE100A8217E256020B53`
- `src/analytics_core/result_identity.py`:
  `1925B1B8892D293838FD3A396A32499BCAF5F628B66464B0BD81A1C4D3B43696`
- `src/analytics_core/serialization.py`:
  `DC750044B8D0008C5848AB7E73ACE309C579174089827104E7A7E900F179865B`
- `src/analytics_core/formula_registry.py`:
  `00A617CBAA00D7B922870E8A34C9BC331C6721DBA352CD10D6DC6E4BC822B6DA`
- `src/reporter/tabulator.py`:
  `A450E331001417855B296709771E35CE82DF39806F62E1DA67D107608BDDC740`
- `src/reporter/calculations.py`:
  `1C49046DB3387D1161A6FFEBEDBF5D2F92061F79442F9B97959C2F64F3A05C10`
- `src/reporter/filters.py`:
  `1F654641DD4E33FB054F1B72551849B65D78F15E4B2E9A75E3A395A0E2D6B223`
- `src/reporter/banners.py`:
  `2190BDF975D5DC59C24809B0547CA31A8F76D9255ECD24839FA1685F05FC945D`
- `src/reporter/significance.py`:
  `33CC670C49838F41EBF3DC190EFF7FD342CF641CADA8EC03EC6AB94C0603C007`

## Database / Excel / M7

- SQLite schema changed: NO
- Productive SQLite migration: NO
- Excel dashboard migration started: NO
- M7 started: NO

## Dependency Changes

No dependency changes.

## Checkpoint

Checkpoint filename:

- `checkpoints/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATED_V3_2026-09-15.zip`

Checkpoint SHA-256:

- Reported externally after archive freeze.

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

## Open Warnings

- Production default remains `LEGACY`.
- Productive Grid/Loop benchmark remains pending by human-accepted warning.
- Canonical productive execution still requires upstream `CanonicalResult`.
- M5 QAEvent severity remains an upstream warning; no M5 change made.
