# Gate 44 First Productive Project End-to-End

## CURRENT STATE

Gate 43 accepts and fingerprints `EXPLORA_PROJECT_SPEC_V1`, but does not bind it to execution. The released Benchmark A package already defines questions, structures, universes, banners, filters, B2 requests and output requests. `run_canonical_project` is the released CANONICAL_V1 execution boundary; Canonical Results feed the accepted Web adapter and Excel renderer independently.

The pre-implementation handoff remains preserved in `GATE44_CODEX_HANDOFF.md`, and its historical package skeleton remains under `evidence/gate44_first_productive_e2e/`. Those records are traceability scaffolding, not the productive release authority.

The authoritative external inputs are `FUNSMX_297140_20260914.sav` (`71B8CC...DBB2F`) and release 1.0.1 (`78AFA3...85A41`). They remain outside Git. Production Master 1.2.0 is repository evidence with SHA-256 `f3a11f...c869c` and VBA SHA-256 `0f879b...b758`.

Manual translation previously connected the released package to Core request IDs, presentation targets and provenance. No Project Spec compiler or productive release orchestrator existed.

## TARGET STATE

The controlled flow is Project Package -> Project Spec -> deterministic execution binding -> CANONICAL_V1 Core -> one Canonical Results set -> Web and Excel presentation -> QA/provenance release.

## GAP

The missing boundary was deterministic, fail-closed translation from a ready Project Spec to the existing released package and request identities. Release-level cross-surface parity and rerun evidence were also absent.

## DECISION

Add a narrow compiler under `project_intake` and a Gate-44 productive orchestrator. The compiler translates identities and policy references only. Core remains the sole statistical authority; Web and Excel receive the same Canonical Results. There is no Legacy fallback.

Dynamic Region is `NOT EXERCISED`: the real productive proportions exceed the qualified 15-digit safe precision envelope. Rounding or weakening that contract is prohibited. Significance is also `NOT EXERCISED`: B2 is requested and preserved, but this run emits no comparisons or significance records.

## IMPLEMENTATION

`EXPLORA_PROJECT_EXECUTION_BINDING_V1` binds source/package hashes, Project Spec fingerprint, released package identity, request/question/structure/universe identities, presentation targets and B1/B2/B3 references. The runner executes the binding twice, records deterministic logical identities, materializes all five Canonical Results, projects Web output and performs plan-derived physical Excel read-back against Production Master 1.2.0.

## VALIDATION

The productive release is under `explora_web_reporter/evidence/gate44/FUNSMX_297140`. It contains no SAV, release ZIP, questionnaire or other customer raw input. Focused Gate-44 validation: 24 passed, 0 failed, 0 skipped. Final relevant and full regression results are recorded in the implementation review and checkpoint.
