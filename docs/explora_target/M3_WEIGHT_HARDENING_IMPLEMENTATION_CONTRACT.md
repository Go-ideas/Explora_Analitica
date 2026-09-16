# M3 — WEIGHT HARDENING / B1 RUNTIME IMPLEMENTATION

**Milestone:** M3
**Scope:** Weight Hardening / B1 Runtime Implementation
**Authority:** `WEIGHT_POLICY_CANONICAL.md` — HUMAN APPROVED
**Dependency:** M2 — Universe Execution — CLOSED / ACCEPTED
**Status of this document:** IMPLEMENTATION CONTRACT
**Implementation authorization:** NOT GRANTED BY THIS DOCUMENT

---

## CURRENT STATE

M0.1 / M1A established and froze the Contracts + Analytics Core boundary.

M2 implemented canonical Universe Execution and is CLOSED / ACCEPTED.

The runtime continues to preserve:

- `LEGACY` as default execution mode;
- canonical/Core capabilities as opt-in/internal;
- no Web migration;
- no SQLite migration;
- no Excel migration;
- no EXPLORA NG migration.

B1 Weight Methodology is HUMAN APPROVED and its sole methodological authority is:

`WEIGHT_POLICY_CANONICAL.md`

M3 must implement that policy deterministically. It must not reinterpret it.

---

# M3 IMPLEMENTATION SCOPE

M3 implements the canonical runtime boundary required to resolve, validate, apply and audit respondent-level analytical weights.

M3 includes:

1. deterministic active-weight resolution;
2. project default weight support;
3. analysis-level override support;
4. explicit unweighted behavior when no weight resolves;
5. validation of supplied weight values;
6. deterministic treatment of missing/non-numeric values;
7. zero-weight behavior;
8. rejection of negative and non-finite weights;
9. preservation of supplied weight values;
10. prohibition of Core normalization;
11. prohibition of Core trimming/capping;
12. canonical base calculation:

- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;

13. weight identity and provenance;
14. Weight QA;
15. integration after M2 Universe resolution;
16. structured error/warning/status behavior;
17. explicit prevention of weighted inference in V1;
18. Legacy-vs-Canonical regression coverage;
19. feature-flag isolation;
20. traceable canonical result output.

M3 is specifically a **Weight Runtime / Base / QA milestone**.

M3 does **not** imply complete migration of every weighted analytical metric.

In particular, M3 must not expand itself into:

- RM migration;
- Grid migration;
- Web migration;
- NPS inference;
- weighted significance;
- complex-survey variance;
- calibration/raking;
- trimming algorithms;
- renderer logic.

Question-specific weighted analytical capabilities may consume the M3 weight runtime later, but they must not force M3 to absorb later milestones.

---

# FILES / AREAS EXPECTED TO CHANGE

Expected implementation area:

`src/analytics_core/`

M3 may add a dedicated weight-runtime component inside Analytics Core responsible for:

- weight resolution;
- weight validation;
- application of weight validity rules;
- canonical base calculation;
- Kish effective N;
- Weight QA generation;
- provenance;
- structured status generation.

The exact module filename may follow the existing repository convention, for example a dedicated weight/weighting module. The filename itself is not a methodological decision.

Additive orchestration changes may be required in:

`src/analytics_core/runner.py`

or the equivalent Core orchestration boundary, exclusively to enforce the sequence:

`Universe → analytical denominator → weight resolution/validation → weighted bases/QA`

Tests and deterministic fixtures are expected to change/add under the corresponding test area.

Test fixtures may include synthetic respondent-level weights and frozen Legacy comparison fixtures.

No renderer or production Web path is required to change.

---

# FILES / AREAS PROTECTED

The following areas are protected during M3.

### M2 Universe implementation

The accepted M2 implementation, including its Universe semantics, must not be modified to accommodate weighting.

In particular, M3 must not change:

- `UniverseRef` resolution;
- Universe registry rules;
- Universe scope vocabulary;
- applicability semantics;
- response-state semantics;
- respondent mask semantics;
- `eligible_n`;
- `excluded_n`;
- zero-eligible behavior;
- Universe `UNSUPPORTED` behavior.

Weighting consumes M2 output. It does not modify it.

### Frozen contracts

The M1A Contract Freeze remains authoritative.

Protected areas include the frozen semantics in:

`src/contracts/vocabulary.py`

`src/contracts/models.py`

`src/contracts/validators.py`

M3 may not silently rename, reinterpret or weaken frozen contract fields.

If M3 reveals that a canonical B1 field is genuinely absent from the frozen contract and cannot be implemented additively without changing contract semantics, implementation must stop and the Contract Freeze must be explicitly reviewed.

M3 itself may not silently reopen M1A.

### Other protected areas

Do not modify as part of M3:

- EXPLORA Web rendering/runtime;
- SQLite schema or persistence;
- EXPLORA Excel;
- EXPLORA NG;
- B1 methodology;
- B2 statistical methodology;
- B3 AI release methodology;
- RM/Grid migration;
- significance engine;
- protected `src/reporter/` production behavior;
- Legacy calculation behavior.

---

# B1 INVARIANTS

The following are non-negotiable M3 invariants.

### INV-W01 — Explicit activation only

A weight may be active only when it resolves through the released project/weight contract.

Variable-name detection, heuristics or AI recommendations cannot activate weighting.

### INV-W02 — No implicit weight

Missing, invalid or unresolved weight information must never produce an implicit:

`weight = 1`

Canonical mode has no `fillna(1)` equivalent.

### INV-W03 — Missing/non-numeric

Missing, NaN and non-numeric/parse-invalid supplied weights do not contribute to the weighted calculation.

They must:

- be excluded from the weighted contribution;
- remain measurable in Weight QA;
- retain counts/rates/reasons;
- never be silently repaired.

They do not by themselves convert the remaining valid respondent weights to another scale.

### INV-W04 — Zero weight

`weight = 0` is valid.

If the respondent belongs to the analytical denominator:

- the respondent remains eligible for `unweighted_n`;
- contributes `0` to weighted numerator/base;
- is counted in zero-weight QA;
- contributes `0` to Kish sums.

Zero weight is not missing.

### INV-W05 — No positive weighted denominator

If the sum of applied valid weights is not positive, the weighted estimate/base is unavailable.

This includes an analysis whose applicable valid weights are all zero.

### INV-W06 — Negative weight

`weight < 0` is:

`UNSUPPORTED V1`

The affected weighted analysis must fail.

It must not exclude the negative respondent and continue silently.

### INV-W07 — Non-finite weight

`+∞` and `-∞` are invalid and blocking.

They cannot enter any weighted denominator, estimate or Kish calculation.

### INV-W08 — Preserve supplied values

The supplied weight is preserved.

Analytics Core must not rewrite the project source variable.

Any validated/calculation representation must remain traceable to the supplied value.

### INV-W09 — No normalization

Core performs no automatic rescaling or normalization.

An externally normalized/calibrated weight may be consumed exactly as supplied when declared in provenance.

### INV-W10 — No trimming/capping

Core performs no automatic trimming or capping.

An externally transformed weight may be used as supplied if its provenance identifies that upstream transformation.

### INV-W11 — Canonical bases

The four canonical base names are frozen:

`unweighted_n`

`weighted_n_raw`

`weighted_n`

`effective_n`

For EXPLORA V1:

`weighted_n_raw = weighted_n = Σ applied valid supplied weights`

There is no second V1 transformation between `weighted_n_raw` and `weighted_n`.

Specifically, `weighted_n` is not:

- normalized N;
- rounded sample N;
- effective N;
- projected respondent count created by Core;
- trimmed N.

The coexistence of `weighted_n_raw` and `weighted_n` preserves the canonical result contract and future extensibility, but their values are equal in V1.

### INV-W12 — Effective N

Kish effective N is:

`effective_n = (Σw)^2 / Σ(w²)`

using the applied valid weights for the corresponding analytical denominator.

It is diagnostic/QA information only.

It must not:

- replace `unweighted_n`;
- replace `weighted_n`;
- determine the metric denominator;
- modify an estimate;
- feed V1 significance;
- automatically block release.

### INV-W13 — Weighted significance

Weighted inference is:

`UNSUPPORTED V1`

M3 must never pass weighted descriptive output through the current unweighted z/Welch significance implementation.

No weighted:

- p-values;
- confidence intervals;
- significance letters

may be generated by M3.

---

# M2 DEPENDENCY RULES

M3 depends on M2 but must not modify M2.

The mandatory execution order is:

**1. Resolve Universe through M2**

M2 remains responsible for deciding who is structurally eligible.

**2. Consume the M2 respondent mask**

The M2 mask is authoritative.

M3 cannot add respondents removed by Universe execution.

M3 cannot remove respondents from the Universe merely because their weight is zero or missing. Weight validity affects weighted contribution, not Universe membership.

**3. Apply metric-specific validity**

Where an analysis has response/metric validity rules, the analytical denominator is formed from:

M2 Universe eligibility

- explicit analysis/filter/banner scope
- metric response validity.

Weighting comes after this denominator is established.

**4. Apply the active weight**

Only then does M3 evaluate the weight contribution.

Therefore:

`Universe membership ≠ weight validity`

and:

`weight validity must never rewrite Universe membership`.

### M2 error propagation

If M2 returns an execution state in which the requested Universe cannot be evaluated, M3 must not invent a replacement Universe.

M3 must propagate the blocking/unsupported condition with traceability.

### Zero eligible

An M2 result with:

`eligible_n = 0`

is valid Universe execution.

M3 must not convert it into a Universe error.

The downstream analytical result may simply have no calculable weighted base.

### No weighted Universe object

M3 must not add weight fields into `UniverseEvaluationResult`.

Weight information belongs to the analytical/weight result boundary, downstream of Universe execution.

---

# WEIGHT RESOLUTION RULE

Weight resolution precedence is deterministic.

### Step 1 — Analysis override

If an explicit analysis-level weight override exists:

- it must reference an authorized registered weight;
- it must be valid for the analysis/project contract;
- it takes precedence over the project default.

A valid analysis override wins.

An unknown, ambiguous or unauthorized override is a blocking configuration error.

It must never fall through silently to the project default.

### Step 2 — Project default

When no analysis override exists, use the explicitly configured project default weight if present and valid.

The default must identify a registered weight deterministically.

### Step 3 — No resolved weight

If neither an analysis override nor project default exists:

**execute unweighted.**

Absence of a weight is not itself an error.

It must not trigger:

- weight-variable guessing;
- name detection;
- AI selection;
- fallback to the first numeric variable;
- fallback to a previous analysis weight.

Canonical behavior is:

`no authorized active weight → unweighted`

### Resolution summary

`valid analysis override`
→ active override

else

`valid project default`
→ active default

else

`no active weight`
→ unweighted

---

# BASE CALCULATION RULES

## `unweighted_n`

`unweighted_n` is the number of unique respondents in the analytical denominator after:

- M2 Universe;
- explicit filters/banner cell where applicable;
- metric applicability;
- metric response-validity rules;

and before weight contribution changes the calculation.

A respondent with:

`weight = 0`

remains in `unweighted_n` when otherwise valid.

A respondent with a missing/non-numeric weight may remain represented in `unweighted_n` because failure of a weight value is not equivalent to failure of Universe or metric membership.

## Applied valid weights

For the weighted base, M3 uses only weight values allowed by B1.

Applied valid weights include:

- valid positive finite weights;
- zero weights.

Missing/non-numeric weights do not contribute.

Negative/non-finite weights block the affected weighted analysis.

## `weighted_n_raw`

`weighted_n_raw`

is the sum of the applied valid supplied weights.

## `weighted_n`

For V1:

`weighted_n = weighted_n_raw`

Therefore:

`weighted_n_raw = weighted_n = Σw`

No normalization, rescaling, trimming or other transformation occurs between them.

## `effective_n`

When mathematically calculable:

`effective_n = (Σw)^2 / Σ(w²)`

If no positive usable weight mass exists, it must not fabricate an effective N.

The result should be unavailable/null with the corresponding QA reason.

## Precision

Internal base calculations must preserve numeric precision.

Presentation rounding is not part of M3.

No M3 calculation may round `weighted_n` merely because the name contains `_n`.

---

# QA / ERROR BEHAVIOR

M3 must generate structured Weight QA.

QA must be available at the analytical scope actually used for the result, not only once at whole-project level.

Minimum diagnostics include:

- active `weight_id`;
- source variable;
- resolution source:
  - analysis override;
  - project default;
  - none;
- weight type/provenance;
- Universe/base reference;
- eligible/analytical unweighted N;
- valid-weight count;
- missing count/rate;
- non-numeric count/rate;
- non-finite count/rate;
- negative count/rate;
- zero count/rate;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;
- weight distribution diagnostics where applicable;
- warnings;
- blocking failures;
- release status.

Weight distribution diagnostics should support at least:

- min;
- P1;
- P5;
- median;
- mean;
- P95;
- P99;
- max;
- CV;
- max/min-positive ratio.

B1 defines no universal threshold that converts these distribution diagnostics into FAIL merely because the distribution is extreme.

### PASS behavior

A weighted calculation may PASS when:

- active weight resolves correctly;
- no blocking weight condition exists;
- there is positive weighted mass;
- required base/provenance fields are produced.

### WARNING behavior

Examples include:

- missing/non-numeric weights excluded according to B1;
- incomplete non-critical upstream methodology description;
- unusual distribution diagnostics without an approved failure threshold.

Warnings must remain visible in canonical QA.

They may not be silently dropped by a renderer.

### FAIL behavior

M3 must block the affected weighted result for at least:

- unresolved explicitly requested weight;
- unknown analysis override;
- invalid project default reference;
- negative weight;
- positive/negative infinity;
- no positive total applied weight;
- attempted automatic normalization;
- attempted automatic trimming/capping;
- attempted weighted use of the unweighted significance engine;
- failure to produce mandatory traceability for an official canonical weighted result.

### No silent repair

M3 must not repair an error merely to produce a number.

---

# PROVENANCE RULE

Every canonical weighted result must permit reconstruction of:

**Project**

- project identity/version.

**Dataset**

- dataset/input identity or version.

**Analysis configuration**

- analysis/configuration version;
- Universe reference;
- applicable analytical scope.

**Weight**

- `weight_id`;
- source variable;
- weight type;
- weight resolution source;
- upstream provenance;
- normalization provenance;
- trimming provenance.

**Engine**

- Core/rules version.

**Result**

- canonical base fields;
- Weight QA;
- warnings/failures;
- result/release status.

The source weight must remain distinguishable from any runtime validation representation.

---

# WEIGHTED SIGNIFICANCE RULE

B2 is not modified by M3.

When a weight is active and inferential significance is requested:

- weighted descriptive execution may continue if otherwise valid;
- significance status is:

`UNSUPPORTED`

- no significance letters are created;
- no unweighted p-value is relabeled as weighted;
- no Kish `effective_n` is substituted into an unweighted significance formula.

This guard is an M3 acceptance requirement.

---

# TEST MATRIX

## A. Resolution

**M3-WR-01 — No weight configured**
Expected: unweighted path; no warning merely for absence of weight.

**M3-WR-02 — Valid project default**
Expected: project default resolves.

**M3-WR-03 — Valid analysis override**
Expected: override wins over project default.

**M3-WR-04 — Unknown override**
Expected: blocking configuration failure; no fallback.

**M3-WR-05 — Invalid project default ID**
Expected: blocking configuration failure.

**M3-WR-06 — Name looks like a weight but is not configured**
Expected: no activation.

**M3-WR-07 — AI/NG candidate only**
Expected: no activation.

---

## B. Value validity

**M3-WV-01 — All positive finite weights**
Expected: PASS.

**M3-WV-02 — Missing weight**
Expected: excluded from weighted contribution; QA count/rate; no `1` imputation.

**M3-WV-03 — NaN weight**
Expected: same deterministic policy as missing.

**M3-WV-04 — Non-numeric value**
Expected: excluded from weighted contribution; reason captured; no implicit coercion/repair.

**M3-WV-05 — Positive infinity**
Expected: FAIL.

**M3-WV-06 — Negative infinity**
Expected: FAIL.

**M3-WV-07 — Negative weight**
Expected: `UNSUPPORTED V1` / affected weighted analysis FAIL.

**M3-WV-08 — Zero weight mixed with positives**
Expected: valid; respondent remains in `unweighted_n`; zero weighted contribution.

**M3-WV-09 — All zero**
Expected: weighted result unavailable/FAIL because total applied weight is zero.

**M3-WV-10 — Extreme positive weight**
Expected: calculation permitted; diagnostics produced; no trimming.

---

## C. Canonical bases

Use a hand-verifiable synthetic fixture including weights such as:

`0, 0.5, 1.0, 1.5, 2.0`

**M3-WB-01 — unweighted N**
Verify respondent count before weight contribution.

**M3-WB-02 — weighted\_n\_raw**
Verify exact sum of valid applied weights.

**M3-WB-03 — weighted\_n**
Verify exact equality:

`weighted_n == weighted_n_raw`

**M3-WB-04 — Kish effective N**
Verify independently hand-calculated Kish value.

**M3-WB-05 — No rounding mutation**
Verify internal bases preserve numeric precision.

**M3-WB-06 — Scale preservation**
Multiply every positive weight by a common constant.

Expected:

- `weighted_n_raw` changes by that scale;
- `weighted_n` changes by that scale;
- Kish `effective_n` remains invariant to common scaling.

This is a particularly useful regression test for detecting accidental normalization.

---

## D. No normalization / trimming

**M3-WN-01 — Expansion-style weights**
Expected: original large scale preserved.

**M3-WN-02 — Externally normalized weights**
Expected: supplied scale preserved.

**M3-WN-03 — Externally trimmed weight**
Expected: supplied values accepted with provenance; no second trimming.

**M3-WN-04 — Very large outlier**
Expected: QA diagnostic only unless another hard validity rule fails.

---

## E. M2 integration

**M3-M2-01 — Universe first**
Confirm same M2 respondent mask whether weighting is on or off.

**M3-M2-02 — Zero-weight respondent**
Confirm M2 eligibility does not change.

**M3-M2-03 — Missing-weight respondent**
Confirm M2 eligibility does not change.

**M3-M2-04 — M2 zero eligible**
Expected: valid Universe result; no fabricated weight error upstream.

**M3-M2-05 — M2 unsupported Universe state**
Expected: M3 does not reinterpret or repair it.

**M3-M2-06 — Exact same Universe evaluated weighted/unweighted**
Expected: identical Universe mask and `eligible_n`.

---

## F. Significance guard

**M3-WS-01 — Weighted result, significance not requested**
Expected: descriptive path valid.

**M3-WS-02 — Weighted result, significance requested**
Expected: significance=`UNSUPPORTED`; no p-values/letters.

**M3-WS-03 — Attempt to call unweighted significance engine using weighted data**
Expected: deterministic block/failure.

**M3-WS-04 — effective\_n present**
Expected: no significance call produced from Kish N.

---

## G. Provenance / QA

**M3-WQ-01 — Complete valid weight**
Expected: full provenance.

**M3-WQ-02 — Missing/non-numeric exclusions**
Expected: exact counts/rates and warning/reason.

**M3-WQ-03 — Zero weights**
Expected: zero counts visible.

**M3-WQ-04 — Negative/non-finite**
Expected: structured failure, not raw uncontrolled exception.

**M3-WQ-05 — External normalization metadata**
Expected: provenance preserved.

**M3-WQ-06 — External trimming metadata**
Expected: provenance preserved.

---

## H. Feature flag / regression

**M3-FL-01 — Flag absent**
Expected: `LEGACY`.

**M3-FL-02 — Explicit LEGACY**
Expected: Legacy behavior unchanged.

**M3-FL-03 — Canonical/Core internal execution**
Expected: M3 path reachable only through authorized Core execution.

**M3-FL-04 — Invalid engine mode**
Expected: existing deterministic mode error behavior preserved.

**M3-FL-05 — Rollback**
Switching back to LEGACY requires no:

- database migration;
- output migration;
- Web migration;
- data conversion.

---

# LEGACY COMPARISON PLAN

The pre-M3 regression baseline is the CLOSED M2 checkpoint.

The currently closed M2 test baseline must remain fully green before and after adding M3.

Legacy remains the production/default comparison path.

Comparison must distinguish **required parity** from **expected canonical divergence**.

### Exact or near-exact parity expected

For cases where:

- both paths explicitly use the same valid weight;
- no invalid/missing values exist;
- no legacy weight inference difference exists;
- Universe/base construction is equivalent;
- the compared quantity uses equivalent formulas;

numerical parity is expected.

Unexpected difference = investigate as potential regression.

### Intentional divergence expected

Differences are expected when Legacy:

- replaces missing weights with `1`;
- repairs non-numeric weights to `1`;
- identifies a weight heuristically;
- accepts behavior prohibited by B1;
- handles negative/non-finite weights differently;
- constructs the analytical base differently from canonical M2.

These are not automatically regressions.

They must be classified.

### Required difference classification

Every Legacy-vs-Canonical difference must be classified as one of:

1. `PARITY`
2. `INTENDED_B1_CHANGE`
3. `M2_BASE_DIFFERENCE`
4. `LEGACY_DEFECT_REPRODUCED`
5. `UNSUPPORTED_V1`
6. `POTENTIAL_REGRESSION`
7. `PRESENTATION_ONLY`

No unexplained numerical delta is acceptable.

---

# FEATURE FLAG RULES

M3 must not change the frozen execution-mode semantics.

`LEGACY` remains default.

M3 must not make Canonical weighting active merely because weight configuration exists.

The M3 capability remains behind the existing Analytics Core boundary.

A separate M3-specific internal flag may be used by implementation if technically useful, but it must:

- default OFF;
- not modify the meaning of `EXPLORA_ANALYTICS_ENGINE`;
- not alter production Legacy behavior;
- be fully removable/reversible.

A new flag is not a methodological requirement.

---

# M3 ACCEPTANCE CRITERIA

M3 can be considered CLOSED only if all of the following are demonstrated.

### Contract

- B1 canonical rules implemented without reinterpretation.
- No frozen contract semantics changed silently.
- No M2 semantics changed.

### Resolution

- analysis override precedence works;
- project default works;
- absence of weight produces unweighted execution;
- heuristic/name/AI activation is impossible.

### Validity

- missing/non-numeric never become `1`;
- zero works as approved;
- negative fails;
- non-finite fails;
- no normalization occurs;
- no trimming occurs.

### Bases

Canonical results correctly retain:

- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`.

And V1 proves:

`weighted_n_raw == weighted_n`

for every valid weighted analysis.

### Kish

`effective_n` matches independent golden calculations and is never used as an inferential N.

### M2

- Universe runs first;
- same Universe membership exists with weighting on/off;
- weight never mutates M2 masks/results.

### QA

- Weight QA is structured;
- exclusions/failures are traceable;
- no silent repair exists;
- no raw implementation exception substitutes for canonical status handling.

### Significance

- weighted significance is explicitly `UNSUPPORTED`;
- no weighted letters/p-values/CI are produced;
- current unweighted significance routines are never reused for weighted results.

### Regression

- complete pre-M3/M2 regression suite remains green;
- M3-focused tests pass;
- Legacy remains default;
- Legacy output is unchanged when M3 is inactive;
- all Legacy-vs-Canonical deltas are classified.

### Architecture

No changes to:

- Web;
- SQLite;
- Excel;
- EXPLORA NG;
- RM/Grid migration;
- B1/B2/B3 methodology.

### Reversibility

Returning to LEGACY requires no migration or cleanup of production data.

---

# BLOCKERS

## Current methodological blockers

**NONE.**

The B1 rules required for this M3 scope are sufficiently frozen.

In particular, the previous potential ambiguity around:

`weighted_n_raw`

versus

`weighted_n`

is closed:

**V1 requires both fields and both equal the sum of applied valid supplied weights.**

## Implementation stop conditions

The following findings would block M3 implementation and require escalation rather than an ad hoc fix:

1. A required canonical B1 field is absent from the frozen contract and adding it would alter frozen semantics.
2. M3 requires changing M2 Universe membership or response-state semantics.
3. M3 cannot be isolated without changing LEGACY default behavior.
4. Existing code requires weighted significance to calculate/release a weighted descriptive result.
5. A production renderer must be modified to make M3 work.
6. SQLite schema migration becomes necessary for M3 runtime correctness.
7. An implementation requires normalization, trimming or weight imputation not authorized by B1.
8. A conflict is discovered between the implementation checkpoint and `WEIGHT_POLICY_CANONICAL.md`.

If any of these occurs:

**STOP.**

Do not resolve it silently inside M3.

---

# CODEX READY

**YES — CONTRACT READY.**

M3 is sufficiently specified for Codex to implement without choosing weight methodology independently.

This status means:

**the implementation contract is ready.**

It does **not** mean:

**Codex is authorized to start automatically.**

Separate explicit human authorization to begin M3 implementation is still required.

---

# FINAL GATE POSITION

**M2:** CLOSED / ACCEPTED — DO NOT REOPEN
**B1:** HUMAN APPROVED — DO NOT MODIFY
**M3 contract:** READY
**M3 implementation:** NOT YET AUTHORIZED BY THIS DOCUMENT
**M4:** NOT STARTED
**Web migration:** NOT AUTHORIZED
**Weighted significance:** `UNSUPPORTED V1`
**Legacy default:** MUST REMAIN

La conclusión es **CODEX READY = YES**, pero sólo en sentido de que el contrato ya está suficientemente cerrado para programarse; no constituye la orden de implementación. Además, haría del test `weighted_n_raw == weighted_n` y del test de invariancia de Kish ante un reescalamiento común dos pruebas obligatorias del gate final de M3, porque detectan de forma muy limpia cualquier normalización no autorizada.
