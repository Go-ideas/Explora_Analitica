# EXPLORA - M5 CANONICAL RESULTS IMPLEMENTATION

**Milestone:** M5 - Canonical Results
**Date:** 2026-09-14
**Authority:** `M5_CANONICAL_RESULTS_IMPLEMENTATION_CONTRACT.md`
**Authority SHA-256:** `A36D8803F84357868C450956A33D8D66B432E1C473494C9C9BE9BE2CF618431D`
**Runtime default:** `LEGACY`

## Status

M5 implements renderer-neutral Canonical Results V1 as an additive contract
and Analytics Core layer. It does not route productive Web or Legacy execution
through canonical results by default.

## Architecture

M5 adds four internal modules:

- `src/analytics_core/results.py`: CanonicalResult assembly, base/value
  helpers, QA/release derivation, significance transport and Legacy comparison.
- `src/analytics_core/formula_registry.py`: explicit versioned Formula
  Registry V1 and deterministic formula evaluators.
- `src/analytics_core/serialization.py`: deterministic JSON-compatible
  canonical serialization and round-trip loading.
- `src/analytics_core/result_identity.py`: stable request, slice, run ID,
  object ID and result fingerprint utilities.

## CanonicalResult Root

`CanonicalResult` remains distinct from Legacy `ReportResult`. The root now
supports typed renderer-neutral collections:

- `manifest`
- `request`
- `slices`
- `bases`
- `values`
- `comparisons`
- `qa_events`
- `release`

The previous skeleton fields remain present and backward compatible.

## Identity Rules

`result_run_id` is mandatory, unique per execution and not a content hash. M5
does not reuse historical run IDs for new executions.

`result_fingerprint` is deterministic over analytical semantics. It excludes
run IDs, timestamps, renderer metadata, labels and run-scoped record IDs.
Equivalent analytical runs can therefore produce the same fingerprint even when
their run IDs differ.

## Request And Slice Identity

`RequestSnapshot` stores `request_id` and `request_fingerprint`. Fingerprints
normalize question IDs, metric refs, banner configuration, filters, weight
override, compatibility profile and execution options. Labels are excluded.

`CanonicalSlice` stores `slice_id` and `slice_fingerprint` from semantic banner,
member, filter and total/member configuration. Visual labels are excluded from
identity.

## Base Model

`CanonicalBase` preserves explicit denominator identity:

- denominator unit;
- denominator ref;
- denominator scope ID;
- universe ref;
- analytical structure identifiers;
- unweighted and weighted base fields;
- active weight ref;
- QA/provenance refs.

M5 consumes M4 denominator ledgers and M3 weight outputs. It does not
reconstruct denominator membership.

## Value Model

`CanonicalValue` is the analytical cell model. `estimate` is the official
analytical value; renderers must not recalculate it. Non-OK statuses require a
null estimate. Real zero values are represented as `value_status=OK` and
`estimate=0`.

Proportions are stored as `0..1` with `unit=PROPORTION`.

## Formula Registry

The Formula Registry is explicit and versioned as `M5_FORMULA_REGISTRY_V1`.
Unknown formula IDs raise a structural error. Known formulas unsupported for a
structure/weight combination produce `ValueStatus.UNSUPPORTED`.

Registered V1 formulas:

- `COUNT`
- `FREQUENCY`
- `PROPORTION`
- `MEAN`
- `STANDARD_DEVIATION`
- `TOP_BOX`
- `BOTTOM_BOX`
- `NPS_DESCRIPTIVE`
- `RM_RESPONDENT_PROPORTION`
- `RM_MENTION_PROPORTION`
- `SCALE_MEAN`

## Significance Transport

M5 transports B2 significance objects into renderer-neutral
`SignificanceRelation` records. It does not implement a new significance engine
and does not copy Legacy significance logic as canonical authority.

Weighted significance, RM mention significance and NPS significance remain
`UNSUPPORTED V1`.

## QA And Release

`QAEvent` is the single structured QA authority for M5. Warnings are QA events,
not a parallel analytical truth.

`CanonicalReleaseState` separates:

- `computation_status`;
- `qa_release_status`;
- `releasable`.

Blocking QA events and failed computation produce a non-releasable result.

## Serialization

Canonical serialization is deterministic JSON-compatible UTF-8:

- stable field names;
- explicit nulls;
- no NaN/Infinity;
- deterministic collection ordering;
- versioned schema;
- semantic round trip.

No productive SQLite schema migration is included.

## Immutability

M5 contract models are frozen dataclasses. Historical result objects are not
mutated in place. New material executions create a new `result_run_id`.
Optional `supersedes_result_run_id` supports lineage.

## Legacy Comparison

M5 adds explicit Legacy to Canonical comparison classification:

- `PARITY`
- `INTENDED_CORRECTION`
- `M2_BASE_DIFFERENCE`
- `M3_WEIGHT_DIFFERENCE`
- `M4_STRUCTURE_DIFFERENCE`
- `UNSUPPORTED_V1`
- `POTENTIAL_REGRESSION`
- `PRESENTATION_ONLY`

Unexplained numerical deltas are classified as `POTENTIAL_REGRESSION` and are
blocking.

## Upstream Integration

M5 consumes upstream outputs only:

- M2 Universe masks and QA are consumed, never modified.
- M3 weight outputs are copied as base metadata, never recalculated.
- M4 denominator ledgers and structural refs are preserved.

## Tests

Focused M5 result:

`39 PASS / 0 FAIL / 0 SKIP`

Full regression:

`276 PASS / 0 FAIL / 0 SKIP`

Legacy parity:

`2 PASS / 0 FAIL / 0 SKIP`

## Known Limitations

- M5 does not migrate Web/UI.
- M5 does not alter productive SQLite schema.
- M5 does not start Excel/VBA/NG.
- Productive Grid/Loop benchmark remains:
  `PENDING - HUMAN ACCEPTED WARNING`.

## Out Of Scope

M6 is not started. Web migration, SQLite persistence redesign, Excel export,
NG/RM/Grid productive migration and new significance methodology are outside
M5.
