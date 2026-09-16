# EXPLORA — FINAL CONTRACT READINESS

**Gate:** FASE 1 — Gate 1 Final Review
**Date:** 2026-09-14
**Overall contract readiness:** `READY WITH CONDITIONS`

## 1. Summary

The contracts are sufficient to start a non-productive M0/M1 implementation milestone. They are not all frozen enough for every later execution milestone.

No remaining condition requires a new B1/B2/B3 methodological decision. The conditions are explicit schema/interface freezes that must occur before the first milestone that executes the corresponding capability.

| Contract | Readiness | Blocking milestone | Condition |
|---|---|---:|---|
| Project Spec | READY WITH CONDITIONS | M1 | Normalize B3 lifecycle; pin policy/spec identities and explicit project universe. |
| Question Spec | READY WITH CONDITIONS | M1 | Normalize B3 lifecycle and release metadata. |
| Structure Spec | READY | M4 production authority | No runtime override in Canonical Mode. |
| Universe Spec | READY WITH CONDITIONS | M2 | Freeze operator signatures/reference typing/missing semantics; remove operator alias mismatch. |
| Weight Spec | READY WITH CONDITIONS | M3 | Constrain draft schema to B1 Canonical V1; no obsolete choices. |
| Metric Spec | READY WITH CONDITIONS | M1 schema / later execution | Add explicit denominator policy and registry compatibility fields. |
| Significance Spec | READY WITH CONDITIONS | M5 canonical significance | Constrain to B2; add machine-readable dependency/independence context. |
| Canonical Results | READY WITH CONDITIONS | M5 | Add B1/B2/B3 traceability and complete statistical/weight fields. |
| QA contract | READY WITH CONDITIONS | M1 | Make contract/schema QA explicit; normalize issue vs aggregate statuses. |
| Visual Spec | READY | M6/M7 | Semantic presentation only. |

## 2. Project Spec — final required semantics

Canonical execution requires:

- `schema_version`
- `project_id`
- `spec_version`
- content hash
- B3 decision/release state = `RELEASED`
- exact dataset identity/fingerprint
- respondent ID binding
- explicit project/global Universe ref
- question registry
- available/default Weight refs
- banner/filter registry
- default or referenced Significance policy where applicable
- canonical policy identities/versions/hashes used by the project
- QA release state
- governance/version lineage
- compatibility mode where applicable

If no project-level eligibility restriction exists, the project must still resolve to an explicit TRUE Universe rather than an undocumented implicit behavior.

## 3. Question Spec — final required semantics

Question Spec remains the canonical question-level methodology contract.

Required runtime-critical fields include:

- stable question identity/version/hash;
- B3 state = `RELEASED`;
- physical type;
- analytic role;
- variable bindings;
- stable category IDs/raw-code mapping;
- Structure ref when applicable;
- Universe ref;
- Metric refs;
- Weight ref/policy where applicable;
- Significance ref where applicable;
- missing semantics;
- zero semantics;
- banner/filter eligibility where used;
- interpretation evidence/review lineage.

Confidence/evidence are audit signals. They never replace `RELEASED` state.

## 4. Structure Spec — readiness

`READY`.

The target structure contract already contains the necessary conceptual authority for:

- parent relationship;
- row/entity axis;
- column/option axis;
- physical variable bindings;
- question/row/column/cell applicability refs;
- selected/not-selected values;
- structural zero;
- structural missing;
- user missing;
- RM exclusivity/open links/duplicate policy.

Before M4, the conceptual schema must be converted to an actual versioned validation schema, but Codex does not need to invent methodology to do so.

## 5. Universe Spec — machine-readiness assessment

### 5.1 Required scopes

Universe must support:

- project-level universe;
- question-level universe;
- row/entity universe;
- column universe;
- cell/applicability universe.

### 5.2 Effective applicability

Canonical methodological applicability is:

`PROJECT ∧ QUESTION ∧ ROW ∧ COLUMN ∧ CELL`

Only the scopes that exist for the structure are added. Row/column/cell omission means no additional restriction at that scope.

Interactive user filters are applied after methodological applicability and are stored separately in the result slice/request.

### 5.3 Structural state distinction

Universe evaluation determines eligibility, not response value.

- not eligible + missing response = structural missing/out of base;
- eligible + missing response = item nonresponse/user missing according to Question/Structure/Metric rules;
- eligible + explicit not-selected value in RM = structural zero/not selected when Structure Spec declares it;
- zero cannot be reclassified from frequency patterns alone.

### 5.4 Activation conditions

Skip/activation conditions are Universe expressions. They may reference previously released questions/categories/variables/universes through stable IDs.

Missing required activation references produce block/review/fail according to B3/QA, never observed-response fallback.

### 5.5 Minimum typed AST registry for Universe v1

Before M2, freeze one signature per operator:

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
gt/gte/lt/lte(variable_ref, scalar)
is_missing(variable_ref)
not_missing(variable_ref)
selected(question_ref, category_ref)
not_selected(question_ref, category_ref)
answered(question_ref)
not_answered(question_ref)
universe_ref(universe_id)
```

The draft `contains_selected` example must be normalized to `selected` or a single other approved name; two synonymous operators are not acceptable in v1.

### 5.6 Universe validation before release

- schema valid;
- all variable/question/category/member refs exist;
- all dependencies are RELEASED;
- operator/type signatures valid;
- no circular Universe refs;
- row/column/cell refs belong to the referenced Structure Spec;
- source/evidence retained;
- contradiction with data/questionnaire handled under B3, not auto-fixed.

### 5.7 Machine-readable conclusion

`READY WITH CONDITION BEFORE M2`.

The conceptual model is sufficient. The operator schema is not yet frozen enough for Codex to invent independently; therefore M2 must not start until the M0 schema package defines the exact signatures above.

## 6. Weight Spec — B1-constrained readiness

Canonical V1 must encode, not choose between:

- explicit registered `weight_id` and variable source;
- weight provenance/type;
- missing/non-numeric: exclude from weighted calculation + QA;
- non-finite: invalid/fail validation;
- zero: valid;
- negative: `UNSUPPORTED V1`, affected weighted analysis fails;
- normalization: `NONE`;
- trimming/capping: `NONE`;
- multiple weights: analysis override → project default → unweighted;
- at most one project default;
- effective N: Kish, diagnostic only;
- weighted significance: `UNSUPPORTED V1`.

Core-supported weighted descriptive outputs in V1:

- percentages;
- means;
- RM respondent %;
- RM mention %;
- descriptive NPS;
- canonical weighted bases/effective N QA.

`READY WITH SCHEMA NORMALIZATION BEFORE M3`.

## 7. Metric Spec — final readiness

### 7.1 Required fields

Every executable Metric Spec requires:

```yaml
metric_id: stable_id
version: semantic_or_contract_version
formula_id: versioned_formula_id
question_ref: released_question_id
universe_ref: released_universe_id
denominator_policy: explicit_policy_or_NOT_APPLICABLE
missing_behavior: explicit_policy
weight_behavior: unweighted | inherit | explicit_weight_ref
parameters: {}
significance_compatibility:
  family: proportion | mean | none
  supported: boolean
release_state: RELEASED
```

Physical field names may differ, but these semantics are mandatory.

### 7.2 Formula Registry responsibilities

The versioned registry must define:

- accepted Question/Structure types;
- required parameters;
- numerator definition;
- denominator definition;
- missing behavior;
- weight behavior/support;
- output scale/unit;
- significance compatibility;
- deterministic invariants;
- registry/formula version.

### 7.3 Denominator requirement

The denominator must never be hidden in renderer code or inferred from whichever response rows happen to exist.

Examples of denominator policies include:

- eligible respondents;
- valid-answer respondents;
- eligible mentions;
- valid numeric observations;
- explicit derived denominator reference;
- not applicable for a pure count where the registry defines no denominator.

### 7.4 Known Web inference to remove from Canonical Mode

- Top2/Bottom codes inferred from scale min/max;
- RM base inferred from selected-response rows;
- Grid/RM fallback reconstruction from metadata;
- ranking created in formatter;
- frequency as generic fallback calculation;
- factor/range materialization without an approved formula identity;
- NPS invoked from a 0–10 range without a released NPS metric definition;
- multiplicity exposed without a final isolated formula contract.

`READY WITH CONDITION`.

## 8. Significance Spec — B2-constrained readiness

Canonical V1 configuration must resolve to:

- enabled/disabled;
- confidence ∈ {0.90, 0.95, 0.99}, default 0.95;
- sidedness = `two_sided`;
- minimum base = `unweighted_n >= 30` per group;
- proportion test = pooled two-proportion z-test;
- expected successes/failures >= 5 under pooled null;
- mean test = Welch independent t-test;
- multiplicity adjustment = Holm;
- family scope = same banner/question/metric/analytical row-or-option/active slice;
- Total excluded;
- sample relationship explicit/validated;
- unsupported domains represented explicitly.

### Required sample relationship field

The comparison context must provide a stable relation such as:

- `independent_disjoint`
- `repeated_or_paired`
- `unknown`

Only `independent_disjoint` is eligible for the approved V1 z/Welch methods. Unknown dependency cannot be guessed.

### Statistical output fields

Every considered pair needs:

- left/right stable member IDs;
- family ID;
- test ID/version;
- significance policy version;
- confidence/alpha/sidedness;
- statistical status;
- reason code;
- inferential unweighted bases;
- relevant diagnostics;
- raw p-value when executed;
- adjusted p-value when applicable;
- adjustment method/version;
- direction;
- QA status/warnings.

`READY WITH SCHEMA NORMALIZATION BEFORE CANONICAL SIGNIFICANCE`.

## 9. Canonical Results — final logical contract

Canonical Results must be renderer-neutral and immutable by run.

### Run envelope

At minimum:

- result schema version;
- immutable `result_run_id`;
- project ID;
- dataset fingerprint/version;
- Project Spec version/hash;
- all referenced Spec IDs/versions/hashes;
- B1/B2/B3 policy identities/versions/hashes;
- Analytics Core version/build;
- ruleset/registry versions/hashes;
- feature flags hash;
- execution timestamp;
- aggregate QA/release status;
- official-release flag/state;
- request/slice definition.

### Base records

At minimum:

- base ID;
- question/row/column/cell/slice identity as applicable;
- Universe ref;
- weight ref when applicable;
- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;
- valid-answer/mention diagnostics as applicable;
- Weight QA/provenance link.

### Value records

At minimum:

- stable value ID;
- question/structure/row/column/category/slice identity;
- metric/formula IDs/versions;
- base ID;
- numerator/denominator where meaningful;
- estimate;
- unit;
- status;
- warning/QA links.

### Significance records

Use B2 pairwise relations as analytical truth. Literal display letters are not canonical.

### Excluded from Canonical Results

- `ReportResult` renderer layout;
- Plotly figures;
- HTML;
- CSS classes;
- Excel ranges/cell addresses;
- VBA state/procedure names;
- pixel coordinates;
- renderer-specific fallbacks.

`READY WITH SCHEMA FREEZE BEFORE M5`.

## 10. QA / release contract

### Layers

1. methodological;
2. input;
3. contract/schema;
4. data;
5. analytical;
6. statistical;
7. renderer;
8. release.

### Issue status vs gate status

Issue/domain statuses may include `PASS`, `WARN`, `INELIGIBLE`, `UNSUPPORTED`, `FAIL` plus B3 review/block states where applicable.

Aggregate release gate uses only:

- `PASS`
- `PASS_WITH_WARNINGS`
- `REVIEW_REQUIRED`
- `FAIL`

### Blocking behavior

A blocking pre-execution methodological/input/contract/data issue prevents official Core execution for the affected scope.

An analytical failure blocks the affected metric/result scope.

A statistical `INELIGIBLE` or `UNSUPPORTED` status does not invalidate a valid descriptive estimate; a statistical `FAIL` blocks the affected requested significance output and may block final release when significance is contractually required.

A renderer mismatch blocks that renderer release, not the underlying valid Canonical Result.

Final official release is blocked by any unresolved blocking issue in required scope, an unresolved B3 CRITICAL review, an unreleased critical Spec, or a blocking renderer issue for the artifact being published.

## 11. Final contract decision

`READY WITH CONDITIONS`.

M0/M1 can begin because the conditions are explicit and do not require methodological invention. Each later milestone has a clear schema-freeze prerequisite documented above.
