# M5 Canonical Execution Adapter Implementation

Status: PASS / IMPLEMENTED / CORRECTIVE REMEDIATED

Contract: M5 Canonical Execution Adapter Contract

Implemented source:

- `explora_web_reporter/src/analytics_core/execution_adapter.py`

Implemented public interface:

- `execute_canonical_request(...) -> CanonicalResult`

Corrective remediation closed:

- `B-M5A-IMPL-01` authoritative slice / fail-closed gap.
- `B-M5A-IMPL-02` provenance / upstream traceability completeness.
- `B-M5A-TEST-01` required negative coverage.

The adapter bridges authoritative upstream Core outputs into existing M5 result authority:

`M2 UniverseEvaluationResult + M3 WeightEvaluationResult when required + M4 StructureExecutionResult + RELEASED Request/MetricSpec -> M5 helpers -> CanonicalResult`

The adapter does not consume raw SAV, raw Web state, Legacy results, pandas frames, or display labels as analytical authority.

## Supported Paths

- RU `COUNT`
- RU `PROPORTION`
- RM `RM_RESPONDENT_PROPORTION`
- RM `RM_MENTION_PROPORTION`
- Filtered slices supplied by authoritative M2 slice masks
- Banner slices supplied as distinct authoritative slice masks
- Unweighted execution

Released formula aliases are mapped to existing M5 Formula Registry IDs:

- `count/v1 -> COUNT`
- `proportion/v1 -> PROPORTION`
- `rm_respondent_proportion/v1 -> RM_RESPONDENT_PROPORTION`
- `rm_mention_proportion/v1 -> RM_MENTION_PROPORTION`

No new formula definitions were created.

## Boundaries

- M2 remains Universe authority.
- M3 remains Weight authority.
- M4 remains Structure and denominator authority.
- M5 remains Formula and CanonicalResult authority.
- B2 significance tests are not implemented here.
- Legacy fallback is prohibited and not imported.
- Web calculations are prohibited and not imported.

## Corrective Hardening

- The adapter no longer synthesizes a Total slice when `ctx.slices == ()`.
- Explicit Total execution now requires an authoritative Total slice and request `execution_options["slice_authority"] == "explicit_total"`.
- Filtered and banner requests fail closed when authoritative slice identity is missing.
- `question_id`, `structure_ref`, `runtime_fingerprint`, `request_id`, `request_fingerprint`, `metric_ref`, `formula_ref`, and `universe_ref` are mandatory.
- M4 upstream ledger identity is preserved in base/value provenance.
- QA refs are propagated consistently across RU, RM respondent, and RM mention paths.
- Weighted requests require M3 result, active weight, and M3 QA reference.

## Test Evidence

- Focused adapter tests: `44 passed`
- M2 regression: `38 passed`
- M3 regression: `45 passed`
- M4 regression: `61 passed`
- M5 regression: `124 passed`
- M6 regression: `97 passed`
- Legacy parity: `3 passed`
- Full regression: `450 passed`

All tests were run with `PYTHONPATH=.` and local pytest basetemp directories.

## Source Audit

Created:

- `explora_web_reporter/src/analytics_core/execution_adapter.py`
- `explora_web_reporter/tests/test_m5_execution_adapter.py`

No protected M2, M3, M4, M5 numerical, M6, Web, Legacy, reporter, or contracts files were modified.

## Warnings

The initial bare `pytest -q` invocation failed collection because `src` was not on `PYTHONPATH`. The operational regression command used `PYTHONPATH=.`.

The default pytest temp root at `C:\Users\conta\AppData\Local\Temp\pytest-of-conta` produced a permission error for two setup fixtures. Using local `--basetemp` resolved the environment issue.

Gate 19 remains blocked until the separate canonical materialization layer resumes and productively executes Benchmark A.
