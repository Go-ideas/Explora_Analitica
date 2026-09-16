# M5 Canonical Results Ordering Remediation V2 Manifest

Date: 2026-09-14

Checkpoint: `checkpoints/M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_V2_2026-09-14.zip`

FINAL ZIP SHA RECORDED EXTERNALLY AFTER ARCHIVE FREEZE.

Runtime default: `LEGACY`

## Scope

This V2 package is a checkpoint recovery for B-M5-IMPL-01 and packaging
identity only.

The current working source already contained the final ordering fix. No
implementation code change was required in this recovery pass.

## Stale Checkpoint Evidence

Old checkpoint SHA-256:

`EB30046FB4E49C8756A3B38DC18BA16B70BF11A32859570262F6E0ABB42179A3`

That hash corresponds to
`M5_CANONICAL_RESULTS_REMEDIATED_2026-09-14.zip`, not this V2 checkpoint.

## Source Hashes

- `explora_web_reporter/src/analytics_core/result_identity.py`: `1925B1B8892D293838FD3A396A32499BCAF5F628B66464B0BD81A1C4D3B43696`
- `explora_web_reporter/src/analytics_core/serialization.py`: `DC750044B8D0008C5848AB7E73ACE309C579174089827104E7A7E900F179865B`

## Test Hashes

- `explora_web_reporter/tests/test_canonical_results_identity.py`: `E0772003BCC086E1C45003E000A500A97233A0BA0072BE73F49542E3199B9799`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`: `AACA34BA003F3672A608A395FCF4D8CD9F694E821D335862A13DDEF1B54891D7`

## Test Evidence

- Focused M5: 72 PASS / 0 FAIL / 0 SKIP
- Full suite: 309 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## Ordering Evidence

- Two-reason permutation: PASS
- Three-reason permutation: PASS
- Duplicate multiplicity preservation: PASS
- QA event order plus release reason order permutation: PASS
- Semantic reason change changes fingerprint: PASS
- `result_run_id` exclusion: PASS
- `execution_timestamp` exclusion: PASS

## Files Modified In This Pass

None. Documentation and packaging only.

## Files Created

- `docs/explora_target/M5_CANONICAL_RESULTS_ORDERING_REMEDIATION_V2.md`
- `docs/explora_target/M5_CANONICAL_RESULTS_ORDERING_REMEDIATION_V2_MANIFEST.md`
- `checkpoints/M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_V2_2026-09-14.zip`

## Contract Files Modified

NO

## Invariance Evidence

- M2 `universe.py`: `D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E`
- M3 `weights.py`: `AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B`
- M4 `structure.py`: `CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56`

Protected Legacy files remain unchanged by this pass.

## Scope Guard

- Dependency changes: NONE
- Database changes: NONE
- Web/UI changes: NONE
- Excel changes: NONE
- M6 changes: NONE
- Numerical deltas to productive Legacy: NONE

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
