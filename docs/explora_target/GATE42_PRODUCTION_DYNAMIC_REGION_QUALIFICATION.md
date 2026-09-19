# Gate 42 Production Master Dynamic Region Qualification

Status: IMPLEMENTED / QUALIFIED FOR HUMAN REVIEW. Starting main:
`d3f35100547038e49e409246ef0368799c1799bb`.

## Artifact Identity

The accepted rollback artifact remains
`EXPLORA_PRODUCTION_MASTER_V1.xlsm`, version 1.1.0, SHA-256
`a8313adf706016b30b8837a7bc42cb80c7ccc281f2663616a7f22b8daa8d10dd`.
The deterministic derivative is `EXPLORA_PRODUCTION_MASTER_V1_2.xlsm`, version
1.2.0, SHA-256 `f3a11f291b6c661f0c937e9c95d7f227c351d7261b2e01aa44dfd4167d5c869c`.
Both contain byte-identical VBA SHA-256
`0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758`.

The candidate is rebuilt only from 1.1.0 by
`scripts/build_gate42_production_master.py`. Fixed ZIP timestamps and core
modification metadata make consecutive builds byte-identical. The baseline is
never opened for writing and remains the rollback artifact.

## Qualified Regions

`PRODUCTION_DYNAMIC_RESULTS_V1` is a RANGE region on `presentation`, anchored by
`ProductionDynamicResultAnchor` at J2. It grows ROWS_AND_COLUMNS from 1x1 to 8x3
inside J2:L9. Ordered fields are canonical estimate, canonical status and a
checksum-pinned Gate 39 significance token. It uses deterministic declared-cell
style propagation, replacement/stale cleanup and formula policy NONE.

`PRODUCTION_DYNAMIC_PROVENANCE_V1` is a fixed 1x1 RANGE at N2. It transports the
released Canonical Result run identity through the Gate 41 provenance role.
Existing production fixed slots, formula E1, tables, names, VBA and all cells
outside these envelopes remain protected.

## Scenario Matrix

| Scenario | Result | Physical evidence |
|---|---|---|
| T42-01 baseline identity | PASS | workbook/VBA hashes exact |
| T42-02 candidate derivation | PASS | distinct 1.2.0; consecutive builds exact |
| T42-03 minimum 1x1 | PASS | J2 read-back and N2 provenance |
| T42-04 nominal 4x2 | PASS | J2:K5 read-back |
| T42-05 expansion | PASS | bounded plan/read-back |
| T42-06 maximum 8x3 | PASS | J2:L9 exact |
| T42-07 contraction | PASS | stale values/status/tokens cleared |
| T42-08 re-expansion | PASS | logical hash equals direct expansion |
| T42-09 overflow | PASS | max+1 rejected; source/output unchanged |
| T42-10 collision | PASS | fixed-slot collision rejected before mutation |
| T42-11 significance | PASS | Core relation/token presented; no calculation |
| T42-12 provenance | PASS | run, plan, region, bounds, renderer and Master identities |
| T42-13 output read-back | PASS | plan-derived physical oracle |
| T42-14 determinism | PASS | plan/logical/read-back fingerprints exact |
| T42-15 fixed-slot compatibility | PASS | candidate fixed renderer output |
| T42-16 Gate 38/39 compatibility | PASS | numeric/significance authority preserved |
| T42-17 VBA preservation | PASS | baseline/candidate/output exact |
| T42-18 protected surfaces | PASS | formulas/names/unrelated surfaces preserved |
| T42-19 no partial mutation | PASS | overflow/collision leave no output |
| T42-20 full regression | PASS | recorded in checkpoint |

## Analytical Boundary

No percentage, base, weighted base, effective n, mean, score, slice, weight or
significance is calculated in Excel or VBA. Core and Canonical Results remain the
only analytical authority. The production region is bounded qualification only;
it does not qualify charts, pivots, slicers, external connections, signatures,
arbitrary growth or general-purpose layout generation.

Machine-readable evidence:
`GATE42_PRODUCTION_DYNAMIC_REGION_CHECKPOINT.json`.
