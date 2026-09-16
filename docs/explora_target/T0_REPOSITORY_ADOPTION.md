# T0 — REPOSITORY ADOPTION

Date: 2026-09-16
Branch: `migration/t0-canonical-baseline`

## Objective

Adopt the latest accepted physical EXPLORA state into GitHub without reopening methodology, refactoring accepted modules, or switching production defaults.

## Frozen Rules

- Do not modify `main` during T0.
- Do not switch the productive default away from `LEGACY`.
- Do not reinterpret B1, B2, or B3.
- Do not refactor M2-M6 solely for repository cleanliness.
- Do not use historical GitHub code as a substitute for the accepted physical baseline.
- Do not infer missing files from documentation.
- Do not upload client/productive data, secrets, runtime SQLite, SAV, logs, caches, or local outputs.

## Current GitHub State

`main` and the migration branch started from commit:

`124384890b3fa048ca5c554ffb1e5ead1d68ee2a`

PR #1 head before this adoption pass:

`80cd6032c4d8a29d54c4dcd870f484c745ee92ec`

The existing repository is the prior Streamlit-era state and is preserved for traceability.

## Adoption Attempt Result

The T0 adoption branch now carries:

- `docs/explora_target/`
- `explora_web_reporter/src/`
- `explora_web_reporter/tests/`
- `explora_web_reporter/app.py`
- `explora_web_reporter/streamlit_app.py`
- `explora_web_reporter/README.md`
- `explora_web_reporter/requirements.txt`

The branch intentionally excludes:

- SAV/ZSAV/POR source data
- productive SQLite/database files
- data sessions
- Streamlit secrets
- `.env`
- output/evidence/checkpoint ZIP history
- pytest and Python caches
- local logs and generated deliverables

## Verification

See:

- `docs/explora_target/T0_AS_IS_INVENTORY.md`
- `docs/explora_target/T0_BASELINE_VERIFICATION.md`
- `docs/explora_target/T0_BASELINE_MANIFEST.md`

Current physical-tree full regression:

`450 PASS / 0 FAIL / 0 SKIP`

Adopted Git payload regression without excluded local database:

`449 PASS / 1 FAIL / 0 SKIP`

Legacy parity:

`2 PASS / 0 FAIL / 0 SKIP`

## Known Warnings

- No single checkpoint ZIP exactly represents the whole current physical source tree.
- `src/canonical_materialization/` is not present in the inspected physical tree.
- Clean-clone/adopted-payload reproducibility fails because `tests/test_database_validation.py` depends on excluded local SQLite file `data/db/BD_Analitica_Explora.db`.

## Merge Policy

Do not merge this branch to `main` until human T0 review accepts the adoption evidence and the reproducibility blocker is resolved by a separately authorized step.

T0 READY TO MERGE: NO
