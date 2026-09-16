# EXPLORA - M3 WEIGHT HARDENING REMEDIATION

**Milestone:** M3 - Weight Hardening / B1 Runtime Implementation
**Corrective pass:** B-M3-01 - NaN Classification Hardening
**Date:** 2026-09-14
**Authority:** `WEIGHT_POLICY_CANONICAL.md`
**Runtime default:** `LEGACY`

## Status

B-M3-01 is remediated inside the M3 Analytics Core weight runtime.

The correction is additive and isolated. It does not change B1 methodology,
frozen contracts, M2 Universe semantics, productive legacy reporter behavior,
Web/UI, SQLite/database behavior, Excel, NG, RM/Grid, or runtime significance.

## Root Cause

The M3 weight runtime classified missing values with a Python `float`-specific
NaN check. Python `float("nan")` and values commonly materialized as
`numpy.float64` were covered, but narrower NumPy floating scalars such as
`numpy.float32(np.nan)` could pass the missing check and then be classified by
the later non-finite guard.

That made NaN classification type-dependent.

## Remediation

`src/analytics_core/weights.py` now identifies numeric NaN values before the
non-finite check by applying the missing/NaN classification to any non-boolean
numeric real value that can be converted to a float.

Classification order remains:

1. missing / NaN;
2. valid finite numeric;
3. zero;
4. negative finite;
5. positive infinity;
6. negative infinity;
7. non-numeric.

NaN is therefore missing QA, not non-finite QA. Positive and negative infinity
remain blocking non-finite values.

## Behavior

Missing / NaN weights:

- are excluded from weighted contribution;
- remain in `unweighted_n` when M2 and metric validity include the respondent;
- increment `WeightQA.missing_count`;
- do not increment `WeightQA.non_finite_count`;
- do not become implicit unit weights;
- do not fail descriptive weighted execution solely because they are NaN.

Infinity weights:

- increment `WeightQA.non_finite_count`;
- block the affected weighted analysis;
- leave `weighted_n_raw`, `weighted_n` and `effective_n` unavailable.

## Mixed Valid + NaN Case

For:

- `r1` weight = `1.0`;
- `r2` weight = `numpy.float32(np.nan)`;
- both respondents eligible in M2;

the canonical result is:

- status: `PASS_WITH_WARNINGS`;
- `unweighted_n`: `2`;
- `weighted_n_raw`: `1.0`;
- `weighted_n`: `1.0`;
- `effective_n`: `1.0`;
- `missing_count`: `1`;
- `non_finite_count`: `0`.

## NaN Types Covered

Focused remediation tests cover:

- `float("nan")`;
- `numpy.float16(np.nan)`;
- `numpy.float32(np.nan)`;
- `numpy.float64(np.nan)`;
- `numpy.longdouble(np.nan)` when available;
- pandas `Series` / DataFrame-like materialization through `Series.to_dict()`;
- explicit `numpy.float32(np.nan)` vs `numpy.float32(np.inf)` and
  `numpy.float32(-np.inf)`.

## M2 Integration

M3 continues to consume `UniverseEvaluationResult.respondent_mask` from M2 as
immutable input. The remediation does not change respondent eligibility,
Universe refs, `eligible_n`, `excluded_n`, zero-eligible behavior, or M2
`FAIL` / `UNSUPPORTED` propagation.

## Test Evidence

Pre-change full baseline:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_nan_pre
```

Result: `172 passed`, `0 failed`, `0 skipped`.

Focused M3 remediation:

```powershell
python -m pytest -q tests\test_weight_runtime.py --basetemp .pytest_tmp_m3_nan_focus
```

Result: `35 passed`, `0 failed`, `0 skipped`.

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_nan_full
```

Result: `176 passed`, `0 failed`, `0 skipped`.

Legacy vs CORE_WRAPPER parity:

```powershell
python -m pytest -q tests\test_core_wrapper_parity.py --basetemp .pytest_tmp_m3_nan_parity
```

Result: `1 passed`, `0 failed`, `0 skipped`.

Productive legacy numerical deltas: none.

## Out Of Scope

The corrective pass did not start M4 and did not modify:

- `src/contracts/`;
- M2 Universe implementation;
- `src/reporter/`;
- significance runtime;
- Web/UI;
- SQLite/database behavior;
- Excel/VBA;
- NG;
- RM/Grid migration.
