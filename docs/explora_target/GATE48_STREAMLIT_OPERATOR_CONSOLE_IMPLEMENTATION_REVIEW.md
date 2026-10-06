# Gate 48 — Streamlit Operator Console Foundation

The combined questionnaire-order extension is documented in
[Operator Review Questionnaire Order Corrective](OPERATOR_REVIEW_QUESTIONNAIRE_ORDER_CORRECTIVE.md).
It changes presentation only and is ACCEPTED / MERGED through PR #26
(Human Review PASS; merge `083aa81260f88dc9dfc3acc6fd4cade0c1152058`).

## SAFE REVIEW PRESELECTION UX CORRECTIVE (2026-10-06)

Authoritative starting main: `4a03d0e703ded522b703a203dcfc77459f5de1e0`.
Branch: `fix/operator-review-safe-preselection`.
Status: ACCEPTED / MERGED as part of the combined corrective in PR #26. This is a UX
corrective, not a new analytical capability or a reopened milestone.

DETERMINISTIC UI PRESELECTION != HUMAN APPROVAL.

`review_editor_state(item)` suggests APPROVED only for persisted PENDING items
whose capability_status is QUALIFIED and final_type is RU, RM, LOOP_RU, or
LOOP_NUMERICO. Existing APPROVED and EXCLUDED decisions remain unchanged.
Configuration roles, unclassified items, grids, LOOP_RM, independent numeric
and scale items, and unqualified/unresolved capabilities receive no approval
suggestion. The helper only populates the editable dataframe and does not mutate
the stored EXPLORA_STRUCTURE_REVIEW_V1 or its authority.

A caption immediately above the editor explains that preselection is a review
aid and becomes human approval only after clicking Guardar revisión humana.
That action continues to pass current editor values through the existing
`finalize_structure_review(...)` path. Operators can override suggested states
and types before saving; no persisted authority type is added.

Both preparation buttons clear `structure_review_editor` widget state when
creating a fresh review from current source analysis. Ordinary reruns preserve
stored human decisions and in-progress editor changes. No source classification,
capability matrix, schema, authoring, B1/B2/B3, respondent-ID contract, formulas,
or canonical runtime changes are included.

Focused tests use generic synthetic source evidence and Streamlit AppTest to
exercise rendering, explicit save, persisted exclusions, editable suggestions,
and stale-editor reset through both preparation routes.

Corrective validation:

- Focused preselection tests: 65 passed, 0 failed, 0 skipped.
- Gate 48 regression: 21 passed, 0 failed, 0 skipped.
- Gate 50 regression: 35 passed, 0 failed, 0 skipped.
- Gate 51 regression: 46 passed, 0 failed, 0 skipped.
- Full repository regression: 1212 passed, 0 failed, 0 skipped (1326.21 seconds).
- Unexpected skips, numerical deltas, customer-specific hardcoding, and warnings: none.
- No customer data or customer-specific fixture is added to Git.
- Historical standalone validation preceded PR creation and merge. The combined
  corrective is now accepted through PR #26; post-merge evidence is recorded in
  [Operator Review Questionnaire Order Corrective](OPERATOR_REVIEW_QUESTIONNAIRE_ORDER_CORRECTIVE.md).

## CURRENT STATE

EXPLORA already had two Streamlit entry points before Gate 48:

- `app.py`: internal legacy Web Reporter workflow around SAV/Datamap/SQLite.
- `streamlit_app.py`: client-facing reporter that uploads a prepared SQLite database.

Those surfaces predate the accepted Project Spec → Execution Release → Generic Package Builder → CANONICAL_V1 architecture. They are preserved unchanged for compatibility.

Gate 49 is CLOSED / ACCEPTED / MERGED through PR #21 at official main
`fe5568e6420541debd01fc410c8cd057210faedf`. Gate 48 has been reconciled
with that accepted capability authority while preserving its feature history.
The reconciled Gate 48 feature is validated and pending Git adoption; it is not
yet accepted, merged or closed.

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


## Source Analysis V1.1

After first operator testing, Gate 48 V1 exposed no action when only SAV and
questionnaire were available. V1.1 adds `Analizar archivos cargados`.

The action uses the existing SPSS reader and a deterministic DOCX text extractor
to produce `EXPLORA_SOURCE_ANALYSIS_V1`. It records source fingerprints,
case/variable counts, variable labels, value-label presence, user-missing
metadata, exact lexical questionnaire evidence, conservative respondent-ID and
weight candidates, and RM naming-pattern candidates.

All suggested roles are explicitly `CANDIDATE_ONLY`. The analysis is
`SOURCE_EVIDENCE_ONLY` and does not become Project Spec authority. No
percentages, analytical bases, weighting, significance, or Canonical Results are
calculated. This closes the immediate UX gap without bypassing the future
Project Spec authoring/human-decision boundary.


## Source Analysis V1.2 — Real-project corrective

The first real source-analysis export exposed an important false-positive class:
numbered loop repetitions such as `P11.1`–`P31.4` were being grouped as RM
solely from their suffix. The SPSS labels contain explicit
`LoopLabel(Looptime)` evidence, so V1.2 separates these into
`LOOP_MEMBER_CANDIDATE` / loop groups and excludes them from RM candidates.

Variables using `_rN` notation are surfaced separately as
`GRID_ROW_CANDIDATE`. GRID remains outside the qualified profile. Gate 49 now
qualifies LOOP_RU and LOOP_NUMERICO, while LOOP_RM remains fail-closed.

The analyzer also records respondent-identity signals and uniqueness ratio even
when a likely identity field is not globally unique. None of these candidates
become Project Spec authority automatically.


## Structure Review V1.3

Gate 48 V1.3 adds an explicit human-review layer between Source Analysis and
Project Spec. The layer is generic and contains no customer/project IDs.

`build_structure_review` converts source-evidence candidates into review items
for RU, RM, NUMERIC, LOOP, GRID, respondent identity, weight and survey-control
metadata. Every item begins as `PENDING` with authority
`HUMAN_REVIEW_REQUIRED`.

The operator can approve, exclude or change the final type in Streamlit. The
saved review returns exactly one of:

- `NEEDS_HUMAN_DECISION`
- `CAPABILITY_GAP`
- `READY_FOR_PROJECT_SPEC_DRAFT`

The accepted post-Gate49 capability matrix is explicit: RU, RM, LOOP_RU and
LOOP_NUMERICO are qualified. LOOP_RM, GRID_ESCALA, GRID_RM, SCALE and standalone
NUMERIC remain fail-closed. Loop significance is also fail-closed pending a
dedicated B2 family contract. Approving an unsupported structure does not
silently execute it; it produces `CAPABILITY_GAP`. Qualified loop structures do
not produce a false capability gap.

Structure Review is a human-reviewed configuration artifact, not a Project Spec
and not a statistical result.

## Post-Gate49 Reconciliation

The console consumes the Gate 49 capability decision only as structure-review
metadata. It does not calculate statistics, approve review items, generate a
Project Spec, or create a parallel execution path. Every proposed structure
still begins `PENDING`; only an explicit human decision can approve or exclude
it. Web and Excel continue consuming Canonical Results through the accepted
runtime and package boundaries.

The capability matrix records the authority for each family. LOOP_RU and
LOOP_NUMERICO cite Gate 49; LOOP_RM and loop significance remain explicitly
fail-closed. No customer-specific logic or raw customer data was introduced.

Post-reconciliation validation:

- Gate 48 focused: 21 passed, 0 failed, 0 skipped.
- Gate 49 focused: 21 passed, 0 failed, 0 skipped.
- Gate 47 released package builder: 66 passed, 0 failed, 0 skipped.
- Full repository regression: 1066 passed, 0 failed, 0 skipped.

No unexpected numerical deltas were observed.
