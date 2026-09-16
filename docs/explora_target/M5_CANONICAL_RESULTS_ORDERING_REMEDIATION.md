# M5 Canonical Results Ordering Remediation

Date: 2026-09-14

Scope: final targeted corrective remediation for B-M5-IMPL-01 only.

M6 was not started.

## Residual Root Cause

The final M5 re-gate found that `release.reasons` preserved construction
order. Two semantically equivalent `CanonicalResult` objects containing the
same release reasons in different input order could produce different
canonical serialized output and different `result_fingerprint` values.

Insertion order is not analytical semantics for release reasons in M5.

## Canonicalization Rule

`release.reasons` is now sorted deterministically before:

- canonical serialization through `to_canonical_data`;
- result fingerprint payload generation through `result_fingerprint`.

The sort key is the stable canonical JSON representation of each reason item.
For V1 plain string reasons, this is deterministic ordering on the exact
canonical string representation.

## Multiplicity

Multiplicity is preserved. Duplicate reasons are not deduplicated, because the
frozen M5 contract does not define `release.reasons` as set semantics.

Example:

`("R2", "R1", "R1")` canonicalizes to `["R1", "R1", "R2"]`.

## Release Semantics

No release decision logic changed.

The following fields keep their previous semantics:

- `computation_status`;
- `qa_release_status`;
- `releasable`;
- B3 conservative fallback behavior.

Only deterministic representation/order changed.

## Files Changed

- `explora_web_reporter/src/analytics_core/result_identity.py`
- `explora_web_reporter/src/analytics_core/serialization.py`
- `explora_web_reporter/tests/test_canonical_results_identity.py`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`

## Tests Added

New ordering coverage verifies:

- `release.reasons` `[R1, R2]` and `[R2, R1]` have the same fingerprint;
- `release.reasons` `[R1, R2]` and `[R2, R1]` serialize identically;
- 3+ reason permutations canonicalize to the same output;
- semantic reason content changes alter the fingerprint;
- duplicate reason multiplicity is preserved;
- QA event order and release reason order are independently canonicalized;
- `result_run_id` remains excluded from fingerprint equivalence;
- `execution_timestamp` remains excluded from fingerprint equivalence;
- canonical JSON round-trip remains lossless after ordering.

## Verification

Pre-change baseline:

- Full suite: 300 PASS / 0 FAIL / 0 SKIP
- Focused M5: 63 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

Post-change verification:

- Focused M5: 72 PASS / 0 FAIL / 0 SKIP
- Full suite: 309 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

The observed gate case now produces the same fingerprint for both QA/release
reason orderings:

`c661825d7b8f6c8daa4a08f3f4fe180e91cbee3cca939dde383fb3aa4764cbe1`

## Invariance

The corrective pass did not modify:

- M2 Universe runtime;
- M3 Weight runtime;
- M4 Structure runtime;
- contract files;
- productive Legacy reporter files;
- significance runtime;
- RM/Grid/Scale builders;
- `grid_loop_detector.py`;
- Web/UI;
- SQLite;
- Excel;
- NG;
- B1/B2/B3 methodology.

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
