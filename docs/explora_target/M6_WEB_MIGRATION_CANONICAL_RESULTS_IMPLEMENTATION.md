# M6 - Web Migration to Canonical Results Implementation

Date: 2026-09-14

Status: implemented for human review.

## Authority

M6 authority:

- `docs/explora_target/M6_WEB_MIGRATION_CANONICAL_RESULTS_CONTRACT.md`

Frozen upstream authorities remain unchanged:

- M2 Universe
- M3 Weight
- M4 Structure / denominators
- M5 Canonical Results
- B1 Weight policy
- B2 Significance policy
- B3 Release policy

## Scope

M6 introduces an explicit Web-side canonical projection layer that consumes
`CanonicalResult` and produces renderer-friendly tables, QA summaries,
release summaries, cache identity, and significance presentation tokens.

The adapter is downstream of Canonical Results. It does not calculate
analytical truth.

## Execution Modes

The execution mode vocabulary was extended additively:

- `LEGACY`
- `CORE_WRAPPER`
- `CANONICAL_V1`
- `DUAL_RUN`

`LEGACY` remains the default when no mode is configured.

`CANONICAL_V1` requires an explicit `CanonicalResult`. If it is missing, the
runner raises an explicit error. It does not silently fall back to Legacy.

`DUAL_RUN` executes Legacy and Canonical separately, then exposes both
artifacts for downstream comparison/projection. Canonical cells are never
filled from Legacy output.

## Web Canonical Package

New package:

- `src/web_canonical/models.py`
- `src/web_canonical/adapter.py`
- `src/web_canonical/significance.py`
- `src/web_canonical/cache.py`
- `src/web_canonical/comparison.py`
- `src/web_canonical/__init__.py`

Responsibilities:

- project `CanonicalResult` into a Web presentation model;
- preserve `result_run_id`, `result_fingerprint`, `request_fingerprint`,
  `value_id`, and `base_id`;
- render M5 `ValueStatus` without adding new status vocabulary;
- group QA and release state without changing semantics;
- create deterministic canonical cache keys;
- create presentation-only significance letters from canonical relations;
- compare DUAL_RUN records using the frozen M5/M6 classification vocabulary.

## Prohibited Behavior

Canonical Web mode does not:

- read raw respondent tables for analytical calculation;
- recalculate estimates;
- recalculate bases or denominators;
- rebuild Universe, filters, banners, weights, or structures;
- execute significance tests;
- mutate M5 values, statuses, release state, or QA;
- reverse-engineer `CanonicalResult` from `ReportResult`;
- silently fall back to Legacy.

## UI Integration

`page_04_reporter.py` now routes explicit execution modes through
`src.analytics_core.runner.generate_report`.

Session artifacts are separated:

- `current_report`: Legacy presentation artifact only.
- `current_report_legacy`: explicit Legacy artifact.
- `current_canonical_result`: canonical analytical authority.
- `current_canonical_projection`: renderer-friendly canonical projection.
- `current_result_contract`: `reportresult_legacy`, `canonical_v1`, or
  `dual_run`.

`page_05_significance.py` uses the same mode boundary. Canonical significance
rendering consumes `SignificanceRelation`; it does not run statistical tests.

`page_06_export.py` keeps existing Legacy executive exports and adds a
canonical CSV projection export with traceability fields. This is not M7 and
does not implement the Excel dashboard migration.

## DUAL_RUN

Allowed classifications only:

- `PARITY`
- `INTENDED_CORRECTION`
- `M2_BASE_DIFFERENCE`
- `M3_WEIGHT_DIFFERENCE`
- `M4_STRUCTURE_DIFFERENCE`
- `UNSUPPORTED_V1`
- `POTENTIAL_REGRESSION`
- `PRESENTATION_ONLY`

Unexplained deltas default to `POTENTIAL_REGRESSION`.

`POTENTIAL_REGRESSION` blocks migration/default switch.

Cross-run matching uses semantic identity and does not rely solely on M5
run-scoped `base_id` or `value_id`.

## Productive Grid / Loop Warning

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

M6 does not convert renderer validation into productive structure validation.

## Test Evidence

Pre-change baseline:

- Full suite: 309 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

Implementation verification before packaging:

- Focused M6: 46 PASS / 0 FAIL / 0 SKIP
- Full suite: 355 PASS / 0 FAIL / 0 SKIP

Final test evidence is recorded in the M6 manifest and final gate response.
