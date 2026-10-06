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
optional dot, underscore, or hyphen separators before the numeric part and
before an optional letter suffix, are
recognized. Matching normalizes case and separators. Bare numbers and narrative
mentions do not create question sequence entries. No AI, customer IDs, numerical
question sorting, section inference, or analytical inference is used.

Each source variable retains direct, header-qualified questionnaire positions
in `questionnaire_exact_positions`. General `questionnaire_evidence` and
`questionnaire_exact_matches` still capture lexical mentions anywhere in text
for source classification; they never authorize question order. Existing
classification behavior remains intact. No questionnaire or an unsupported format yields no
sequence and deterministic fallback order.

## Display ordering

`review_editor_items(review, analysis)` returns ordered copies with optional
`questionnaire_order_key`, `questionnaire_question_ref`, and mapping status.
It never writes those fields into the stored Structure Review schema.

LOOP, RM, and GRID items use their normalized logical parent identity. Repeated
positions for the same identity use the earliest stable paragraph position.
Variable items first match their normalized identity against explicit heading
sequence entries. Otherwise label tokens may match those heading identities as
candidate order evidence. Legacy unqualified exact-position arrays and general
lexical mention counts are not used as order positions. Retained sequence source
text is reparsed with the corrected grammar, repairing separated suffixes and
rejecting narrative entries. Without usable heading sequence evidence, older
Source Analysis falls back deterministically to the technical/unmapped block.

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

## Human Review corrective - B-ORQO-01 / B-ORQO-02

Starting accepted feature head: `de1c9618a0520f3caafa15d7a085e000aa21e152`.
The safe-preselection portion is accepted and its semantics remain unchanged.
The questionnaire-order corrective is pending Human Review / Git Adoption.

QUESTIONNAIRE ORDER AUTHORITY = EXPLICIT QUESTION HEADING SOURCE EVIDENCE.
GENERAL LEXICAL MENTION != QUESTION ORDER AUTHORITY.

B-ORQO-01: `exact_questionnaire_positions(...)` now accepts only paragraphs
beginning with an explicit heading identity matching the normalized variable.
A programmer instruction mentioning a question, or another question heading
referring to that variable, does not supply an order position. General bounded
lexical evidence remains available separately and is unchanged. The renderer
reconstructs positions from the heading sequence rather than trusting legacy
unqualified position arrays. Label fallback continues to require a corresponding
explicit heading. Competing logical identities remain unresolved.

B-ORQO-02: separators before optional alphabetic suffixes are normalized without
collapsing the suffix into its parent. Generic forms `X8`, `X.8` normalize to
`X8`; `X8a`, `X.8a`, `X8.a`, and `X.8.a` normalize to `X8A`. `X8` and `X8A`
remain distinct. The same rules apply to all supported letter prefixes. Partial
matches of malformed suffixes and bare numeric headings are rejected. This is
conservative lexical parsing, not semantic questionnaire understanding.

Synthetic coverage checks narrative mentions before/after real headings,
repeated narrative references, references from another heading, direct heading
matching, preserved general lexical evidence, legacy fallback and legacy suffix
repair, separator variants, parent/suffix distinction, malformed tokens, and
presentation authority boundaries. No customer benchmark artifacts are committed.

Corrective validation (2026-10-06; `python -m pytest ... -q`):

- Focused questionnaire-order tests: 41 passed, 0 failed, 0 skipped.
- Focused accepted safe-preselection tests: 65 passed, 0 failed, 0 skipped.
- Gate48 regression: 21 passed, 0 failed, 0 skipped.
- Gate49 regression: 21 passed, 0 failed, 0 skipped.
- Gate50 regression: 35 passed, 0 failed, 0 skipped.
- Gate51 regression: 46 passed, 0 failed, 0 skipped.
- Full repository regression: 1253 passed, 0 failed, 0 skipped (990.16 seconds).
- Unexpected numerical deltas and customer-specific hardcoding: none.
- Fixtures are synthetic; no customer source artifacts are added to Git.
- Real benchmark smoke check: not run; source was not located in the workspace
  search. Synthetic blocker regressions provide implementation validation.
- Safe-preselection service, review UI, persisted authority, and stale-editor
  reset behavior are unchanged; accepted historical commits are preserved.
- A new corrective commit is published on the same feature branch. Human Review
  remains pending; no PR or merge is performed.


## Validation (original implementation)

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
