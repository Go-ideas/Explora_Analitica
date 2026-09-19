# EXPLORA Project Spec V1

Contract ID: `EXPLORA_PROJECT_SPEC_V1`

Machine-readable schema:
`explora_web_reporter/src/project_intake/explora_project_spec_v1.schema.json`.
Normative runtime validation:
`explora_web_reporter/src/project_intake/contract.py`.

## Boundary

Project Spec is accepted structured configuration between source intake and the
existing Core/materialization contracts. It is not a Canonical Result and does
not calculate percentages, bases, means, weights, or significance.

Mandatory semantic domains are project identity, dataset binding and
fingerprints, stable question/variable/category identity, structured universes,
B1-compatible weights, banners, filters, B2 significance requests, output
intent, ambiguity/AI decisions and provenance. Empty arrays explicitly represent
optional capabilities such as weights, banners, filters and significance.

Supported question identity vocabulary is `RU`, `RM`, `MENTION`, `PARENT_RM`,
`NUMERIC`, `SCALE`, `GRID_ESCALA`, `GRID_RM`, `LOOP_RM`, `LOOP_RU`, and
`LOOP_NUMERICO`. This vocabulary maps intake identity to already accepted Core
structures; it does not assert every physical source encoding can be inferred.
Free text and unknown structures are unsupported and fail closed.

## Deterministic And Human Decisions

Structured rules with complete references are deterministic. AI may propose
labels, type mappings, relationships, and universe interpretations, but every
material proposal records `decision_id`, evidence, proposal, release state,
approval requirement, final value and provenance. A pending material decision
produces `NEEDS_HUMAN_DECISION`; B3 authority is not bypassed.

Ambiguities are classified as `INFORMATIONAL`, `WARNING`, `BLOCKING`, or
`HUMAN_DECISION_REQUIRED`. Unresolved material ambiguity cannot produce
`READY_FOR_EXECUTION`.

## Readiness API

`validate_project(path_or_mapping) -> IntakeResult` is the Gate 43 callable
contract. It returns project/spec identity, source fingerprints, normalized spec
fingerprint, status, issues, ambiguity decisions, unsupported capabilities and
the explicit readiness boolean. It does not invoke Core.

`canonical_project_spec_json` sorts object keys with fixed separators and UTF-8
ASCII escaping. `project_spec_fingerprint` is SHA-256 over those canonical bytes.

## Project Package Convention

```text
PROJECT/
  input/          dataset, questionnaire, datamap, metadata
  config/         project_spec.json and accepted decisions
  canonical/      materialized inputs and Canonical Results
  web/            presentation outputs
  excel/          presentation outputs
  qa/             validation and release evidence
  provenance/     hashes, versions, lineage
```

The convention is a target packaging boundary, not a forced migration of the
current repository layout. Source filenames never define project identity.

## Derived Variables

Project Spec distinguishes source-already-calculated values, approved bounded
deterministic transforms, and unsupported proposals. Gate 43 does not add an
expression engine. AI-only transforms cannot become executable configuration.

## Provenance And Policy

Every ready spec references source artifacts and `B1_V1`, `B2_V1`, `B3_V1`.
Downstream Core, Canonical Results, renderer and QA versions remain responsible
for their own established provenance. Presentation intent is separate and may
change labels/order/decimals/inclusion, never analytical values.
