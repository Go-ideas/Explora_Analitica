# M7 Excel Renderer Current State

Date: 2026-09-17. Phase: M7A audit only. Status: PASS for current-state
analysis, not implementation or release approval. Human current-state review:
PASS. Human contract review: PASS WITH REQUIRED CLOSURE; M7-01 through M7-10
are incorporated in the companion contract. Closure adds documentation only.
Authoritative starting main: `0fe9caf1f7d9b942035403b28a89672eb92baf37`.
Local branch: `docs/m7-excel-renderer-contract`; starting worktree: clean.

## Evidence And Search Boundary

Source links below are relative to this document. Inspection covered the six
requested export/UI files, Core results/serialization/identity/execution adapter,
every file in canonical_materialization, and the applicable tests. Accepted M5
results and execution-adapter documents, M6 contract and V3 remediation,
materialization review, Gate 19 review and Gate 32 review were read as historical
evidence, not rewritten as current approvals. Gate 33 user authorization supplies
the accepted program state and permits only M7A.

`rg --files --hidden --no-ignore` searched the checkout and surrounding
`C:/Users/conta/Go ideas/Local Go ideas - Documentos/Desarrollo/Explora Analitica`
workspace for `.xlsm`, `.bas`, `.cls` and visual-named files (excluding Git,
virtualenv and node_modules internals). No matches. This does not prove that a
Master exists nowhere else or inside an unexamined archive. An external artifact
must be supplied explicitly if one exists.

## What The Existing Exporters Do

| Component / evidence | Actual behavior | Classification |
| --- | --- | --- |
| [excel_exporter.py](../../explora_web_reporter/src/export/excel_exporter.py), export_revision_excel | Creates fresh revision XLSX: row-count summary, BD_Pivot, respondent/question/variable/option tables, sampled long tables (5,000-row cap), risks, structures, dashboard config, factors and recommendations | LEGACY ONLY / technical audit |
| Same file, export_report_table_to_excel and write_executive_report_sheet | Writes supplied wide DataFrame to Tabla, configuration, optional significance and notes; grouped headers, widths, formats, letter placement, freeze panes and zebra rows | REUSE WITH ADAPTATION for styling, not authority |
| [pivot_exporter.py](../../explora_web_reporter/src/export/pivot_exporter.py) | Reconstructs respondent-level rows from respuestas_long, RM, scales and open text; attaches respondent banners and first two configured filters. BD_Pivot is a data sheet, not an Excel PivotTable | LEGACY ONLY |
| [report_exporter.py](../../explora_web_reporter/src/export/report_exporter.py) | Consumes Legacy ReportResult.table, base, notes, significance/legend and display settings; writes one or multiple fresh XLSX sheets | REPLACE official input adapter; adapt presentation helpers |
| [project_exporter.py](../../explora_web_reporter/src/export/project_exporter.py) | ZIP packaging of those XLSX reports, Plotly HTML and technical files; saved ReportResult exports | REUSE packaging with canonical manifest adaptation; existing report paths LEGACY ONLY |
| [page_06_export.py](../../explora_web_reporter/src/ui/page_06_export.py) | Canonical projection branch downloads official or internal-QA CSV; otherwise current/saved Legacy reports use XLSX/ZIP. Technical downloads remain separate | Existing Web integration; NOT an Excel dependency |
| [web_canonical/export.py](../../explora_web_reporter/src/web_canonical/export.py) | Serializes CanonicalWebProjection.table to CSV, preserving official/internal path distinction and release fields | Reference only; M7 must not consume Web projection |

No exporter evaluates metric formulas, applies weights, derives official
denominators, or runs significance tests. Revision row counts are technical
inventory counts, not official analytical bases. Pivot reconstruction emits RM
`valor=1`, takes existing weights as row attributes and resolves duplicate
respondent attributes with keep-first. It is raw-data preparation, not a
CanonicalResult renderer; using it for Excel-side statistics would violate M7.

However, existing display code is not numerically identity-neutral:
`_excel_percentage_values` divides label-classified percentage columns by 100;
`_write_report_cells` divides Valor rows containing top2box/bottombox by 100.
Header parsing uses ` | ` and numeric-code stripping. These are Legacy display
conventions, not canonical metric/structure authority. They must not be applied
blindly to canonical proportions. `_report_config` also uses truthy defaults
(`base_before_filters or base`, `min_base or 'No aplica'`), which cannot establish
faithful zero/status transport. No changes to these paths were made.

## Structure, Bases, Warnings And Significance

The low-level writer accepts any supplied tabular shape, not a released list of
question structures. Revision exports contain RU/RM, scales, open text and a
Grid/Loop sample sheet; the pivot builder does not directly consume that Grid/Loop
table. Rendering a DataFrame proves no canonical GRID/LOOP compatibility.
Existing project tests demonstrate RU wide reports and integrated/separate
significance; layout tests demonstrate supplied multi-metric tables.

Bases are exported as ReportResult.base/configuration and existing table content.
There is no identity-linked CanonicalBase transport, weighted-base/effective-n
contract or release-aware Excel QA envelope. Notes are transported, and revision
risks are exported, but comprehensive QAEvent/QAIssue warning transport is NOT
FOUND. Significance letters/legend and separate tables are supplied by Legacy;
the writer does not test significance. No canonical significance-to-Excel mapping
or Core-issued letter-token input contract is implemented.

## Libraries And Macro Safety

requirements.txt declares pandas, openpyxl and xlsxwriter without version pins.
Observed audit environment: pandas 2.2.3, XlsxWriter 3.2.5, openpyxl 3.1.5.
Writers use pandas.ExcelWriter(engine='xlsxwriter'); openpyxl is used for
reading and test inspection. No keep_vba/template-copy/VBA-preservation path
was found in production exports. No production VBA source was found.

XlsxWriter cannot read or modify an existing workbook; embedding an extracted VBA
binary in a newly created file is a different capability, not safe preservation
of a full Master. See [official FAQ](https://xlsxwriter.readthedocs.io/faq.html)
and [macro documentation](https://xlsxwriter.readthedocs.io/working_with_macros.html).
openpyxl documents keep_vba preservation but warns that unrecognized shapes can
be lost during load/save. See [official tutorial](https://openpyxl.readthedocs.io/en/stable/tutorial.html).
Thus safe Master round-trip preservation is UNKNOWN / NOT DEMONSTRATED, not
guaranteed by having either dependency installed.

MASTER XLSM = NOT FOUND within the searched scope.
Version, location, checksum, sheets, named ranges/tables, macros and configuration
contract: UNKNOWN / unavailable because no Master artifact was found.
No productive Master was created to fill this gap.

VISUAL SPEC RUNTIME CONTRACT = GAP. No VisualSpec class, executable validator,
released schema or runtime visual_spec selection was found in src. Conceptual
Visual Spec references in M5/target documents and hardcoded styles are not a
released executable contract. A new renderer-side contract requires human review.

## Workbook Formula Inspection

An in-memory probe used the unchanged tests/test_project_exports.py `_report`
fixture and existing single/combined writers, inspecting OOXML with ZipFile and
ElementTree (no workbook saved in the repo):

| Probe | Cell formulas | Conditional formatting formulas | Classification |
| --- | --- | --- | --- |
| Normal single report | NONE | MOD(ROW(),2)=0 | PRESENTATION_ONLY |
| Normal combined report | NONE | MOD(ROW(),2)=0 | PRESENTATION_ONLY |
| Synthetic response label '=1+1' | 1+1 | MOD(ROW(),2)=0 | UNKNOWN / untrusted formula injection; arithmetic but not an official Core metric |

No VBA project was present in these generated XLSX packages. The only intentional
formula found in source exports is zebra formatting. Generic worksheet.write
and pandas export allow formula-like source strings to become formulas; therefore
arbitrary input formula absence is NOT guaranteed. No intentional official
analytical Excel formula was found. The future renderer must write source text
literally and reject official numeric formula cells. This is an M7 gap, not a
remediation authorization or a newly introduced upstream regression. Human M7-06
freezes literal handling for all label/note/warning/metadata/config/project text,
including leading =,+,-,@, as mandatory future implementation/QA. M7-07 prohibits
official ANALYTICAL formulas and requires UNKNOWN formulas to fail review.

## Hardcoding And Upstream Capability Limits

No Benchmark A/client/question IDs were found in src/export. There are fixed
sheet names, two technical filter slots, Spanish heading conventions, metric-label
heuristics and colors/layouts. These are presentation/Legacy conventions, not
approved canonical semantics.

The audit also observed EXISTING upstream project-shaped assumptions:
canonical_materialization/orchestrator.py `_question_spec` assigns
`universe_ref='U_BENCHMARK_ELIGIBLE_V1'`, and materializer validates historical
package flags including default_execution_mode=LEGACY. The latter is released
package metadata, not the live Canonical default. These frozen paths are not
modified or generalized by M7A; generic project coverage is NOT established by
Benchmark A acceptance. A future demand needing upstream changes must return to
Core/human authorization, not be patched in Excel.

Execution adapter `_execute_metric` dispatches existing RU-family count,
proportion/top/bottom and RM respondent/mention paths; formula aliases for means,
SD and NPS do not alone establish dispatch support. It transports supplied
SignificanceRelation comparisons but does not implement B2 tests here. M7 may
render only eligible results actually provided; it cannot enable missing metrics,
weighted execution or statistical families itself.

## Reuse Decision

REUSE: filename/sheet-name safety ideas, ZIP packaging primitives and formatting
patterns after their own identity/text-safety checks.
REUSE WITH ADAPTATION: widths, borders, number formats, grouped headers, existing
note/significance display and packaging manifests; remove label-based authority
and percentage rescaling for canonical input.
LEGACY ONLY: ReportResult report/saved-report input paths, technical revision,
raw BD_Pivot reconstruction and Datamap review exports.
REPLACE: official canonical input validation/mapping, identity-linked workbook
records, template writer, release/provenance/QA integration. These are future
requirements; no replacement code was introduced.

## Validation Evidence

Commands ran from explora_web_reporter with python -m pytest and controlled
external basetemp C:/Users/conta/m7a_temp/{focused,full}. JUnit reports remain
external at C:/Users/conta/m7a_temp/{focused,full}.xml. After closure edits, the
same unchanged-code suites are rerun with new evidence under
C:/Users/conta/m7a_temp/closure/{focused,full}.xml and separate external basetemp.

Focused selection: commercial_excel_exports (3), pivot_exporter (1),
project_exports (4), multi_metrics_layout (3), m6_release_export_remediation (4),
contract_canonical_result (3), contract_renderer_neutrality (2),
canonical_results_serialization (10), canonical_results_identity (11),
canonical_results_significance_transport (5), canonical_results_qa_release (10),
canonical_default_switch (17), canonical_default_switch_benchmark_a (9).

| Scope | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Excel/export focused (first five modules) | 15 | 0 | 0 |
| Canonical contract/identity/transport focused (next six modules) | 41 | 0 | 0 |
| Gate 32 focused (last two modules) | 26 | 0 | 0 |
| Combined focused | 82 | 0 | 0 |
| Full regression | 602 | 0 | 0 |

No tests were edited, removed or weakened. The full count remains the accepted
602 baseline. Unexpected skips/numerical deltas: NONE detected. Benchmark A
focused tests retain 94/94 exact parity, BA-03 scope and repeated determinism.
Full regression exercises all existing accepted paths, not a new Excel renderer.
An initial inline probe had a PowerShell quoting/SyntaxError; it was rerun
successfully through stdin without changing any source or test.

## Gaps And Review Readiness

M7A can complete with these explicit gaps: absent Master; absent Visual Spec
runtime schema; unproved macro/control preservation; no canonical Excel mapping;
no Core-issued significance-letter contract; exact Excel numeric representation
limits; unproved generic project/metric coverage. No M7A blocker remains.
All implementation/release gaps are carried to the contract/scope manifest and
require decisions before the relevant later phase. No M2-M6 semantics changed.
