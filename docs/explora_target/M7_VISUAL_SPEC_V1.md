# M7 Visual Spec V1

Contract ID: M7_VISUAL_SPEC_V1. Status: FROZEN for Gate 35 contract definition.
Date: 2026-09-17. No runtime validator or renderer is implemented by this document.
Authority: adopted M7A boundaries and Gate 35 authorization. Current gaps and
acceptance evidence are maintained only in M7_PREREQUISITE_CONTRACTS_GATE_ASSESSMENT.md.

## Declarative envelope

Required fields: schema_version (exact contract ID), visual_spec_id, revision,
project_id, result_refs, master_interface_version, numeric_profile_version,
sections and provenance_refs. result_refs contain result_run_id,
result_fingerprint and request fingerprint from the supplied canonical source.
The immutable serialized spec has a content checksum. Unknown fields/versions,
duplicate IDs, missing references and cross-project references fail closed.
Labels never establish identity. No expressions, queries, metric derivations,
statistical thresholds, universe definitions or weight instructions are allowed.

V1 wire representation is UTF-8 JSON. IDs/versions/references are nonempty strings;
revision is a positive integer; order is a nonnegative integer; sections, visuals,
result_refs and source_bindings are ordered arrays, with at least one entry where
required. Optional reference arrays default empty; optional annotations default
absent, not a numeric/null analytical value. Labels are objects with text, language
and optional source_ref; display_profile_ref is a profile ID from the numeric
contract. Each source binding is an object with result_run_id, record_role,
record_id, field_name and slot_id. record_role is value, base, slice, comparison,
qa or provenance. field_name must be an existing canonical field allowed by the
mapping contract. Slot compatibility and source type/unit must match exactly.
No free-form expression or wildcard selection field is accepted.

Each section has section_id, order, sheet_role, title and visuals. Each visual
has visual_id (unique stable presentation ID), order, role, source_bindings,
labels, display_profile_ref, warning_refs and significance_presentation_refs.
Stable IDs are explicit and unchanged by label edits; order is explicit, with
ID as deterministic tie-breaker. Stable means within this versioned spec lineage,
not an alteration of canonical identity.

Roles V1: result_table, base_table, significance_table, qa_table and provenance.
Charts, calculated summaries, respondent drilldowns and arbitrary formulas are
unsupported V1. Source bindings enumerate exact result/value/base/slice/comparison
IDs and destination semantic slots. They cannot select raw respondents or create
new analytical slices. A result table can arrange already computed values;
it cannot aggregate, divide, subtotal or rank them analytically.
Destinations use Master role/slot identities, never question-label heuristics.

Labels are supplied presentation text with explicit language and authoritative
source reference when available. Missing labels use the stable ID as a visibly
identified technical label, never an inferred response/category identity.
No fabricated source version or questionnaire metadata is permitted.
All labels/configuration text are literal writes under the Master safety policy.

## Formatting and status

display_profile_ref resolves M7_EXCEL_NUMERIC_DISPLAY_PROFILE_V1.
Allowed presentation overrides: title, label, order, approved style ID and
suppression annotation. No change of canonical unit or stored value is allowed.
Canonical status and QA are copied, not reevaluated. Suppression requires explicit
presentation_reason and authority_ref; it hides a presentation slot but retains
canonical payload/status and audited cell mapping. It is not a new ValueStatus.
Critical/blocking QA cannot be hidden by suppression or warning selection.

warning_refs resolve supplied QA identifiers; unresolved references fail closed.
Non-OK sources cannot become ordinary numeric display cells. Not computed means
no supplied result for a declared binding, recorded as MISSING_SOURCE in renderer
QA, not a new Core enum; required bindings fail the render.
Optional bindings show an explicit not-computed annotation without a numeric cell.

Filter/banner selectors bind existing slice_id and request filter_refs only.
A selector may navigate/hide pre-rendered views; neither Excel nor VBA computes
new percentages, bases, weights or significance on interaction.

## Validation boundary

Core owns statistical semantics and release eligibility. Visual Spec owns
placement, labels and formatting only. Use existing canonical validation and
release policy before official rendering. Deserialization alone is insufficient.
An absent or non-releasable canonical release blocks official workbook publication.
An internal diagnostic artifact must be distinctly non-official and cannot bypass
this gate by changing its title. No Legacy fallback.
