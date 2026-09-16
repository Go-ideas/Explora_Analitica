# M5 Canonical Results Ordering Remediation Manifest

Date: 2026-09-14

Checkpoint: `checkpoints/M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_2026-09-14.zip`

Runtime default: `LEGACY`

## Authority

- `docs/explora_target/M5_CANONICAL_RESULTS_IMPLEMENTATION_CONTRACT.md`

## Scope

This manifest covers only the final B-M5-IMPL-01 residual correction for
deterministic `release.reasons` ordering.

No M6 work was started.

## Pre-Change Test Result

- Full suite: 300 PASS / 0 FAIL / 0 SKIP
- Focused M5: 63 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## Final Test Result

- Focused M5: 72 PASS / 0 FAIL / 0 SKIP
- Full suite: 309 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## Files Modified

- `explora_web_reporter/src/analytics_core/result_identity.py`
- `explora_web_reporter/src/analytics_core/serialization.py`
- `explora_web_reporter/tests/test_canonical_results_identity.py`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`

## Files Created

- `docs/explora_target/M5_CANONICAL_RESULTS_ORDERING_REMEDIATION.md`
- `docs/explora_target/M5_CANONICAL_RESULTS_ORDERING_REMEDIATION_MANIFEST.md`
- `checkpoints/M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_2026-09-14.zip`

## Contract Files Modified

NO

## Canonicalization Evidence

- `release.reasons` insertion order no longer changes `result_fingerprint`.
- `release.reasons` insertion order no longer changes canonical JSON output.
- Different semantic reason content still changes `result_fingerprint`.
- Duplicate reasons preserve multiplicity.
- QA event ordering and release reason ordering are canonicalized independently.
- `result_run_id` remains excluded from fingerprint equivalence.
- `execution_timestamp` remains excluded from fingerprint equivalence.

## Regression Status

- B-M5-IMPL-02 remains RESOLVED.
- B-M5-IMPL-03 remains RESOLVED.
- B-M5-IMPL-04 remains RESOLVED.

## Invariance Evidence

- M2 `universe.py`: `D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E`
- M3 `weights.py`: `AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B`
- M4 `structure.py`: `CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56`

Protected Legacy source remains unchanged by this corrective pass.

## Scope Guard

- Dependency changes: NONE
- Database changes: NONE
- Web/UI changes: NONE
- Excel changes: NONE
- M6 changes: NONE
- Numerical deltas to productive Legacy: NONE

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

## Checkpoint Hash

The final checkpoint SHA-256 is reported after ZIP finalization to avoid a
self-referential archive hash.
