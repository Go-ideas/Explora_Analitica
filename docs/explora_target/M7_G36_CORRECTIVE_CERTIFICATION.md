# Gate 36 Corrective Certification

Date: 2026-09-18. Current corrective decision; historical four-document blocked
assessment at c4a9ed8efdbb81ae54b2f07d3881f8a7c527f9a1 remains unchanged.
Entry main: 35d4df739998d768dcefaef27fbe373df2ee1143.
Branch: feature/m7-master-vba-readiness. No merge or M7B implementation authority.

## Intake and privacy

EXTERNAL_XLSM_FIXTURE_A is human-supplied, real-project stress evidence only.
It is NOT a Master or a generic fixture. The local source path was supplied by
the human outside Git; its filename, labels, business data and VBA code are not
retained in this evidence package. No macros were executed and no VBProject
object was accessed. The source file remains under user control and unchanged.
Whole-file SHA256: cb3b545d5b379596a93f80af4de009f4a01ac384613777ecaecc92e464a29742.
Size: 15773323 bytes. Valid macro-enabled package, OLE VBA payload and valid VBA
relationship independently confirmed. Inventory: 205 parts, 8 sheets (5 visible,
3 hidden), 10 defined names, 250883 formula cells, 135 chart XML parts,
13 pivot-related parts, 10 slicer-related parts, 1 connections part, no tables.
All identities/content in manifests use hashes; source business labels are absent.

Temporary working and derived files existed only outside Git. No raw part was
extracted to an individual file. Derivatives were deleted after each probe.
The original was not deleted. Anonymized metadata remains permissible evidence.
The external connection-part inspection found no refreshOnLoad=true attribute;
native automation disabled macros/events/link updates and used manual calculation.
This was not a VBA safety/code audit or authorization to reuse/execute those macros.

## Candidate results and deterministic selection

- openpyxl 3.1.5: NOT APPLICABLE for full stress round-trip under the imposed
  64 MiB XML-part resource bound. The 360034374-byte pivot cache exceeds it.
  This is a conservative triage limitation, not a fabricated destruction result.
  Generic XLSX generation/readback uses openpyxl; it is not certified for complex
  Master round-trips. No warning-based failure was invented for an unexecuted save.
- Native Excel 16.0 / pywin32 310: FAIL exact VBA preservation on actual Save As.
  VBA before: b7fdbafcc21e66531e0fa63142df4ee9739b13d80ff41f10fec845f3464eaf58.
  VBA after: 5ea720448210955f9f377bc1cbf534e68843640723432f9de6177b2a5e384fa4.
  No equivalence proof is supplied, so the binary change is not waived.
  Sheet/name/formula inventories and VBA relationships survived, but styles,
  shared strings, worksheet/workbook metadata also changed. Windows + Excel
  deployment would be mandatory for that candidate; it is NOT selected.
- XlsxWriter 3.2.5: NOT APPLICABLE to read/modify/preserve an existing Master.
  New-file creation and VBA embedding do not meet the required use case.
- Targeted OOXML: PASS for the precisely bounded declared-cell operation below.

Canonical V1 backend: Python 3.13.3 standard ZipFile + lxml 6.0.0 namespace-preserving
XML editing, tested zlib runtime 1.3.1. CERTIFIED for this bounded operation profile.
Selection is based on exact unchanged-part proof and failure of native exact-VBA
preservation, not convenience. lxml is already installed; the separate
scripts/requirements-gate36.txt pins certification tooling, not production routing.
A namespace-preserving parser is needed because unused OOXML compatibility prefixes
must survive serialization; a broad custom Excel engine is not justified.

## Supported operation profile

Certification helpers live under explora_web_reporter/scripts, not production
export modules. Source is immutable; destination must be separate and absent.
Macro mode requires .xlsm, macro content type, genuine supplied OLE VBA project
and valid VBA relationship. preserve_vba=False is rejected before a write.
The external stress modification was one initially empty XFD1 cell in sheet1.xml,
with literal CERTIFICATION_ONLY. Dimension/row-span hints may extend accordingly.
Every other source part must retain identical SHA256; no parts may be lost.
Stages are inspected and discarded on errors; completed output is published last.

Generic interface mode validates required roles, registry ownership, table/name
bindings, interface version and capacity profile. It modifies registered B2
scalar slots in presentation or renderer-owned audit roles, presentation F1 text,
or the explicitly allowlisted E1 certification-only formula. User/Master/VBA marker
regions remain untouched. Physical worksheet parts resolve through workbook
relationships, not project labels. Required interfaces cannot be silently created.
Formula writing is test infrastructure ONLY: official renderer V1 still permits
no newly authored formulas under frozen Gate 35 semantics.
Literal =,+,-,@ and whitespace/tab-prefixed variants round-trip exactly as text.
Numeric writes are finite typed scalars within the bounded precision checks;
tested scalar readback is exact. No statistical calculation or implicit fallback.

Unsupported: table resizing/growth, layout or chart editing, new parts, VBA editing,
signature-bearing packages, new formula authoring outside the certification slot,
arbitrary projects/labels/slot mappings, and unsupported precision/configuration.
They require separate fixtures/review, not automatic feature expansion.
This helper is not a complete normative Master validator, canonical adapter,
publication pipeline or implementation of the frozen numeric profile.
Future production use must validate full release/QA/provenance and exact storage
requirements independently; generic fixture mode must never become macro fallback.

## Preservation and determinism evidence

Targeted stress VBA before/after:
b7fdbafcc21e66531e0fa63142df4ee9739b13d80ff41f10fec845f3464eaf58.
VBA/content types/relationships pass. All untouched package parts are byte-identical,
including styles, charts, pivots, slicers, connections, drawings and caches.
No part additions/loss; normalized source worksheet comparison excludes only the
declared technical cell and corresponding dimension/row-span hints.
Other values/formulas/names/sheet states remain equal.
Structured tables are NOT APPLICABLE on the external stress fixture (zero).
Generic table/name/format preservation is independently tested instead.

Generic fixture is generated reproducibly by create_generic during tests: genuine
XLSX with no VBA, no client data and no claimed production status. It represents
all frozen semantic roles, stable table/name/registry IDs, ownership markers,
protected audit and user-editable surfaces, hidden states and literal/formula slots.
The VBA-owned marker is a concept only, not fake VBA. No client VBA is reused.
Fixture schema demonstrates interface feasibility; it is not a canonical result
workbook or a substitute for future production Master adoption.
Repeated identical generic declared-cell edits produce identical part hashes.
ZIP ordering/compression/timestamps are not workbook-content authority.
Large XML parts use streaming exact hashes; unmodified secondary worksheets also
use exact hashes. Only declared worksheet hints and isolated core modified timestamp
are normalized. No analytical value, formula or VBA field is excluded.

## Fail-closed coverage

Focused negative tests cover missing VBA, wrong source extension, missing macro
content type/relationship, corrupt ZIP, incompatible destination, dropping-VBA mode,
missing semantic role/name/table, incompatible ownership/write kind, unknown formula
and non-finite numeric input. Negative defective packages contain generic data only
and are never presented as genuine VBA fixtures. No degraded output is certified.
Role registry and required named-range destinations are validated before writes.

## Current gap disposition and readiness

| ID | Corrective disposition |
| --- | --- |
| B-G36-01 | RESOLVED: authentic external stress source supplied and fingerprinted |
| B-G36-02 | HISTORICAL NON-BLOCKING: no VBProject access or security change needed |
| G-M7-03 | RESOLVED FOR M7B FOUNDATION only: frozen interface plus generic reproducible fixture |
| G-M7-04 | RESOLVED for bounded declared-cell backend above; no broad backend certification |

PRODUCTION MASTER AVAILABLE = NO. Source workbook is never relabeled as Master.
M7B foundation can target a stable generic interface and preserve opaque macro-bearing
parts without requiring production Master design now. This is sufficient for
foundation readiness, not productive workbook integration/release.
GATE 36 CORRECTIVE STATUS = PASS. M7B READY = YES for foundation only.
M7B AUTHORIZED = NO.
Production Master adoption, wider operation profiles and final integration/QA remain
separate future acceptance requirements. No M2-M6, runtime or Gate 35 semantics change.

## Acceptance and tests

G36-C01..C03: authentic intake and exact VBA stress PASS.
G36-C04..C06: bounded backend/content types/relationships PASS.
G36-C07..C09: names/formulas PASS; tables PASS in generic fixture only.
G36-C10..C13: literals/fail-closed/interface/determinism PASS within declared scope.
G36-C14..C16: no production renderer or frozen semantic changes.
G36-C17: focused certification 46 passed / 0 failed / 0 skipped.
Generic interface subset: 37 passed / 0 failed / 0 skipped, 9 intentionally deselected.
G36-C18: full regression 648 passed / 0 failed / 0 skipped (84.60 seconds).
Pass-count increase is exactly 46 added Gate 36 certification tests above baseline 602.
No unexpected skips or regression failures. Default remains CANONICAL_V1.
Existing export smoke: 14 passed / 0 failed / 0 skipped.
Anonymized evidence: M7_G36_ANONYMIZED_CERTIFICATION_EVIDENCE.json.
External JUnit/evidence: C:/Users/conta/g36_temp/corrective.
Historical failed probes/resource normalization trials are not hidden as product
regressions; final successful stress proof is the basis of scoped certification.

Commands from explora_web_reporter:
- `python -m pytest tests/test_gate36_certification.py -q --basetemp C:\Users\conta\g36_temp\corrective\focused_release --junitxml C:\Users\conta\g36_temp\corrective\focused_release.xml`
- `python -m pytest tests/test_gate36_certification.py -q -k "generic or interface or targeted or literal or formula" --basetemp C:\Users\conta\g36_temp\corrective\generic --junitxml C:\Users\conta\g36_temp\corrective\generic.xml`
- `python -m pytest -q --basetemp C:\Users\conta\g36_temp\corrective\full_release --junitxml C:\Users\conta\g36_temp\corrective\full_release.xml`
- External stress probes accept a supplied local source path and external temporary
  directory; no client path/filename is embedded in source or committed evidence.
Export smoke uses the existing five-file group documented by the historical assessment.
No push, PR or merge is authorized by this evidence commit.
