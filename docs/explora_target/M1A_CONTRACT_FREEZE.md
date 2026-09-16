# EXPLORA — M1A-F CONTRACT FREEZE

**Milestone:** M1A-F — Contract Freeze & Version Control Checkpoint
**Date:** 2026-09-14
**Status:** PASS — M2 not authorized

## Frozen Scope

M1A-F freezes the M0.1/M1A contract and Analytics Core boundary surface only.
It does not implement Universe execution, canonical runtime weights, Holm
execution, Canonical Result persistence, Web migration, SQLite changes, NG
changes, Excel, VBA or OpenAI API work.

## Frozen Vocabularies

Shared vocabularies live in `explora_web_reporter/src/contracts/vocabulary.py`.

- `ReleaseLifecycle`: `PROPOSED`, `REVIEW_REQUIRED`, `APPROVED`, `REJECTED`, `RELEASED`.
- `ReleaseMode`: `AUTO`, `REVIEW`, `MANUAL`.
- `ExecutionMode`: `LEGACY`, `CORE_WRAPPER`.
- `QAIssueLifecycle`: `OPEN`, `RESOLVED`, `WAIVED`.
- `QAIssueState`: `PASS`, `WARN`, `FAIL`.
- `StatisticalQAState`: `PASS`, `WARN`, `INELIGIBLE`, `UNSUPPORTED`, `FAIL`.
- `StatisticalState`: `SIGNIFICANT`, `NOT_SIGNIFICANT`, `INELIGIBLE`, `UNSUPPORTED`, `NOT_TESTED`, `FAIL`.
- `AggregateReleaseState`: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, `REVIEW_REQUIRED`.
- `SampleRelationship`: `INDEPENDENT`, `PAIRED`, `REPEATED`, `PANEL`, `UNKNOWN`.
- `CanonicalBaseMeasure`: `unweighted_n`, `weighted_n_raw`, `weighted_n`, `effective_n`.

`APPROVED` remains distinct from `RELEASED`; only `RELEASED` Specs may cross
the future canonical execution boundary.

## Frozen Contract Semantics

Contracts live in `explora_web_reporter/src/contracts/models.py`.

- `ReleaseMetadata` carries B3 release state, mode, policy/version/hash and audit fields.
- `UniverseExpression`, `UniverseRef`, and `UniverseSpec` freeze the V1 AST shell.
- `WeightSpec` represents B1 only as contract authority; it does not alter legacy weighting.
- `MetricSpec` keeps denominator policy/reference separate from Canonical Result numeric denominators.
- `SignificanceSpec` represents B2 configuration and traceability only; it does not execute Holm or rewrite legacy z/Welch.
- `SignificanceComparison` preserves stable pairwise relation fields for future Canonical Results.
- `QAIssue` and `QAEnvelope` keep issue lifecycle, issue/domain state and aggregate release state separate.
- `CanonicalResult` is a renderer-neutral skeleton and is not populated from `ReportResult`.

## Universe AST Freeze

The V1 operator registry is frozen to:

`true`, `false`, `and`, `or`, `not`, `eq`, `neq`, `in`, `not_in`, `gt`,
`gte`, `lt`, `lte`, `is_missing`, `not_missing`, `selected`,
`not_selected`, `answered`, `not_answered`, `universe_ref`.

`contains_selected` and arbitrary Python/SQL operators are rejected. `universe_ref`
requires a structured `UniverseRef`, not free-form text.

## Validator Freeze

Validators live in `explora_web_reporter/src/contracts/validators.py` and cover:

- B3 release guard: only `RELEASED` specs pass.
- Project, Question and Structure identity fields.
- B1 Weight policy constraints and project-default uniqueness.
- Weight override rejection for unknown, ambiguous and out-of-scope overrides.
- Universe operator arity, operand types, refs and circular references.
- Metric denominator policy presence.
- B2 Significance confidence, alpha, sidedness, base rule, Holm, Total exclusion, sample relationship and weighted-inference guard.
- Canonical Result run identity and renderer-neutral base/value record sanity.

## Core Boundary Freeze

Analytics Core boundary lives in `explora_web_reporter/src/analytics_core/`.

- `interface.py`: `AnalyticsRequest` and `AnalyticsCore` protocol.
- `mode.py`: strict `EXPLORA_ANALYTICS_ENGINE` resolution.
- `legacy_adapter.py`: delegates to existing `src.reporter.tabulator.generate_report`.
- `runner.py`: resolves `LEGACY` or `CORE_WRAPPER` and delegates through `LegacyAdapter`.

Default mode is `LEGACY`. Invalid execution mode raises an explicit error and
is never silently coerced to legacy.

## Renderer Neutrality

`src/contracts/`, `analytics_core/interface.py`, `analytics_core/mode.py` and
`analytics_core/runner.py` do not import Streamlit, Plotly, Excel/openpyxl,
VBA, UI modules or export modules. The only Analytics Core module allowed to
import legacy reporter code is `legacy_adapter.py`.

## Tests Added Or Expanded

M1A-F expands the contract/core test set from 33 to 45 tests.

Added freeze coverage:

- QA vocabularies are distinct and non-interchangeable.
- `SampleRelationship.REPEATED` is explicitly represented.
- Canonical base names are frozen.
- Universe malformed arity and operand types fail.
- `universe_ref` must be structured.
- Weight missing-to-one is not a canonical policy.
- Weight override unknown/ambiguous/out-of-scope failures.
- Significance alpha, Total exclusion and traceability defaults.
- Metric denominator policy/reference remains distinct from result denominator.
- `CanonicalResult` is not `ReportResult`.
- Renderer-neutral static import checks.

## Test Result

Full suite command:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m1af_full
```

Result:

- PASS: 110
- FAIL: 0
- SKIP: 0

Parity command:

```powershell
python -m pytest -q tests/test_core_wrapper_parity.py --basetemp .pytest_tmp_m1af_parity
```

Result:

- PASS: 1
- FAIL: 0
- SKIP: 0

Numerical deltas: none detected.

## Version-Control Checkpoint

No Git repository was found in the workspace or parent directories. A hash-based
checkpoint manifest/archive is therefore used instead of a Git commit. No Git
repository was initialized.

Generated caches, pytest temp directories, local environment files, client
datasets and SQLite outputs are excluded from the checkpoint.

## Deferred Extensions

Deferred to later authorized milestones only:

- M2 executable Universe.
- M3 B1 canonical runtime weighting.
- M4 released Structure Spec authority for RM/Grid/Loop.
- M5 Canonical Result persistence and B2 significance relations execution.
- M6 Web migration.
- M7 Excel renderer.

M2 remains **not ready** from this checkpoint alone.
