# M5 Canonical Results Ordering Remediation V2

Date: 2026-09-14

Scope: checkpoint recovery for B-M5-IMPL-01 and packaging identity only.

M6 was not started.

## Gate Recovery Context

The prior final re-gate received the stale checkpoint
`M5_CANONICAL_RESULTS_REMEDIATED_2026-09-14.zip`, whose SHA-256 is:

`EB30046FB4E49C8756A3B38DC18BA16B70BF11A32859570262F6E0ABB42179A3`

That archive did not contain the ordering remediation state. The current V2
checkpoint is created under a new filename to prevent another stale attachment
or identity error:

`checkpoints/M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_V2_2026-09-14.zip`

FINAL ZIP SHA RECORDED EXTERNALLY AFTER ARCHIVE FREEZE.

## Current Source Decision

The working source tree already contained the final ordering remediation before
this recovery pass.

New implementation code change required: NO.

No M5 runtime semantics were changed during this pass.

## Source Hashes

- `explora_web_reporter/src/analytics_core/result_identity.py`: `1925B1B8892D293838FD3A396A32499BCAF5F628B66464B0BD81A1C4D3B43696`
- `explora_web_reporter/src/analytics_core/serialization.py`: `DC750044B8D0008C5848AB7E73ACE309C579174089827104E7A7E900F179865B`

## Test Hashes

- `explora_web_reporter/tests/test_canonical_results_identity.py`: `E0772003BCC086E1C45003E000A500A97233A0BA0072BE73F49542E3199B9799`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`: `AACA34BA003F3672A608A395FCF4D8CD9F694E821D335862A13DDEF1B54891D7`

## Pytest Counts

- Focused M5: 72 PASS / 0 FAIL / 0 SKIP
- Full suite: 309 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## B-M5-IMPL-01 Behavior

`release.reasons` is canonicalized before result fingerprint calculation and
before canonical serialization.

The ordering key is deterministic semantic content:

- string reasons sort by their exact canonical string representation;
- structured reasons would sort by stable canonical serialization of their
  semantic fields.

Duplicate reasons are preserved. The frozen M5 contract does not define
`release.reasons` as set semantics.

Verified behavior:

- `[R1, R2]` and `[R2, R1]` serialize identically and fingerprint identically;
- all permutations of `[R1, R2, R3]` produce one canonical ordering, one
  canonical serialization, and one fingerprint;
- `[R1, R1, R2]` and `[R2, R1, R1]` preserve both `R1` occurrences;
- semantic reason change `R2 -> R9` changes the fingerprint;
- QA event ordering and release reason ordering are canonicalized independently;
- `result_run_id` remains excluded from fingerprint equivalence;
- `execution_timestamp` remains excluded from fingerprint equivalence.

## Checkpoint Contents

The V2 checkpoint includes:

- M5 canonical result source files;
- M5 contract extension files;
- all M5 canonical result test modules;
- implementation, remediation, ordering remediation, and V2 recovery docs;
- protected source required for audit where practical;
- app/config/test files needed to reproduce the suite where practical.

## Invariance

- M2 `universe.py`: `D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E`
- M3 `weights.py`: `AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B`
- M4 `structure.py`: `CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56`

Protected Legacy source, Web/UI, SQLite, Excel, NG, and B1/B2/B3 methodology
were not modified.

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
