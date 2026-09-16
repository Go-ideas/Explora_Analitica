# EXPLORA PROGRAM STATE

Date: 2026-09-15
Repository: Go-ideas/Explora_Analitica
Migration branch: migration/t0-canonical-baseline

## Repository adoption status

T0 — REPOSITORY ADOPTION: IN PROGRESS

The existing `main` branch is preserved as the pre-migration Streamlit-era repository state. It MUST NOT be overwritten during T0.

Current pre-migration `main` / migration branch ancestor:

- commit: `124384890b3fa048ca5c554ffb1e5ead1d68ee2a`
- date: 2026-09-08
- current GitHub CI status checks at this commit: none reported

## Canonical program state carried into migration

Methodological authorities already established outside this repository remain authoritative and must be imported without semantic reinterpretation:

- B1 — Weight Methodology: HUMAN APPROVED / CANONICAL
- B2 — Significance / Statistical Policy: HUMAN APPROVED / CANONICAL
- B3 — AI Release Policy: HUMAN APPROVED / CANONICAL

Accepted implementation history to preserve during adoption includes the closed M2–M6 line and later canonical execution/materialization work. T0 is NOT authorized to reopen, refactor, or redesign those accepted areas merely to fit GitHub.

## Execution default

- Production default: `LEGACY`
- CANONICAL_V1: explicit selection only
- DUAL_RUN: explicit selection only
- Default switch during T0: NOT AUTHORIZED

## T0 authority rule

The target Git baseline is accepted only after the following identity is demonstrated:

`last accepted physical EXPLORA checkpoint == adopted repository baseline == reproducible test state`

Until this equality is proven, this branch is a migration staging branch and MUST NOT be merged to `main`.

## Physical checkpoint candidates located in ChatGPT Library

The migration process located these relevant artifacts:

1. `M5_CANONICAL_EXECUTION_ADAPTER_CORRECTIVE_REVIEW_CHECKPOINT_2026-09-15.zip`
   - Library path: `/EXPLORA — Core & Evolution/M5_CANONICAL_EXECUTION_ADAPTER_CORRECTIVE_REVIEW_CHECKPOINT_2026-09-15.zip`
   - duplicate staging copy also located under `/EXPLORA_TMP/`
   - size: 19,665 bytes
   - expected SHA-256 from the corrective review package: `B273D859FB29FA01129B8DE622646A197D48472DCB3B0E568E42AFFD15A81159`
   - reported focused adapter tests: 44 PASS / 0 FAIL / 0 SKIP
   - reported full regression: 450 PASS / 0 FAIL / 0 SKIP

2. `M6_WEB_MIGRATION_CANONICAL_RESULTS_2026-09-14.zip`
   - Library path: `/EXPLORA_TMP/M6_WEB_MIGRATION_CANONICAL_RESULTS_2026-09-14.zip`
   - size: 311,602 bytes
   - expected SHA-256 from M6 review: `097D5410BD9EEC6DA376687C8D35D108352BDCCAB250BA3DF0D29F8F7655FBF3`
   - historical pre-corrective M6 package; NOT automatically authoritative over later corrective states

3. `BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1.zip`
   - Library path: `/EXPLORA_TMP/BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1.zip`
   - project release package, not a substitute for the source-code baseline

## Current migration blocker

The ChatGPT Library references above are visible and identified, but their raw ZIP bytes are not currently authorized for materialization into the execution container. Therefore:

- archive SHA-256 cannot yet be independently recomputed here;
- archive contents cannot yet be physically expanded here;
- source cannot yet be committed from those archives without fabricating or inferring files;
- T0 cannot honestly be declared PASS yet.

This is an input-access blocker, not an architectural blocker.

## T0 required exit criteria

Before merge to `main`:

- authoritative physical checkpoint selected;
- actual archive SHA-256 verified;
- archive expanded and inventoried;
- canonical contracts verified;
- protected source verified;
- repository `.gitignore` reviewed against actual package contents;
- focused milestone tests PASS;
- full regression PASS;
- Legacy parity PASS;
- no unexplained numerical deltas to Productive Legacy;
- no unauthorized M2–M6 or Legacy modifications;
- source tree committed to this migration branch;
- clean-clone reproducibility demonstrated;
- T0 assessment = PASS or explicitly human-accepted PASS WITH WARNINGS.

## Merge policy

Do not merge this branch to `main` until T0 is closed.

No new product functionality is authorized as part of repository adoption.
