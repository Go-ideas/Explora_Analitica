# M7 Excel Renderer Scope Manifest

Date: 2026-09-17. Gate 33 = PASS; M7 entry authorized.
Phase: M7A CONTRACT CLOSURE / DOCUMENTATION ADOPTION ONLY.
Current-state review: PASS. Contract review: PASS WITH REQUIRED CLOSURE.
Contract closure status: FROZEN FOR GIT REVIEW upon successful validation/commit.
Starting main / expected commit parent: 0fe9caf1f7d9b942035403b28a89672eb92baf37.
Branch: docs/m7-excel-renderer-contract. One documentation-only commit authorized;
push/PR/merge and M7B remain unauthorized. Final commit SHA is Git evidence, not
a self-referential document field.

## Authorized Deliverables

Added documentation:
1. M7_EXCEL_RENDERER_CURRENT_STATE.md: source audit, dependencies, library/template
   evidence, workbook formula probe, classification, gaps and baseline tests.
2. M7_EXCEL_RENDERER_CONTRACT_DRAFT.md: canonical input mapping, proposed Master
   mechanism/storage, renderer configuration, authority boundaries and future QA.
3. M7_EXCEL_RENDERER_SCOPE_MANIFEST.md: scope and human decision checklist.

Modified documentation: EXPLORA_PROGRAM_STATE.md, reconciling current accepted
history through Gate 32 and Gate 33 entry. Historical gate documents unchanged.
Files deleted: NONE. Source/tests/dependencies/binary templates modified: NONE.
Final adopted diff must contain exactly these four documents, with a clean
worktree after commit. No rename: DRAFT filename is deliberately retained because
field-level mapping/storage schemas are DEFINED / DRAFT, not frozen runtime
interfaces. Human decisions M7-01 through M7-10 freeze normative boundaries only.

## Scope Boundary

M7A performs inspection, records frozen human boundaries and draft field-level
contract proposals, and tests unchanged
code. It does not implement a renderer, Visual Spec validator, Master, macros,
Excel automation, connected workflow or statistical capability. M7B foundation,
M7C Master/VBA and M7D productive release are NOT AUTHORIZED. No later phase starts
automatically. M2-M6/B1-B3, accepted materialization, Gate 19 and Gate 32 remain
authoritative and semantically untouched.

## Exit Checklist

| Requirement | Evidence / result |
| --- | --- |
| Existing behavior / Legacy dependencies | Current-state component table and source links: DEFINED |
| CanonicalResult integration | Draft input/mapping/eligibility: DEFINED |
| Master status | NOT FOUND in checkout/surrounding workspace; version/location/checksum UNKNOWN |
| Visual Spec status | RUNTIME CONTRACT = GAP; proposed separate contract, not implemented |
| Analytical/presentation separation | Draft authority/responsibilities: DEFINED |
| Filter/banner/slicer and VBA boundaries | Static canonical slices only; generic interaction, no local analytics: DEFINED |
| Renderer config/provenance/versioning | Proposed ID-based config and audit storage: DEFINED for review |
| Warning/base/significance transport | Existing record mapping and letter-token limitation: DEFINED |
| QA/fail-closed | Draft QA table and negative matrix: DEFINED |
| Benchmark A | Five requests + 94-record scope + BA-03 identity + read-back/negative plan: DEFINED |
| Unsupported areas/ambiguities | Decision register below: EXPLICIT |
| Upstream semantics / implementation | No source/test changes, no production renderer/VBA: VERIFIED |

## Decision Register

| ID | Gap / ambiguity | Owner / required decision | Blocking scope |
| --- | --- | --- | --- |
| M7-G01 | No Master artifact or ranges/macros/version/checksum | Human/template owner supplies reviewed representative Master and interface inventory | .xlsm integration/release; not M7A |
| M7-G02 | No executable/released Visual Spec | Human approves independent presentation schema/version/validator and supported visual families | M7B |
| M7-G03 | Safe Master package/macro/control preservation unproved | Engineering/human approves backend after representative template round-trip, Excel/security compatibility; no backend frozen in this closure | Productive Master manipulation |
| M7-G04 | No canonical Excel mapping/release/provenance writer | Accept draft mappings/storage/capacities, then separately authorize implementation | M7B |
| M7-G05 | Legacy header/row heuristics and formula injection | Future writer must use units/IDs and literal text with QA; no Legacy remediation performed | Official M7 output |
| M7-G06 | Significance relations lack released Excel letter-token input | Core/human chooses approved token source or V1 relation/status-only unsupported-letter display | Letter feature, not record transport |
| M7-G07 | Excel numeric precision limits vs exact scalar contract | Human approves representability profile and fail-closed read-back rule | M7B official numeric rendering |
| M7-G08 | Generic project/metric/GRID/LOOP support not demonstrated by Benchmark A | Scope eligible supplied results; any frozen upstream expansion returns to Core/human | Broader support, not M7A |
| M7-G09 | Connected Core request/refresh protocol absent | Separate interface/security authorization; static V1 rejects missing slices | Connected mode, not static rendering |

No M7A completion blocker. These gaps prevent treating the draft as productive
implementation authorization. No accepted result is reopened or reinterpreted.

## Validation And Governance

Original evidence: C:/Users/conta/m7a_temp/focused.xml and full.xml.
Closure rerun evidence: C:/Users/conta/m7a_temp/closure/focused.xml and full.xml.
Excel/export focused: 15 PASS / 0 FAIL / 0 SKIP.
Canonical contract/identity/transport focused: 41 PASS / 0 FAIL / 0 SKIP.
Gate 32 focused: 26 PASS / 0 FAIL / 0 SKIP.
Combined focused: 82 PASS / 0 FAIL / 0 SKIP.
Full regression: 602 PASS / 0 FAIL / 0 SKIP; no test-count change.
Unexpected skips/numerical deltas: NONE detected. Formula probe is synthetic audit
evidence, not an official analytical execution or new regression.

M7A CONTRACT = FROZEN FOR GIT REVIEW after successful closure commit.
M7A READY FOR GIT REVIEW = YES after clean validation and documentation commit.
M7B IMPLEMENTATION AUTHORIZED = NO.
PUSH = NO. PR CREATED = NO. MERGE = NO.
Next destination: CORE / HUMAN REVIEW, M7A Git Review. No automatic later phase.

## Human Closure Traceability

M7-01: renderer-only analytical authority frozen.
M7-02: absent Master accepted; controlled identity/version/checksum/compatibility
and frozen worksheet/table/range/macro/config description required, schema pending.
M7-03: versioned renderer-neutral Visual Spec required; separately accepted before
M7B authorization, no implemented runtime claim.
M7-04: preservation of VBA, sheets, ranges, tables, defined names, relationships
and valid macro-enabled output required; important binary hashes, fail closed;
backend NOT FROZEN.
M7-05: Core significance only; unaccepted letter representation UNSUPPORTED.
M7-06: all source text literal including =,+,-,@; future malicious fixtures mandatory.
M7-07: PRESENTATION_ONLY / ANALYTICAL / UNKNOWN inventory; official analytical
formulas prohibited, UNKNOWN fails review.
M7-08: slices selected, never computed in Excel; future connected mode separate.
M7-09: canonical stored value unchanged; deterministic configured display only.
M7-10: Benchmark A plus generic/synthetic matrix mandatory; upstream capability
limits explicit, no universal Benchmark rules. All ten decisions are incorporated
in the companion contract, without source/test/template/VBA implementation.
