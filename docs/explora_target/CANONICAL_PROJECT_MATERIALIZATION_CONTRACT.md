# CANONICAL PROJECT MATERIALIZATION CONTRACT

## CANONICAL MATERIALIZATION CONTRACT STATUS

**PASS — CONTRACT FROZEN / READY FOR IMPLEMENTATION**

Este contrato cierra las decisiones arquitectónicas necesarias para implementar la capa de materialización canónica.

Esto **NO cambia** el estado operativo de Gate 19:

**GATE 19: BLOCKED**

El blocker `B-BA-CRT-03` queda:

**CONTRACTUALLY RESOLVED / IMPLEMENTATION OPEN**

Es decir:

- ya está definido qué debe construirse;
- todavía no existe evidencia de que la capacidad funcione productivamente;
- Benchmark A todavía no puede declararse ejecutado canónicamente;
- Gate 19 sólo podrá reabrirse para aceptación cuando exista implementación, tests y ejecución BA-01…BA-05.

No se autoriza:

- DUAL\_RUN productivo;
- cambio de default;
- M7;
- Excel;
- migración adicional Web;
- modificación metodológica de M2–M5.

---

# 1. ARCHITECTURAL POSITION

La nueva capacidad vive **antes de M2**.

Flujo congelado:

`Source SAV`
\+
`RELEASED Project Package`
→
`Canonical Project Materializer`
→
`CanonicalRuntimeInput`
\+
`CanonicalRequestSnapshot`
→
`M2 Universe`
→
`M3 Weight`
→
`M4 Structure`
→
`M5 CanonicalResult`

Posteriormente, fuera del alcance de este contrato:

`CanonicalResult`
→
`M6 Web / DUAL_RUN`

El materializador:

**NO es Analytics Core.**

**NO es un tabulador.**

**NO es un replacement del current analytic DB builder.**

**NO es un renderer.**

Su única responsabilidad es convertir una fuente física autorizada y configuración RELEASED en entradas canónicas determinísticas y validadas que el Core pueda ejecutar.

---

# 2. INPUT AUTHORITY

La autoridad de entrada se compone de dos elementos obligatorios.

### 2.1 Physical data authority

El archivo SAV físico indicado por el proyecto.

Para Benchmark A:

`FUNSMX_297140_20260914.sav`

Expected SHA-256:

`71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F`

Expected source N:

`1534`

El hash se valida contra los bytes físicos del archivo antes de cualquier ejecución.

Un archivo con el mismo nombre y distinto hash:

**FAIL.**

### 2.2 Configuration authority

Sólo el:

`RELEASED Project Package`

puede suministrar autoridad metodológica al runtime.

Benchmark A:

`BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1.zip`

Expected SHA-256:

`34FA5E694E8A44FFE952EB2A0B4737B06B3650D856141ED8C0570A63C7290B79`

La precedencia se congela como:

`Project Spec`
→
`Question Spec`
→
`Structure Spec`
→
`Universe Spec`

más los registros RELEASED de:

- Weight;
- Metric;
- Significance;
- Banner/filter;
- Request Matrix.

El SPSS dictionary puede validar la realidad física del SAV.

No puede sobreescribir una decisión RELEASED.

El cuestionario autoritativo forma parte de la trazabilidad de cómo fue construida y aprobada la configuración del proyecto; no vuelve a interpretarse durante cada runtime para cambiar Question/Structure Specs.

---

# 3. OUTPUT AUTHORITY

Existen dos autoridades diferentes y no deben confundirse.

### Runtime input authority

`CanonicalRuntimeInput`

Es la autoridad congelada de los datos físicos que M2–M5 pueden consumir.

No contiene resultados estadísticos oficiales.

### Analytical output authority

`CanonicalResult`

generado exclusivamente mediante M2 → M3 → M4 → M5.

Sólo M5 sigue siendo la autoridad oficial de resultados.

No son autoridad analítica:

- runtime manifest;
- request snapshot;
- SQLite legado;
- Web;
- Excel;
- QA report;
- renderer artifact;
- materializer output distinto de CanonicalRuntimeInput.

---

# 4. RUNTIME INPUT FORMAT DECISION

## DECISION

**OPTION B — FROZEN CANONICAL OBJECT WITH DETERMINISTIC SERIALIZATION**

Se crea un único contrato lógico:

`CanonicalRuntimeInput`

Schema inicial:

`canonical-runtime/1`

La autoridad persistida será una serialización canónica determinística del objeto.

La representación in-memory utilizada durante ejecución es solamente una proyección temporal de ese mismo artefacto.

No constituye una segunda autoridad.

### V1 physical persistence

V1 utilizará un **documento JSON canónico determinístico**, no el SQLite analítico legado.

Razones:

1. evita hacer obligatorio el actual `build_analytic_database(...)`;
2. evita exigir datamap;
3. evita introducir otro SQLite con semántica potencialmente confundible con el Legacy analytic DB;
4. permite congelar exactamente los inputs que recibe Core;
5. permite fingerprint lógico reproducible;
6. no obliga a M2–M5 a leer infraestructura Web/SQLite;
7. mantiene la nueva capa aislada.

El JSON canónico es un **artefacto interno del runtime canónico**. No redefine el soporte de inputs Legacy.

### Canonical scalar preservation

Los valores no pueden depender de cómo una biblioteca JSON represente incidentalmente tipos.

La serialización debe preservar de forma explícita y determinística al menos:

- numeric;
- string;
- missing/null;
- respondent identity;
- category identity.

Valores numéricos, missing y strings deben poseer representación canónica estable para fingerprinting.

No se permite que:

`1`

y

`1.0`

cambien de identidad incidentalmente entre ejecuciones por una conversión de serializer.

### One-authority rule

No se crearán en V1 simultáneamente:

- canonical SQLite;
- canonical JSON;
- canonical Parquet;

como tres fuentes equivalentes.

Sólo `CanonicalRuntimeInput canonical-runtime/1` es autoridad.

Cualquier representación adicional futura requerirá una decisión de arquitectura y deberá ser una persistencia del mismo contrato lógico, no una nueva semántica.

---

# 5. RESPONDENT IDENTITY DECISION

Se congelan dos modos y un orden de precedencia.

### Mode 1 — RELEASED\_SOURCE\_ID

Si existe una variable de respondent ID autoritativa declarada en RELEASED configuration:

se utiliza exactamente esa variable.

Debe ser:

- resoluble;
- no ambigua;
- válida;
- única a nivel respondent.

Duplicados o identidad inválida:

**FAIL.**

### Mode 2 — SOURCE\_ROW\_ORDINAL\_V1

Si el proyecto no tiene respondent ID autoritativo, V1 permite utilizar el orden físico del SAV.

Identidad:

`1..N`

en el mismo orden entregado por el reader del source SAV.

Este mecanismo es explícitamente una:

**TECHNICAL RUNTIME IDENTITY**

No una variable analítica.

No debe incorporarse como categoría, banner o pregunta.

Su estabilidad está anclada al source fingerprint.

Si se modifica el orden físico de registros, el dataset fingerprint cambia y se trata como otra fuente.

No se permite generar:

- UUID aleatorio;
- session-based ID;
- timestamp ID;
- hash dependiente de path.

---

# 6. PHYSICAL BINDING RULE

La regla V1 es:

**EXACT RELEASED BINDING ONLY**

Ejemplo:

`Q_TOP_LEVER`
→
`Q_TOP_LEVER`

RM:

`Q_DELIVERY_APPS`
→
`Q_DELIVERY_APPS#1`
`Q_DELIVERY_APPS#2`
`Q_DELIVERY_APPS#98`
`Q_DELIVERY_APPS#99`

Se prohíbe durante runtime:

- fuzzy match;
- substring inference;
- case normalization para encontrar una variable distinta;
- búsqueda por label;
- alias inventado;
- regex fallback;
- posición de columna como sustituto de nombre;
- runtime type inference que cambie el Spec.

Los nombres físicos deben coincidir exactamente con el binding RELEASED.

Binding inexistente:

**FAIL.**

Más de una resolución posible:

**FAIL.**

Labels SPSS pueden utilizarse para QA.

No establecen analytical identity.

---

# 7. DATAMAP REQUIREMENT DECISION

**DATAMAP REQUIRED: NO**

Un proyecto canónico no requiere un datamap separado si su RELEASED package contiene bindings suficientes y determinísticos.

Por tanto Benchmark A puede utilizar directamente:

`SAV dictionary`
\+
`RELEASED physical bindings`

Si un proyecto dispone de un datamap:

sólo podrá utilizarse cuando dicho datamap sea un artefacto RELEASED explícitamente referenciado por el package.

No se permite:

- buscar automáticamente un XLSX cercano;
- construir automáticamente un datamap;
- usar un datamap Legacy no declarado;
- derivar uno mediante AI;
- derivar uno mediante Web heuristics.

Ausencia de datamap no es error por sí sola.

Ausencia de binding RELEASED sí lo es.

---

# 8. UNIVERSE RESPONSIBILITY

### Materializer

Debe:

- conservar las variables físicas requeridas;
- resolver las referencias de Universe Spec;
- verificar que existan los inputs físicos necesarios;
- entregar valores raw.

No debe:

- ejecutar el universo metodológico;
- calcular bases finales;
- excluir respondents;
- reinterpretar missing como applicability;
- duplicar predicates de M2.

### Authority

**M2 remains Universe authority.**

Si un Universe Spec no puede resolverse:

**FAIL BEFORE ANALYTICAL EXECUTION.**

---

# 9. WEIGHT RESPONSIBILITY

### Materializer

Puede únicamente:

- resolver el binding físico del weight autorizado;
- entregar los valores originales de dicha variable;
- identificar explícitamente configuración unweighted.

No valida metodológicamente el peso.

### M3 authority

M3 conserva autoridad sobre:

- missing;
- zero;
- negative;
- non-numeric;
- non-finite;
- weighted\_n\_raw;
- weighted\_n;
- effective\_n;
- Weight QA.

No existe normalización en materialization.

No existe trimming.

No existe capping.

No existe fabricación automática de `1.0`.

Para:

`weight_ref = NONE`

el materializador entrega:

**explicit UNWEIGHTED configuration**

No una columna sintética de peso unitario.

Benchmark A es:

**UNWEIGHTED.**

---

# 10. STRUCTURE RESPONSIBILITY

El materializador resuelve:

`Structure Spec`
→
`physical variables`

y conserva sus valores.

No calcula:

- selected/not selected;
- respondent denominator;
- mention denominator;
- duplicate handling;
- exclusive handling;
- Grid calculations;
- Loop calculations.

### Authority

**M4 remains Structure authority.**

RU, RM, Grid y Loop semantics nunca se duplican en materialization.

---

# 11. METRIC RESPONSIBILITY

El materializador no calcula:

- COUNT;
- PROPORTION;
- MEAN;
- RM\_RESPONDENT\_PROPORTION;
- RM\_MENTION\_PROPORTION;
- Top/Bottom Box;
- significance;
- bases estadísticas.

Debe únicamente resolver que el request hace referencia a un Metric/Formula RELEASED existente y autorizado.

### Authority

**M5 remains CanonicalResult authority.**

B2 remains Significance methodology authority wherever significance is eligible.

---

# 12. REQUEST SNAPSHOT CONTRACT

Cada ejecución analítica deberá producir un:

`CanonicalRequestSnapshot`

Schema inicial:

`canonical-request/1`

El snapshot contiene como mínimo:

- `project_id`;
- `request_id`;
- `question_id`;
- `structure_ref`;
- `universe_ref`;
- `weight_ref`;
- `metric_ref / formula_ref`;
- filter identity;
- banner identity;
- event/category identity cuando aplique;
- significance configuration/ref;
- runtime schema version;
- runtime fingerprint;
- RELEASED package fingerprint;
- referenced Spec versions/hashes;
- request schema version;
- request fingerprint.

El snapshot debe reflejar exclusivamente una entrada de la RELEASED Request Matrix.

Puede permitirse seleccionar:

`request_id`

o un conjunto de `request_id`.

No puede permitirse modificar durante ejecución:

- metric;
- universe;
- weight;
- filter;
- banner;
- event;
- category;
- significance settings;

mediante parámetros ad-hoc que contradigan el Request Matrix.

Cambiar cualquiera de esos elementos requiere una nueva configuración RELEASED.

---

# 13. FINGERPRINT CONTRACT

Todos los fingerprints canónicos V1 utilizarán:

**SHA-256**

salvo fingerprints ya congelados por M5, que conservan su contrato existente.

### 13.1 Source fingerprint

SHA-256 de los bytes físicos del SAV.

Debe cambiar si cambia el archivo.

No depende del path.

### 13.2 RELEASED package fingerprint

SHA-256 del package RELEASED físico declarado.

Debe coincidir con su manifest/expected fingerprint.

### 13.3 Runtime fingerprint

SHA-256 sobre la representación canónica de `CanonicalRuntimeInput`.

Incluye solamente contenido semántico del runtime:

- schema/version;
- project identity;
- source fingerprint;
- package fingerprint;
- respondent identity mode;
- respondent order/identity;
- physical variable identity;
- raw values utilizados por el runtime;
- category identities;
- structure identities;
- resolved refs;
- provenance semántica.

Excluye:

- source path;
- extraction folder;
- temp directory;
- session ID;
- timestamp de ejecución;
- filesystem timestamps.

Debe cambiar si cambia cualquier analytical input materializado.

### 13.4 Request fingerprint

SHA-256 sobre la representación canónica de `CanonicalRequestSnapshot`.

Incluye:

- runtime fingerprint;
- request identity;
- todos los refs/hashes analíticos relevantes.

Excluye:

- execution timestamp;
- session;
- transient location;
- result\_run\_id.

### 13.5 CanonicalResult fingerprint

**M5 remains authority.**

La nueva capa no redefine el algoritmo M5.

El resultado debe conservar trazabilidad hacia:

- request fingerprint;
- runtime fingerprint;
- source fingerprint;
- package/spec fingerprint.

Repeated identical analytical execution deberá preservar:

- runtime fingerprint;
- request fingerprint;
- result fingerprint;
- values;
- bases;
- QA analítico.

Puede cambiar:

- result\_run\_id;
- execution timestamp.

---

# 14. QA CONTRACT

Debe existir un gate de:

**PRE-M2 MATERIALIZATION QA**

Ningún request llega a M2 si existe QA FAIL.

### Required QA

**QA-SOURCE-N**

`source_n`

debe quedar registrado.

Benchmark A:

`1534`.

**QA-RUNTIME-N**

`runtime_n == source_n`

La materialización no puede reducir ni incrementar respondents.

**QA-BINDINGS**

Todos los physical bindings requeridos existen exactamente una vez.

**QA-VALUE-RECONCILIATION**

Los valores fuente y runtime deben ser iguales donde no existe transformación explícita.

V1 espera:

**no analytical transformation during materialization.**

**QA-MISSING**

Valid/missing counts de cada binding deben reconciliar entre source y runtime.

**QA-CATEGORY-DOMAIN**

Los códigos observados deben ser compatibles con el RELEASED category domain y explicit missing semantics.

Un label de texto diferente no modifica el code identity.

Un observed analytical code no permitido por RELEASED Spec:

**FAIL.**

**QA-RESPONDENT-IDENTITY**

Identidad estable y única.

**QA-PACKAGE-INTEGRITY**

Todos los objetos referenciados existen, corresponden al mismo proyecto y son RELEASED.

**QA-REFERENCE-INTEGRITY**

Question → Structure → Universe → Weight → Metric → Filter/Banner → Request references deben resolverse sin dangling references.

### QA warnings

Warnings pueden existir para información no autoritativa, por ejemplo discrepancias informativas de labels que no alteren code identity.

Un warning:

- debe registrarse;
- no puede cambiar datos;
- no puede cambiar Specs;
- no puede activar un fallback.

---

# 15. FAIL-CLOSED CONDITIONS

Debe abortarse materialization cuando ocurra cualquiera de las siguientes condiciones:

1. source SHA mismatch;
2. RELEASED package SHA mismatch;
3. project\_id mismatch;
4. source N incompatible con una expectativa RELEASED cuando dicha expectativa esté congelada;
5. non-RELEASED object referenced;
6. physical binding missing;
7. physical binding ambiguous;
8. duplicate/invalid authoritative respondent identity;
9. incompatible category domain;
10. missing Structure ref;
11. missing Universe ref;
12. missing Weight ref;
13. missing Metric ref;
14. missing filter/banner ref requerido;
15. missing Request ref;
16. incompatible schema/version;
17. dangling reference;
18. runtime/source N mismatch;
19. runtime/source value reconciliation failure;
20. request parameters contradict RELEASED Request Matrix;
21. unsupported canonical scalar representation;
22. inability to invoke M2–M5 without leaving the approved analytical path.

No existe:

`try canonical → fallback Legacy`.

No existe:

`canonical error → approximate calculation`.

No existe:

`missing binding → infer from labels`.

El error debe ser explícito.

---

# 16. CANONICALRESULT ORCHESTRATION DECISION

## DECISION

**A NEW ISOLATED ORCHESTRATION ENTRY POINT IS REQUIRED.**

Conceptual responsibility:

`run_canonical_project(...)`

El nombre definitivo puede seguir las convenciones del repositorio, pero la responsabilidad queda congelada.

### Allowed responsibilities

1. validate source fingerprint;
2. validate RELEASED package fingerprint/state;
3. load SAV through the existing reader capability;
4. create exact physical bindings;
5. construct `CanonicalRuntimeInput`;
6. execute pre-M2 QA;
7. persist/fingerprint canonical runtime input;
8. obtain a RELEASED request by request\_id;
9. create `CanonicalRequestSnapshot`;
10. invoke existing M2;
11. invoke existing M3;
12. invoke existing M4;
13. invoke existing M5;
14. obtain the actual `CanonicalResult`;
15. write execution evidence.

### Explicitly forbidden

The orchestration layer may not:

- calculate a percentage;
- calculate a mean;
- calculate RM respondent %;
- calculate RM mention %;
- calculate significance;
- independently create bases;
- patch an M4 result;
- alter a released spec;
- change a released metric;
- use Legacy;
- mix Legacy with canonical;
- call Web calculations as substitute for Core.

### Interface rule

If implementation discovers that M2–M5 cannot be invoked through their current public interfaces without editing frozen analytical logic:

**STOP.**

Do not modify M2–M6 incidentally.

Return a separate:

`INTERFACE CHANGE REQUIRED`

gate identifying the exact minimal interface-only modification.

This contract does not pre-authorize such a change.

---

# 17. NEW MODULES REQUIRED

Preferred isolated package:

`src/canonical_materialization/`

Minimum conceptual surface:

`models.py`

Defines renderer-neutral materialization contracts such as:

- CanonicalRuntimeInput;
- runtime manifest;
- CanonicalRequestSnapshot.

`materializer.py`

Responsible for:

- SAV → exact bound canonical inputs;
- no analytical calculations.

`fingerprints.py`

Responsible for deterministic canonical serialization/fingerprints.

`qa.py`

Responsible for pre-M2 materialization reconciliation and fail-closed QA.

`request.py`

Responsible for binding RELEASED Request Matrix records into immutable request snapshots.

`orchestrator.py`

Responsible for sequencing materialization → request → M2 → M3 → M4 → M5.

Additional modules should not be created unless implementation demonstrates a concrete responsibility that cannot remain cleanly within these boundaries.

---

# 18. EXISTING MODULES TOUCHED

## Planned modifications

**NONE**

The new layer may consume/import existing capabilities including conceptually:

- SPSS reader;
- contract models/validators;
- M2 Universe;
- M3 Weight;
- M4 Structure;
- M5 Results.

Consuming an existing module is not equivalent to modifying it.

The Web `request_binding` layer must not become canonical request authority simply because similar logic exists there.

Canonical request binding must remain renderer-neutral.

---

# 19. FROZEN M2–M6 CHANGES REQUIRED

**NO**

This is an explicit implementation constraint.

Any later evidence that a frozen interface must change requires a separate approval before the change.

Therefore:

`M2: NO CHANGE`

`M3: NO CHANGE`

`M4: NO CHANGE`

`M5: NO CHANGE`

`M6: NO CHANGE`

---

# 20. TEST MATRIX

| IDTestRequired result |                                                               |                                                         |
| --------------------- | ------------------------------------------------------------- | ------------------------------------------------------- |
| MAT-001               | Valid source hash                                             | PASS                                                    |
| MAT-002               | Source hash mismatch                                          | FAIL CLOSED                                             |
| MAT-003               | Valid RELEASED package hash                                   | PASS                                                    |
| MAT-004               | Package hash mismatch                                         | FAIL CLOSED                                             |
| MAT-005               | Non-RELEASED spec referenced                                  | FAIL CLOSED                                             |
| MAT-006               | Exact RU binding exists                                       | PASS                                                    |
| MAT-007               | RU binding missing                                            | FAIL CLOSED                                             |
| MAT-008               | Ambiguous physical binding                                    | FAIL CLOSED                                             |
| MAT-009               | RM physical set resolves exactly                              | PASS                                                    |
| MAT-010               | RM member missing                                             | FAIL CLOSED                                             |
| MAT-011               | No datamap + complete released bindings                       | PASS                                                    |
| MAT-012               | No datamap + incomplete bindings                              | FAIL CLOSED                                             |
| MAT-013               | Source respondent ID valid/unique                             | PASS                                                    |
| MAT-014               | Source respondent ID duplicated                               | FAIL CLOSED                                             |
| MAT-015               | No respondent ID → SOURCE\_ROW\_ORDINAL\_V1                   | PASS                                                    |
| MAT-016               | Source N equals runtime N                                     | PASS                                                    |
| MAT-017               | Source/runtime N mismatch                                     | FAIL CLOSED                                             |
| MAT-018               | Raw source/runtime values equal                               | PASS                                                    |
| MAT-019               | Silent value mutation                                         | FAIL CLOSED                                             |
| MAT-020               | Valid/missing frequencies reconcile                           | PASS                                                    |
| MAT-021               | Category domain compatible                                    | PASS                                                    |
| MAT-022               | Undeclared observed analytical category                       | FAIL CLOSED                                             |
| MAT-023               | Valid filter binding                                          | PASS                                                    |
| MAT-024               | Missing filter binding                                        | FAIL CLOSED                                             |
| MAT-025               | Valid banner binding                                          | PASS                                                    |
| MAT-026               | Missing banner binding                                        | FAIL CLOSED                                             |
| MAT-027               | `weight_ref=NONE`                                             | Explicit UNWEIGHTED; no unit-weight column              |
| MAT-028               | Materializer attempts weight normalization                    | TEST MUST FAIL                                          |
| MAT-029               | Materializer attempts Universe evaluation                     | TEST MUST FAIL                                          |
| MAT-030               | Materializer calculates analytical metric                     | TEST MUST FAIL                                          |
| MAT-031               | Same runtime input twice                                      | Same runtime fingerprint                                |
| MAT-032               | Different source path, same content                           | Same runtime fingerprint                                |
| MAT-033               | Different temp folder/session                                 | Same runtime fingerprint                                |
| MAT-034               | Bound analytical value changes                                | Different runtime fingerprint                           |
| MAT-035               | Same released request twice                                   | Same request fingerprint                                |
| MAT-036               | Analytical request field changes through new RELEASED version | Different request fingerprint                           |
| MAT-037               | Ad-hoc request override contradicts matrix                    | FAIL CLOSED                                             |
| MAT-038               | M2 invoked from materialized input                            | PASS                                                    |
| MAT-039               | M3 invoked after M2                                           | PASS                                                    |
| MAT-040               | M4 invoked after M3                                           | PASS                                                    |
| MAT-041               | M5 produces CanonicalResult                                   | PASS                                                    |
| MAT-042               | Legacy fallback attempted                                     | TEST MUST FAIL                                          |
| MAT-043               | Web calculation used as Core substitute                       | TEST MUST FAIL                                          |
| MAT-044               | BA-01 productive fixture/path                                 | PASS                                                    |
| MAT-045               | BA-02 productive fixture/path                                 | PASS                                                    |
| MAT-046               | BA-03 productive fixture/path                                 | PASS                                                    |
| MAT-047               | BA-04 productive fixture/path                                 | PASS                                                    |
| MAT-048               | BA-05 productive fixture/path                                 | PASS                                                    |
| MAT-049               | Same Benchmark A execution repeated                           | Same request/result fingerprints and analytical content |
| MAT-050               | Different execution timestamp/run\_id only                    | Analytical fingerprints unchanged                       |

Test success must include:

**0 unexpected FAIL**

and

**0 silent SKIP**

for contract-critical materialization tests.

---

# 21. BENCHMARK A ACCEPTANCE CRITERIA

Benchmark A remains the first productive proof.

Required project:

`FUNSMX_297140`

`Uber — Rider-to-Eater Catalyst`

Required source:

`FUNSMX_297140_20260914.sav`

Required source SHA-256:

`71B8CC2843C1C65A92D7F18FE631EA3AAD4CBD47BC936EC28C205BAC8D0DBB2F`

Expected N:

`1534`

Required RELEASED package:

`BENCHMARK_A_FUNSMX_297140_CANONICAL_PROJECT_RELEASE_V1.zip`

Required package SHA-256:

`34FA5E694E8A44FFE952EB2A0B4737B06B3650D856141ED8C0570A63C7290B79`

### Required requests

All must execute from their RELEASED definitions:

`BA-01`

`BA-02`

`BA-03`

`BA-04`

`BA-05`

No manual reconstruction of those requests is permitted.

Collectively, the acceptance set must exercise:

- RU;
- RM respondent;
- RM mention;
- real filter;
- real banner;
- B2 significance candidate;
- unweighted execution.

Not required in this gate:

- Grid;
- Loop;
- productive weights.

### For each BA request

Required evidence:

1. released request located;
2. immutable request snapshot generated;
3. request fingerprint generated;
4. runtime fingerprint referenced;
5. M2 execution evidenced;
6. M3 execution evidenced;
7. M4 execution evidenced;
8. M5 generates CanonicalResult;
9. result fingerprint exists;
10. source/package/spec provenance exists;
11. QA result exists;
12. no Legacy path used.

### B2 significance candidate

The materializer does not decide whether significance is inferentially supported.

The request must reach the existing B2/M5 eligibility path.

That authority must return the frozen B2 behavior:

- valid significance result when eligible; or
- explicit unsupported/ineligible state when required by B2.

It must never invent significance simply to satisfy Benchmark A.

### Numerical acceptance

This contract does not invent expected percentages, bases, means or significance values for BA-01…BA-05.

Numeric assertions must come from:

- approved Benchmark A expected evidence;
- existing released fixture;
- or separately validated benchmark truth.

Absence of a numeric target in this contract must not be replaced with an AI-generated expected number.

---

# 22. PRODUCTIVE EVIDENCE OUTPUTS

A successful Benchmark A materialization/execution must leave evidence sufficient to reconstruct the run:

`runtime_manifest`

Containing:

- project\_id;
- runtime schema;
- source identity/fingerprint;
- package identity/fingerprint;
- respondent identity mode;
- source N;
- runtime N;
- referenced specs;
- materialization state.

`canonical runtime artifact`

`runtime_fingerprint`

`request snapshots`

One per BA request.

`request_fingerprints`

`CanonicalResult artifacts`

Produced by M5.

`source/runtime reconciliation`

Including:

- N;
- bindings;
- missing;
- domains;
- value equality evidence.

`QA events`

Including all WARN/FAIL/PASS materialization events required for traceability.

`release/execution state`

The materializer records state but cannot independently promote a failed analytical result to official release.

Renderer outputs are explicitly excluded from analytical authority.

---

# 23. BACKWARD COMPATIBILITY

`LEGACY remains executable.`

`LEGACY remains default.`

The canonical materializer is a new isolated execution capability.

It does not replace:

- current SAV + datamap Legacy workflow;
- current SQLite Legacy workflow;
- current reporter default.

No numerical Legacy outputs may change as a consequence of this implementation.

No mixed Legacy/Canonical result is permitted inside one canonical execution.

M6 DUAL\_RUN remains a later consumer of the resulting CanonicalResult.

---

# 24. BLOCKERS

## Contract blockers

**NONE**

All architectural decisions required by this contract are now explicit.

## Runtime blocker

`B-BA-CRT-03` remains operationally open because the materialization/orchestration capability has not yet been implemented and validated.

Therefore Gate 19 remains blocked.

## Conditional future blocker

If Codex demonstrates with repository evidence that an existing frozen M2–M5 public interface cannot be used without changing frozen code:

status becomes:

`BLOCKED — FROZEN INTERFACE CHANGE REQUIRED`

and that specific change must return for approval.

Codex must not make the change implicitly.

---

# 25. IMPLEMENTATION READY

**YES**

The contract provides sufficient deterministic decisions to implement:

- source verification;
- package verification;
- physical binding;
- CanonicalRuntimeInput;
- respondent identity;
- request snapshots;
- fingerprints;
- QA;
- fail-closed behavior;
- M2–M5 orchestration;
- Benchmark A tests.

---

# 26. CODEX READY

**YES**

Codex may implement **only the Canonical Project Materialization capability defined here**.

Authorization does not extend to:

- M2 changes;
- M3 changes;
- M4 changes;
- M5 changes;
- M6 changes;
- productive DUAL\_RUN;
- default switch;
- Excel/M7;
- NG modifications;
- Web redesign;
- new statistical methodology.

---

# FINAL GATE DECISION

**CANONICAL MATERIALIZATION CONTRACT: PASS / FROZEN**

**IMPLEMENTATION READY: YES**

**CODEX READY: YES**

**FROZEN M2–M6 CHANGES REQUIRED: NO**

**GATE 19: BLOCKED — UNCHANGED**

**B-BA-CRT-03: CONTRACT RESOLVED / IMPLEMENTATION AND PRODUCTIVE VALIDATION PENDING**

The next legitimate step is implementation of the isolated materialization layer and its test matrix.

It is **not** DUAL\_RUN.

It is **not** M7.

It is **not** a default switch.