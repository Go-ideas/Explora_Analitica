# EXPLORA — IMPLEMENTATION MILESTONE M0/M1 DRAFT

**Purpose:** define the first Codex milestone after Gate 1.
**Status:** architecture-approved scope draft only; no implementation has started.
**Date:** 2026-09-14

## 1. Recommended first milestone

**Milestone name:** `M0.1 / M1A — Contract & Core Boundary Scaffolding`

The first Codex milestone should create the versioned contract/validation boundary and a disabled-by-default Analytics Core wrapper around the current reporter path, without changing production analytical behavior.

This is deliberately smaller than “implement Analytics Core”.

### Objective

Prove that the repository can contain:

1. machine-readable canonical contract schemas;
2. deterministic schema/release validators;
3. an Analytics Core service/interface boundary;
4. a legacy adapter behind an explicit feature flag;
5. regression fixtures proving zero product behavior change when the flag remains legacy/default.

No canonical calculation rewrite belongs in this milestone.

## 2. IN SCOPE

### 2.1 Contract package

Create versioned schema/model definitions for the minimum contracts needed by the wrapper:

- Project Spec;
- Question Spec;
- Structure Spec;
- Universe Spec shell plus frozen v1 operator signatures;
- Weight Spec constrained to B1;
- Metric Spec with explicit denominator policy;
- Significance Spec constrained to B2;
- Canonical Result logical models sufficient for schema tests, without production persistence;
- QA issue/gate models;
- B3 release metadata/lifecycle model.

### 2.2 Deterministic validators

Implement validators that can reject, at minimum:

- non-`RELEASED` critical Specs passed to Canonical execution entry points;
- invalid/missing spec IDs/versions;
- unresolved references;
- invalid Universe operator/signature/ref;
- forbidden Canonical V1 Weight choices;
- invalid Metric Spec without denominator policy when required;
- invalid Significance Spec outside B2 V1;
- incompatible B3 lifecycle/release metadata;
- duplicate/ambiguous project default weight;
- obvious circular Universe references;
- missing run-manifest identity fields.

These validators do not calculate study results.

### 2.3 Analytics Core boundary

Introduce a narrow internal interface such as conceptually:

`AnalyticsCore.generate(request, released_contract_bundle) -> result_adapter_output`

For this milestone, the only executable implementation may be a **legacy adapter** that delegates to current `generate_report()` behavior.

The interface must make future canonical execution possible without forcing current UI to change immediately.

### 2.4 Feature flag

Introduce an explicit engine selection with default preserving current behavior, conceptually:

`analytics_engine = legacy | core_wrapper`

Requirements:

- default = existing legacy path;
- `core_wrapper` delegates to the same current calculations in this milestone;
- no project is automatically enrolled;
- the flag and selected mode are visible in QA/test output.

### 2.5 Regression harness

Freeze a small set of deterministic fixtures and compare:

- legacy direct call;
- core-wrapper delegated call.

Expected result for M1A: same analytical outputs under the same legacy behavior profile.

The harness should compare at least:

- question identity;
- table values;
- bases exposed by existing result;
- selected metrics;
- significance output where currently available;
- warnings/errors where observable.

This is wrapper parity, not validation of target methodology.

## 3. OUT OF SCOPE

The milestone must not:

- implement Universe execution against study data;
- change denominator/base behavior;
- harden production weights;
- change current `missing -> 1` legacy behavior inside the legacy path;
- implement B1 canonical weighted calculations;
- replace RM/Grid runtime inference;
- implement Holm in the productive reporter path;
- change z/Welch behavior;
- implement weighted significance;
- introduce canonical result persistence;
- migrate Web to Canonical Results;
- build or modify EXPLORA Excel;
- change EXPLORA NG;
- change questionnaire/datamap interpretation behavior;
- delete or refactor legacy paths broadly;
- retire SQLite schemas;
- alter existing production UI defaults;
- add project/client/question-specific hardcoding.

## 4. FILES / MODULES LIKELY AFFECTED

Exact paths may be adjusted after repository inspection, but the expected blast radius should remain narrow.

### New modules recommended

Under the main audited implementation `explora_web_reporter/`:

- `src/contracts/` or equivalent
  - Project/Question/Structure/Universe/Weight/Metric/Significance/QA/result models
  - schema versions
  - validators
- `src/core/` or equivalent
  - core interface/protocol
  - request/result envelope
  - `legacy_adapter.py`
- `src/config/analytics_mode.py` or equivalent feature-flag configuration

### Existing modules touched minimally

Likely integration points:

- `src/reporter/tabulator.py`
  - expose/delegate current `generate_report()` through adapter without changing internals;
- `src/reporter/calculations.py`
  - ideally no calculation change; may only need stable call boundary/import cleanup if unavoidable;
- `src/reporter/significance.py`
  - no methodology change; only wrapper exposure if required;
- UI reporter entry point such as `src/ui/page_04_reporter.py`
  - only if a non-default hidden/internal mode injection is needed for tests; no product behavior change;
- project/app configuration module
  - feature flag definition/default.

### Files explicitly not to modify for this milestone unless required for test wiring

- EXPLORA NG knowledge/instructions;
- Excel renderer/macros/master;
- legacy forks/copies outside the main audited implementation;
- historical data fixtures except controlled test copies;
- methodological canonical policy documents.

## 5. TESTS REQUIRED

### 5.1 Contract schema tests

For each contract:

- valid minimal object passes;
- missing required identity/version fails;
- invalid lifecycle fails;
- unresolved references fail;
- incompatible enum/policy values fail.

### 5.2 B1 guardrail tests

Schema/validator must reject or classify correctly:

- `IMPUTE_ONE` in Canonical Weight Spec;
- negative allowed policy;
- normalization other than NONE in V1;
- Core trimming/capping enabled in V1;
- weighted significance enabled;
- multiple project defaults.

No weighted calculations are implemented here.

### 5.3 B2 guardrail tests

Canonical Significance Spec validation must reject:

- unsupported confidence such as 97%;
- one-sided canonical mode;
- base rule other than approved unweighted n>=30 unless a future approved version exists;
- multiple-comparison `NONE` under Canonical V1;
- weighted inference mode;
- missing sample-relation/dependency state where significance is requested.

No new statistical execution is implemented here.

### 5.4 B3 lifecycle tests

- `PROPOSED` cannot reach canonical execution;
- `REVIEW_REQUIRED` cannot reach canonical execution;
- `APPROVED` cannot reach canonical execution;
- `REJECTED` cannot reach canonical execution;
- only `RELEASED` passes release-state validation;
- unresolved CRITICAL review blocks;
- missing required release audit data fails schema/release validation.

### 5.5 Universe grammar tests

- every v1 operator validates its exact signature;
- unknown operator fails;
- unresolved refs fail;
- circular `universe_ref` fails;
- `contains_selected` is rejected if canonical name is `selected`;
- arbitrary Python/SQL is not accepted as expression payload.

These are parser/schema tests, not data evaluation tests.

### 5.6 Metric contract tests

- proportion metric without denominator policy fails;
- unknown `formula_id` fails/unsupported according to selected registry capability;
- display label alone cannot select formula;
- significance compatibility is explicit.

### 5.7 Wrapper parity tests

For frozen legacy fixtures:

- direct legacy execution == core-wrapper delegated execution;
- no changed values/bases/significance/ordering beyond explicitly tolerated serialization differences;
- default engine mode remains legacy;
- flag can switch to wrapper in tests;
- disabling/removing wrapper route returns original behavior.

### 5.8 Existing regression suite

All current tests must continue to pass. The audited baseline previously reported 65 passing tests; the milestone must establish the current repository baseline first and then demonstrate no regression.

## 6. ACCEPTANCE CRITERIA

M0.1/M1A passes only if all are true:

1. No current production calculation changes.
2. Default runtime path remains legacy.
3. Canonical contract models are versioned and machine-validatable.
4. B1/B2/B3 invalid configurations are rejected deterministically rather than delegated to Codex/AI judgment.
5. Universe v1 operator signatures are frozen in schema/tests.
6. Metric denominator is explicit in the schema.
7. B3 lifecycle is normalized and only `RELEASED` can enter canonical execution boundary.
8. A Core interface exists without duplicating statistical logic.
9. Core wrapper can call existing behavior behind a feature flag.
10. Wrapper parity tests pass on selected fixtures.
11. Existing regression tests pass.
12. No EXPLORA Excel work exists in the diff.
13. No EXPLORA NG behavioral change exists in the diff.
14. No client/project/question hardcoding is added.
15. A rollback test proves the feature flag can return entirely to the pre-milestone path.

## 7. ROLLBACK

Rollback must be trivial and tested:

1. set `analytics_engine=legacy` globally/default;
2. bypass new Core wrapper and validators from productive calls;
3. retain new schemas/tests as inert artifacts if desired, or revert the milestone commit;
4. no data migration rollback is required because this milestone creates no canonical production persistence;
5. no historical SQLite/result artifacts are rewritten.

The milestone must be deliverable as one or a small number of isolated commits so it can be reverted without touching project data.

## 8. Benchmark/fixture condition

Before parity can be claimed, freeze representative fixtures from the existing repository/project evidence. At minimum include:

- a standard RU/frequency case;
- an RM case;
- a scale/mean/Top2-style legacy case;
- a banner + significance case;
- a weighted legacy case for wrapper parity only.

These fixtures are not proof that legacy methodology is canonical. They prove the wrapper did not change behavior.

## 9. Exit and next-step rule

Passing M0.1/M1A does not automatically authorize M2.

M2 requires explicit confirmation that the Universe schema/operator contract has passed its freeze tests and that selected benchmark questionnaire/datamap cases cover the required universe shapes.

## 10. First Codex milestone decision

**RECOMMENDED: YES.**

This milestone is small, reversible, feature-flagged, testable, does not change product behavior, and does not require Codex to invent methodology.

No implementation prompt is generated by this document.
