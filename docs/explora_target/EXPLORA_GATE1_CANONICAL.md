# EXPLORA — GATE 1 CANONICAL ARCHITECTURE

**Canonical architecture source after Gate 1 Final Review**
**Date:** 2026-09-14
**Gate status:** `PASS WITH CONDITIONS`
**Codex readiness:** `YES — first bounded M0/M1 milestone only`

> This file consolidates the Gate 1 architecture. It does not replace or rewrite the human-approved methodological sources `WEIGHT_POLICY_CANONICAL.md`, `SIGNIFICANCE_POLICY_CANONICAL.md`, or `AI_RELEASE_POLICY_CANONICAL.md`. Those files remain authoritative within B1/B2/B3. If this consolidated architecture conflicts with one of them on methodology, the corresponding B1/B2/B3 canonical policy governs.

## 1. Canonical system principle

EXPLORA V1 uses one analytical source of truth.

`QUESTIONNAIRE + DATABASE + METADATA`
→ `EXPLORA NG / deterministic extraction`
→ `B3 RELEASE PROCESS`
→ `RELEASED SPECS`
→ `QA PRE-EXECUTION GATE`
→ `ANALYTICS CORE`
→ `QA POST-EXECUTION GATE`
→ `CANONICAL RESULTS`
→ `WEB / EXCEL RENDERERS`.

The responsibilities are fixed:

- EXPLORA NG interprets and proposes.
- Human-approved policies define methodological boundaries.
- RELEASED Specs define project-specific runtime methodology/configuration.
- Analytics Core calculates, validates execution and produces official analytical results.
- QA Core controls deterministic gates and release evidence.
- Canonical Results are the immutable renderer-neutral analytical output of a run.
- Web and Excel present the same Canonical Results and do not become statistical engines.
- Codex develops and maintains the software; Codex is not a runtime methodological decision maker.

## 2. Final authority hierarchy

1. **Human-approved canonical policies**
   - `WEIGHT_POLICY_CANONICAL.md`
   - `SIGNIFICANCE_POLICY_CANONICAL.md`
   - `AI_RELEASE_POLICY_CANONICAL.md`
2. **Approved Target Architecture / ADRs**
3. **RELEASED Project / Question / Structure / Universe / Weight / Metric / Significance Specs**
4. **Analytics Core deterministic execution under versioned registries/rules**
5. **Canonical Results for an immutable result run**
6. **Web / Excel renderers**
7. **Legacy behavior only inside explicit legacy/regression/rollback paths**

Questionnaire/database/metadata remain versioned source evidence. They do not bypass the release process, and Specs cannot invent observed data.

## 3. Permanent invariants

1. NG is not numerical authority.
2. Only `RELEASED` critical Specs are runtime authority.
3. Core never repairs methodology by semantic guessing.
4. Web cannot overwrite Specs or recalculate official values in Canonical Mode.
5. Excel cannot independently calculate official statistics.
6. Legacy cannot defeat Canonical Mode.
7. Universe/applicability is resolved before weight contribution.
8. Structural zero and structural missing are distinct states.
9. Metric denominators are explicit/versioned, not renderer inference.
10. Unsupported inference is represented explicitly, never as a blank implying no difference.
11. Statistical truth is stable pairwise relation records, not display letters.
12. Every official result is traceable to project, dataset, configuration, policies, code/rules, QA and result version.
13. A released Spec/result is immutable; corrections create a new version/run.
14. AI uncertainty remains visible and follows B3 release governance.
15. No project/client/question-specific rule is hardcoded into Core.

## 4. B1 Weight Methodology — incorporated boundary

B1 is HUMAN APPROVED and closed.

Canonical V1 requirements:

- weight activation requires explicit released configuration and validation;
- AI/name detection can produce a candidate but cannot activate weighting;
- missing/NaN and non-numeric weights are excluded from weighted calculation and logged in Weight QA;
- invalid values are never silently replaced with 1;
- non-finite values fail validation and do not enter a weighted denominator;
- zero weight is valid and may remain in `unweighted_n` when otherwise metric-valid;
- negative weight is `UNSUPPORTED V1` and fails the affected weighted analysis;
- no Core normalization/rescaling;
- no Core trimming/capping;
- multiple weight resolution = valid analysis override → project default → unweighted;
- at most one project default;
- universe and metric-valid response rules resolve before weight contribution;
- canonical bases include `unweighted_n`, `weighted_n_raw`, `weighted_n`, `effective_n`;
- in V1, `weighted_n_raw = weighted_n = Σ applied valid supplied weights`;
- Kish `effective_n = (Σw)^2 / Σ(w²)` is diagnostic/QA only;
- weighted percentages, means, RM respondent %, RM mention % and descriptive NPS are Core-supported;
- weighted significance/inference is `UNSUPPORTED V1`;
- Web/Excel never repair, normalize, trim, impute or recalculate weight-based results.

Any Target Weight Spec options that contradict these rules are obsolete for Canonical V1 and must be rejected by schema/validation.

## 5. B2 Significance / Statistical Policy — incorporated boundary

B2 is HUMAN APPROVED and closed.

Canonical V1 requirements:

- default confidence 95%; allowed 90/95/99%;
- all canonical tests two-sided;
- minimum test base `unweighted_n >= 30` in each group;
- pooled two-proportion z-test for eligible respondent-level binary outcomes in independent/disjoint groups;
- pooled expected successes and failures >=5 in each group;
- Welch independent-samples t-test for eligible means;
- canonical multiple-comparison correction = Holm;
- same-banner/question/metric/analytical-row-or-option/active-slice comparison family;
- Total excluded;
- canonical comparison statuses distinguish `SIGNIFICANT`, `NOT_SIGNIFICANT`, `INELIGIBLE`, `UNSUPPORTED`, `NOT_TESTED`, `FAIL`;
- stable pairwise relations are canonical truth;
- Web/Excel may translate stable IDs into visible letters but never recompute significance;
- weighted significance, NPS significance, RM mention significance, paired/repeated methods, panel misuse, complex-sample inference, subgroup-vs-Total, cross-banner and unknown-dependency inference remain `UNSUPPORTED V1` as defined by B2;
- `effective_n` is never inferential N.

Canonical Significance Spec must carry or reference a deterministic sample relationship state. Core may not infer independence from display labels.

## 6. B3 AI Auto-Release — incorporated boundary

B3 is HUMAN APPROVED and closed.

Official release modes:

- `AUTO`
- `REVIEW`
- `MANUAL`

Official decision lifecycle:

- `PROPOSED`
- `REVIEW_REQUIRED`
- `APPROVED`
- `REJECTED`
- `RELEASED`

Only `RELEASED` may be consumed by Analytics Core.

V1 has no universal numeric confidence threshold. Confidence is supporting evidence only and cannot override conflicts, missing evidence, unsupported structures, MANUAL capability rules, incomplete dependencies or QA.

Unresolved CRITICAL review blocks release.

AI cannot activate a weight, authorize an unapproved method, or convert missing evidence into runtime certainty.

`SUPERSEDED` may be used as version lineage state, but not as a substitute for the B3 decision lifecycle.

## 7. Final Project / Question / Structure authority

### Project Spec

Owns:

- project/dataset identity and fingerprint;
- respondent key;
- project/global Universe ref;
- question registry;
- banner/filter registry;
- available/default Weight refs;
- project-level explicit defaults;
- policy/spec references;
- release state;
- QA release state;
- compatibility mode;
- governance/version lineage.

A Canonical project must resolve an explicit project universe. If all respondents are eligible, use an explicit TRUE universe.

### Question Spec

Owns:

- stable question identity;
- physical type and analytic role;
- variable/category bindings;
- Structure ref;
- Universe ref;
- Metric refs;
- Weight/Significance refs where applicable;
- missing and zero semantics;
- eligibility metadata;
- interpretation evidence/review lineage.

### Structure Spec

Owns logical response shape for RU/RM/Grid/Loop independently of physical SPSS naming:

- parent;
- axes and stable member IDs;
- physical bindings;
- selected/not-selected semantics;
- structural zero;
- structural missing;
- user missing;
- question/row/column/cell applicability refs;
- RM exclusivity/open links/duplicate policy.

Legacy detectors may produce candidates/QA evidence but cannot override RELEASED Structure Spec in Canonical Mode.

## 8. Universe Spec — canonical architecture contract

Universe is a versioned executable typed expression, not only free text and not observed response N.

Supported scopes:

- project;
- question;
- row/entity;
- column;
- cell.

Effective methodological applicability:

`PROJECT ∧ QUESTION ∧ ROW ∧ COLUMN ∧ CELL`

Interactive user filters apply after methodological eligibility and are recorded separately in the analysis request/slice.

### Universe v1 operator signatures to freeze in M0 before M2

```text
true()
false()
and(args: expression[2+])
or(args: expression[2+])
not(arg: expression)
eq(variable_ref, scalar)
neq(variable_ref, scalar)
in(variable_ref, scalar[])
not_in(variable_ref, scalar[])
gt(variable_ref, scalar)
gte(variable_ref, scalar)
lt(variable_ref, scalar)
lte(variable_ref, scalar)
is_missing(variable_ref)
not_missing(variable_ref)
selected(question_ref, category_ref)
not_selected(question_ref, category_ref)
answered(question_ref)
not_answered(question_ref)
universe_ref(universe_id)
```

One stable operator name is allowed per v1 semantic. The draft `contains_selected` example must normalize to `selected` or another single canonical name before M2.

All refs must resolve to released IDs. Circular refs are invalid. Arbitrary project Python/SQL is forbidden.

Structural meaning:

- `eligible=false` + missing response = structural missing/out of base;
- `eligible=true` + missing response = in-base item nonresponse under explicit rules;
- `eligible=true` + RM not-selected value = structural zero/not-selected when declared by Structure Spec.

Missing activation references never fall back to observed responses.

## 9. Weight Spec — canonical V1 schema constraints

Weight Spec is configuration, not calculation.

It must identify:

- stable weight ID/version;
- variable/source;
- provenance/type;
- scope;
- project-default flag where applicable;
- B1 policy identity/version;
- release state;
- QA/review evidence.

Canonical V1 validators must reject:

- `IMPUTE_ONE`;
- negative allowed;
- normalization other than NONE;
- Core trimming/capping enabled;
- weighted significance enabled;
- ambiguous/multiple project defaults;
- unknown/out-of-scope analysis override.

## 10. Metric Spec and Registry — canonical contract

Every executable metric must have:

- `metric_id`;
- `version`;
- `formula_id`;
- `question_ref`;
- `universe_ref`;
- explicit `denominator_policy` or registry-declared `NOT_APPLICABLE`;
- `missing_behavior`;
- `weight_behavior`;
- `parameters`;
- `significance_compatibility`;
- `RELEASED` state and traceability.

The versioned Metric Registry defines:

- accepted question/structure types;
- numerator;
- denominator;
- required parameters;
- missing behavior;
- weight behavior;
- output unit;
- significance family compatibility;
- invariants;
- formula version.

Canonical Mode must not infer formula/denominator from display labels, scale min/max, response-row presence or formatter behavior.

Current legacy behaviors requiring explicit canonical replacement include Top2/Bottom inference, RM response-presence base, grid fallback reconstruction, ranking inside formatter, generic frequency fallback, unversioned factor/range logic, NPS from range alone and incomplete multiplicity formula identity.

## 11. Significance Spec — canonical V1 constraints

Significance Spec must resolve to B2-approved semantics only.

Required conceptual fields:

- policy/spec ID and version;
- enabled/disabled;
- confidence;
- alpha;
- sidedness;
- minimum base rule;
- proportion test ID/version;
- mean test ID/version;
- expected-count rule;
- Holm method/version;
- family-scope rule;
- Total exclusion;
- sample relationship/dependency state;
- unsupported behavior;
- release state.

`NONE` multiple-comparison correction is not canonical V1; it is legacy/regression only.

## 12. Canonical Results — final logical model

Canonical Results are immutable, long/tidy and renderer-neutral.

### Run envelope must pin

- result schema version;
- `result_run_id`;
- project ID;
- dataset fingerprint/version;
- Project Spec version/hash;
- referenced Spec IDs/versions/hashes;
- B1/B2/B3 policy identities/versions/hashes;
- Core version/build;
- ruleset/registry versions/hashes;
- feature flags;
- request/slices;
- execution timestamp;
- QA/release status;
- official release state.

### Base records must support

- question/row/column/cell/slice identity;
- Universe ref;
- Weight ref/provenance link;
- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;
- valid-answer/mention diagnostics where applicable.

### Value records must support

- stable identity;
- question/structure/row/column/category/slice identity;
- metric/formula ID/version;
- base ID;
- numerator/denominator where meaningful;
- estimate;
- unit;
- status;
- QA/warning links.

### Significance records must support

- stable left/right member IDs;
- family ID;
- test ID/version;
- B2 policy version;
- confidence/alpha/sidedness;
- statistical status;
- reason code;
- unweighted inferential bases;
- expected-count/variance diagnostics as relevant;
- raw p-value;
- Holm-adjusted p-value;
- adjustment method/version;
- direction;
- QA/warnings.

Literal display letters are not statistical truth.

### Never canonical

- Plotly objects;
- HTML/CSS;
- `ReportResult` layout;
- Excel cell addresses;
- VBA state;
- pixels/coordinates;
- renderer-only fallbacks.

## 13. QA architecture

Final QA layers:

1. METHODOLOGICAL QA
2. INPUT QA
3. CONTRACT/SCHEMA QA
4. DATA QA
5. ANALYTICAL QA
6. STATISTICAL QA
7. RENDERER QA
8. RELEASE QA

### Issue/domain states

Use domain-appropriate states such as:

- `PASS`
- `WARN`
- `INELIGIBLE`
- `UNSUPPORTED`
- `FAIL`

B3 may additionally route decisions to review/block before release.

### Aggregate gate states

- `PASS`
- `PASS_WITH_WARNINGS`
- `REVIEW_REQUIRED`
- `FAIL`

`WARN` is not an aggregate release state.

### Blocking semantics

Core official execution/result scope is blocked by unreleased critical Specs, invalid contracts/references, blocking input/data integrity failures, non-executable required Universe, invalid required Weight contract, unknown required Metric formula or analytical invariant failure.

Statistical `INELIGIBLE` or `UNSUPPORTED` does not invalidate a valid descriptive result. Statistical `FAIL` blocks the affected requested significance result and may block final release if that significance output is contractually required.

Renderer mismatch blocks that renderer's release, not the underlying valid Core run.

Final release is blocked by any unresolved blocking issue in required scope, unresolved B3 CRITICAL review, unreleased critical Spec, required renderer failure or incomplete run traceability.

## 14. Backward compatibility

Temporary modes:

- `LEGACY`
- `HYBRID_VALIDATION`
- `CANONICAL`

One official result run may not silently mix analytical truth from modes.

Every material Legacy-vs-Canonical difference is classified:

- `EXPECTED_METHODOLOGICAL_CHANGE`
- `DEFECT`
- `UNKNOWN_REQUIRES_REVIEW`

Legacy parity never overrides canonical policy.

## 15. Migration sequence

Approved sequence:

### M0 — contracts only

Freeze schemas, registries, validators, traceability and Gate conditions. No production calculation change.

### M1 — Analytics Core wrapper around existing behavior

Create Core interface and legacy adapter behind feature flag. Regression parity under legacy profile. No calculation rewrite.

### M2 — executable Universe

Execute frozen Universe v1. No observed-response fallback. Row/cell universes require frozen Structure Spec context; runtime inference cannot be canonical authority.

### M3 — weights hardening

Implement B1 canonical descriptive weighting and Weight QA. Legacy weight behavior remains isolated in legacy profile.

### M4 — RM/Grid authority

Make RELEASED Structure Spec authoritative for RM/Grid/Loop in Canonical Mode. Runtime detector becomes import-assist/QA only.

### M5 — Canonical Results

Implement/persist renderer-neutral Canonical Results and canonical B2 significance relations under frozen schemas.

### M6 — Web migration

Web consumes Canonical Results and stops owning official analytical calculations/re-inference in Canonical Mode.

### M7 — Excel Renderer

Excel consumes the same Canonical Results/Visual Spec. No independent statistics in Excel/VBA.

No milestone advances automatically.

## 16. Final ADR register

- ADR-001 `APPROVE`
- ADR-002 `APPROVE WITH CONDITION`
- ADR-003 `APPROVE WITH CONDITION`
- ADR-004 `APPROVE`
- ADR-005 `APPROVE`
- ADR-006 `APPROVE` — resolved by B1
- ADR-007 `APPROVE WITH CONDITION`
- ADR-008 `APPROVE` — resolved by B2
- ADR-009 `APPROVE` — Holm canonical V1
- ADR-010 `APPROVE WITH CONDITION`
- ADR-011 `APPROVE`
- ADR-012 `APPROVE WITH CONDITION`
- ADR-013 `APPROVE` — resolved by B3
- ADR-014 `APPROVE`
- ADR-015 `APPROVE`
- ADR-016 `APPROVE`

Conditions are schema/milestone exit criteria, not unresolved methodology.

## 17. First Codex milestone

**Approved recommended scope:** `M0.1 / M1A — Contract & Core Boundary Scaffolding`.

### IN SCOPE

- actual machine-readable contract models/schemas;
- B1/B2/B3 deterministic validators;
- Universe v1 signature schema;
- explicit Metric denominator schema;
- B3 lifecycle normalization;
- QA issue/gate models;
- Core interface;
- legacy adapter;
- feature flag `legacy | core_wrapper` with default legacy;
- wrapper parity/regression tests;
- rollback test.

### OUT OF SCOPE

- Universe data execution;
- weight behavior changes;
- RM/Grid authority migration;
- Holm productive migration;
- statistical formula rewrite;
- Canonical Results production persistence;
- Web behavior migration;
- EXPLORA NG changes;
- EXPLORA Excel;
- broad refactor;
- client/project hardcoding.

### Acceptance

- no productive numerical change;
- default remains legacy;
- invalid B1/B2/B3 config rejected deterministically;
- only RELEASED enters canonical boundary;
- Universe grammar and Metric denominator frozen in schema/tests;
- wrapper equals direct legacy execution on frozen fixtures;
- existing tests pass;
- rollback proven.

## 18. Remaining risks

### Methodological

No unresolved P0 blocker. Future unsupported methods require separate approval.

### Architectural

Universe grammar, Metric denominator, B3 lifecycle normalization, sample relationship location, Canonical Results traceability and QA layer normalization must be frozen at their designated milestone exits.

### Implementation

Current reporter mixes IO/inference/calculation/rendering; wrapper first, refactor later.

### Migration

Freeze representative real fixtures before parity/retirement decisions. Grid production evidence remains incomplete in audited SQLite artifacts.

### QA

Expand E2E coverage for universes, weights, structured results and renderer parity before rollout.

### Renderer

Current Web analytical fallbacks remain a risk until M6; Excel is blocked until M7.

## 19. Gate 1 final status

**GATE 1 STATUS:** `PASS WITH CONDITIONS`

**CANONICAL ARCHITECTURE:** sufficiently defined for incremental implementation.

**APPROVED ADRS:** all ADRs have an APPROVE or APPROVE WITH CONDITION disposition.

**CONDITIONAL ADRS:** ADR-002, ADR-003, ADR-007, ADR-010, ADR-012.

**REMAINING BLOCKERS:** no unresolved methodological blocker; only milestone-specific contract/schema exit conditions.

**IMPLEMENTATION RISKS:** contained through feature flags, dual-run, tests, rollback and explicit legacy isolation.

**FIRST CODEX MILESTONE:** `M0.1 / M1A — Contract & Core Boundary Scaffolding`.

**CODEX READY:** `YES — only for that bounded milestone`.

This Gate does not authorize automatic code execution, automatic progression to M2, modification of EXPLORA NG/Web behavior, or construction of EXPLORA Excel.
