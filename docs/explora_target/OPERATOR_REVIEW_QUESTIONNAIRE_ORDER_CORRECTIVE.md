# Operator Console - questionnaire order and safe preselection

Status: bounded Operator Console UX corrective pending Human Review / Git Adoption.
No analytical milestone is reopened and no capability is added.

Authoritative starting main: `4a03d0e703ded522b703a203dcfc77459f5de1e0`.
Branch: `fix/operator-review-safe-preselection-questionnaire-order`.
This branch retains the safe-preselection corrective from local commit
`369801d644a3d99b64dddbf7f2e10c78ed07cb3c` and extends its presentation behavior.

QUESTIONNAIRE ORDER = DETERMINISTIC SOURCE/PRESENTATION EVIDENCE.
DETERMINISTIC PRESELECTION != HUMAN APPROVAL.

## Source evidence

Source Analysis includes optional `questionnaire.question_sequence` entries:
`question_ref`, `paragraph_index`, and `source_text`. Paragraph indices are
zero-based positions in the DOCX paragraph sequence, including empty paragraphs.
The existing `paragraphs_extracted` count continues to count non-empty text.
Evidence text preserves normalized paragraph content, bounded to 240 characters.
The evidence authority is `SOURCE_PRESENTATION_EVIDENCE_ONLY`.

Only explicit paragraph-leading tokens containing letters then digits, with an
optional dot, underscore, or hyphen separator and optional letter suffix, are
recognized. Matching normalizes case and separators. Bare numbers and narrative
mentions do not create question sequence entries. No AI, customer IDs, numerical
question sorting, section inference, or analytical inference is used.

Each source variable also retains all exact lexical questionnaire match
positions. Existing bounded questionnaire text evidence and classification
behavior remain intact. No questionnaire or an unsupported format yields no
sequence and deterministic fallback order.

## Display ordering

`review_editor_items(review, analysis)` returns ordered copies with optional
`questionnaire_order_key`, `questionnaire_question_ref`, and mapping status.
It never writes those fields into the stored Structure Review schema.

LOOP, RM, and GRID items use their normalized logical parent identity. Repeated
positions for the same identity use the earliest stable paragraph position.
Variable items prefer exact variable-name position evidence. Otherwise label
tokens may match explicit questionnaire identities as candidate order evidence.
Older Source Analysis with only bounded exact-match evidence can still match
its variable identity against the question sequence.

Distinct competing questionnaire identities are unresolved and receive no
position. At a shared mapped position, groups precede individual items; detection
order then item ID provide stable tie breakers. Unmapped/unresolved rows appear
after mapped rows in original detection order. Without questionnaire evidence,
all rows preserve existing detection order.

The editor shows non-editable position, question reference, and block columns.
The final block is labelled Roles técnicos / sin posición inequívoca en cuestionario.
A mapped META_CONTROL remains META_CONTROL/PENDING: ordering implies no approval.

## Human authority and session safety

Only persisted PENDING + QUALIFIED + RU/RM/LOOP_RU/LOOP_NUMERICO receives an APPROVED
editor suggestion. Existing APPROVED/EXCLUDED decisions remain unchanged.
Roles and unsupported/unresolved types receive no approval suggestion.

The operator can edit estado, tipo_final, and nota_humana. Only clicking
Guardar revisión humana invokes the unchanged `finalize_structure_review(...)`
path and persists explicit human decisions, including HUMAN_APPROVED.
Saving the sorted table still matches decisions by item ID; stored item order
and question semantics remain unchanged.

A successful new Source Analysis clears both the old review and editor widget
state. Both fresh-review preparation buttons also clear editor widget state.
Ordinary reruns preserve existing human decisions and current editor changes.

No statistical formula, B1/B2/B3, Project Spec analytical semantics, Execution
Release semantics, runtime, Gate49 loop semantics, significance, weight, or
respondent-ID methodology changes are included. Tests and DOCX/SAV artifacts
are generic and synthetic; no customer artifacts are added to Git.

## Validation

- Focused questionnaire-order + safe-preselection tests: 79 passed, 0 failed, 0 skipped.
- Gate48 regression: 21 passed, 0 failed, 0 skipped.
- Gate49 regression: 21 passed, 0 failed, 0 skipped.
- Gate50 regression: 35 passed, 0 failed, 0 skipped.
- Gate51 regression: 46 passed, 0 failed, 0 skipped.
- Full repository regression: 1226 passed, 0 failed, 0 skipped (1637.83 seconds).
- Unexpected skips, numerical deltas, customer-specific hardcoding, and warnings: none.
- Validation completed on 2026-10-06 using `python -m pytest ... -q`.
- Focused Streamlit AppTest covers default row order, save-by-item identity,
  preserved review authority, stale state on both fresh-review routes, and
  reset following successful analysis of a new source.

PR creation and merge are not performed.
