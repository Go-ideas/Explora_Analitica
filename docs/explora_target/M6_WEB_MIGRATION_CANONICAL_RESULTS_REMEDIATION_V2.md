# M6 - Web Migration to Canonical Results Remediation V2

Date: 2026-09-15

Status: final targeted corrective remediation implemented for re-gate.

## Scope

The M6 final re-gate left three blockers open:

- B-M6-IMPL-01 - Request / Result Binding
- B-M6-IMPL-02 - DUAL_RUN Runtime Comparison
- B-M6-IMPL-06 - Contract Test Matrix

Previously closed blockers remain closed:

- B-M6-IMPL-03 - significance grain
- B-M6-IMPL-04 - release/export gating
- B-M6-IMPL-05 - session stale-state protection

## B-M6-IMPL-01

Request/result binding now uses normalized semantic equality for analytical
request components. It no longer treats filters or banners as subset coverage.

Examples now rejected:

- Web filters `{}` vs Canonical filters `{"region": ("north",)}`
- Web filter `north` vs Canonical filters `{}`
- Web no banner / Total vs Canonical banner `segment_a`
- Web banner `segment_a` vs Canonical no banner

Equivalent ordering of the same normalized values remains accepted.

Required slice coverage is derived from the normalized Web request:

- Total-only request requires Total slice.
- Banner request requires the matching banner/member slice.
- Filter/banner request requires the matching canonical slice coverage.

Manual `requested_slice_ids` remains an additional guard, but is not the only
coverage mechanism.

## B-M6-IMPL-02

`DUAL_RUN` comparison no longer accepts side-channel records as authoritative
runtime comparison inputs.

Runtime comparison records are derived from:

- the actual Legacy result produced by the `DUAL_RUN` execution;
- the actual `CanonicalResult` bound to that same execution.

M6-only options are sanitized before calling Legacy. The Legacy tabulator was
not modified.

False parity prevention is implemented: when actual Legacy and Canonical
values differ, a `PARITY` classification is rejected and converted to
`POTENTIAL_REGRESSION`, which blocks migration/default switch readiness.

If Legacy output lacks deterministic semantic identity, runtime reports a
matching limitation / review condition rather than fabricating IDs from
labels.

## B-M6-IMPL-06

Focused M6 coverage increased from 80 to 90 tests.

New/updated integration coverage includes:

- filter absence vs presence in both directions;
- banner absence vs presence in both directions;
- exact normalized filter and banner matching;
- request-derived slice coverage;
- missing banner/filter slice without manual `requested_slice_ids`;
- actual Legacy artifact comparison;
- actual CanonicalResult comparison;
- side-channel parity prevention;
- M6-only option sanitization before Legacy;
- real `LegacyAdapter.generate` DUAL_RUN path;
- comparison provenance;
- previously closed significance/export/session tests.

## Test Evidence

Pre-change baseline:

- Focused M6: 80 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Reported full suite: 389 PASS / 0 FAIL / 0 SKIP

Post-change verification:

- Focused M6: 90 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 399 PASS / 0 FAIL / 0 SKIP

## Protected Areas

No changes were made to M2, M3, M4, M5 analytical modules, B1/B2/B3 policies,
Legacy analytical reporter modules, productive SQLite schema, Excel, or M7.

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
