# M7 Prerequisite Contracts Gate Assessment

Date: 2026-09-17. Gate 35: contract definition only.
Authoritative starting main: 8c2a61d9b921c9cc26c28b5afd33541aabc5976c.
Branch: docs/m7-prerequisite-contracts-v1. No implementation authorization.
This is the current Gate 35 decision/gap register; adopted M7A documents remain
historical evidence, not a second live register. FROZEN means normative V1
documentation under this authorization, not merged adoption or runtime delivery.

## Audit evidence

Source root: explora_web_reporter.
- src/export/excel_exporter.py: fresh pandas/XlsxWriter XLSX; label-classified
  percentage scaling and presentation-only zebra conditional formula.
- src/export/report_exporter.py: Legacy ReportResult writer/metadata adapter,
  not an official CanonicalResult consumer.
- src/export/pivot_exporter.py: respondent long-data preparation, not canonical
  workbook tables or an implemented Excel PivotTable interface.
- src/export/project_exporter.py: ZIP, technical XLSX and HTML packaging.
- src/export/datamap_exporter.py and src/ui/page_02_datamap_review.py:
  metadata/review workbooks created fresh via XlsxWriter, not a Master interface.
- src/ui/page_06_export.py and src/web_canonical/export.py: canonical CSV release
  path versus Legacy XLSX paths; no M7 renderer abstraction.
- requirements.txt: pandas/openpyxl/xlsxwriter; observed environment versions
  2.2.3 / 3.1.5 / 3.2.5 respectively; unpinned dependencies are not a backend guarantee.
- tests/test_project_exports.py: existing Legacy export fixtures and packaging.
  Canonical contracts/results/identity tests exist separately; no physical
  macro-preservation conformance fixture or executable Visual Spec V1 was found.
  Other relevant tests: test_commercial_excel_exports.py,
  test_reporter_metadata.py and test_canonical_results_significance_transport.py.
  Physical checkout search for .xlsx/.xltx/.xltm found no workbook/template files;
  current tests construct temporary workbooks rather than adopt a controlled Master.
- src/contracts/models.py and vocabulary.py: exact canonical fields/statuses.
  src/analytics_core serialization/results/result_identity: source serialization,
  validation/release and identity authority, not workbook semantics.
- Existing canonical materialization/adapter support is bounded by released
  upstream structures/dispatch. Generic project coverage is not established by BA.

Physical search scope: checkout and surrounding Explora Analitica workspace,
including hidden/ignored files except .git/.venv/node_modules; rg file search for
*.xlsm, *.bas, *.cls and Visual-like paths yielded no artifact matches.
MASTER PHYSICAL ARTIFACT = NOT FOUND. Version/location/checksum unavailable.
This does not claim absence on other machines or inside uninspected archives.

In-memory unchanged Legacy export probes: normal inspected report/project exports
had no cell formulas; conditional formatting used MOD(ROW(),2)=0.
Synthetic external label =1+1 became a formula in the current writer.
This is a literal-safety gap, not evidence of official analytical recomputation.
No workbook or production writer was changed to remediate it.
No reusable Master/VBA-preserving load/save path was found. Packaging and
filename-safety primitives are reusable; layouts/formats need adaptation;
Legacy ReportResult and BD_Pivot stay Legacy-only.

## Current decision and gap register

| ID | Gate 35 disposition | Remaining delivery requirement |
| --- | --- | --- |
| G-M7-01 | RESOLVED CONTRACTUALLY: Visual Spec V1 frozen | validator/renderer unimplemented |
| G-M7-02 | RESOLVED CONTRACTUALLY: semantic Master interface frozen | physical artifact conformance/adoption |
| G-M7-03 | OPEN: Master NOT FOUND / NOT ADOPTED | obtain controlled artifact and manifest |
| G-M7-04 | OPEN BACKEND GAP; preservation/fail-closed contract frozen | backend selection and preservation fixtures |
| G-M7-05 | RESOLVED CONTRACTUALLY: exact storage/display profile frozen | numeric round-trip backend certification |
| G-M7-06 | RESOLVED CONTRACTUALLY: field/role mapping frozen | canonical workbook integration |
| G-M7-07 | RESOLVED CONTRACTUALLY: supplied-token interface frozen | authorized token producer/envelope if letters required |

No new source schema, enum, statistical policy or runtime selection is introduced.
Literal/formula policy, provenance and determinism are frozen in the Master and
mapping contracts. No physical Master conformance is inferred from documentation.
Existing M7A field proposals are superseded for current Gate 35 decisions by these
V1 contracts, without retrospective modification of adopted evidence.

## Acceptance matrix

| Criterion | Result / normative evidence |
| --- | --- |
| G35-01 | PASS: Visual Spec V1 declarative source bindings, no statistical DSL |
| G35-02 | PASS: numeric profile separates authority/storage/display |
| G35-03 | PASS: frozen precision, exact modes, formats and missing states |
| G35-04 | PASS: Master semantic registry, no project hardcoding |
| G35-05 | PASS: explicit ownership/mutation/atomic publication |
| G35-06 | PASS: preservation inventory/hash proof, inability fails closed |
| G35-07 | PASS: scoped physical search establishes NOT FOUND |
| G35-08 | PASS: mapping covers canonical fields/roles and structural identity |
| G35-09 | PASS: significance transport and supplied-token-only policy |
| G35-10 | PASS: null/unsupported/suppressed/absent separate sidecars |
| G35-11 | PASS: literal writes; no newly authored formulas V1 |
| G35-12 | PASS: provenance pinned to available actual inputs |
| G35-13 | PASS: normalized exact-content determinism oracle |
| G35-14 | PASS: BA and generic future fixture plan below |
| G35-15 | PASS: documentation-only diff, M2-M6 unchanged |
| G35-16 | PASS: M7B/Master/VBA not implemented |
| G35-17 | PASS: authoritative suite 602 passed / 0 failed / 0 skipped |

## Future fixture plan (definitions, not implemented tests)

Benchmark A: accepted BA-01 through BA-05 canonical results; 40/4/4/40/6 records,
94/94 accepted Legacy/Canonical exact parity. BA-03 preserves MENTION / PARENT_RM /
STR_Q_DELIVERY_APPS_RM_V1 identity; no universal assumptions from these IDs.
Accepted external source FUNSMX_297140_20260914.sav SHA256:
71b8cc2843c1c65a92d7f18fe631ea3aad4cbd47bc936ec28c205bac8d0dbb2f.
Release package BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1_0_1.zip:
78afa38484dc4b27fdd0ab5c3f8f2b80b2b49cabc67a57361b94beb591685a41.
Real evidence remains external under _gate19_inputs/benchmark_a; no client data
or workbook was imported. Gate 32 and Gate 19 accepted evidence demonstrate
analytical parity, not Excel preservation/rendering correctness.

| Future fixture | Required oracle |
| --- | --- |
| Simple frequency, zero and nonzero | exact source values, COUNT/PROPORTION formats, no recalculation |
| Banner and filtered slices | exact slice/member/filter IDs; navigation selects existing results |
| Weighted / unweighted | separate supplied base fields/weight ref, no substitution |
| Significance available | exact relationships, authorized supplied tokens/legend |
| Significance unsupported / absent | distinct source status and letter-display annotation |
| Null / suppressed / not computed | no zero coercion, separate status and suppression authority |
| Unsafe labels/config/tokens | =,+,-,@ and prefixed variants remain exact text, no formula/link nodes |
| RM/multiselect | mention/respondent denominator scope identity unchanged |
| Grid/Loop supported upstream | axes preserved, no inference of unsupported execution |
| Provenance and long payload | exact chunk reassembly, all required pinned versions |
| Numeric precision edge | exact readback, explicit exact_text, rejection of unsafe numeric mode |
| Controlled macro Master | binary/module/relationship/style/control preservation or fail closed |
| Repeat/update render | normalized determinism, no stale cells, user/Master areas unchanged |

Use schema-valid supplied canonical fixtures; unsupported upstream scenarios stay
unsupported. If a fixture requires new analytics, request separate Core authority,
not renderer remediation. No generic coverage claim is made until tests execute.

## Closure

Gate 35 can pass contract acceptance with the explicitly permitted backend gap and
proven Master absence. M7B READY = NO: physical Master adoption/backend proof remain
open; a separate implementation authorization is still mandatory.
No M7B/M7C/M7D, productive VBA, new workbook or Excel analytical calculations.
Regression command from explora_web_reporter:
`python -m pytest --basetemp C:\Users\conta\g35_temp\full --junitxml C:\Users\conta\g35_temp\full.xml`.
Result: 602 passed / 0 failed / 0 skipped, exit 0, 40.17 seconds.
External JUnit: C:/Users/conta/g35_temp/full.xml. No unexpected skips.
All existing parity/identity/transport tests passed; no numerical deltas were
detected by those tests. This is not a claim of future Excel rendering parity.

Closure status: Gate 35 PASS (contract-definition scope only).
Final scope: six new V1/assessment documents and current program-state update.
No source/test changes, commits, push, PR, merge or physical workbook creation.
HEAD remains the authoritative starting SHA. Worktree is intentionally not clean:
only the seven authorized documentation changes are uncommitted.
Contract-stage blockers: NONE. Delivery warnings: G-M7-03 physical Master,
G-M7-04 backend certification, generic coverage unproven, literal safety not
implemented in Legacy writers and token producer absent if letter output is needed.
Current register above is the sole live disposition of these gaps.
