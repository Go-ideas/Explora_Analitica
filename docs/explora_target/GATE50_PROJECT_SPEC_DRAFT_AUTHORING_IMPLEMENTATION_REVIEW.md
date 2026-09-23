# Gate 50 — Project Spec Draft Authoring Implementation Review

## CURRENT STATE

Official starting main is `7d5c9c0f35b1f024c50f5c0cf54b2c757dc16aab`.
Gate 48 and Gate 49 are closed, accepted and merged. The Operator Console
already carries source analysis and explicit human Structure Review, but it had
no accepted transition to Project Spec.

## TARGET STATE

Provide a generic deterministic authoring service and an in-session Operator
Console action that creates a validator-backed `EXPLORA_PROJECT_SPEC_V1` draft.

## GAP

The accepted architecture required operators to manually construct Project Spec
JSON after review. Category labels, missing ranges, exclusions and review
fingerprints were not all available to a deterministic authoring layer.

## DECISION

Add `src/project_spec_authoring/authoring.py` as a separate non-statistical
module. Enrich Source Analysis with deterministic `value_labels` and
`missing_ranges`, preserving backward-compatible fields. Keep the existing
Project Spec upload as an advanced import route.

## IMPLEMENTATION

The authoring service:

- accepts only ready, human-reviewed structures;
- requires one approved respondent ID and explicit project metadata;
- authors RU, RM, LOOP_RU and LOOP_NUMERICO only;
- retains exclusions and configuration variables as non-executable evidence;
- creates deterministic categories and loop iterations;
- emits one total universe and one WEB-only output request;
- emits no automatic weight, banner, filter, significance, derived variable,
  AI interpretation or Excel request;
- calls the existing `validate_project` exactly once for generated drafts; and
- returns structured status, issues, ambiguities, provenance and fingerprint.

The Operator Console stores a valid generated draft directly in session, shows
status/errors/warnings/ambiguities/fingerprint and provides a JSON download.

## VALIDATION

Focused synthetic controls cover ready and fail-closed states, all qualified
question families, exclusions, respondent identity, category and loop ordering,
fingerprints, provenance, deterministic bytes, empty unsupported configuration,
validator delegation, hardcoding absence and statistical-authority separation.

No real customer source, identity, fixture or derived package is committed.
Observed validation:

- Gate 50 focused: 35 passed, 0 failed, 0 skipped.
- Gate 48 regression: 21 passed, 0 failed, 0 skipped.
- Gate 49 regression: 21 passed, 0 failed, 0 skipped.
- Gate 47 regression: 66 passed, 0 failed, 0 skipped.
- Full repository regression: 1101 passed, 0 failed, 0 skipped.

No unexpected numerical delta was observed.
