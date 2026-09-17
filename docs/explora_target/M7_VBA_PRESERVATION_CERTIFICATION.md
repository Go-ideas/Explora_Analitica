# M7 VBA Preservation Certification

Gate 36, 2026-09-17. Result: NOT CERTIFIED.
B-G36-01: no genuine macro-bearing source fixture found.
B-G36-02: Excel security blocks programmatic VBProject access.

Environment probe: isolated win32com.client.DispatchEx('Excel.Application'),
Visible=False, DisplayAlerts=False, temporary unsaved workbook.
Excel version 16.0. Reading VBProject.VBComponents.Count returned:
"The programmatic access to the Visual Basic project is not trusted"
(localized Excel diagnostic, HRESULT -2146827284).
Workbook closed without saving and Excel instance quit in finally.
No security setting changed, macro executed, workbook saved or VBA module inserted.
Native Excel availability is not equivalent to fixture-authoring capability.
A human may supply a reviewed harmless macro-bearing fixture; do not require
weakening global Trust Center settings to unblock certification.

## Certification status

VBA binary preservation, macro-enabled package integrity, names/tables/formulas,
literal writes, required interface checks and fail-closed negative tests:
NOT TESTED against a genuine .xlsm fixture. No backend receives conditional PASS.
Existing Legacy XLSX tests cannot certify macro preservation.

## Required future evidence

For each viable backend: inventory source ZIP content types/relationships and
semantic structures; record vbaProject.bin hash; copy to staged destination;
apply authorized literal/numeric change; save .xlsm; inspect all required parts.
Compare VBA hash, sheets/visibility, names, tables, formulas, literal types/text,
styles, controls, relationships and signature-bearing parts. Reject unexplained
part loss. Validate structural open without macro execution.

Negative cases must reject: absent VBA source; wrong source extension; missing
preservation mode; absent VBA relationship; corrupt ZIP; wrong output extension;
missing semantic registry; mandatory name/table absent. Failure must prevent
publication, not become a warning. These cases remain planned, not executed.

Test =,+,-,@ literals and whitespace/control-prefixed variants through typed text
writes, preserving exact content and absence of formula/external-link nodes.
An allowlisted certification formula must remain a formula. No generic sanitization
or inference. This does not authorize production renderer formulas.

Determinism: compare exact VBA hash and normalized manifests of sheet IDs,
visibility, names, table definitions, target values/types, formulas, literals,
styles and supplied fixture provenance. Exclude ZIP timestamps/order/compression
and isolated generation timestamp only. Preserve all input hashes/semantic fields.
Repeated round-trip proof remains pending; strategy is defined, not certified.
