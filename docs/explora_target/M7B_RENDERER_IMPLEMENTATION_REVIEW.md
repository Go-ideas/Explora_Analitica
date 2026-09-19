# Gate 37 M7B Renderer Implementation Review

Starting main: d74ba842bc05be1ef327047cbfa72ebbbc2e6f8c.
Branch: feature/m7b-renderer-implementation.
Implementation identity: the commit containing this review; resolve with Git.
Status: implementation validation passed; awaiting independent review.
No push, PR, merge or later milestone is authorized by this implementation.

## Implemented boundary

CanonicalResult -> validated RenderRequest -> immutable deterministic RenderPlan
-> explicit released Master slots -> bounded worksheet OOXML mutation
-> structural/readback QA -> publication of a new XLSM.

The renderer uses existing canonical validation, serialization and fingerprint
APIs. It snapshots nested source data and checks canonical result/request/release
identity before rendering. Configuration and Master ReleaseMetadata must be
valid and checksum-pinned. No legacy analytical adapter, statistic, formula
evaluation, significance producer, COM automation or VBA-project modification
is introduced. M2-M6 and the frozen Gate 35/36 documents are unchanged.

The public typed API is in explora_web_reporter/src/excel_renderer. Call
plan_render(request, master_path) before render(request, master_path,
output_path, plan=plan). The writer recomputes the plan against a verified
Master snapshot and refuses incomplete/tampered plans or an existing output.
The source and output paths are caller inputs, never hardcoded dependencies.

## Mapping and numerical safety

Physical sheet names are resolved from the released role registry. Configuration
rows and table columns are read from the explicitly declared table bounds;
defined names must resolve to exactly one cell. Numeric and literal slots,
status sidecars and label targets must already be declared and materialized.
No coordinate guessing, closest-cell fallback or table growth is performed.

Example: value identity -> estimate -> official_value -> RendererSlot ->
presentation!B2 -> numeric 0.5 -> frozen PROPORTION format 0.0%.
The scalar remains 0.5. No percentage is calculated. Labels are literal Visual
Spec text or a technical canonical ID accompanied by TECHNICAL_ID_LABEL.

Numeric storage is explicitly exact_numeric or exact_text. Numeric publication
requires the frozen digit/magnitude limits and exact scalar/type readback.
Formatting is preapproved Master formatting, not analytical rounding. Null and
non-OK fields stay blank with status sidecars, never zero. Negative zero,
denormal floating-point values and precision-as-displayed Masters fail closed.
These additional guards reflect documented Excel limitations:
[Excel floating-point behavior](https://learn.microsoft.com/en-us/troubleshoot/microsoft-365-apps/excel/floating-point-arithmetic-inaccurate-result),
[Excel specifications](https://support.microsoft.com/en-us/excel/excel-specifications-and-limits).
Explicit exact_text keeps the canonical serialized scalar and a visible mode
annotation; there is no automatic precision fallback.

All structured canonical records have separate audit columns containing exact
serialized JSON text. This protected audit representation is not an Excel
numeric authority. Complete canonical JSON is additionally transported in
ordered bounded chunks with encoding, total length and checksum. Unused declared
audit body cells are cleared, preventing stale results. Presentation lifecycle
records use ALL_RUNS/stale IDs, not fabricated canonical analytical identities.

Supplied significance envelopes are pinned by checksum and checked against the
canonical run, comparison, family/test/direction and target value/slice/member.
Tokens are literal transport only, scoped by envelope/comparison/value; a reused
symbol is not a universal comparison identity. Non-significant and other
non-eligible states cannot acquire significance through presentation. Missing
required tokens fail; otherwise LETTER_DISPLAY_UNSUPPORTED is recorded.

## Package preservation

Gate 36 inspect_package is reused for package certification. The batch writer
extends the certified targeted lxml/ZIP approach to explicitly bounded existing
cells; new focused tests certify this extension, not merely the older single-cell
helper. lxml==6.0.0 is pinned as the namespace-preserving backend.

No whole-workbook rewrite occurs in production. Existing styles, target
attributes, formulas, relationships, tables/names and undeclared content are
preserved. Untouched package parts are byte-identical. Edited sheets undergo
canonical XML comparison allowing only declared cell content/type changes.
Every planned scalar, literal type and format is read back. VBA must match
exactly. A temporary stage is hard-linked to a new destination only after PASS;
an existing or racing destination is never overwritten.

## Authorized generic fixture

Test infrastructure:
explora_web_reporter/tests/fixtures/m7b/generic_macro_renderer_fixture.xlsm.

XLSM SHA256:
846fc71ae54e02a99a8278f662dcc15584c1e4575030398ddb4825363471bc06.
VBA SHA256:
0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758.
Gate 36 generic.xlsx seed SHA256:
3517fc1a052296bbba935344d94d84f10178174e78e33dd91c57ef23430df6e4.

Independent checks verified hashes, CRC, unique ZIP members, macro content type,
OLE VBA and workbook relationship, the 11 generic sheets, named slots and Gate 36
interface. Seed parts match exactly except macro content types/relationship;
only the VBA part was added. No customer workbook or VBA was used.

Static source inspection using isolated oletools 0.60.2 found Module1.say_hello
with a generic message box; other modules contain attributes only. No executable
auto-event source was found. No macros were executed. This is not compiled
p-code security certification. Human authorization identifies the official
XlsxWriter sample origin; the exact upstream revision is unavailable and the
current upstream binary has a different hash. Do not claim current-upstream
byte identity. The accepted supplied hash, extracted source and BSD license
are retained. Companion provenance JSON was absent and was transparently
reconstructed from authorization plus independent checks.

The original fixture is committed unchanged. build_test_master constructs a
generic capacity-expanded declared-interface test Master using openpyxl only
in test infrastructure, preserving its VBA. Render certification runs on that
approved test Master. Neither fixture is a Production Master. Test preparation
is not a production writer or customer-template conversion.

## Evidence and scope limits

scripts/gate37_review_evidence.py creates external portable plan/QA evidence
and removes generic runtime workbooks afterward. Machine evidence is summarized
in M7B_RENDERER_IMPLEMENTATION_EVIDENCE.json after final validation. Determinism
means identical canonical/configuration/token and controlled Master bytes;
separately generated test Masters can have different creation timestamps.

Bounded implementation: preallocated cells/tables, the eleven registered roles,
frozen numeric profiles and explicit upstream tokens. Signed packages, chart
generation, table growth, arbitrary formulas, optional missing-source rendering,
suppression/style overrides and an invariant-display-text slot adapter are not
implemented. Unsupported declarations fail closed. The invariant half-even
helper is tested, but numeric Excel glyphs remain viewer-local presentation.
Production Master qualification, broad metric/project coverage and later M7
certification are not asserted. No genuine frozen-contract gap was established.

Files added: renderer package; M7B test helper and focused tests; the four generic
fixture/provenance/source/license materials; external review-evidence generator;
this review and its machine evidence. File modified: requirements.txt only.
No Core, runtime default, program-state or frozen contract modifications.

## Validation

Final acceptance: focused M7B 103 passed / 0 failed / 0 skipped (100-case
focused run plus three focused provenance-reference cases, all included in the
final full run); Gate 36 and canonical/runtime regression 260 passed / 0 failed /
0 skipped; full regression 751 passed / 0 failed / 0 skipped. No unexpected
numerical delta was detected. Results are recorded in the accompanying machine
evidence.
Early local iterations corrected renderer/test defects before acceptance; those
iterations are not represented as accepted regression passes.
