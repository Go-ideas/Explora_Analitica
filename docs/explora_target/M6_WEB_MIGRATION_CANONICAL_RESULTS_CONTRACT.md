# M6 — WEB MIGRATION TO CANONICAL RESULTS CONTRACT

Estado de entrada:

- M1A-F: PASS
- M2 — Universe Execution: CLOSED / ACCEPTED
- M3 — Weight Hardening: CLOSED / ACCEPTED — PASS WITH WARNINGS
- M4 — RM / GRID Authority: CLOSED / ACCEPTED — PASS WITH WARNINGS
- M5 — Canonical Results: CLOSED / ACCEPTED — PASS WITH WARNINGS
- B1 — Weight Methodology: HUMAN APPROVED / CANONICAL
- B2 — Significance Policy: HUMAN APPROVED / CANONICAL
- B3 — AI Auto-Release Policy: HUMAN APPROVED / CANONICAL
- `CanonicalResult` es la autoridad analítica renderer-neutral
- `ReportResult` continúa siendo Legacy / presentation-oriented
- `LEGACY` continúa como default productivo

Checkpoint canónico M5:

`M5_CANONICAL_RESULTS_ORDERING_REMEDIATED_V2_2026-09-14.zip`

SHA-256:

`BD6F776FCC3C5BBC253BB765D1CEB7686B92C27076463D23769F4EEC7A540C7F`

M6 todavía NO está autorizado para implementación.

Este chat tiene una sola responsabilidad:

**definir y cerrar el contrato de M6 — Web Migration to Canonical Results antes de permitir trabajo en Codex.**

NO desarrollar código.

NO modificar M2.

NO modificar M3.

NO modificar M4.

NO modificar M5.

NO modificar B1/B2/B3.

NO iniciar Excel.

NO modificar EXPLORA NG.

NO rediseñar SQLite productivo.

NO iniciar M7.

==================================================
1. OBJETIVO DE M6
==================================================

Migrar progresivamente Explora Web para que deje de utilizar cálculos renderer-side como autoridad analítica y pase a consumir:

`CanonicalResult`

producido por M5.

Target:

Released Specs
→ M2 Universe
→ M4 Structure / denominators
→ M3 Weight
→ B2 Significance
→ M5 Canonical Results
→ M6 Web Renderer

Web podrá:

- seleccionar vistas;
- ordenar;
- pivotear;
- añadir labels;
- formatear;
- construir tablas;
- construir charts;
- presentar QA;
- presentar significance;
- gestionar interacción de usuario.

Web NO podrá recalcular analytical truth.

==================================================
2. PRINCIPIO DE AUTORIDAD
==================================================

Congelar:

`CanonicalResult = analytical authority`

`Web = renderer / interaction layer`

Web NO puede recalcular:

- Universe;
- applicability;
- denominator membership;
- weights;
- weighted bases;
- percentages;
- proportions;
- means;
- standard deviation;
- Top/Bottom Box;
- NPS;
- scores;
- significance;
- QA decisions;
- release decisions.

Si un valor analítico no existe en CanonicalResult:

Web no lo infiere.

Debe solicitar una nueva ejecución válida al Core.

==================================================
3. LEGACY TRANSITION MODEL
==================================================

Al inicio de M6:

`LEGACY = default`

Definir explícitamente modos equivalentes a:

`LEGACY`

`CANONICAL_V1`

`DUAL_RUN`

Determinar:

- quién selecciona el modo;
- cómo se identifica el modo en runtime;
- cómo se evita mezclar modos;
- cómo se registra provenance;
- cómo se vuelve a Legacy ante rollback.

Ningún cambio de default queda autorizado por el contrato M6 por sí solo.

==================================================
4. NO MIXED ANALYTICAL TRUTH
==================================================

Un output oficial no puede mezclar silenciosamente:

algunas celdas Legacy

+

algunas celdas Canonical.

Cada ejecución/vista debe tener autoridad analítica inequívoca.

Si un valor Canonical no está disponible:

no completar esa celda con Legacy dentro del mismo resultado Canonical.

Debe existir:

- structured unsupported/error;
o
- ejecución Legacy separada y explícita.

==================================================
5. CURRENT WEB INVENTORY
==================================================

Auditar conceptualmente el Web actual y clasificar funciones actuales en:

`RENDERER ONLY`

`LEGACY ANALYTICAL`

`MUST MIGRATE TO CANONICAL`

`COMPATIBILITY ONLY`

`OUT OF SCOPE`

Revisar específicamente cualquier lógica actual relacionada con:

- totals;
- banners;
- filters;
- bases;
- percentages;
- proportions;
- means;
- scores;
- NPS;
- weights;
- effective N;
- significance;
- letters;
- RU;
- RM;
- Grid;
- Loop;
- warnings;
- summaries;
- exports;
- cache/session state.

==================================================
6. CANONICAL WEB ADAPTER
==================================================

Definir un adapter único:

`CanonicalResult`
→
`Web projection / presentation model`

El adapter puede:

- seleccionar records;
- pivotear long → wide;
- ordenar;
- unir labels;
- generar display metadata;
- agrupar QA;
- generar presentation tokens.

El adapter NO puede:

- recalcular `estimate`;
- reconstruir denominator;
- recalcular base;
- recalcular weight;
- ejecutar significance;
- modificar ValueStatus;
- modificar release state.

==================================================
7. REPORTRESULT BOUNDARY
==================================================

Congelar relación:

`CanonicalResult`
→ Web adapter
→ renderer-friendly object

`ReportResult` puede mantenerse temporalmente para compatibilidad Legacy.

Está prohibido:

`ReportResult.table`
→ reverse engineering
→ CanonicalResult

También está prohibido usar `ReportResult` como fuente analítica cuando execution mode sea `CANONICAL_V1`.

==================================================
8. SLICE CONTRACT
==================================================

Web debe consumir:

`slice_id`

producido por Canonical Results.

Debe utilizar identidad analítica estable para:

- Total;
- banner members;
- filtros;
- combinaciones de banners;
- combinaciones de filtros.

Labels son display metadata.

Web no debe reconstruir la identidad analítica a partir de texto como:

`CDMX - Hombres - 18-24`.

==================================================
9. FILTER CONTRACT
==================================================

Distinguir explícitamente:

M2 Universe

vs

user filters / view selection.

Los filtros interactivos Web pueden solicitar/seleccionar slices válidos.

No pueden convertirse en un segundo Universe engine.

Definir cuándo un cambio de filtro:

- reutiliza CanonicalResult existente;
o
- requiere una nueva ejecución Core.

==================================================
10. TOTAL / BANNERS
==================================================

Definir cómo Web renderiza:

- Total;
- banner dimensions;
- banner members;
- combinations.

Las bases y valores deben venir de CanonicalResult.

No reconstruir:

Total
ni banner calculations

desde raw dataframe dentro del renderer Canonical.

==================================================
11. BASE RENDERING CONTRACT
==================================================

Web consume CanonicalBase.

Debe poder presentar:

`unweighted_n`

`weighted_n_raw`

`weighted_n`

`effective_n`

según corresponda.

`effective_n` continúa siendo diagnóstico.

No debe mostrarse como base descriptiva normal salvo que la vista lo solicite explícitamente.

Web no deduce N desde:

percentage × total

ni desde otra métrica.

==================================================
12. DENOMINATOR UNIT
==================================================

Web debe respetar:

`denominator_unit`

`denominator_ref`

`denominator_scope_id`

Nunca deducir denominator semantics por:

- question type;
- chart;
- label;
- nombre de variable.

Especialmente:

RESPONDENT denominator

!=

MENTION denominator

aunque ambos tengan el mismo número.

==================================================
13. RU CONTRACT
==================================================

Definir rendering Canonical de RU para:

- count;
- proportion;
- mean/scale;
- standard deviation;
- Top/Bottom Box cuando exista;
- valid zero;
- NO_VALID_BASE;
- unsupported/ineligible/error.

Web no vuelve a clasificar:

VALID_CATEGORY
ORDINARY_MISSING
STRUCTURAL_MISSING
INVALID_OUT_OF_DOMAIN.

==================================================
14. RM CONTRACT
==================================================

Definir rendering separado para:

`RM_RESPONDENT_PROPORTION`

y:

`RM_MENTION_PROPORTION`

Web debe poder mostrar ambas sin mezclar bases.

No recalcular:

selected respondents
mentions
not-selected
duplicate policy
mention scope.

Todo proviene de M4/M5.

==================================================
15. GRID CONTRACT
==================================================

Definir consumo de:

GRID_ESCALA

GRID_RM

Preservando:

- structure_id;
- row/entity ID;
- column/option ID;
- denominator scope;
- applicability;
- bases;
- values.

Web no puede volver a inferir Grid desde nombres físicos de variables.

==================================================
16. LOOP CONTRACT
==================================================

Definir consumo de:

LOOP_RU

LOOP_RM

LOOP_NUMERICO

Preservando:

- entity_id;
- loop_instance_id;
- option/category;
- denominator scope;
- dependency metadata;
- bases;
- values.

No introducir:

LOOP_RANGO

si M4 no lo soporta.

==================================================
17. WEIGHT CONTRACT
==================================================

Web consume resultados ponderados producidos por Core/M5.

Prohibido en canonical mode:

`fillna(1)`

normalización

trimming

capping

weight imputation

recalcular Kish

reinterpretar zero/negative/missing weights.

Web sólo presenta:

values
bases
weight QA
provenance.

==================================================
18. VALUE STATUS RENDERING
==================================================

Definir presentación de:

`OK`

`NO_VALID_BASE`

`UNSUPPORTED`

`INELIGIBLE`

`ERROR`

Reglas mínimas:

`NO_VALID_BASE != 0%`

`UNSUPPORTED != blank`

`ERROR != 0`

valid zero:
`OK + estimate=0`

El renderer puede decidir texto/símbolo visual, pero no cambiar la semántica.

==================================================
19. SIGNIFICANCE RENDERING CONTRACT
==================================================

Web consume M5 SignificanceRelation.

No ejecuta tests estadísticos.

Puede generar presentation tokens como letras únicamente desde:

relaciones pairwise canónicas.

Las letras:

- no son analytical truth;
- no se almacenan como replacement de relations;
- no modifican p-values;
- no modifican decisions.

Confirmar:

`no letters != not significant`

==================================================
20. SIGNIFICANCE UNSUPPORTED
==================================================

Web debe distinguir:

NOT_REQUESTED

UNSUPPORTED

INELIGIBLE

TESTED_NOT_SIGNIFICANT

TESTED_SIGNIFICANT

Especialmente:

weighted significance = UNSUPPORTED V1

RM mention significance = UNSUPPORTED V1

NPS significance = UNSUPPORTED V1

No mostrar ausencia de letras como evidencia estadística.

==================================================
21. QA / WARNING CONTRACT
==================================================

Web consume:

`QAEvent`

Puede:

- agrupar;
- resumir;
- ordenar;
- mostrar;
- ocultar detalles detrás de un drill-down.

No puede cambiar:

- qa_domain;
- severity;
- blocking;
- code;
- release impact.

No crear un segundo warning engine paralelo.

==================================================
22. RELEASE STATE CONTRACT
==================================================

Web consume:

`computation_status`

`qa_release_status`

`releasable`

UI no puede convertir libremente:

`releasable = false`

a:

`true`.

Si existe posteriormente un flujo humano autorizado por B3:

debe ser explícito, trazable y fuera de una mutación silenciosa del CanonicalResult.

==================================================
23. CACHE CONTRACT
==================================================

Auditar cache/session state actual.

Definir identidad mínima de cache para canonical mode usando como corresponda:

`result_run_id`

`result_fingerprint`

`request_fingerprint`

`slice_id`

execution mode

schema version.

Evitar:

mostrar datos de run A

bajo filtros/selección del run B.

==================================================
24. SESSION STATE
==================================================

Definir qué elementos son:

presentation/session only

versus:

analytical request changes.

Ejemplos presentation-only:

- chart type;
- sort visual;
- expanded/collapsed panels.

Ejemplos que pueden requerir nueva ejecución:

- metric requested;
- weight override;
- filter fuera del CanonicalResult actual;
- banner config no existente en current run.

Cerrar esta frontera.

==================================================
25. EXPORT CONTRACT
==================================================

Definir exports de Web.

Export puede:

- pivotear;
- ordenar;
- aplicar labels;
- aplicar formatting.

No puede recalcular analytical truth.

Todo valor exportado debe rastrearse a:

`value_id`

`base_id`

y `result_run_id` cuando aplique.

M7 Excel Dashboard continúa fuera de scope.

==================================================
26. PRESENTATION ROUNDING
==================================================

M5 conserva full precision.

Web puede aplicar presentation rounding.

Definir:

- dónde ocurre;
- cómo se evita modificar canonical values;
- cómo se compara Legacy vs Canonical antes de rounding.

Comparaciones numéricas deben hacerse antes de presentation rounding.

==================================================
27. DUAL-RUN CONTRACT
==================================================

Definir ejecución:

LEGACY

vs

CANONICAL_V1

para la misma solicitud.

Comparación debe usar clasificaciones congeladas por M5:

PARITY

INTENDED_CORRECTION

M2_BASE_DIFFERENCE

M3_WEIGHT_DIFFERENCE

M4_STRUCTURE_DIFFERENCE

UNSUPPORTED_V1

POTENTIAL_REGRESSION

PRESENTATION_ONLY

Todo delta no explicado:

POTENTIAL_REGRESSION

y bloquea migración/default switch.

==================================================
28. DUAL-RUN GRAIN
==================================================

Definir cómo se empatan Legacy vs Canonical:

question

metric

slice/banner

row/entity

option/category

base

value

significance relation cuando aplique.

No empatar únicamente por labels.

==================================================
29. LEGACY PARITY
==================================================

No exigir parity donde exista una:

INTENDED_CORRECTION

M2_BASE_DIFFERENCE

M3_WEIGHT_DIFFERENCE

M4_STRUCTURE_DIFFERENCE

ya aprobada.

Pero ninguna diferencia puede quedar sin clasificación.

==================================================
30. FEATURE FLAG
==================================================

M6 debe introducir o utilizar un mecanismo explícito de selección.

Ejemplo conceptual:

`result_contract = reportresult_legacy`

`result_contract = canonical_v1`

`result_contract = dual_run`

No fijar el nombre técnico todavía si repository architecture recomienda otro.

Debe existir rollback explícito.

==================================================
31. DEFAULT MODE SWITCH CRITERIA
==================================================

Definir exactamente cuándo puede cambiarse:

`LEGACY = default`

a:

`CANONICAL_V1 = default`.

Recomendación mínima:

- M6 implementation PASS;
- M6 regression PASS;
- dual-run satisfactorio;
- cero unexplained deltas;
- scopes V1 cubiertos;
- rollback probado;
- cache/session probado;
- human approval explícita.

El cambio de default NO ocurre automáticamente al terminar código.

==================================================
32. SILENT FALLBACK PROHIBITION
==================================================

Dentro de una ejecución CANONICAL:

si algo falla,

Web NO puede calcular silenciosamente con Legacy y mostrarlo como Canonical.

Fallback sólo puede ser:

- explícito;
- separado;
- identificado como Legacy;
- auditable.

==================================================
33. ERROR HANDLING
==================================================

Definir comportamiento para:

CanonicalResult missing

unsupported schema_version

invalid fingerprint

missing value/base reference

ValueStatus.ERROR

result not releasable

adapter failure

unsupported structure

unexpected M5 contract version.

No ocultar errores sustituyendo números Legacy.

==================================================
34. RELEASE / DISPLAY POLICY
==================================================

Definir qué puede mostrar Web cuando:

computation_status = COMPLETE

pero:

releasable = false.

Distinguir:

internal QA view

vs

official released output.

No inferir que un valor calculado puede mostrarse productivamente.

==================================================
35. RENDERER NEUTRALITY PROTECTION
==================================================

M6 no puede contaminar M5.

Prohibido introducir imports Web en:

results.py

result_identity.py

serialization.py

formula_registry.py

M5 contracts canónicos.

Toda lógica Streamlit/Plotly vive aguas abajo.

==================================================
36. WEB MODULE BOUNDARY
==================================================

Definir dónde debe vivir:

Canonical Web Adapter

projection/pivot logic

label resolution

significance display tokens

QA rendering

cache integration

sin mezclarlo con Analytics Core.

Proponer arquitectura mínima, no código.

==================================================
37. SQLITE BOUNDARY
==================================================

M6 no rediseña SQLite productivo.

Si se necesita recordar:

result_run_id

o canonical mode

proponer primero una estrategia sin migración o una extensión mínima.

Cualquier schema migration productiva requerirá decisión explícita.

==================================================
38. PERFORMANCE
==================================================

M6 puede optimizar:

adapter access

pivoting

cache

rendering

pero:

performance optimization != semantic change.

No alterar valores para acelerar Web.

Definir benchmarks separados para:

correctness

y:

performance.

==================================================
39. OBSERVABILITY
==================================================

Definir logging/telemetry mínima para saber:

execution mode

result_run_id

result_fingerprint

adapter version

schema version

renderer errors

fallback events

dual-run deltas.

No registrar datos sensibles innecesarios.

==================================================
40. WEB MIGRATION PHASES
==================================================

Proponer si M6 conviene dividirse internamente en fases, por ejemplo:

M6A — adapter + explicit canonical mode

M6B — core views RU/RM

M6C — Grid/Loop/weights/significance

M6D — dual-run + rollback + default-switch gate

Si se propone subdivisión:

debe seguir siendo un solo milestone M6 de gobierno.

No iniciar implementación todavía.

==================================================
41. PROTECTED AREAS
==================================================

M6 no modifica semánticamente:

M2 Universe

M3 Weight

M4 Structure / denominators

M5 Canonical Results

B1

B2

B3

EXPLORA NG

Excel

Legacy calculations

salvo routing/compatibility estrictamente necesario y explícitamente autorizado.

==================================================
42. PRODUCTIVE GRID / LOOP WARNING
==================================================

Preservar:

`PRODUCTIVE GRID/LOOP BENCHMARK = PENDING — HUMAN ACCEPTED WARNING`

M6 no puede convertir:

renderer works

en:

structure productively validated.

==================================================
43. TEST MATRIX
==================================================

Diseñar test matrix M6 para al menos:

1. LEGACY remains default.
2. Explicit CANONICAL_V1 mode.
3. DUAL_RUN mode.
4. Canonical adapter does not recalculate estimate.
5. Total rendering.
6. Banner rendering.
7. User filter rendering.
8. slice_id identity.
9. RU count/proportion.
10. RU mean/scale.
11. RM respondent proportion.
12. RM mention proportion.
13. respondent vs mention bases separate.
14. GRID_ESCALA.
15. GRID_RM.
16. LOOP_RU.
17. LOOP_RM.
18. LOOP_NUMERICO.
19. weighted descriptive value.
20. canonical base rendering.
21. effective_n diagnostic only.
22. NO_VALID_BASE.
23. valid zero.
24. UNSUPPORTED.
25. INELIGIBLE.
26. ERROR.
27. significance tested significant.
28. significance tested not significant.
29. significance unsupported.
30. no-letter != not significant.
31. QAEvent rendering.
32. blocking QA preserved.
33. release state preserved.
34. non-releasable internal view.
35. deterministic cache key.
36. no stale cache across runs.
37. schema mismatch.
38. invalid fingerprint.
39. missing value/base reference.
40. explicit rollback.
41. no silent fallback.
42. dual-run PARITY.
43. INTENDED_CORRECTION.
44. M2_BASE_DIFFERENCE.
45. M3_WEIGHT_DIFFERENCE.
46. M4_STRUCTURE_DIFFERENCE.
47. UNSUPPORTED_V1.
48. POTENTIAL_REGRESSION.
49. PRESENTATION_ONLY.
50. unexplained delta blocks migration.
51. Legacy output unchanged.
52. M2/M3/M4/M5 invariance.
53. Web adapter renderer-only imports.
54. M5 modules remain free of Streamlit/Plotly.
55. no SQLite migration.
56. no Excel work.

==================================================
44. ACCEPTANCE CRITERIA
==================================================

M6 sólo puede cerrar cuando:

1. Web consume CanonicalResult como analytical authority.
2. Web no recalcula analytical truth.
3. Canonical adapter es renderer-side.
4. ReportResult no reconstruye CanonicalResult.
5. LEGACY sigue disponible durante gate.
6. explicit canonical mode funciona.
7. dual-run es auditable.
8. all deltas classified.
9. no unexplained numerical deltas.
10. RU cubierto.
11. RM respondent cubierto.
12. RM mention cubierto.
13. GRID cubierto.
14. LOOP cubierto.
15. weighted descriptive cubierto.
16. significance renderer no ejecuta tests.
17. QA preservado.
18. release state preservado.
19. cache identity segura.
20. no silent fallback.
21. rollback probado.
22. M2 invariant.
23. M3 invariant.
24. M4 invariant.
25. M5 invariant.
26. Legacy numerical behavior invariant.
27. no SQLite productive migration.
28. Excel not started.
29. Productive Grid/Loop warning preserved.
30. Default switch requires separate explicit human decision.

==================================================
45. OUT OF SCOPE
==================================================

Quedan fuera de M6:

- Excel Dashboard;
- VBA;
- M7;
- nueva metodología estadística;
- weighted significance;
- nuevas fórmulas M5;
- nueva Universe language;
- nueva Structure inference;
- NG redesign;
- SQLite redesign;
- eliminación definitiva de Legacy;
- cambio automático de default;
- Productive Grid/Loop validation.

==================================================
46. REQUIRED OUTPUT
==================================================

Devuelve:

M6 CONTRACT STATUS

CURRENT WEB ANALYTICAL INVENTORY

TARGET WEB AUTHORITY MODEL

EXECUTION MODE CONTRACT

CANONICAL WEB ADAPTER CONTRACT

REPORTRESULT TRANSITION CONTRACT

SLICE CONTRACT

FILTER CONTRACT

TOTAL / BANNER CONTRACT

BASE RENDERING CONTRACT

DENOMINATOR CONTRACT

RU CONTRACT

RM RESPONDENT CONTRACT

RM MENTION CONTRACT

GRID CONTRACT

LOOP CONTRACT

WEIGHT CONTRACT

VALUE STATUS RENDERING CONTRACT

SIGNIFICANCE RENDERING CONTRACT

QA / WARNING CONTRACT

RELEASE STATE CONTRACT

CACHE CONTRACT

SESSION STATE CONTRACT

EXPORT CONTRACT

PRESENTATION ROUNDING CONTRACT

DUAL-RUN CONTRACT

DUAL-RUN MATCHING GRAIN

LEGACY COMPARISON CONTRACT

FEATURE FLAG CONTRACT

ROLLBACK CONTRACT

DEFAULT MODE SWITCH CRITERIA

ERROR HANDLING CONTRACT

SQLITE BOUNDARY

PERFORMANCE CONTRACT

OBSERVABILITY CONTRACT

PROPOSED M6 INTERNAL PHASES

FILES / AREAS EXPECTED TO CHANGE

FILES / AREAS PROTECTED

TEST MATRIX

ACCEPTANCE CRITERIA

RISKS

BLOCKERS

CODEX READY YES/NO

No generar código.

No autorizar automáticamente M6.

No iniciar M7.