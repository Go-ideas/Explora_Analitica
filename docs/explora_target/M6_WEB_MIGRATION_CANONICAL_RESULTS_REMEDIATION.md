# M6 - Web Migration to Canonical Results Remediation

Date: 2026-09-15

Status: targeted corrective remediation implemented for human re-gate.

## Gate Result Remediated

Previous gate result:

- FAIL - IMPLEMENTATION NONCONFORMANT

Corrective scope:

- B-M6-IMPL-01 - Canonical request / result binding
- B-M6-IMPL-02 - DUAL_RUN runtime comparison
- B-M6-IMPL-03 - significance presentation grain
- B-M6-IMPL-04 - release-gated exports
- B-M6-IMPL-05 - stale session authority
- B-M6-IMPL-06 - contract test matrix closure

## B-M6-IMPL-01

Implemented deterministic request/result binding in
`src/web_canonical/request_binding.py`.

Validated request dimensions:

- question identity
- metric refs
- filters
- banner configuration
- weight override
- execution options
- request fingerprint
- requested slice coverage

If the supplied `CanonicalResult` does not cover the current Web request,
runtime raises `CanonicalRequestBindingError` with
`NEW_CORE_EXECUTION_REQUIRED`.

No fallback to Legacy occurs.

## B-M6-IMPL-02

`DUAL_RUN` now performs runtime comparison in
`src/analytics_core/runner.py`.

`DualRunExecution` now carries:

- legacy result reference
- canonical result reference
- comparison result
- aggregate comparison status
- `potential_regression`
- limitations
- observability payload

Unexplained deltas become `POTENTIAL_REGRESSION` and block migration/default
switch readiness.

If Legacy lacks deterministic semantic identity records, runtime reports a
matching limitation / review condition rather than inventing IDs from labels.

## B-M6-IMPL-03

Significance presentation tokens are no longer attached globally by `slice_id`.

Tokens are attached to `CanonicalValue` only when:

- the value references the canonical `comparison_id`;
- question identity matches;
- metric identity matches;
- the value slice participates in the pairwise relation.

Letters remain presentation-only. No B2 statistics are executed or changed.

## B-M6-IMPL-04

Implemented release-gated canonical export paths in
`src/web_canonical/export.py`.

Export paths:

- `OFFICIAL_RELEASED_EXPORT`
- `INTERNAL_QA_EXPORT`

Official export requires `releasable=true`.

Non-releasable canonical output can be exported only through explicit internal
QA export.

## B-M6-IMPL-05

Implemented request-bound session safeguards in `src/web_canonical/session.py`.

Every current analysis artifact is bound to:

- execution mode
- request identity
- question ids
- request fingerprint
- result run id when applicable
- result fingerprint when applicable

New execution attempts invalidate the previous current analysis before
running. Failures clear current result state and record the failed binding.

Rollback is explicit and recorded as an observability event.

## B-M6-IMPL-06

Added integration tests for:

- request/result binding
- question/metric/filter/banner/weight mismatch
- slice coverage
- DUAL_RUN runtime comparison
- all eight frozen comparison classifications
- `POTENTIAL_REGRESSION` blocking
- significance cross-metric/question/family/scope grain
- release-gated exports
- internal QA export
- stale session invalidation
- explicit rollback observability
- QA projection
- release state preservation

## Test Evidence

Pre-change baseline:

- Focused M6: 46 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Reported full baseline: 355 PASS / 0 FAIL / 0 SKIP

Post-change:

- Focused M6: 80 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 389 PASS / 0 FAIL / 0 SKIP

## Protected Areas

No changes were made to M2, M3, M4, M5 analytical modules, B1/B2/B3 policy,
Legacy analytical reporter modules, productive SQLite schema, Excel, or M7.

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
