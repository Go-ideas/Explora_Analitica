# EXPLORA — M2 UNIVERSE EXECUTION

**Milestone:** M2 — Universe Execution
**Date:** 2026-09-14
**Status:** PASS
**Default runtime mode:** `LEGACY`

## Scope

M2 adds an internal Universe evaluator for the frozen Universe V1 AST. It does
not migrate Web, SQLite, Excel, NG, runtime weights, runtime significance or
RM/Grid authority.

## Implementation Location

Universe execution lives in:

`explora_web_reporter/src/analytics_core/universe.py`

The evaluator is intentionally internal to Analytics Core. It is not wired into
the production Streamlit reporter path.

## Evaluation Context

`UniverseEvaluationContext` is explicit and conceptual. It exposes:

- respondent IDs;
- field values;
- response state;
- selection state;
- applicability state;
- explicit Universe registry;
- explicit scope-to-UniverseRef bindings;
- traceability.

The Universe AST does not access Pandas, SQLite, UI, Web renderers, Excel or
legacy reporter heuristics. DataFrame-backed adapters can be added later without
changing the contract.

## UniverseRef

`universe_ref` requires:

- structured `UniverseRef`;
- exact `universe_id`;
- explicit registry;
- existing `UniverseSpec`;
- `RELEASED` state for runtime authority;
- no fuzzy matching;
- no label/name lookup.

Direct and indirect cycles fail with structured evaluation status.

## Response Semantics

`selected`, `not_selected`, `answered` and `not_answered` use explicit
`ResponseState`.

`not_selected` is not implemented as simple `not selected`. It requires:

`applicable == True AND category explicitly_not_selected`

Missing selection evidence, unknown applicability or absent response state is
`UNSUPPORTED`. `missing` and `not applicable` never become `not_selected`.

`not_answered` means no valid answer in an explicitly applicable context.
Out-of-universe respondents do not become `not_answered`.

## Scope Semantics

M2 does not invent universal scope composition. The evaluator executes only an
explicit `scope_universe_refs` binding or an explicit Universe expression that
composes refs. If a scope has no composition rule, the result is `UNSUPPORTED`.

Supported scope labels for explicit binding are:

- project;
- question;
- row/entity;
- column;
- cell.

## Result

`UniverseEvaluationResult` is renderer-neutral and includes:

- Universe ref;
- Universe Spec version;
- evaluator/rules version;
- respondent mask;
- input N;
- eligible N;
- excluded N;
- status;
- reasons/warnings;
- QA envelope;
- traceability.

No weighted fields are included. Zero eligible respondents is valid when the
Universe executes successfully.

## Tests

M2 adds 19 Universe tests and expands renderer-neutral coverage. The suite now
contains 129 passing tests.

Covered:

- boolean/comparison operators;
- zero eligible valid result;
- missing field vs missing value;
- renderer-neutral result shape;
- `not_selected` with applicable true;
- `not_selected` with applicable false;
- `not_selected` with applicability unknown;
- `not_answered` in-scope;
- `not_answered` out-of-universe;
- unknown selection state unsupported;
- unknown UniverseRef;
- non-RELEASED UniverseRef;
- direct cycle;
- indirect cycle;
- exact registry ID resolution;
- scope without composition no inference;
- explicit scope ref execution;
- weights do not alter Universe result.
- legacy/canonical Universe comparison classification without forcing match.

## Test Result

```powershell
python -m pytest -q --basetemp .pytest_tmp_m2_full_final
```

Result:

- PASS: 129
- FAIL: 0
- SKIP: 0

## Guardrails Confirmed

- `LEGACY` remains default.
- No production UI change.
- No SQLite change.
- No dependency change.
- No runtime weight behavior change.
- No runtime significance behavior change.
- No RM/Grid migration.
- No Excel or NG work.
- M3 is not started.
