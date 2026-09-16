# EXPLORA PROGRAM STATE

Date: 2026-09-16
Repository: Go-ideas/Explora_Analitica
Migration branch: migration/t0-canonical-baseline

## Repository Adoption Status

T0 — REPOSITORY ADOPTION: IN PROGRESS / BLOCKED ON REPRODUCIBILITY

The existing `main` branch is preserved as the pre-migration Streamlit-era repository state. It MUST NOT be overwritten during T0.

Pre-migration GitHub state:

- `main`: `124384890b3fa048ca5c554ffb1e5ead1d68ee2a`
- PR #1 / migration branch before adoption: `80cd6032c4d8a29d54c4dcd870f484c745ee92ec`

## Canonical Program State Carried Into Migration

Methodological authorities remain authoritative and were imported without semantic reinterpretation:

- B1 — Weight Methodology: HUMAN APPROVED / CANONICAL
- B2 — Significance / Statistical Policy: HUMAN APPROVED / CANONICAL
- B3 — AI Release Policy: HUMAN APPROVED / CANONICAL

Accepted implementation history preserved in the physical source includes:

- M2 — Universe Execution
- M3 — Weight Hardening
- M4 — RM / Grid Authority
- M5 — Canonical Results
- M5 Canonical Execution Adapter
- M6 — Web Migration to Canonical Results

`src/canonical_materialization/` was not present in the inspected physical tree and is recorded as NOT FOUND for T0.

## Execution Default

- Production default: `LEGACY`
- `CANONICAL_V1`: explicit selection only
- `DUAL_RUN`: explicit selection only
- Default switch during T0: NOT AUTHORIZED / NOT PERFORMED

## Physical Baseline Evidence

Physical project root:

`C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica\explora_web_reporter`

Checkpoint candidates verified from local bytes:

1. `M5_CANONICAL_EXECUTION_ADAPTER_CORRECTIVE_REVIEW_CHECKPOINT_2026-09-15.zip`
   - SHA-256: `B273D859FB29FA01129B8DE622646A197D48472DCB3B0E568E42AFFD15A81159`
   - Historical expected SHA: MATCH
   - Reported focused adapter tests: 44 PASS / 0 FAIL / 0 SKIP
   - Current focused adapter tests: 44 PASS / 0 FAIL / 0 SKIP

2. `M6_WEB_MIGRATION_CANONICAL_RESULTS_REMEDIATED_V3_2026-09-15.zip`
   - SHA-256: `1BAE7A3D48A3A196E95957BAD27D506D36253C83C692C52A8FB1B066CC2AD3C7`
   - Sampled files from this checkpoint match the current physical tree for M6/web/core files.

No single checkpoint ZIP was found that exactly represents the whole current physical source tree. T0 therefore records source/checkpoint reconciliation as AMBIGUOUS and requires human review before merge.

## Current Regression State

Executed from `explora_web_reporter/` with `PYTHONPATH=.`:

- M2: 31 PASS / 0 FAIL / 0 SKIP
- M3: 45 PASS / 0 FAIL / 0 SKIP
- M4: 61 PASS / 0 FAIL / 0 SKIP
- M5: 75 PASS / 0 FAIL / 0 SKIP
- M5 Execution Adapter: 44 PASS / 0 FAIL / 0 SKIP
- M6: 97 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP
- Full regression, physical tree: 450 PASS / 0 FAIL / 0 SKIP
- Full regression, adopted Git payload without excluded client DB: 449 PASS / 1 FAIL / 0 SKIP
- Materialization tests: NOT FOUND

Blocking adopted-payload failure:

- `tests/test_database_validation.py::test_validate_reporter_database_accepts_builder_database`
- The test requires `data/db/BD_Analitica_Explora.db`.
- The file exists only in the local physical workspace, is 17,551,360 bytes, SHA-256 `1B0BD28180844EBC3CA59A1467B78EE6D486DB6CB8CC71E3D16B3388B77174DB`, and is prohibited from GitHub upload by T0 rules for productive/local databases.

## T0 Required Exit Criteria

Before merge to `main`:

- Human review accepts AMBIGUOUS source/checkpoint reconciliation, or a single global checkpoint is supplied.
- A separate authorized remediation replaces the local productive DB dependency with a non-sensitive committed fixture or adjusts the test contract.
- Clean-clone reproducibility passes.
- No client/productive data is added to Git.
- T0 assessment is accepted by human review.

## Merge Policy

Do not merge this branch to `main` until T0 is closed.

No new product functionality is authorized as part of repository adoption.
