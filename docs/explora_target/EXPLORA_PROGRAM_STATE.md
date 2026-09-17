# EXPLORA PROGRAM STATE

Date: 2026-09-17
Repository: Go-ideas/Explora_Analitica
Authoritative main: `0fe9caf1f7d9b942035403b28a89672eb92baf37`
Documentation working branch: `docs/m7-excel-renderer-contract`

## Current Accepted State

This is the current program-state index, reconciled under Gate 33 authorization.
It supersedes this index's T0-era operational status, not historical gate evidence.
Human authorization accepts M2-M6 and Gates 27, 30, 19 and 32. No frozen
methodological/analytical contract is reopened by this documentation update.

| Milestone / gate | Current state |
| --- | --- |
| T0 repository adoption | CLOSED / ACCEPTED, merged through PR #1 |
| M2 Universe | CLOSED / ACCEPTED |
| M3 Weight Hardening | CLOSED / ACCEPTED |
| M4 Structure and Mention Identity | CLOSED / ACCEPTED |
| M5 Canonical Results | CLOSED / ACCEPTED |
| M5 Execution Adapter | CLOSED / ACCEPTED |
| M6 Web Canonical migration | CLOSED / ACCEPTED |
| Gate 27 M4 post-merge validation | CLOSED |
| Gate 30 Canonical Materialization | CLOSED / ACCEPTED; implementation FOUND in src/canonical_materialization |
| Gate 19 Productive DUAL_RUN | CLOSED / ACCEPTED; Benchmark A 94/94 exact parity |
| Gate 32 Canonical Default Switch | CLOSED / ACCEPTED, PR #5 merged and post-merge validated |
| Gate 33 M7 entry | PASS / AUTHORIZED; M7A current-state/contract phase only |
| M7A Current State | PASS / HUMAN REVIEW ACCEPTED |
| M7A Contract | FROZEN FOR GIT REVIEW, effective upon successful documentation-closure validation and commit |
| M7B Renderer implementation | NOT AUTHORIZED |
| M7C Master/VBA | NOT AUTHORIZED |
| M7D Productive release | NOT AUTHORIZED |

## Accepted Merge History

Verified first-parent main history:
- PR #1 adoption: `8d7781d` (abbreviated repository SHA).
- PR #2 mention identity: `c2dc54e74931993dc50493ebba0b77a92e855479`.
- PR #3 materialization: `e465457d7e6e23d13bea8d43955c1a84790f5d65`.
- PR #4 Gate 19 correction: `6c0bf08895603b2b80b6a3c5fb5e1fea744b9d30`.
- PR #5 Gate 32 switch: `0fe9caf1f7d9b942035403b28a89672eb92baf37`.

PR #5 parents are exactly pre-merge main
`6c0bf08895603b2b80b6a3c5fb5e1fea744b9d30` and accepted feature
`011a5778a3aeeaa5492be050fbae4972633363d1`, in that order.

## Current Runtime And Evidence

Authoritative resolver: explora_web_reporter/src/analytics_core/mode.py.
Absent explicit selector and absent EXPLORA_ANALYTICS_ENGINE -> CANONICAL_V1.
Explicit CANONICAL/CANONICAL_V1, LEGACY and DUAL_RUN remain supported; explicit
request selection wins over environment. Invalid selection fails closed.
Canonical failure never silently executes Legacy. Legacy compatibility/rollback
is available through explicit selection. Existing saved explicit selections stay
explicit. Default runtime = CANONICAL_V1; Legacy rollback = AVAILABLE / EXPLICIT.
Historical package metadata default_execution_mode=LEGACY is not the
live runtime default and remains unchanged.

Gate 32 post-merge validation on authoritative main: PASS. Default/explicit
Canonical results, fingerprints and request snapshots EXACT. Benchmark A BA-01
through BA-05 PASS. BA-03: MENTION / PARENT_RM /
STR_Q_DELIVERY_APPS_RM_V1. Gate 19 comparison scope: 94 comparable, 94/94 exact.
Focused switch 26/0/0; Gate 19 38/0/0; materialization 51/0/0; full 602/0/0
(passed/failed/skipped). No unexpected skips, numerical/structural/unexplained
deltas or silent fallback; determinism PASS and provenance COMPLETE.
Post-merge worktree clean; no source/contracts/statistical changes during validation.

External Gate 32 post-merge evidence:
`C:/Users/conta/gate32_temp/post_merge/{focused.xml,full.xml,benchmark_evidence.json}`.
Accepted physical Benchmark source/package remain outside Git; no client data
was imported as part of this state reconciliation.

## M7 Entry And Current Work

M7 = Excel Renderer, independent of Web over the same CanonicalResults. Core
owns all official numbers, bases, weights, structure/mention scope, significance,
warnings and QA decisions. Excel/VBA are presentation/interaction only.
M7 STARTED = YES, M7A contract/current-state phase ONLY.

M7A artifacts:
- [Current state](M7_EXCEL_RENDERER_CURRENT_STATE.md).
- [Contract draft](M7_EXCEL_RENDERER_CONTRACT_DRAFT.md).
- [Scope manifest](M7_EXCEL_RENDERER_SCOPE_MANIFEST.md).

MASTER XLSM = NOT FOUND in the inspected repository/surrounding workspace.
VISUAL SPEC RUNTIME CONTRACT = GAP. Macro/control-preserving template backend,
numeric exactness profile, canonical workbook mapping and optional significance
letter-token input require review before their implementation phases.
No Master, renderer code or productive VBA has been built. No M7B/M7C/M7D
automatic entry, push, PR or merge is authorized by Gate 33.

M7A untouched-code baseline rerun: export focused 15/0/0, canonical contract /
transport focused 41/0/0, Gate 32 focused 26/0/0, full 602/0/0. External JUnit:
`C:/Users/conta/m7a_temp/{focused.xml,full.xml}`. Only the four authorized current
documentation files changed; historical milestone/gate documents remain immutable.
Human M7A current-state review PASS; contract review PASS WITH REQUIRED CLOSURE.
The closure handoff freezes M7-01 through M7-10 authority/safety requirements and
authorizes one documentation-only commit. Upon successful commit M7A CONTRACT =
FROZEN FOR GIT REVIEW; field-level mappings/storage schemas remain DEFINED / DRAFT.
Master is NOT FOUND, Visual Spec runtime remains GAP and exact backend NOT FROZEN.
Literal/formula safety, preservation fail-closed, significance unsupported-letter
boundary, canonical vs display value and Benchmark plus generic fixture policy
are frozen requirements, not implemented behavior. M7B remains NOT AUTHORIZED
until separate Visual Spec acceptance and explicit implementation authorization.
Closure regression evidence: C:/Users/conta/m7a_temp/closure/{focused.xml,full.xml}.
No push/PR/merge permitted. Next destination: CORE / HUMAN REVIEW, M7A Git Review.

## Historical Evidence

Historical adoption/reproducibility findings remain unchanged in
[T0 baseline verification](T0_BASELINE_VERIFICATION.md),
[T0 repository adoption](T0_REPOSITORY_ADOPTION.md) and
[T0 inventory](T0_AS_IS_INVENTORY.md). These record dated T0 observations,
not the current runtime, implementation inventory or merge policy.
The current accepted state is the table above; do not apply historical blocked
or Legacy-default statements as current instructions.
