# EXPLORA PROGRAM STATE

Date: 2026-09-17
Repository: Go-ideas/Explora_Analitica
Authoritative main: `8c2a61d9b921c9cc26c28b5afd33541aabc5976c`
Documentation working branch: `docs/m7-prerequisite-contracts-v1`

## Current Accepted State

This is the current program-state index, advanced under Gate 35 authorization.
The accepted M7A closure snapshot remains historical evidence in Git. Gate 34
adoption and the human waiver do not retrospectively amend that snapshot.
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
| M7A Current State / Gate 34 | CLOSED / ACCEPTED / ADOPTED through PR #6 |
| M7A Contract | ADOPTED; historical boundaries retained |
| Gate 35 prerequisite contracts | PASS; V1 CONTRACTS FROZEN; full regression 602/0/0 |
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
- PR #6 M7A adoption: `8c2a61d9b921c9cc26c28b5afd33541aabc5976c`.

PR #6 parents are the Gate 32 main above and accepted documentation feature
`d394941d57aeb6c4c24fba010f32d3cee7a02e31`. M7A adoption post-merge
regression: 602/0/0, with focused 15/0/0, 41/0/0 and 26/0/0.
External evidence: C:/Users/conta/m7a_temp/adoption_post_merge/{focused.xml,full.xml}.

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
M7 STARTED = YES, contract-definition phases ONLY. M7A is adopted;
Gate 35 defines prerequisite V1 interfaces, not productive implementation.

M7A artifacts:
- [Current state](M7_EXCEL_RENDERER_CURRENT_STATE.md).
- [Contract draft](M7_EXCEL_RENDERER_CONTRACT_DRAFT.md).
- [Scope manifest](M7_EXCEL_RENDERER_SCOPE_MANIFEST.md).

Current Gate 35 contracts:
- [Visual Spec V1](M7_VISUAL_SPEC_V1.md).
- [Master interface V1](M7_MASTER_INTERFACE_CONTRACT_V1.md).
- [Canonical workbook mapping V1](M7_CANONICAL_TO_WORKBOOK_MAPPING_V1.md).
- [Numeric display profile V1](M7_EXCEL_NUMERIC_DISPLAY_PROFILE_V1.md).
- [Significance presentation V1](M7_SIGNIFICANCE_PRESENTATION_INTERFACE_V1.md).
- [Gate assessment and current gap register](M7_PREREQUISITE_CONTRACTS_GATE_ASSESSMENT.md).

MASTER XLSM = NOT FOUND in the inspected repository/surrounding workspace.
Visual Spec, mapping, numeric, significance, provenance, determinism and safety
contracts are frozen V1 documentation, not executable runtime contracts.
VBA preservation backend remains GAP. Physical Master adoption and backend
certification remain open. M7B READY = NO; M7B/M7C/M7D NOT AUTHORIZED.
No Master, renderer code, productive VBA or tests are added. Gate 35 does not
authorize a commit, push, PR or merge. Historical M7A evidence remains unchanged.
Gate 35 regression evidence and closure are indexed in the current assessment.

## Historical Evidence

Historical adoption/reproducibility findings remain unchanged in
[T0 baseline verification](T0_BASELINE_VERIFICATION.md),
[T0 repository adoption](T0_REPOSITORY_ADOPTION.md) and
[T0 inventory](T0_AS_IS_INVENTORY.md). These record dated T0 observations,
not the current runtime, implementation inventory or merge policy.
The current accepted state is the table above; do not apply historical blocked
or Legacy-default statements as current instructions.
