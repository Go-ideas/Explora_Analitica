# M6 - Web Migration to Canonical Results Remediation V3

Date: 2026-09-15

Status: final corrective remediation implemented for M6 re-gate.

## Scope

This pass is limited to the remaining V2 gate blockers:

- B-M6-IMPL-01 - Request / Result Binding
- B-M6-IMPL-02 - DUAL_RUN Runtime Comparison
- B-M6-IMPL-06 - Contract Test Matrix

Previously resolved blockers remain regression-covered:

- B-M6-IMPL-03 - significance grain
- B-M6-IMPL-04 - release/export gating
- B-M6-IMPL-05 - session stale-state protection

No M2, M3, M4, M5, B1, B2, B3, Legacy analytical calculation, SQLite, Excel,
or M7 changes are included.

## B-M6-IMPL-01

Request binding now validates both request semantic identity and effective
CanonicalSlice coverage.

The V3 binding path derives required slice descriptors from the normalized Web
request, independent of manual `requested_slice_ids`. Descriptors include:

- Total/member status;
- banner dimension/member identity when available;
- exact normalized filter identity;
- actual Web banner shape such as `banner=("segment",)` and
  `banner_mode="nested"`.

Filtered Total requests now require a Total slice with exactly the requested
filter identity. Unfiltered Total slices no longer satisfy filtered requests.
Slices with extra unrequested filters are rejected. Equivalent filter ordering
is normalized deterministically.

## B-M6-IMPL-02

Productive DUAL_RUN now derives comparison records from the actual artifacts in
the execution:

- `LegacyAdapter.generate()` produces the actual Legacy `ReportResult`;
- `legacy_projection.py` projects comparable values from that ReportResult;
- the bound `CanonicalResult` is projected from its actual bases, values, and
  slices;
- semantic matching, classification, aggregate status, and blocking are applied
  after both projections.

Side-channel `legacy_comparison_records` and `canonical_comparison_records` no
longer control productive DUAL_RUN. They remain sanitized away from Legacy
execution and are ignored by runtime comparison.

Legacy projection does not recalculate percentages, bases, weights,
significance, or canonical values. It reads already-produced Legacy summary
outputs and emits limitations for records that cannot be deterministically
mapped without fabricating IDs from labels.

## B-M6-IMPL-06

Focused M6 coverage increased from 90 to 97 tests.

New V3 coverage includes:

- filtered request with unfiltered Total slice rejection;
- exact filtered Total acceptance;
- extra filter rejection;
- missing filter rejection;
- equivalent filter order acceptance;
- actual Web banner shape with missing banner slice rejection;
- actual Web banner shape with valid banner slice acceptance;
- runner-level request/slice binding without manual `requested_slice_ids`;
- real LegacyAdapter DUAL_RUN producing comparison records;
- actual Legacy/Canonical parity;
- actual Legacy/Canonical delta classified as POTENTIAL_REGRESSION;
- actual POTENTIAL_REGRESSION blocking;
- side-channel records ignored in productive DUAL_RUN;
- partial Legacy identity limitation without fabricated IDs.

## Test Evidence

Pre-change baseline:

- Focused M6: 90 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Reported full suite: 399 PASS / 0 FAIL / 0 SKIP

Post-change verification:

- Focused M6: 97 PASS / 0 FAIL / 0 SKIP
- M5 focused: 72 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full suite: 406 PASS / 0 FAIL / 0 SKIP

## Protected Areas

Verified unchanged by SHA-256:

- M2 `src/analytics_core/universe.py`
- M3 `src/analytics_core/weights.py`
- M4 `src/analytics_core/structure.py`
- M5 analytical result modules
- Legacy analytical reporter modules

## Productive Grid / Loop

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
