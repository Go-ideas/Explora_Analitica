# Gate 43 Project Intake and Project Spec Review

## Current State

Execution contracts are mature but intake configuration is fragmented. See
`GATE43_PROJECT_INTAKE_CURRENT_STATE.md`. The narrow Core `ProjectSpec`, M2
universes, M3/B1 weights, M4 structures, M5 requests, materialization packages,
Web bindings and M7 presentation contracts remain authoritative.

## Target State

`EXPLORA_PROJECT_SPEC_V1` is the reproducible semantic package accepted before
Core execution. `validate_project` deterministically returns either
`READY_FOR_EXECUTION`, `VALIDATION_FAILED`, or `NEEDS_HUMAN_DECISION` with a
separate `IntakeResult`.

## Gap

The repository lacked one versioned source-to-execution readiness boundary,
durable ambiguity/AI decisions, and a deterministic whole-spec fingerprint.

## Decisions

- Add a pre-Core intake package instead of expanding the existing Core model.
- Use JSON plus a checked-in JSON Schema and strict Python cross-reference
  validation; JSON Schema alone cannot enforce reference integrity.
- Preserve B1/B2/B3 by reference and fail closed on conflicts.
- Keep physical input formats separate from canonical semantics.
- Treat presentation intent as non-analytical.
- Do not implement questionnaire parsing, statistical execution, project
  running, UI, or a general derived-variable language.

## Implementation

The `src/project_intake` package implements loading, canonical serialization,
SHA-256 fingerprinting and structured readiness results. Generic fixtures cover
the smallest runnable spec and a representative multi-domain spec. Twelve
fixture scenarios cover the mandatory invalid and ambiguous conditions.

## Validation

Focused tests cover schema/version, stable IDs, required fields, references,
question types, categories, universes, B1 weights, B2 requests, B3 decisions,
outputs, provenance, round-trip serialization, deterministic fingerprints and
fail-closed readiness. Regression evidence is recorded in the Gate 43
checkpoint after execution.

## Open Ambiguities

No human decision is required to accept the V1 boundary. Future source adapters
must define how particular questionnaire/datamap formats produce proposals, and
future project-runner work must define compilation from an accepted Project Spec
to released materialization packages.

## Out Of Scope

Real project execution, source-format parsers, OCR, AI orchestration, a UI,
statistical logic, unrestricted derived expressions, legacy migration, and any
change to M2-M7 analytical semantics.

## Next Recommended Gate

A separately authorized gate may implement a deterministic Project Spec to
released-package adapter and runner dry-run. Gate 43 does not authorize it.
