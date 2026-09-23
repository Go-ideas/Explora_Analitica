# Gate 48 — Streamlit Operator Console Foundation

## CURRENT STATE

EXPLORA already had two Streamlit entry points before Gate 48:

- `app.py`: internal legacy Web Reporter workflow around SAV/Datamap/SQLite.
- `streamlit_app.py`: client-facing reporter that uploads a prepared SQLite database.

Those surfaces predate the accepted Project Spec → Execution Release → Generic Package Builder → CANONICAL_V1 architecture. They are preserved unchanged for compatibility.

Gate 47 is CLOSED / ACCEPTED / MERGED through PR #20 at official main
`8cc7a0c7ea17e29c96dfcbbfee278690c3d0eba2`.

## TARGET STATE

Add a separate operational console for the canonical flow without making Streamlit a statistical authority.

New entry point:

`explora_web_reporter/operator_console.py`

Deployable in Streamlit Community Cloud by selecting that file as the main app.

## GAP

Before Gate 48 there was no UI that could:

1. accept a real SAV source artifact;
2. validate `EXPLORA_PROJECT_SPEC_V1`;
3. surface human/AI decisions;
4. apply an explicit B3 human release decision;
5. validate `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`;
6. build the deterministic ten-file RELEASED package;
7. execute the accepted Generic Productive Runtime;
8. expose QA/provenance outputs for download.

The existing Streamlit reporter cannot be used as authority for canonical calculations because it contains historical reporter/tabulation behavior.

## DECISION

Create an additive Operator Console instead of rewriting `app.py` or
`streamlit_app.py`.

The console is orchestration/presentation only. Official statistics remain owned by
EXPLORA Core / CANONICAL_V1.

Raw customer uploads are written only to an ephemeral per-session workspace under
the operating-system temp directory. They are never added to Git by console code.

Gate 48 V1 executes WEB-only productive intents. If the Project Spec contains an
EXCEL output, execution fails closed with a QualifiedMaster integration message.
This prevents creation of an alternate Excel path outside M7.

Questionnaire and datamap uploads are evidence-only in Gate 48 V1. The console
does not claim to generate Project Spec automatically because no accepted
questionnaire/datamap → Project Spec authoring engine exists yet.

## IMPLEMENTATION

Added:

- `src/operator_console/service.py`
- `src/operator_console/__init__.py`
- `operator_console.py`
- `tests/test_gate48_operator_console.py`

The service delegates to accepted contracts/functions:

- `validate_project`
- `validate_execution_release`
- `build_released_package`
- `run_generic_productive`

B3 approval modifies only the release-decision envelope in the session copy of
Execution Release configuration. Analytical configuration is never auto-approved
or rewritten.

## VALIDATION TARGET

Focused Gate 48 controls cover:

- session-local uploads;
- SHA-256 capture;
- filename sanitization;
- explicit B3 approval;
- no mutation of analytical release fields during B3 approval;
- WEB/EXCEL intent detection;
- fail-closed Excel execution in Console V1;
- package requirement before execution;
- WEB readiness.

Full repository regression remains required before merge.

## DEPLOYMENT

Streamlit Community Cloud configuration:

Repository:
`Go-ideas/Explora_Analitica`

Branch during review:
`feature/gate48-streamlit-operator-console`

Main file:
`explora_web_reporter/operator_console.py`

Dependencies:
`explora_web_reporter/requirements.txt`

Do not point the Operator Console deployment at `app.py` or
`streamlit_app.py`; those are separate historical/reporting surfaces.
