# M7 Excel Renderer Contract Draft

Date: 2026-09-17. Boundary contract: M7A_EXCEL_RENDERER_BOUNDARIES_V1.
Status: FROZEN FOR GIT REVIEW upon successful documentation validation/commit.
Authority: Gate 33 and human M7A contract-closure decisions M7-01 through M7-10.
Those decisions are frozen normative requirements. The retained DRAFT filename
identifies field-level mapping/storage/schema proposals that are still DRAFT,
not implemented or frozen runtime interfaces. This document is not an executable
Visual Spec, production renderer, or authorization for M7B/M7C/M7D.

## Status Terminology

CURRENT STATE = observed existing behavior; TARGET STATE = required future
behavior; GAP = absent capability/evidence; DECISION = human-approved boundary;
IMPLEMENTATION = executable behavior actually present; VALIDATION = executed
evidence or explicitly labeled future test requirements.
CanonicalResult -> Excel mapping contract: DEFINED / DRAFT at field level.
Authority and safety boundaries: FROZEN FOR GIT REVIEW.
Production M7 implementation: NOT IMPLEMENTED / NOT AUTHORIZED.

## Human-Approved Closure Decisions

### M7-01 - Excel Is A Renderer

Analytics Core -> Canonical Results -> Excel Renderer remains official authority.
Excel/VBA must not independently calculate official percentages, counts, bases,
weighted bases, means, scores, tests, significance, universes or weights. Web and
Excel may differ visually, never analytically for the same canonical result identity.

### M7-02 - Controlled Master Dependency

CURRENT STATE: MASTER XLSM = NOT FOUND; accepted, with no invented template or
placeholder. The future Master is a controlled, versioned dependency requiring
template_id, template_version, template_fingerprint/checksum and
compatible_renderer_contract_version before productive use. Required worksheets,
tables, named ranges, macro interfaces and configuration surfaces must have a
frozen description. Exact schema remains GAP until the artifact exists; M7B must
not assume any of those structures silently.

### M7-03 - Visual Spec Required

TARGET ARCHITECTURE CONCEPT is not IMPLEMENTED/FROZEN RUNTIME CONTRACT.
CURRENT STATE: VISUAL SPEC RUNTIME CONTRACT = GAP. A versioned Visual Spec is
required before productive rendering and must be separately accepted before
M7B authorization. Eventual V1 describes renderer-neutral result/section order,
visual family, hierarchy, visibility, display labels, number/display formats,
warning/note and significance presentation intent, and explicitly allowed
renderer hints. It cannot redefine analytical semantics. No executable Visual
Spec is introduced by this closure.

### M7-04 - Preservation Is Fail-Closed

The exact backend is NOT FROZEN. Reading/saving .xlsm does not approve a backend.
Before productive Master manipulation demonstrate VBA project, required worksheets,
named ranges, Excel tables, defined names and workbook relationships preservation,
plus macro-enabled output validity. Hash important embedded binary parts before
and after where applicable. If preservation cannot be demonstrated: FAIL CLOSED.
No degraded .xlsx, silent macro removal or silent VBA rebuild is allowed.

### M7-05 - Significance Transport Only

Tests and eligibility remain Core/B2 authority. Excel displays supplied accepted
significance; it must not independently manufacture letters from raw values.
Without an accepted presentation-ready representation:
SIGNIFICANCE LETTER DISPLAY = UNSUPPORTED for that contract version. Any future
renderer-neutral presentation contract is a separate approval dependency; M5
CanonicalResult semantics stay unchanged. This freezes the display boundary,
not a missing letter-token schema.

### M7-06 - Literal Text Safety

The observed synthetic '=1+1' formula conversion is a mandatory M7B implementation
and QA requirement, not production remediation in this handoff. Question,
category, banner and variable labels; notes; warning text; metadata; configuration
text; and all project-provided strings intended as text must be written literally.
At minimum account for leading '=', '+', '-' and '@'; do not change legitimate
canonical numeric negative values into text. Future malicious/synthetic fixtures
must cover each trigger across those text surfaces, inspect saved cell types and
formula inventory, and verify literal read-back without unintended execution.

### M7-07 - Formula Classification

All workbook formulas must be classified PRESENTATION_ONLY, ANALYTICAL or UNKNOWN.
OFFICIAL ANALYTICAL FORMULAS IN EXCEL = PROHIBITED. Presentation-only formulas
are permitted only if explicitly allowlisted by the renderer contract and never
the source of official analytical truth. UNKNOWN formulas fail review until
classified. The Legacy label probe is UNKNOWN/untrusted; it is not an approved
formula or canonical metric. Zebra formatting is PRESENTATION_ONLY.

### M7-08 - Interaction Is Not Computation

Excel interaction != Excel analytical computation. Static interactions select
among existing approved canonical slices. Future connected mode, only if separately
authorized: Excel/request -> Core execution -> Canonical Results -> Excel
presentation. Never Excel slicer -> local statistical recalculation. A missing
slice is FAIL / UNSUPPORTED, not local reconstruction.

### M7-09 - Canonical Value Versus Display Value

CANONICAL VALUE is the stored authoritative numerical value. DISPLAY VALUE is
its renderer-configured presentation, including decimal places, percent formats,
thousand separators, suppressed display or textual base presentation. Formatting
must not alter the stored official canonical value. Display-only rounding must be
deterministic and renderer-configured; no analytical/upstream rounding or canonical
value alteration is allowed. Numeric representability profile remains a GAP,
not permission to approximate stored official values. Suppressed display cannot
silently suppress critical warnings or remove identity/provenance.

### M7-10 - Benchmark And Generic Coverage

Benchmark A BA-01 through BA-05 is mandatory, including BA-03 MENTION / PARENT_RM /
STR_Q_DELIVERY_APPS_RM_V1, but is not universal specification evidence. Generic/
synthetic contract fixtures are also mandatory for applicable frozen upstream
capabilities. No project-specific benchmark characteristics become reusable rules.
Fixtures are planned here, not added or implemented by this documentation closure.

## Authority And Dependencies

Project/materialization -> Core -> CanonicalResult -> independent Excel renderer
-> project workbook. No Excel -> Web dependency. No raw data, ReportResult,
wide Web tables or Legacy projection may replace canonical numerical authority.
M2-M6, B1/B2/B3, materialization, Gate 19 and Gate 32 remain frozen.
Renderer configuration never enters canonical request/result fingerprinting.

## Input And Eligibility

Input is an explicit ordered collection of eligible CanonicalResult objects or
their existing canonical JSON representation, plus released renderer/template
configuration and upstream structured labels/spec provenance. No calculations
are requested from the renderer. Use existing validation/serialization APIs;
deserialization alone is not eligibility validation. Require:

| Authority | Existing fields / renderer requirements |
| --- | --- |
| Result | result_schema_version, result_fingerprint, manifest.result_fingerprint; verify consistency using existing Core validation/fingerprint rules |
| Execution | result_run_id, core_version, manifest.ruleset/core_version |
| Project/data | project_id, dataset_fingerprint, project_spec_ref |
| Request | request.request_id/request_fingerprint and complete snapshot; preserve released IDs rather than inventing them |
| Configuration | manifest.source_spec_refs and upstream released package/spec versions and hashes; runtime/package fingerprints from accepted evidence |
| Release/QA | existing release.releasable, computation_status, qa_release_status, reasons; QAEnvelope and QAEvents transported without reclassification |

Official output requires existing upstream release eligibility, not an independent
Excel release decision. Missing release or identity, unknown schema, contradictory
refs, unresolvable base/slice/value joins or non-releasable input blocks official
generation. A separately labeled internal-QA artifact may display provided
non-releasable records only if explicitly requested and approved; it is never an
official-output fallback. Mixed project/dataset collections are rejected in V1;
multiple result runs require explicit run-selection mapping and no silent mixing.
Versions/hashes absent from CanonicalResult must come from a validated upstream
companion manifest, not guessed from labels. No CanonicalResult fields are added.

## CanonicalResult To Excel Mapping

| Canonical record | Proposed normalized workbook record | Rule |
| --- | --- | --- |
| CanonicalValue | value_id, run/result identity, question/structure/slice/metric/formula IDs, base_id, all row/entity/column/option/category/loop IDs, semantic_order, unit, estimate, numerator, denominator, statuses and refs | Copy supplied numbers/status; never derive estimate from numerator/denominator |
| CanonicalBase | base_id, result identity, scope/unit/ref, universe/active weight, unweighted_n, weighted_n_raw, weighted_n, effective_n, dimensions/status/refs | Copy all measures, never sum/reweight/recompute or substitute another base |
| CanonicalSlice | slice_id/fingerprint, is_total, banner/member/filter refs and configuration | Select exact existing slices, not inferred Total or locally pooled members |
| SignificanceRelation | comparison_id, family/scope/metric/slice/member refs, status/direction, raw/adjusted p-values, test/policy metadata and refs | Transport existing relationships; no eligibility/test/adjustment/letters generation |
| QAEnvelope / QAEvent / release | issue/event IDs, state/lifecycle/scope/blocking/messages/related IDs, reasons and release decision | Preserve visibility and full structured payload; no warning suppression |
| Manifest/request/spec evidence | original canonical payload and source identities | Keep reconstructable upstream authority separate from renderer provenance |

Every displayed official value/base has a separate cell-map entry:
sheet + cell/range/chart-point locator -> result_run_id + result_fingerprint +
value_id/base_id/comparison_id/qa_id + exact source-field path + unit + format.
Cell coordinates are renderer metadata, never analytical IDs. Labels are joined
through structured released IDs; missing labels cannot change structure/metric.
Order follows semantic_order or an explicit complete renderer order of known IDs;
sorting or hiding affects display only, with omissions recorded in cell-map QA.
No recomputation is permitted to support a requested display layout.

Proportions remain canonical numeric proportions with Excel number formats;
no automatic /100 based on headers, question text or row labels. Preserve null,
zero, unsupported/error/status distinctions; no null-to-zero coercion. Store
authoritative JSON scalar representations alongside worksheet numeric cells.
Excel precision/range limits mean universal binary/decimal exactness cannot be
assumed: values that cannot round-trip to the exact canonical scalar under the
accepted numeric profile block official numeric rendering. Human review must
approve that profile and limits before M7B. Number formatting may round displayed
text but must not round stored official values or alter analytical identity.

## Renderer Configuration And Visual Spec

Separate proposed renderer config contains schema/version/release/hash, template
ID/version/checksum, sheet/section placements, ID-based orders, visual family,
formats, locale and visibility. It may not contain formulas, universes, weight
policies, structure reinterpretation or significance methodology. Unknown fields,
duplicate placements, collisions/overflow and unresolved refs fail validation.

VISUAL SPEC RUNTIME CONTRACT = GAP. Before M7B freeze an independently versioned
renderer-side schema/validator, allowed visual families, placement capacities,
label provenance, order/visibility rules, exact numeric profile and QA/release
rules. The Phase 1/M5 conceptual Visual Spec is not executable authority. Do not
smuggle metric overrides into visual configuration. No upstream semantic change
is required by this proposed presentation contract; requests requiring one stop
and return to Core/human review.

## Master Interface And Technical Mechanism

Target: one reusable EXPLORA_MASTER.xlsm plus project-specific canonical
data/configuration -> a project .xlsm, not a per-study VBA build.
MASTER XLSM = NOT FOUND. Existing fresh-XLSX XlsxWriter code cannot populate a
preserved Master. Safe macro/template preservation remains unproved.

Proposed mechanism is copy-on-write population of a validated Master: never
modify the released template in place. Template contract must enumerate exact
version/checksum, required sheets, named ranges/tables and column schemas,
writable ranges, immutable parts, capacities, allowed formula inventory, VBA
project hash, controls/links/slicer relationships and macro entry-point versions.
Write literal canonical data/config/provenance only to declared destinations;
publish atomically only after QA and package-part integrity verification.

No backend is frozen or approved by this closure. openpyxl keep_vba is only a
candidate for feature-compatible templates, subject to representative round-trip
tests; it is not proof of preserving controls/shapes/slicers/signatures. Native
Excel automation or targeted OOXML population are alternatives requiring explicit
dependency/security/platform review. XlsxWriter new-file + extracted VBA is not
Master preservation. Before productive Master manipulation separately select and
approve a backend against a supplied test template, document supported Excel
versions and verify all preservation evidence required by M7-04.
Without that evidence .xlsm output is UNSUPPORTED, not downgraded silently to XLSX.

## Provenance Storage Proposal

Freeze on human acceptance, with no upstream schema mutation:
visible EXPLORA_Provenance sheet for project, spec versions/hashes, result runs,
renderer/config/template versions/hashes, UTC generated_at and QA/release status.
Protected audit sheets EXPLORA_Results, EXPLORA_Bases, EXPLORA_Slices,
EXPLORA_Significance, EXPLORA_QA and EXPLORA_CellMap contain the structured records
above. EXPLORA_CanonicalPayload stores the original canonical JSON in numbered,
bounded text chunks plus content hashes to avoid Excel cell-length truncation.
These are proposed new template requirements, not ranges found in an existing
Master. A detached QA manifest records output checksum and preservation evidence;
the workbook cannot contain its own final-file hash without circularity.
Hidden/protected sheets provide organization, not cryptographic trust. Canonical
hashes and signed/released input authority must be independently verifiable.

Versioning distinguishes input schema/Core rules, renderer contract/version,
Visual Spec/config version, template version and VBA interface version. Reject
incompatible combinations; timestamp/output ZIP metadata may vary, but normalized
record/cell-map content must be deterministic for identical inputs/config.

## Python, Excel And VBA Responsibilities

Python renderer validates and copies authoritative results, joins released labels,
lays out data, preserves template parts, records provenance and verifies output.
It does not call Legacy or Web calculations. Core execution/materialization are
upstream and separately authorized, not renderer fallback responsibilities.

Excel/VBA may navigate, show/hide approved sections, select existing canonical
slices, refresh presentation and manage UI state. No weight normalization/cap/
repair, denominator derivation, aggregation, score/NPS/box calculation or statistics.
Generic VBA only; study-specific logic belongs in structured configuration.
No VBA development or productive Master construction is authorized now.

Static filters/banners/slicers select a declared existing slice/result. Filtering
respondent rows or summing displayed cells cannot create a new official slice.
Missing combinations return FAIL / UNSUPPORTED. Future connected requests may
invoke Core only through a separately approved request-bound interface and return
new eligible CanonicalResults; no connected protocol is implemented/authorized.

Significance is Core/B2 authority: display supplied states, relations, markers and
legends. Do not perform z/t tests, Holm, eligibility or letter assignment. Existing
SignificanceRelation has no released Excel letter-token contract. V1 can transport
relations/statuses without fabricated letters; if letter display is required,
obtain approved upstream presentation tokens or return UNSUPPORTED. Missing
significance is not 'not significant'. Unsupported status stays visible.

## Renderer QA And Fail Closed

| QA requirement | Acceptance / failure rule |
| --- | --- |
| Authority/release | All source records validated and official eligibility preserved |
| Identity and coverage | Exact source/run/record joins and complete requested cell-map, no ambiguity |
| Values and bases | Read-back numeric scalar equality; canonical payload/hash unchanged; precision failures block |
| Units/status/missing | Exact unit/status/null/zero distinction, no label-based conversion |
| Warnings/QA | All critical/blocking notices visible; full issue/event relationships transported |
| Significance | Exact supplied status/direction/relation/token if available; no manufactured inference |
| Order/layout | Semantic order or explicit approved ID permutation; no dropped/overlapping/truncated records |
| Visual support | Unsupported family/layout surfaced, no substitute metric/structure |
| Template | Required sheets/ranges/tables/capacity and version/checksum match |
| Macros/parts | VBA and immutable package parts unchanged; controls/slicers/links intact; compatibility verified |
| Formulas/security | Only allowlisted presentation formulas; official numeric cells literal; source text literal, no formula injection |
| Determinism/provenance | Repeat normalized records/map and refs exact; generated timestamp recorded separately |

An official-output failure stops publication and produces a diagnostic, never
Legacy substitution, local statistics, synthesized results, a metric swap,
warning removal or different template/format. An existing warning tolerated by
upstream release remains visible; Excel may not tighten/loosen B3 silently.

## Benchmark And Negative Validation Matrix

M7A defines this future matrix; it does not generate the workbook or start M7D.

| Case | Future Excel assertion |
| --- | --- |
| BA-01 | All canonical values/bases and IDs exact; accepted 40-record comparison reference |
| BA-02 | Exact canonical RM respondent records; accepted 4-record reference |
| BA-03 | Exact 4-record mention reference and MENTION / PARENT_RM / STR_Q_DELIVERY_APPS_RM_V1 transported |
| BA-04 | Exact canonical filtered slice/request identity; 40-record reference; no local filter calculation |
| BA-05 | Exact 6-record banner reference/member coverage; no pooled or inferred Total |
| Repeated generation | Same source/package/runtime/result fingerprints, normalized cells/records/map; timestamp variance explained |
| Missing slice/metric/base/label/ref | Fail/unsupported, no local fill or Legacy fallback |
| QA failure/missing release/warnings | Official output blocked as applicable; no suppressed critical warning |
| Wrong template/missing range/overflow/macro change | Fail before publish; original Master untouched |
| Null/zero/weighted/effective-n/unsupported significance | Exact existing records/status; test fixtures only where Core supplies eligible results |
| Formula-like labels/precision boundary | Literal text and exact numeric profile enforced; unsupported numeric values fail |
| GRID/LOOP/mean/NPS and significance letters | Explicit coverage approval or UNSUPPORTED; no claim of support based on generic table writer |

Generic/synthetic fixtures are a required independent axis, not synonyms for the
Benchmark rows. Their future matrix includes:

| Capability | Generic/synthetic assertion under frozen upstream contracts |
| --- | --- |
| RU and RM | Unrelated project/label IDs; exact values, units and respondent/mention bases, no label inference |
| Grid and applicable Loop | Preserve supplied row/entity/column/loop identity and structural missing/zero; absent upstream capability stays UNSUPPORTED |
| Weighted/unweighted | Transport supplied weighted_n_raw/weighted_n/effective_n and active weight/QA exactly; never apply or repair weights |
| Bases and warnings | Zero/null/status distinctions; all critical messages and references preserved |
| Significance | Supplied relations/status/tokens only; missing accepted letter representation returns UNSUPPORTED |
| Category order | Preserve semantic order or explicit ID-based display permutation without changing source identity |
| Unsupported states | Visible statuses; unknown metric/visual/slice rejected with no substitute |
| Literal/formula safety | Leading =,+,-,@ on every M7-06 text surface; literal saved types/read-back; UNKNOWN formula blocks review |
| Template structures | Missing worksheet/table/range/defined name, incompatible version and changed binary/relationship fail closed |
| Provenance | Exact project/spec/run/record mapping, configuration versions/hashes and source payload reconstruction |
| Deterministic rendering | Repeated normalized cells/maps/records exact; timestamp/container variance isolated |

These fixtures use existing eligible upstream results where available, or frozen
contract fixtures with explicit status/limitations. They must not add unsupported
Core calculations merely to satisfy an Excel test. No new tests are authorized now.

Each official Excel cell traces to its exact canonical record. Accepted Gate 19
94/94 parity is an upstream reference, not proof of future workbook fidelity;
Excel-to-canonical read-back must independently pass. Web visual parity is not
required. Benchmark-specific IDs appear only in this validation plan, never as
production renderer rules.

## Decisions Required Before Later Phases

Separate acceptance must resolve Visual Spec schema/QA, numeric profile, template
artifact/interface and preservation backend, provenance storage names/capacities,
supported structures/metrics and optional significance token source. No schema or
semantic remediation to M2-M6 is authorized. M7B/M7C/M7D need separate explicit
authorization even after this draft is accepted.
