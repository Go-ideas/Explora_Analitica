# M7 Master Interface Contract V1

Contract ID: M7_MASTER_INTERFACE_CONTRACT_V1. Status: FROZEN normative interface.
Physical Master: NOT FOUND. No sheet/name/table described here is claimed to
exist in an inspected workbook. This contract specializes the adopted M7A
semantic-role proposal; physical conformance remains a separate adoption gate.

## Manifest and semantic roles

A future controlled Master must supply master_id, version, artifact_sha256,
interface_version, compatible_visual_spec_versions and a role registry.
Registry records: role_id, sheet identity, visibility, owner, slot_id,
table/named-range binding, permitted columns, capacity and update policy.
Coordinates are resolved from verified bindings, not fixed project coordinates.
Duplicate/unresolved roles, capacity overflow or incompatible versions fail closed.

| Required role | Visibility | Ownership / policy |
| --- | --- | --- |
| presentation | visible | renderer writes declared result/label/status slots only |
| provenance | visible | renderer replaces declared provenance table |
| results / bases / slices | protected audit | renderer replaces declared canonical tables |
| significance / qa / cell_map | protected audit | renderer replaces declared transport tables |
| canonical_payload | protected audit | renderer replaces ordered exact serialization chunks |
| configuration | visible | Master definitions; user edits only declared navigation/preferences |
| navigation | visible | Master/VBA-owned; renderer preserves |

Role IDs are independent of physical sheet names. Tables require stable record IDs,
source IDs and run identity. CellMap requires visual_id, slot_id, resolved
sheet/table/row/column, source result/record/field, unit, storage mode, status,
display format and suppression authority. Provenance and QA must remain inspectable;
protection is accidental-edit protection, not encryption or access control.
No client/brand/question/project/Benchmark identities in this interface.

## Ownership and mutation

Renderer may update/clear/replace declared renderer-owned table bodies and
presentation slots only. Clear stale renderer records before atomically replacing
them; do not leave previous-run cells. Preserve declared headers/styles/layout.
Creating missing required sheets/tables/names is prohibited: incompatible Master
fails rather than being repaired. Registry may authorize table body growth within
capacity; resizing must preserve table metadata and references.
Master-owned styles, charts, controls, names, formulas and layout are preserved.
VBA modules, binaries, relationships and controls are preserved, never rewritten.
User-owned content is preserved; overlap with renderer writes is a fatal conflict.
VBA/user permissions cannot make official metric/base/QA/payload slots editable.
No deletion of unknown structures; unknown ownership blocks publication.
Write to a separate staged output, validate, then publish atomically. Never mutate
the controlled input Master. On failure discard staged output, retain input.

## Literal and formula safety

Every external label, brand, question, option, note, token and configuration text
uses LITERAL_WRITE (OOXML text/string), even with leading =, +, -, @, whitespace
or control characters before such prefixes. Disable writer formula/URL inference.
Preserve the exact text; do not silently strip prefixes or prepend visible apostrophes.
Disallow invalid XML characters with explicit diagnostic rather than lossy cleanup.
Test round-trip cell type, text and absence of formula nodes/external relationships.
Numeric source scalars use typed numeric writes, never label-based parsing.

FORMULA_WRITE requires a versioned allowlist keyed by semantic slot, exact formula,
dependencies and PRESENTATION_ONLY classification. V1 permits no newly authored
cell formulas. Existing reviewed presentation-only conditional zebra formatting
may be preserved. ANALYTICAL formulas for official metrics/bases/significance are
prohibited. UNKNOWN formulas require human classification before Master adoption.
No external-link creation, DDE, dynamic formula interpolation or arbitrary macros.
Navigation/filter/banner interaction selects precomputed canonical slices only.

## VBA and backend preservation

Input/output must be genuine .xlsm with macro-enabled content types and intact
vbaProject.bin, byte-identical binary/module payloads, relevant relationships,
controls, defined names, sheet identities, table metadata and required structures.
Inventory package parts, content types, relationships and ownership before writing.
Compare preserved-part hashes and normalized structures afterward; detect missing
parts, lost modules, broken references or changed signature-bearing content.
A signed artifact requires verification that the chosen workflow retains its
signature; an unverified signature path blocks release. Do not invoke VBA in QA.

Current exporters use pandas/XlsxWriter to create fresh .xlsx, not preserve Master.
XlsxWriter cannot read/modify an existing workbook; embedding an extracted VBA
binary in a new file is not proof of template preservation.
See https://xlsxwriter.readthedocs.io/faq.html and
https://xlsxwriter.readthedocs.io/working_with_macros.html.
openpyxl keep_vba is not sufficient blanket certification; its documented load/save
limitations include shapes: https://openpyxl.readthedocs.io/en/stable/tutorial.html.
Neither library is approved here. Native Excel automation or targeted OOXML edits
also need fixture-based preservation proof. Backend remains GAP.
Inability to inspect or preserve ANY required component is fatal, never a warning
that allows a silently degraded workbook. No macro-free fallback.

