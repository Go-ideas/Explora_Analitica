# T0 BASELINE MANIFEST

Date: 2026-09-16

## Repository

- GitHub repository: `Go-ideas/Explora_Analitica`
- Target branch: `migration/t0-canonical-baseline`
- Main branch modified during T0: NO
- PR: #1, `T0 — Adopt canonical EXPLORA baseline`

## Adopted Source State

- Adopted physical project: `explora_web_reporter/`
- Adopted source files: `explora_web_reporter/src/`
- Adopted tests: `explora_web_reporter/tests/`
- Adopted canonical docs: `docs/explora_target/`
- Excluded runtime/client artifacts: data, SAV, DB, ZIP checkpoints, evidence, logs, caches, local env files.

## Checkpoints

- Authoritative checkpoint candidate: `checkpoints/M5_CANONICAL_EXECUTION_ADAPTER_CORRECTIVE_REVIEW_CHECKPOINT_2026-09-15.zip`
- SHA-256: `B273D859FB29FA01129B8DE622646A197D48472DCB3B0E568E42AFFD15A81159`
- Checkpoint SHA verified: YES
- Source/checkpoint reconciliation: AMBIGUOUS, because no single checkpoint ZIP exactly represents the whole current physical source tree.

Additional verified checkpoint:

- `checkpoints/M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATED_V3_2026-09-15.zip`
- SHA-256: `1BAE7A3D48A3A196E95957BAD27D506D36253C83C692C52A8FB1B066CC2AD3C7`

## Runtime

- Python: `3.13.3`
- Dependencies: `explora_web_reporter/requirements.txt`
- Test path requirement: `PYTHONPATH=.`

## Test Summary

- M2: `31 passed / 0 failed / 0 skipped`
- M3: `45 passed / 0 failed / 0 skipped`
- M4: `61 passed / 0 failed / 0 skipped`
- M5: `75 passed / 0 failed / 0 skipped`
- M5 adapter: `44 passed / 0 failed / 0 skipped`
- M6: `97 passed / 0 failed / 0 skipped`
- Legacy parity: `2 passed / 0 failed / 0 skipped`
- Materialization: `NOT FOUND`
- Full regression, physical tree: `450 passed / 0 failed / 0 skipped`
- Full regression, adopted Git payload: `1 failed / 449 passed / 0 skipped`

## Execution Default

- Production default: `LEGACY`
- `CANONICAL_V1`: explicit selection only
- `DUAL_RUN`: explicit selection only
- Default switch during T0: NO

## Provenance

The migration adopts the physically inspected source tree and records the absence of a single global checkpoint. Accepted methodology B1/B2/B3 and M2-M6 source semantics were not intentionally modified during T0.

## Remaining Conditions Before Merge

- Human review of AMBIGUOUS checkpoint/source reconciliation.
- Clean-clone/adopted-payload reproducibility blocker: `tests/test_database_validation.py` requires excluded `data/db/BD_Analitica_Explora.db`.
- No merge to `main` until T0 is accepted.
