# EXPLORA - M2 UNIVERSE EXECUTION REMEDIATION

**Milestone:** M2 - Universe Execution
**Date:** 2026-09-14
**Corrective scope:** B-M2-01, B-M2-02, B-M2-03 only
**Gate status:** ready to return to Human Implementation Gate
**Default runtime mode:** `LEGACY`

## Pre-Change Baseline

```powershell
python -m pytest -q --basetemp .pytest_tmp_m2_corrective_pre
```

Result:

- PASS: 129
- FAIL: 0
- SKIP: 0

## B-M2-01 - Unstructured Type Failure

Root cause:

`src/analytics_core/universe.py` used direct Python comparison and membership
operators for `eq`, `neq`, `in`, `not_in`, `gt`, `gte`, `lt` and `lte`. Some
invalid operand combinations could leak raw Python exceptions, while equality
and membership could silently return boolean results for incompatible domains.

Code change:

- Added explicit comparison-domain validation before comparison execution.
- Added controlled `UniverseEvaluationError` translation for invalid comparison
  execution.
- Preserved no-coercion semantics for values such as `"18"` and `18`.
- Structured failures preserve status, reasons, QA and traceability through the
  existing `UniverseEvaluationResult` path.

Tests:

- `"18" gte 18`
- `"18" gt 18`
- `"18" lt 18`
- `"18" lte 18`
- incompatible `eq`, `neq`, `in`, `not_in`
- valid typed comparisons for the same operator family

Result:

Structured `FAIL`; no raw `TypeError`, no silent coercion and no plain `False`
for incompatible operand types.

## B-M2-02 - Scope Vocabulary Leakage

Root cause:

`evaluate_scope()` resolved `scope_universe_refs[scope]` before checking the
frozen V1 scope vocabulary. An explicit binding for an unknown scope such as
`foo` could execute.

Code change:

- Added `SUPPORTED_SCOPE_IDS_V1`.
- Validated scope identifier before explicit binding lookup.
- Preserved exact identifiers without aliases, fuzzy matching or case
  normalization.

Frozen V1 scope identifiers:

- `project`
- `question`
- `row/entity`
- `column`
- `cell`

Tests:

- valid `project` scope executes with explicit binding;
- valid `question` scope executes with explicit binding;
- valid `row/entity` scope executes with explicit binding;
- valid `column` scope executes with explicit binding;
- valid `cell` scope executes with explicit binding;
- unknown `foo` scope does not execute even when an explicit binding exists.

Result:

Unknown/non-V1 scopes return structured `UNSUPPORTED` before `UniverseRef`
resolution.

## B-M2-03 - Silent Reference Coercion

Root cause:

M2 runtime evaluation used `str(...)` for variable, question and category refs.
Invalid refs such as `123` could become `"123"` and match context keys.

Code change:

- Added strict runtime reference validation for:
  - field / variable refs;
  - question refs;
  - category refs;
  - `UniverseRef.universe_id`.
- Rejected non-string or blank refs through the structured evaluation result
  path.
- Kept structured `UniverseRef` requirement unchanged.

Tests:

- numeric variable ref `123` with context key `"123"` fails;
- numeric question ref fails;
- numeric category ref fails;
- correctly typed exact string refs continue to execute.

Result:

No silent `str(...)` reference coercion remains in the M2 Universe execution
path.

## Operator Runtime Coverage

Runtime tests now directly cover the full V1 Universe operator set:

- `true`
- `false`
- `and`
- `or`
- `not`
- `eq`
- `neq`
- `in`
- `not_in`
- `gt`
- `gte`
- `lt`
- `lte`
- `is_missing`
- `not_missing`
- `selected`
- `not_selected`
- `answered`
- `not_answered`
- `universe_ref`

Unknown operators reaching the evaluator boundary return a structured `FAIL`.

## ResponseState Warning

Non-blocking hardening was added locally in M2 execution:

- if the same category is present in `selected_categories` and
  `explicitly_not_selected_categories`, evaluation returns a structured `FAIL`.

No `ResponseState` redesign and no frozen contract changes were made.

## Regression Preservation

Preserved:

- `not_selected = applicable == True AND explicitly_not_selected`;
- `applicable=False -> not_selected=False`;
- unknown applicability -> `UNSUPPORTED`;
- missing is not `not_selected`;
- out-of-scope is not `not_answered`;
- zero eligible can be a valid `PASS`;
- weights do not affect Universe eligibility.

## Test Evidence

Focused M2 corrective suite:

```powershell
python -m pytest -q tests\test_universe_evaluator.py tests\test_universe_evaluator_refs.py tests\test_universe_evaluator_scopes.py tests\test_universe_evaluator_response_states.py tests\test_universe_evaluator_corrective.py tests\test_contract_renderer_neutrality.py --basetemp .pytest_tmp_m2_corrective_focus
```

Result:

- PASS: 33
- FAIL: 0
- SKIP: 0

Full suite:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m2_corrective_full
```

Result:

- PASS: 141
- FAIL: 0
- SKIP: 0

Legacy vs CORE_WRAPPER parity:

```powershell
python -m pytest -q tests\test_core_wrapper_parity.py --basetemp .pytest_tmp_m2_corrective_parity
```

Result:

- PASS: 1
- FAIL: 0
- SKIP: 0
- Numerical deltas: none

## Guardrails

No changes were made to:

- `src/contracts/models.py`;
- runtime weights;
- runtime significance;
- RM/Grid migration;
- Web migration;
- UI;
- SQLite/database behavior;
- Excel;
- VBA;
- NG;
- productive legacy reporter behavior.

Protected legacy files were not modified:

- `src/reporter/tabulator.py`
- `src/reporter/calculations.py`
- `src/reporter/significance.py`
- `src/reporter/filters.py`
- `src/reporter/banners.py`
- `src/reporter/multi_metrics.py`

## Open Warnings

- No Git repository is present in this workspace or parent directories, so
  checkpoint identity is represented by SHA-256 manifests and archive hashes.
- The corrective pass should return to the Human Implementation Gate. Test
  success alone is not claimed as final M2 gate approval.

## Out Of Scope Confirmed

M3 was not started.
