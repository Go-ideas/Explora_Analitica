# EXPLORA — WEIGHT POLICY CANONICAL

**Module:** 05A — Weight Methodology
**Gate:** GATE 1 — B1
**Status:** HUMAN APPROVED — CANONICAL B1 SOURCE
**Approval date:** 2026-09-14
**Scope:** EXPLORA V1 descriptive weighting methodology. No code implementation and no automatic B2 progression.
**Evidence basis:** EXPLORA NG AS-IS, EXPLORA Web AS-IS, plus the verified FASE 1 sources `06_UNIVERSE_SPEC_DRAFT.md`, `07_WEIGHT_SPEC_DRAFT.md`, `08_METRIC_SPEC_DRAFT.md`, `09_SIGNIFICANCE_SPEC_DRAFT.md`, `10_CANONICAL_RESULTS_DRAFT.md`, `12_QA_ARCHITECTURE.md`, `17_ARCHITECTURE_DECISION_REGISTER.md`, `19_GATE_1_ASSESSMENT.md`, and `PHASE1_SOURCE_MANIFEST.md`.

## 1. Authority

This document is the single canonical B1 source for weight methodology in subsequent EXPLORA phases. If an earlier B1 document conflicts with this file, this file governs.

The methodology preserves the architectural boundary established in FASE 1: EXPLORA NG may interpret/propose; Analytics Core calculates, validates and stores official weighted results; Web and Excel present Canonical Results and do not independently calculate weighting.

Decision vocabulary in this source is limited to `APPROVED RULE`, `DEFER`, and `UNSUPPORTED V1`.

## 2. Approved rules

### WR-01 — Explicit configuration and validation
**Status: APPROVED RULE**

A weight may be used only when it is explicitly configured through the released project/weight contract and successfully validated. Name-based discovery or an AI recommendation may identify a candidate but cannot activate weighting.

### WR-02 — No silent substitution
**Status: APPROVED RULE**

A missing, non-numeric, non-finite, negative, or otherwise invalid value is never silently replaced with `1`. Legacy `fillna(1.0)` behavior is non-canonical.

### WR-03 — Missing/non-numeric weight
**Status: APPROVED RULE**

Missing/NaN and non-numeric/parse-invalid weights are excluded from the weighted calculation. Each exclusion must be recorded in Weight QA with count/rate and reason. Exclusion from the weighted calculation does not by itself remove an otherwise eligible respondent from `unweighted_n`.

### WR-04 — Zero weight
**Status: APPROVED RULE**

`weight = 0` is valid. If the respondent belongs to the metric universe, the respondent may remain in `unweighted_n`, contributes 0 to weighted numerator/denominator, and remains visible in Weight QA. If the total applied valid weight for an analytical denominator is 0, the weighted estimate is unavailable and the affected analysis fails.

### WR-05 — Non-finite weight validation
**Status: APPROVED RULE**

Non-finite weights (`+∞`/`-∞`) fail validation and cannot enter a weighted analytical denominator. Negative weights are governed separately under `UNSUPPORTED V1`.

### WR-06 — Preserve original weights / no automatic normalization
**Status: APPROVED RULE**

EXPLORA V1 preserves the supplied weight values. Analytics Core performs no automatic normalization/rescaling. An externally normalized or calibrated weight may be consumed as supplied when its provenance is recorded.

### WR-07 — No automatic trimming/capping
**Status: APPROVED RULE**

Analytics Core performs no automatic trimming/capping in V1. A weight already transformed upstream may be consumed as supplied with provenance. Configurable Core trimming/capping is listed separately under `DEFER`.

### WR-08 — Multiple weights
**Status: APPROVED RULE**

A project may register multiple weights. Resolution is deterministic:

1. explicit valid analysis-level override, when the contract permits it;
2. project default weight;
3. otherwise unweighted.

There may be at most one project default. Unknown, ambiguous, or out-of-scope overrides are blocking configuration failures.

### WR-09 — Universe before weighting
**Status: APPROVED RULE**

Methodological universe/applicability and metric-valid response rules are resolved before weight contribution is applied. Weighting does not redefine structural zero, structural missing, or respondent eligibility.

### WR-10 — Canonical bases
**Status: APPROVED RULE**

Canonical Results preserve at least:

- `unweighted_n`
- `weighted_n_raw`
- `weighted_n`
- `effective_n`

`unweighted_n` is the count of unique metric-valid respondents after universe/applicability/filter rules and before weight contribution changes.

`weighted_n_raw` is the sum of applied valid supplied weights. `weighted_n` is the weighted base after any approved transformations. In V1 there is no Core normalization or trimming, therefore:

`weighted_n_raw = weighted_n = Σ applied valid weights`

### WR-11 — Effective N (Kish)
**Status: APPROVED RULE**

When applicable, Analytics Core calculates Kish effective sample size:

`effective_n = (Σw)^2 / Σ(w^2)`

In V1 it is diagnostic / QA only. It must not:

- replace `unweighted_n`;
- define a metric denominator;
- modify a weighted estimate;
- be used for significance;
- automatically block a release.

Inferential use of `effective_n` is `DEFER`.

### WR-12 — Weighted percentages
**Status: APPROVED RULE**

Weighted percentages are calculated exclusively by Analytics Core under the versioned Metric Spec/Registry. General form:

`weighted_pct = Σ(w_i × I_i) / Σ(w_i)`

The denominator membership comes from the approved metric universe/response rules, not from renderer logic.

### WR-13 — Weighted means
**Status: APPROVED RULE**

Weighted means are calculated exclusively by Analytics Core:

`weighted_mean = Σ(w_i × x_i) / Σ(w_i)`

over metric-valid observations with valid applied weights.

### WR-14 — Weighted RM respondent %
**Status: APPROVED RULE**

Analytics Core calculates respondent-level RM percentages. Each valid respondent contributes its weight once to the denominator and at most once per selected option to the option numerator. Duplicate respondent × option mentions are deduplicated before weighting.

### WR-15 — Weighted RM mention %
**Status: APPROVED RULE**

Analytics Core calculates weighted mention share. Each valid mention inherits its respondent's applied weight; numerator is weighted mentions for the option and denominator is total weighted mentions in the same valid analytical universe.

### WR-16 — Weighted descriptive NPS
**Status: APPROVED RULE**

Weighted NPS is supported descriptively in Analytics Core:

`NPS = (weighted promoter share - weighted detractor share) × 100`

Passives remain in the denominator. This approval does not imply weighted inferential testing.

### WR-17 — Renderer boundary
**Status: APPROVED RULE**

EXPLORA Web and EXPLORA Excel consume Canonical Results. They must not select, repair, normalize, trim, impute, or recalculate weights, weighted percentages, weighted means, RM metrics, NPS, bases, or effective N.

### WR-18 — Weight QA
**Status: APPROVED RULE**

Every weighted result must carry enough QA/provenance to reproduce and audit the calculation, including at minimum:

- weight identity/source/provenance;
- analytical universe/base reference;
- counts/rates for missing, non-numeric, non-finite, negative and zero weights;
- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- Kish `effective_n` when applicable;
- distribution diagnostics needed by Weight QA;
- structured warnings/failures and release status.

QA never silently repairs weights.

## 3. Unsupported V1

### UV1-01 — Negative weights
**Status: UNSUPPORTED V1**

Negative weights are not analytically supported. The affected weighted analysis fails.

### UV1-02 — Weighted significance / weighted inference
**Status: UNSUPPORTED V1**

No weighted inferential method, p-value, confidence interval, or significance-letter engine is approved for V1. Weighted descriptive results may be released when otherwise valid, but significance eligibility for the weighted path is structured as `UNSUPPORTED`. Current unweighted z/Welch logic cannot be reused as weighted inference.

## 4. Deferred

The following are outside B1/V1 and require separate future approval before implementation:

- configurable trimming/capping inside Core;
- generation, raking, post-stratification, or calibration of weights by Core;
- methodology for weighted significance/inference;
- universal thresholds for extreme weights, CV, max/min ratios, design effects, or effective-N ratios;
- inferential use of `effective_n`;
- complex-survey variance systems, replicate weights, BRR, jackknife, bootstrap or equivalent design-based inference.

## 5. Canonical result and QA implications

A valid weighted analytical result must be reproducible from dataset + released specs + Core/rules version and must preserve the canonical bases above. Missing/non-numeric exclusions are deterministic weight-policy behavior and must be observable in QA. Negative or non-finite weights are not repaired.

An official release requires successful Weight Spec resolution, valid Core calculation, no blocking QA issue, and renderer parity with Canonical Results. `effective_n` is diagnostic and is not by itself a release gate in V1.

## 6. Legacy compatibility

Historical EXPLORA Web behavior may be reproduced only in an explicitly isolated legacy/regression path. Legacy behavior is evidence for comparison, not an alternative canonical policy. Before production replacement, representative weighted projects require regression comparison and classification of intended methodological differences versus defects.

## 7. Traceability

Every released weighted result must be traceable to project/configuration, dataset, Weight/Universe/Metric specs, Core/rules version, weight provenance, canonical bases, QA evidence, result version and release status.

## 8. B1 closure

**B1 STATUS: HUMAN APPROVED — METHODOLOGICAL GATE CLOSED.**

`WEIGHT_POLICY_CANONICAL.md` is the B1 canonical methodological input for subsequent phases. This closure does not assert implementation and does not authorize automatic advancement to B2.
