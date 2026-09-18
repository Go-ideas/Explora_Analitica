# M7 Excel Backend Decision V1

Gate 36, 2026-09-17. Decision: NOT CERTIFIED. Canonical backend: NONE.
No dependencies introduced; no frozen Gate 35 semantics changed.

| Candidate / observed version | Mechanism | Certification limitation |
| --- | --- | --- |
| openpyxl 3.1.5 | load_workbook(keep_vba=True), save .xlsm | no genuine fixture round-trip; unsupported shapes/control fidelity not certified |
| XlsxWriter 3.2.5 | new workbook with supplied add_vba_project binary | cannot load/modify existing Master; recreating structure is not preservation |
| pandas 2.2.3 | engine wrapper | not an independent VBA-preservation backend |
| Native Excel 16.0 / win32com available | native read/save macro-enabled workbook | genuine fixture absent; VBProject access blocked; structures/security still need proof |
| targeted OOXML via standard ZIP/XML tooling | preserve untouched parts and edit declared nodes | no audited manipulation helper/fixture; relationships/signatures need validation |

openpyxl may retain cell formulas with data_only=False and names/tables, but
preservation of the full required Master package is not demonstrated. keep_vba=False
must be rejected in a future guarded helper. XlsxWriter can author formulas/names/
tables/styles, not preserve an existing workbook by reading it.
Native Excel could preserve a supplied macro-bearing source without VBProject
authoring access; this possibility is NOT disproved by the security probe, but
cannot be certified without the source artifact and required negative tests.
No capability above constitutes successful certification.

Official capability references already identified by adopted contracts:
https://openpyxl.readthedocs.io/en/stable/tutorial.html
https://xlsxwriter.readthedocs.io/faq.html
https://xlsxwriter.readthedocs.io/working_with_macros.html
Installed versions recorded by importlib.metadata; win32com module discovered
through importlib.util.find_spec. oletools not installed.
Exact pywin32 distribution version is recorded in the Gate assessment evidence.

Future selection must pin a tested backend/version/configuration, prove guarded
invocation and scoped preservation, and inventory unsupported Master features.
No subjective default backend or dependency addition is justified while blocked.
G-M7-04 remains OPEN. Supply a controlled fixture first, then compare viable
backends with exact binary and normalized package/structure evidence.
