# T0 — REPOSITORY ADOPTION

Date: 2026-09-15
Branch: `migration/t0-canonical-baseline`

## Objective

Adopt the latest accepted physical EXPLORA state into GitHub without reopening methodology, refactoring accepted modules, or switching production defaults.

## Frozen rules

- Do not modify `main` during T0.
- Do not switch the productive default away from `LEGACY`.
- Do not reinterpret B1, B2, or B3.
- Do not refactor M2–M6 solely for repository cleanliness.
- Do not use historical GitHub code as a substitute for the accepted checkpoint.
- Do not infer missing files from documentation.

## Current GitHub state

`main` and the migration branch started from commit:

`124384890b3fa048ca5c554ffb1e5ead1d68ee2a`

The existing repository is the prior Streamlit-era state and is preserved for traceability.

## Adoption sequence

1. Select the authoritative physical checkpoint.
2. Verify its SHA-256 from the actual archive bytes.
3. Expand it outside `main`.
4. Inventory source, tests, contracts, docs, checkpoints, runtime/data artifacts.
5. Exclude customer/productive data and local secrets from Git.
6. Compare protected areas against accepted manifests/hashes.
7. Run focused tests.
8. Run full regression.
9. Run Legacy parity.
10. Record numerical deltas, if any.
11. Commit the validated source tree to this branch.
12. Re-run from a clean clone or equivalent clean checkout.
13. Produce `T0_BASELINE_VERIFICATION.md`.
14. Only after T0 acceptance, open/merge a PR into `main`.

## Codex role during T0

Codex may be used for mechanical inspection and independent verification, but it must not make corrective changes until discrepancies are classified.

Recommended Codex instruction:

```text
EXPLORA — T0 REPOSITORY ADOPTION / AS-IS INVENTORY

Objective:
Inspect the supplied physical EXPLORA checkpoint and the GitHub migration branch.

DO NOT modify production code.
DO NOT refactor.
DO NOT implement new functionality.
DO NOT update frozen contracts.
DO NOT switch execution defaults.

Return:
1. repository/checkpoint tree
2. Python/runtime version
3. dependencies
4. test commands
5. focused suites by milestone
6. full regression command
7. Legacy parity command
8. canonical contracts found
9. protected files
10. manifests/checkpoints present
11. SQLite/data files that must remain outside Git
12. generated artifacts that must remain outside Git
13. discrepancies between checkpoint and migration branch
14. AS_IS_INVENTORY.md
15. TEST_BASELINE.md

Do not remediate discrepancies. Classify them only.
```

## Current blocker

The relevant checkpoint ZIPs were located in ChatGPT Library, but raw-byte materialization to the execution environment is currently unavailable. This prevents independent SHA calculation, archive expansion, test execution from those bytes, and source commit.

T0 remains `IN PROGRESS / BLOCKED ON PHYSICAL CHECKPOINT BYTE ACCESS`.
