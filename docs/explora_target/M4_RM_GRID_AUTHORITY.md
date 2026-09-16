# EXPLORA - M4 RM / GRID AUTHORITY

**Milestone:** M4 - RM / GRID AUTHORITY
**Date:** 2026-09-14
**Authority:** `M4_RM_GRID_AUTHORITY_IMPLEMENTATION_CONTRACT.md`
**Default runtime mode:** `LEGACY` / `legacy_inference`

## Scope

M4 adds an isolated Analytics Core runtime for RELEASED StructureSpec authority.
It supports RU, RM, GRID_ESCALA, GRID_RM, LOOP_RM, LOOP_RU and LOOP_NUMERICO.

M4 does not migrate Web, SQLite, Excel, NG, reporter calculations,
significance, weights, or productive legacy tabulation behavior.

## Runtime Location

Structure execution lives in:

`explora_web_reporter/src/analytics_core/structure.py`

The module is renderer-neutral and does not import Streamlit, Plotly, Excel,
SQLite, Pandas, reporter utilities, weights, or the significance engine.

## Contract Additions

M4 adds StructureSpec supporting types to:

- `explora_web_reporter/src/contracts/vocabulary.py`
- `explora_web_reporter/src/contracts/models.py`
- `explora_web_reporter/src/contracts/validators.py`
- `explora_web_reporter/src/contracts/__init__.py`

The additions are backward-compatible. Existing StructureSpec construction is
unchanged. M4 executable validation is explicit through `enforce_m4=True`.

## Authority

Canonical structure execution is available only in `released_spec` authority
mode. Default remains `legacy_inference`, which returns REVIEW_REQUIRED and
does not perform canonical M4 execution.

Runtime authority requires:

- RELEASED ProjectSpec;
- RELEASED QuestionSpec;
- RELEASED StructureSpec;
- explicit physical variable bindings;
- explicit question-level M2 UniverseRef;
- explicit row/column/cell/loop applicability composition when such scopes are
  used;
- no runtime detector override over RELEASED Specs.

Detector evidence can produce a warning, but cannot rewrite the RELEASED
StructureSpec.

## M2 Integration

M4 consumes `UniverseEvaluationResult.respondent_mask` as immutable input.

M4 does not modify:

- Universe refs;
- Universe masks;
- `eligible_n`;
- `excluded_n`;
- zero-eligible semantics;
- M2 FAIL / UNSUPPORTED behavior.

Missing M2 results, M2 FAIL, or M2 UNSUPPORTED are returned as structured
M4 failures or review-required results. M4 does not repair Universe execution.

## M3 Integration

M4 does not consume or transform weights. Weight values in the execution
context do not alter Structure records or denominator ledgers.

M4 produces unweighted structural records and denominator ledgers only.
Weighted structural percentages and weighted significance remain outside M4.

## Structural Zero and Missing

Structural zero is produced only from explicit not-selected values in an
applicable context. Missing values are ordinary missing or explicit
not_answered according to released completion policy.

Out-of-universe records are structural missing, not not_selected and not
not_answered.

## Denominators

M4 produces renderer-neutral denominator ledgers.

Supported V1 denominator units:

- respondent;
- respondent-option;
- mention;
- instance.

Zero denominators are represented as `VALID_ZERO_BASE` unless there is an
independent contract/runtime failure.

## Duplicates and Exclusivity

Duplicate policy is explicit:

- `keep`;
- `deduplicate_by_category`;
- `error`.

Exclusive option conflicts block canonical execution without deleting records.

## Loops

Supported loop types:

- LOOP_RM;
- LOOP_RU;
- LOOP_NUMERICO.

Loop execution requires explicit loop instance identity. LOOP_RANGO is not
implemented in M4 V1.

Repeated dependency is surfaced in denominator ledger QA/traceability; it does
not call significance and does not infer a statistical correction.

## Legacy Comparison

Legacy-vs-canonical comparison is isolated and classified as:

- `PARITY`;
- `INTENDED_CORRECTION`;
- `POTENTIAL_REGRESSION`;
- `UNSUPPORTED`;
- `REVIEW_REQUIRED`.

Canonical behavior is not altered to match legacy.

## Tests

M4 adds 40 focused tests.

Covered:

- StructureSpec authority extensions;
- RELEASED-only runtime authority;
- default legacy mode;
- RM selected/not_selected semantics;
- not_selected with applicable false;
- not_answered only inside question universe;
- missing field vs missing value;
- valid zero eligible / zero base;
- invalid out-of-domain values;
- M2 FAIL / UNSUPPORTED propagation;
- M2 mask immutability;
- weight-value invariance;
- duplicate policies;
- exclusive option conflicts;
- RU category mapping;
- GRID scope composition gap;
- GRID_RM row/column/cell Universe consumption;
- GRID_ESCALA category mapping;
- LOOP_RM repeated dependency;
- LOOP_RU;
- LOOP_NUMERICO;
- LOOP_RANGO rejection;
- detector disagreement warning without override;
- renderer-neutral import guard;
- legacy parity and declared methodological correction.

## Test Result

Pre-change baseline:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_baseline
```

Result:

- PASS: 176
- FAIL: 0
- SKIP: 0

Focused M4:

```powershell
python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_rm_grid_legacy_parity.py
```

Result:

- PASS: 40
- FAIL: 0
- SKIP: 0

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_final
```

Result:

- PASS: 216
- FAIL: 0
- SKIP: 0

Legacy parity:

```powershell
python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_parity
```

Result:

- PASS: 2
- FAIL: 0
- SKIP: 0

## Guardrails

- `LEGACY` remains default.
- M2 files were not modified.
- M3 files were not modified.
- Reporter tabulation/calculations/filters/banners/significance were not
  modified.
- Web/UI was not modified.
- SQLite/persistence was not modified.
- Excel/VBA was not modified.
- NG was not modified.
- RM/Grid legacy builders and detectors were not modified.
- M5 was not started.

## Known Limitations

M4 provides the canonical StructureSpec authority runtime and test harness. It
does not wire canonical structure execution into productive Web/reporting
flows, persistence, Excel export, or significance. Those remain deferred to
later authorized milestones.
