# EXPLORA - M5 CANONICAL RESULTS REMEDIATION

**Milestone:** M5 - Canonical Results corrective remediation
**Date:** 2026-09-14
**Authority:** `M5_CANONICAL_RESULTS_IMPLEMENTATION_CONTRACT.md`
**Scope:** targeted remediation only

## Status

M5 corrective remediation addresses the four implementation blockers identified
by the final gate. M6 was not started.

## B-M5-IMPL-01 - Result Fingerprint / Deterministic Ordering

Root cause:

`result_fingerprint` hashed canonical collections in the order supplied by
runtime construction. Equivalent `slices`, `bases`, `values`, `comparisons` and
`qa_events` permutations could produce different fingerprints.

Source correction:

`src/analytics_core/result_identity.py` now canonicalizes M5 collections before
hashing. Run-scoped IDs, compatibility QA envelope fields, labels, timestamps
and renderer metadata remain excluded from the semantic fingerprint.

Tests added:

Focused tests now permute canonical collections and verify identical
`result_fingerprint` for equivalent analytical semantics.

Final behavior:

Accidental construction order does not affect the analytical fingerprint.

## B-M5-IMPL-02 - Non-Finite Handling + QA

Root cause:

Formula execution could silently drop non-finite observations and still return
`ValueStatus.OK`.

Source correction:

`src/analytics_core/formula_registry.py` now treats non-finite M5 analytical
inputs or outputs as formula errors instead of silently excluding them.
`src/analytics_core/results.py` converts those non-OK formula outcomes into
structured QA events with null estimates.

Tests added:

Focused tests cover `NaN`, `+Infinity`, `-Infinity`, non-finite formula output,
null estimate, QA event generation and serialization with no NaN/Infinity.

Final behavior:

M5 does not silently discard non-finite analytical evidence.

## B-M5-IMPL-03 - Unknown / Unsupported Formula QA + Release

Root cause:

Unknown formula IDs raised a low-level registry exception without producing a
blocking QA event and non-releasable CanonicalResult. Known unsupported
combinations returned `UNSUPPORTED` without auditable QA.

Source correction:

`src/analytics_core/results.py` adds `value_and_qa_from_formula`, which returns
both the canonical value and the QA events required by the M5 contract.
Unknown formulas produce blocking `UNKNOWN_FORMULA_ID` QA and `ValueStatus.ERROR`.
Known unsupported combinations produce `ValueStatus.UNSUPPORTED` plus structured
QA.

Tests added:

Focused paired tests cover unknown formula vs known unsupported formula and
verify release consumption of blocking QA.

Final behavior:

Unknown configuration errors and unsupported combinations are no longer
collapsed into the same path.

## B-M5-IMPL-04 - Release Model / B3 Conservative Gate

Root cause:

`derive_release_state(())` treated absence of QA events as sufficient release
evidence and returned `PASS / releasable=true`.

Source correction:

Release derivation now requires explicit positive `b3_release_evidence` before
marking a run releasable. Empty QA without B3 evidence yields
`REVIEW_REQUIRED / releasable=false`. Blocking QA, `FAIL` and `REVIEW_REQUIRED`
states force `releasable=false`.

Tests added:

Focused release tests cover conservative fallback, positive B3-compatible
evidence, blocking QA, review-required events, failed computation,
`PASS_WITH_WARNINGS`, unknown formula blocking QA and potential regression
blocking behavior.

Final behavior:

Numbers and empty QA alone do not imply release eligibility.

## Coverage Additions

M5 focused coverage was expanded from 39 to 63 tests.

Additional coverage demonstrates:

- fingerprint permutation invariance;
- serialization permutation invariance;
- RU count, proportion, valid zero, no valid base, mean, standard deviation,
  Top Box and Bottom Box;
- RM respondent and RM mention bases/values as distinct M4-denominator
  consumers;
- GRID_ESCALA, GRID_RM, LOOP_RU, LOOP_RM and LOOP_NUMERICO canonical assembly;
- LOOP_RANGO remains outside authorized V1 execution;
- significance transport states for not requested, unsupported, ineligible,
  tested not significant and tested significant fixtures;
- upstream QA domain preservation for Universe, Weight, Structure and
  Statistical evidence.

## Test Evidence

Pre-change baseline:

`276 PASS / 0 FAIL / 0 SKIP`

Pre-change focused M5:

`39 PASS / 0 FAIL / 0 SKIP`

Pre-change Legacy parity:

`2 PASS / 0 FAIL / 0 SKIP`

Post-remediation focused M5:

`63 PASS / 0 FAIL / 0 SKIP`

Post-remediation full regression:

`300 PASS / 0 FAIL / 0 SKIP`

Post-remediation Legacy parity:

`2 PASS / 0 FAIL / 0 SKIP`

## Protected Invariance

M2, M3, M4, productive Legacy reporter files, significance runtime,
RM/Grid/Scale builders, `grid_loop_detector.py`, Web/UI, SQLite, Excel, VBA and
NG were not modified.

## Productive Grid / Loop Benchmark

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

No productive Grid/Loop validation is claimed by this remediation.
