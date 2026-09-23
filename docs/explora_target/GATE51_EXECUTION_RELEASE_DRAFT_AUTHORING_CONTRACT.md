# Gate 51 — Execution Release Draft Authoring Contract

## CURRENT STATE

Gate 50 produces validator-accepted `EXPLORA_PROJECT_SPEC_V1`. Gate 46/47 define
and build `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`; Gate 49 defines qualified loop
release representation. Previously the operator had to construct ER JSON.

## TARGET STATE

Deterministically map a READY Project Spec, explicit source authority and
explicit release/package metadata to a B3-pending Execution Release draft.

## GAP

The accepted validator required an approved B3 envelope and could not validate a
pending draft. No generic mapping service or in-session console action existed.

## DECISION

`EXPLORA_EXECUTION_RELEASE_DRAFT_AUTHORING_V1` maps RU, RM, LOOP_RU and
LOOP_NUMERICO only. `validate_execution_release` gains an additive
`require_approved=False` mode; its default remains approval-required. Draft mode
accepts only the exact empty pending B3 envelope and therefore cannot simulate
human authority.

Deterministic mappings are:

- RU and LOOP_RU → `PROPORTION`;
- RM → `RM_RESPONDENT_PROPORTION`, only with unambiguous accepted binary 0/1 states;
- LOOP_NUMERICO → `MEAN`;
- Project Spec weights → B1 release entries without normalization/trimming;
- no weight → `EXPLICITLY_UNWEIGHTED` requests;
- empty banners, filters and significance remain empty;
- WEB outputs decompose into one deterministic request per question.

Non-WEB intent, unsupported types/significance, incomplete loops, ambiguous RM
states, non-empty rules lacking released members, missing source authority and
missing package metadata fail closed.

## AUTHORITY

Project identity and fingerprint come from Project Spec. Dataset/questionnaire
authority is explicit and fingerprinted. Release/package identity and
`internal_project_name` are explicit operator inputs; display name and filenames
never supply customer identity. B3 decision ID, basis and timestamp remain null
until the existing human approval workflow runs.

## DETERMINISM

No UUID, timestamp or statistical result enters the draft. Canonical sorted JSON
is byte-identical for identical Project Spec, source authority and operator
metadata. The authoring layer invokes formula registry identities but never
evaluates formulas or reads raw survey rows.
