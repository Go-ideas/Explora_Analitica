# Gate 50 — Project Spec Draft Authoring Contract

## CURRENT STATE

Gate 48 produces deterministic `EXPLORA_SOURCE_ANALYSIS_V1` evidence and a
human-reviewed `EXPLORA_STRUCTURE_REVIEW_V1`. Gate 49 qualifies RU, RM,
LOOP_RU and LOOP_NUMERICO. The accepted `validate_project` contract remains the
only authority that can classify an `EXPLORA_PROJECT_SPEC_V1` as executable.

## TARGET STATE

Convert a `READY_FOR_PROJECT_SPEC_DRAFT` Structure Review into a deterministic
Project Spec draft without calculating statistics, approving decisions or
inventing unsupported analytical configuration.

## GAP

Before Gate 50, an operator had to author and re-upload Project Spec JSON even
after completing Structure Review. Source Analysis also retained only category
counts, not the value-label evidence needed for deterministic category authoring.

## DECISION

`EXPLORA_PROJECT_SPEC_DRAFT_AUTHORING_V1` accepts exactly:

1. `EXPLORA_SOURCE_ANALYSIS_V1`;
2. `EXPLORA_STRUCTURE_REVIEW_V1` in `READY_FOR_PROJECT_SPEC_DRAFT`;
3. source fingerprints embedded in Source Analysis; and
4. explicit `project_id`, `display_name`, `project_version` and `spec_version`.

Project identity is never inferred from filenames. The output is classified as
`DRAFT_VALID`, `DRAFT_REQUIRES_HUMAN_DECISION` or `DRAFT_INVALID`. Final schema
and semantic validation is delegated to the accepted `validate_project`.

## FIELD AUTHORITY

| Project Spec area | Gate 50 authority |
|---|---|
| project | Explicit operator input only |
| dataset | SAV fingerprint and deterministic Source Analysis inventory |
| source metadata fingerprints | Dataset, questionnaire, datamap, Source Analysis and Structure Review evidence |
| questions | HUMAN_APPROVED qualified Structure Review items only |
| universes | One accepted project-total `true` universe; no routing inference |
| weights | Empty when none approved; B1 `NONE` transformations for explicitly approved source weights |
| banners / filters | Empty; metadata variables remain available configuration evidence |
| significance_requests | Empty; LOOP significance remains fail-closed |
| derived_variables | Empty; no expressions are invented |
| output_requests | One WEB-only request over approved questions; no Excel intent |
| ambiguities | Material source incompatibilities block authoring and are returned structurally |
| ai_interpretations | Empty because deterministic extraction is not AI interpretation |
| provenance | Source/review fingerprints, authoring version, human authority and B1/B2/B3 refs |

## QUESTION AUTHORING

- RU and RM preserve reviewed source variables and deterministic SPSS categories.
- LOOP_RU and LOOP_NUMERICO preserve one logical parent, naturally ordered
  member variables and explicit iteration identities.
- HUMAN_EXCLUDED items remain non-executable authoring evidence.
- META_CONTROL variables remain available configuration evidence.
- Exactly one HUMAN_APPROVED respondent ID is required.
- Unsupported approved types, absent variables, incompatible categories,
  incomplete loops and duplicate logical identities fail closed.

Category identity derives from the canonical raw value, never from an inferred
meaning. Empty or incompatible labels require a human decision. Raw data is not
modified or read by the authoring module.

## DETERMINISM

Canonical serialization uses sorted keys, ASCII JSON and compact separators.
No wall-clock value or random identifier enters the draft. Identical Source
Analysis, Structure Review and operator metadata produce byte-identical output
and fingerprints.

## AUTHORITY BOUNDARIES

Gate 50 performs no percentages, bases, weighting, significance or canonical
statistics. It does not generate Execution Release, approve B3, normalize or
trim weights, infer routing, define banners/filters, or add Excel intent.
