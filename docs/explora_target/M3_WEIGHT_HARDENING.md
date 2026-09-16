# EXPLORA - M3 WEIGHT HARDENING

**Milestone:** M3 - Weight Hardening / B1 Runtime Implementation
**Date:** 2026-09-14
**Authority:** `WEIGHT_POLICY_CANONICAL.md`
**Default runtime mode:** `LEGACY`

## Scope

M3 adds an internal B1 canonical weight runtime in Analytics Core. It implements
deterministic active-weight resolution, B1 weight validation, weighted
contribution, canonical bases, Kish effective N, Weight QA, provenance,
M2-downstream sequencing and a weighted-significance guard.

M3 does not migrate Web, SQLite, Excel, NG, RM/Grid authority or production
reporter behavior.

## Runtime Location

Weight execution lives in:

`explora_web_reporter/src/analytics_core/weights.py`

The module is renderer-neutral and does not import Streamlit, Plotly, Excel,
SQLite readers, Web UI, reporter calculations or the significance engine.

## Resolution

Active weight resolution is deterministic:

1. explicit valid analysis-level override;
2. explicit valid project default;
3. otherwise unweighted.

No weight is activated by variable name, datamap role, AI/NG candidate, first
numeric variable or previous analysis state.

`ProjectSpec.default_weight_ref` and `WeightSpec.is_project_default` are not
allowed to become independent runtime authorities. If both are present and
disagree, M3 returns structured configuration `FAIL`.

Unknown, ambiguous or out-of-scope override is a blocking error and does not
fall through to project default.

## No-Weight Behavior

No configured active weight is semantically unweighted:

- active weight is `None`;
- resolution source is `none`;
- weighted contribution is not performed;
- `weighted_n_raw` is `None`;
- `weighted_n` is `None`;
- `effective_n` is `None`;
- `unweighted_n` remains available.

M3 does not synthesize unit weights.

## Value Validity

M3 distinguishes valid finite numeric weights, zero, missing/NaN, non-numeric,
negative and non-finite values.

Missing, NaN and non-numeric values are excluded from weighted contribution and
recorded in Weight QA. They remain in `unweighted_n` when M2 and metric
validity include them.

`weight = 0` is valid, remains in `unweighted_n`, contributes zero to weighted
bases and Kish sums, and is visible in Weight QA.

Negative weights are `UNSUPPORTED V1` and block the affected weighted analysis.
Positive or negative infinity is invalid and blocking.

No missing, invalid or non-numeric value is replaced with `1`.

## Canonical Bases

M3 produces:

- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`.

For V1:

`weighted_n_raw == weighted_n == sum(valid applied supplied weights)`

There is no normalization, rescaling, trimming, capping, winsorization,
imputation or rounding mutation.

## Kish Effective N

When calculable:

`effective_n = (sum(w) ** 2) / sum(w ** 2)`

Kish effective N is diagnostic / QA only. It does not replace `unweighted_n`,
replace `weighted_n`, define a metric denominator, modify estimates, feed
significance or automatically block release.

If there is no positive usable weight mass, `effective_n` is unavailable with
structured QA. If the analytical denominator has respondents and total applied
valid weight is not positive, the weighted base is unavailable and the affected
weighted analysis fails.

## Weight QA

`WeightQA` records:

- active weight ID;
- source variable;
- resolution source;
- weight provenance;
- Universe/base reference;
- analytical scope;
- `unweighted_n`;
- valid-weight count;
- missing, non-numeric, non-finite, negative and zero counts/rates;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;
- distribution diagnostics;
- warnings;
- blocking failures;
- aggregate status.

Distribution diagnostics include min, P1, P5, median, mean, P95, P99, max, CV
and max/min-positive ratio. B1 defines no universal threshold that converts an
extreme but valid distribution into a failure.

## Provenance

`WeightProvenance` records available project, dataset, analysis, Universe,
weight, B1 policy and Core/rules version identities. Missing non-critical
metadata is represented as `None`; M3 does not fabricate unavailable
provenance.

Externally normalized or trimmed weights may be consumed as supplied when
their upstream provenance is provided. Core does not transform them again.

## M2 Sequencing

M3 consumes `UniverseEvaluationResult.respondent_mask` from M2 as immutable
input. It does not alter Universe refs, masks, scopes, `eligible_n`,
`excluded_n`, zero-eligible semantics or M2 `FAIL` / `UNSUPPORTED` behavior.

Execution order is:

M2 Universe -> metric-valid denominator -> active weight resolution -> weight
validation -> weighted contribution -> canonical bases / Weight QA.

## Significance Guard

M3 DOES NOT IMPLEMENT WEIGHTED SIGNIFICANCE.

When a weight is active and significance is requested, descriptive weighted
execution may remain valid, but significance status is `UNSUPPORTED`. M3 does
not call `src/reporter/significance.py`, does not calculate weighted p-values,
confidence intervals or letters, and does not use Kish effective N as
inferential N.

## Legacy Comparison

Legacy remains default and productive behavior remains unchanged. Legacy
weight behavior, including historical `fillna(1.0)`, remains isolated in the
legacy profile.

Legacy-vs-canonical weight differences are classified as:

- `PARITY`;
- `INTENDED_B1_CHANGE`;
- `M2_BASE_DIFFERENCE`;
- `LEGACY_DEFECT_REPRODUCED`;
- `UNSUPPORTED_V1`;
- `POTENTIAL_REGRESSION`;
- `PRESENTATION_ONLY`.

Canonical B1 differences are classified; M3 does not alter canonical behavior
to match legacy.

## Tests

M3 adds 31 focused tests. The suite now contains 172 passing tests.

Covered:

- no configured weight;
- project default;
- analysis override;
- override precedence;
- unknown and out-of-scope override;
- invalid project default;
- conflicting default authorities;
- no heuristic/name/AI activation;
- missing, NaN, non-numeric, zero, negative, positive infinity and negative
  infinity;
- all zero weights;
- extreme positive weights;
- canonical base golden values;
- `weighted_n_raw == weighted_n`;
- Kish golden calculation;
- Kish scale invariance;
- no rounding mutation;
- expansion-style weights;
- externally normalized/trimmed provenance;
- M2 mask invariance;
- metric validity before weight contribution;
- M2 zero eligible;
- M2 `FAIL` / `UNSUPPORTED` propagation;
- significance guard;
- no import/call to unweighted significance engine;
- QA counts/rates;
- provenance;
- feature flag default `LEGACY`;
- rollback without migration.

## Test Result

Focused M3:

```powershell
python -m pytest -q tests\test_weight_runtime.py --basetemp .pytest_tmp_m3_focus_only
```

Result:

- PASS: 31
- FAIL: 0
- SKIP: 0

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_full
```

Result:

- PASS: 172
- FAIL: 0
- SKIP: 0

Legacy vs CORE_WRAPPER parity:

```powershell
python -m pytest -q tests\test_core_wrapper_parity.py --basetemp .pytest_tmp_m3_parity
```

Result:

- PASS: 1
- FAIL: 0
- SKIP: 0
- Productive legacy numerical deltas: none

## Guardrails

- `LEGACY` remains default.
- M2 Universe files and semantics are unchanged.
- Frozen contracts are unchanged.
- Protected reporter files are unchanged.
- No dependency change.
- No database/SQLite change.
- No UI/Web change.
- No Excel/VBA change.
- No NG change.
- No RM/Grid migration.
- No weighted significance.
- M4 is not started.

## Known Limitations

M3 provides the canonical weight runtime/base/QA layer. It does not migrate all
metric families into canonical result execution, does not persist Canonical
Results, and does not replace the Web reporter runtime. Those remain deferred
to later authorized milestones.
