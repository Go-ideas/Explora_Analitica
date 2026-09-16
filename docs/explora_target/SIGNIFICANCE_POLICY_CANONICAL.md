# EXPLORA — SIGNIFICANCE POLICY CANONICAL

**Module:** 05B — Significance & Statistical Policy
**Gate:** GATE 1 — BLOCKER B2
**Status:** HUMAN APPROVED — CANONICAL B2 SOURCE
**Approval date:** 2026-09-14
**Scope:** EXPLORA V1 statistical significance/inference policy. No code implementation and no automatic progression to B3.

## 1. Authority

This document is the single canonical B2 source for significance/statistical methodology in EXPLORA V1.

If an earlier B2 draft, recommendation, decision matrix, Web legacy behavior, EXPLORA NG guidance, or other B2 document conflicts with this file, this file governs for Canonical Mode.

The approved architectural boundary is:

- Analytics Core is the only layer authorized to calculate statistical significance.
- EXPLORA Web and EXPLORA Excel only present significance already contained in Canonical Results.
- A renderer must never calculate, recompute, adjust, repair, reinterpret, or overwrite p-values, adjusted p-values, eligibility, status, direction, comparison-family membership, or statistical relationships.
- Metric names or display labels are never sufficient by themselves to choose a statistical test.
- Unsupported, ineligible, or untested cases must be represented explicitly and must never be converted into silent absence of letters.

B1 Weight Methodology remains closed and has precedence on weighting. In particular:

- weighted descriptive calculations may exist under the canonical Weight Policy;
- weighted significance / weighted inference is `UNSUPPORTED V1`;
- `effective_n` is diagnostic / QA only;
- `effective_n` must not be used as inferential N;
- current unweighted z/Welch logic must not be adapted silently to weighted results.

## 2. Approved statistical status vocabulary

At comparison level, Canonical Results must distinguish at least:

- `SIGNIFICANT`
- `NOT_SIGNIFICANT`
- `INELIGIBLE`
- `UNSUPPORTED`
- `NOT_TESTED`
- `FAIL` or equivalent execution/configuration failure status

The absence of a significance letter never implies `NOT_SIGNIFICANT`.

`INELIGIBLE`, `UNSUPPORTED`, `NOT_TESTED`, and `FAIL` must remain distinguishable from a valid executed test that returned `NOT_SIGNIFICANT`.

## 3. Confidence and sidedness

**APPROVED RULE**

- Default confidence = `95%`.
- Configurable confidence values in V1 = `90%`, `95%`, `99%`.
- `alpha = 1 - confidence`.
- All canonical V1 significance tests are `two-sided`.
- 97% is not a supported canonical V1 confidence level.

## 4. Minimum test base

**APPROVED RULE**

The default hard minimum test base is:

`unweighted_n >= 30`

for each group participating in a comparison.

Rules:

- eligibility uses unweighted respondent base;
- weighted N and `effective_n` do not replace this base;
- the minimum-base check is necessary but not sufficient to establish test eligibility;
- any future override must be explicit, versioned, tied to an approved test/profile, and cannot silently change the canonical default.

No universal V1 reporting-caution threshold is approved by B2. A project may define an explicit nonblocking caution rule separately, without changing the inferential formula.

## 5. Proportion test

### 5.1 Supported statistical shape

**APPROVED RULE**

Use a pooled two-proportion z-test only for respondent-level binary outcomes compared between independent/disjoint groups.

Eligible examples may include:

- categorical respondent proportions;
- RM respondent percentage for the same option across independent groups;
- Top Box / Bottom Box after explicit respondent-level binary derivation in Metric Spec;
- other derived binary respondent indicators only when Metric Spec explicitly declares proportion-test compatibility.

### 5.2 Canonical formula

For groups 1 and 2:

- `p1 = x1 / n1`
- `p2 = x2 / n2`
- pooled estimate under H0: `p = (x1 + x2) / (n1 + n2)`
- `SE = sqrt(p * (1-p) * (1/n1 + 1/n2))`
- `z = (p1 - p2) / SE`
- `p_raw = 2 * (1 - Phi(abs(z)))`

The test is two-sided.

### 5.3 Eligibility

A pair is eligible only when all of the following hold:

- both groups are independent/disjoint;
- the outcome is respondent-level binary;
- both groups have `unweighted_n >= 30`;
- numerators are valid respondent counts with `0 <= x <= n`;
- under the pooled null, expected successes are >=5 in both groups;
- under the pooled null, expected failures are >=5 in both groups;
- the standard error is finite and non-degenerate;
- the case is otherwise supported by the released Metric/Significance Spec.

Expected counts are:

- `n1*p`
- `n1*(1-p)`
- `n2*p`
- `n2*(1-p)`

The bases and expected counts used for eligibility are unweighted even when a descriptive weighted result also exists.

### 5.4 Extreme proportions

One group may be 0% or 100% only when the pooled expected-count adequacy requirements still pass.

If both groups are 0%, or both are 100%, pooled variance is degenerate and the comparison is `INELIGIBLE`; Core must not fabricate a p-value.

## 6. Mean test

### 6.1 Supported statistical shape

**APPROVED RULE**

For eligible means from independent groups, use the Welch independent-samples t-test.

The Metric Spec must first establish that the metric is valid for a mean-based comparison.

### 6.2 Canonical formula

`t = (mean1 - mean2) / sqrt(s1^2/n1 + s2^2/n2)`

with Welch–Satterthwaite degrees of freedom and a two-sided p-value.

### 6.3 Eligibility

- independent/disjoint groups;
- unweighted observations for inference;
- valid numeric mean-compatible metric;
- missing handling defined by Metric Spec;
- each group meets `unweighted_n >= 30`;
- required variance calculations are finite.

### 6.4 Degenerate variance

If both groups have variance zero, the comparison is `INELIGIBLE`.

No artificial p-value may be generated, including the historical shortcut of p=0 when means differ or p=1 when means are equal.

If only one group has zero variance and the Welch calculation remains finite, execution may proceed with a structured warning.

## 7. Multiple comparisons

**APPROVED RULE**

Canonical V1 uses Holm step-down correction.

Core must preserve:

- raw p-value;
- Holm-adjusted p-value;
- direction of the difference;
- eligibility/status;
- reason codes;
- test version;
- significance-policy version.

Where Holm applies, significance decisions and rendered letters are based on the adjusted p-value.

`NONE` correction is allowed only under an explicit legacy/regression profile and is not Canonical Mode.

## 8. Comparison family

**APPROVED RULE**

A comparison family consists of all eligible pairwise comparisons between categories of the same banner for the same:

- question;
- metric;
- analytical row, option, or derived indicator;
- active analytical/filter slice represented by that canonical result context.

The following must not be combined into one Holm family:

- different banners;
- different questions;
- different metrics;
- different rows/options/derived indicators.

Pairs with status `INELIGIBLE` or `UNSUPPORTED` do not participate in the Holm adjustment and preserve their own reason/status.

If an execution failure makes the set of eligible pairwise tests incomplete, QA must prevent the family from being represented as a complete canonical Holm result until the supported comparisons are resolved.

## 9. Banners and Total

**APPROVED RULE**

- Canonical comparisons occur by default only within the same banner.
- Cross-banner significance = `UNSUPPORTED V1`.
- Total is excluded from comparison families.
- Automatic subgroup-vs-Total significance = `UNSUPPORTED V1`.
- Analytics Core must not infer independence from labels alone.

## 10. Significance relations and display letters

**APPROVED RULE**

Analytics Core does not use letters as the statistical source of truth.

Core stores pairwise statistical relations using stable IDs, including:

- compared member IDs;
- family/group ID;
- eligibility/status;
- raw p-value;
- adjusted p-value when applicable;
- direction of the difference;
- reason/warning codes;
- method/test version;
- policy version.

Web/Excel may map stable members to display tokens such as A/B/C according to the current visual order.

The canonical truth remains the pairwise relation, not the literal letter.

The absence of a letter must never be interpreted automatically as `NOT_SIGNIFICANT`.

Renderers must be able to distinguish at least:

- NOT SIGNIFICANT;
- INELIGIBLE;
- UNSUPPORTED;
- NOT TESTED.

## 11. RM policy

### 11.1 RM respondent percentage

**APPROVED RULE**

RM respondent % may use the proportion-test family only when comparing the same RM option between independent groups.

Each respondent must contribute at most once to the binary indicator for that option after respondent-option deduplication.

Comparing different RM options selected by the same respondents using an independent two-proportion z-test is `UNSUPPORTED V1`.

### 11.2 RM mention percentage

**UNSUPPORTED V1**

RM mention significance is not supported in V1.

Mentions are clustered within respondents and may have unequal per-respondent contribution; the independent Bernoulli z-test must not be used.

## 12. Top Box / Bottom Box

**APPROVED RULE**

Top Box and Bottom Box may use the canonical proportion-test family only when Analytics Core first generates an explicit respondent-level binary indicator under the released Metric Spec.

No test may be selected only because a row is labeled “Top Box” or “Bottom Box.”

## 13. Independent waves / tracking

**APPROVED RULE**

z-test/Welch comparisons between waves are permitted only when the released Project/Question Spec declares and validates that the samples are independent.

If dependency is unknown:

`UNSUPPORTED / REVIEW`

If respondents are repeated/panel observations, independent-sample tests are not allowed.

## 14. Unsupported V1

The following are explicitly `UNSUPPORTED V1`:

- weighted significance / weighted inference;
- NPS significance;
- RM mention significance;
- paired/repeated significance;
- panel comparisons using independent-sample tests;
- complex-sample significance without an approved survey-inference methodology;
- automatic subgroup-vs-Total significance;
- cross-banner significance;
- inference when dependency is unknown;
- inferential use of `effective_n`.

Unsupported status is an explicit methodological result, not a blank and not `NOT_SIGNIFICANT`.

## 15. Deferred

The following are outside the approved V1 methodology and require a future human-approved policy before implementation:

- weighted/survey inference;
- paired/repeated methods;
- NPS inferential method;
- RM mention cluster-aware inference;
- generic conversion/funnel inference;
- complex-design variance estimation;
- sparse-proportion exact alternatives;
- optional exploratory FDR profile.

Deferral does not prevent B2 closure because the V1 behavior for these cases is explicitly bounded.

## 16. Statistical QA

**APPROVED RULE**

Before any test, Analytics Core must validate at least:

- declared/validated independence;
- minimum unweighted base;
- expected-count adequacy when applicable;
- variance / degeneracy;
- weighting status;
- comparison-family definition;
- test support.

Allowed QA states:

- `PASS`
- `WARN`
- `INELIGIBLE`
- `UNSUPPORTED`
- `FAIL`

QA must not silently repair assumptions, invent independence, substitute `effective_n`, or silently select another test.

### QA interpretation

- `PASS`: supported test executed under the released policy with no blocking issue.
- `WARN`: supported test executed, with a nonblocking condition retained in Canonical Results/QA.
- `INELIGIBLE`: the test family is supported in principle, but the specific pair fails an eligibility requirement such as minimum base, expected counts, or degeneracy.
- `UNSUPPORTED`: V1 has no approved inferential method for this case.
- `FAIL`: configuration/data/execution violates a required supported contract and blocks the requested significance output.

## 17. Canonical Results requirements

Each tested or considered comparison must retain enough structured information to reproduce and audit the decision.

At minimum, conceptually preserve:

- significance eligibility;
- statistical status;
- reason/status code;
- test ID;
- test/formula version;
- Significance Policy version;
- confidence;
- alpha;
- sidedness;
- comparison-family ID;
- stable member IDs;
- unweighted inferential bases;
- numerator/expected-count diagnostics when relevant;
- variance diagnostics when relevant;
- raw p-value when executed;
- Holm-adjusted p-value when applicable;
- adjustment method/version;
- direction;
- warnings;
- QA/release status.

Physical field names may evolve through schema reconciliation, but the statistical meaning above is mandatory.

## 18. Legacy compatibility

Historical EXPLORA Web behavior is evidence for regression, not a source of canonical methodology.

A dedicated legacy/regression profile may reproduce historical behavior, including no multiple-comparison correction where needed for parity analysis.

Every material Legacy-vs-Canonical difference must be classified as:

- `EXPECTED_METHODOLOGICAL_CHANGE`
- `DEFECT`
- `UNKNOWN_REQUIRES_REVIEW`

Canonical Mode must not be altered only to force legacy parity.

## 19. Versioning and traceability

Every official significance result must be traceable to:

- project;
- released configuration/specs;
- dataset/version;
- analytical universe;
- metric definition;
- Significance Policy version;
- test/formula version;
- multiple-comparison method/version;
- parameters;
- QA evidence;
- Canonical Results version;
- release status.

## 20. B2 closure

**B2 STATUS: HUMAN APPROVED — METHODOLOGICAL GATE PASSED.**

All B2 closure topics required for EXPLORA V1 are either:

- explicitly approved;
- explicitly `UNSUPPORTED V1`; or
- explicitly `DEFERRED`.

No unresolved methodological decision remains that requires Analytics Core/Codex to invent a significance rule during V1 implementation.

This closure does not assert implementation completion, regression completion, production release, or automatic progression to B3.

**Do not advance automatically to B3.**
