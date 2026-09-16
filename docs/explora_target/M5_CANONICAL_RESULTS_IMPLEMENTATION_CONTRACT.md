# M5 — CANONICAL RESULTS IMPLEMENTATION CONTRACT

**Canonical contract package for EXPLORA Core M5.**

This file consolidates the approved M5 conceptual contract and the final schema closure.
Implementation authorization is governed separately in `00 — Gobierno y Roadmap de Explora`; this document defines the frozen implementation contract and does not itself authorize M6.

---

# 13 — M5 Contract — Canonical Results

Sí. Éste debe ser el siguiente contrato formal de EXPLORA Core.

El estado de entrada es suficiente para abrir M5: M2 — Universe Execution, M3 — Weight Hardening y M4 — RM/Grid Authority están cerrados y aceptados. M5 no reabre ninguno de ellos. En particular, M4 ya entrega la estructura normalizada y la separación correcta de denominadores que M5 necesita para construir resultados canónicos. M5 todavía no implica migrar Web ni comenzar Excel.

## M5 — CANONICAL RESULTS CONTRACT

**Estado de entrada**

`M1A-F: PASS`

`M2 — Universe Execution: CLOSED / ACCEPTED`

`M3 — Weight Hardening: CLOSED / ACCEPTED — PASS WITH WARNINGS`

`M4 — RM / GRID Authority: CLOSED / ACCEPTED`

`B1 — Weight Methodology: HUMAN APPROVED / CANONICAL`

`B2 — Significance Policy: HUMAN APPROVED / CANONICAL`

`B3 — AI Auto-Release Policy: HUMAN APPROVED / CANONICAL`

`LEGACY` continúa siendo el modo productivo default.

M5 todavía **NO está autorizado para implementación**.

Este chat tiene una sola responsabilidad:

**definir y cerrar el contrato de M5 — Canonical Results antes de permitir trabajo en Codex.**

No desarrollar código. No modificar M2, M3 ni M4. No migrar Web. No construir EXPLORA Excel. No modificar EXPLORA NG. No cambiar metodologías de weights o significance. No cambiar SQLite productivo como consecuencia de este contrato.

---

## 1. OBJETIVO DE M5

M5 debe establecer una representación oficial, determinística y renderer-neutral de los resultados producidos por EXPLORA Core.

La secuencia TARGET queda:

`Released Project Spec → Core execution → Canonical Results → Web / Excel`

Web y Excel deben poder recibir posteriormente el mismo `result_run_id` y los mismos registros analíticos.

M5 no debe calcular una versión para Web y otra para Excel.

M5 tampoco debe convertir una tabla visual en la nueva fuente de verdad.

El objeto actual:

`ReportResult.table`

puede seguir existiendo en LEGACY, pero **no será el contrato canónico**.

---

## 2. CURRENT STATE

Actualmente `ReportResult` mezcla responsabilidades.

Contiene simultáneamente identidad de pregunta, configuración analítica, bases, filtros, banners, ponderador, resultados, significancia, tablas wide, summaries, warnings, notas e incluso objetos relacionados con presentación.

La tabla final ya está estructurada alrededor de necesidades de visualización/exportación, con columnas del tipo:

`Total | %`

`Total | n`

`Banner A | %`

`Banner A | n`

Eso funciona para el sistema actual, pero no es una fuente única apropiada para Web + Excel.

SQLite tampoco constituye por sí mismo el resultado canónico: persiste datos analíticos y metadata útiles, pero parte del resultado oficial sigue dependiendo de ejecución runtime.

---

## 3. TARGET STATE

Analytics Core debe producir un:

`CanonicalResult`

que represente exclusivamente verdad analítica.

Debe ser independiente de:

HTML, Plotly, Streamlit, Excel, posiciones de celdas, VBA, colores, tamaños, columnas físicas del reporte o cualquier otra decisión de renderer.

Canonical Results debe contener todo lo necesario para reconstruir de manera determinística una salida analítica sin recalcular estadísticas fuera del Core.

El modelo lógico mínimo será:

```text
CanonicalResult
│
├── manifest
├── request
├── slices
├── bases
├── values
├── significance
├── warnings
└── qa
```

---

## 4. PRINCIPIO CENTRAL DE AUTORIDAD

Una vez generado un Canonical Result válido:

**el número almacenado en Canonical Results es el resultado analítico oficial del run.**

Web puede formatearlo.

Excel puede formatearlo.

Un export puede pivotarlo.

Un Visual Spec puede ordenar o decidir cómo mostrarlo.

Pero ninguno puede recalcular:

- porcentajes;
- bases;
- medias;
- scores;
- NPS;
- rankings analíticos;
- pesos;
- significancia;
- denominadores.

Si un renderer necesita un valor que no existe en Canonical Results, debe solicitar una nueva ejecución válida al Core.

No puede inferirlo.

---

## 5. RESULT RUN

Cada ejecución canónica debe tener una identidad inmutable:

`result_run_id`

Un `result_run_id` representa una ejecución específica con un conjunto específico de inputs, configuración, reglas y código.

Como mínimo debe quedar vinculado a:

```text
project_id
dataset_fingerprint
project_spec_version
project_spec_hash
analytics_core_version
ruleset_version
feature_flags
canonical_result_schema_version
executed_at
qa_release_status
```

Un cambio que pueda modificar resultados requiere un nuevo `result_run_id`.

Un run histórico no se modifica retroactivamente.

---

## 6. REQUEST SNAPSHOT

Canonical Results debe conservar qué fue solicitado al Core.

Esto incluye conceptualmente:

```text
question_ids
metric_refs
banner_selection
filter_selection
weight_ref
execution / compatibility profile
```

Este bloque documenta la solicitud.

No sustituye los Specs liberados ni redefine metodología.

La selección de filtros interactivos debe quedar diferenciada del Universe metodológico establecido por M2.

---

## 7. SLICE CONTRACT

Una columna analítica no debe identificarse mediante texto visual como:

`CDMX - Hombres - 18 a 24`

Debe existir un identificador estable:

`slice_id`

Un slice representa una combinación analítica exacta de Total, banner members y filtros aplicados.

Ejemplo conceptual:

```yaml
slice_id: S00017
banner_members:
  - dimension_id: REGION
    member_id: CDMX
  - dimension_id: SEX
    member_id: MALE
user_filters:
  - ...
```

Las etiquetas son metadata.

La identidad analítica son IDs.

---

## 8. BASE CONTRACT

Las bases se almacenan como objetos explícitos.

No deben deducirse posteriormente desde porcentajes ni desde tablas renderer-friendly.

Base mínima:

```yaml
base_id:
question_id:
row_member_id:
column_member_id:
slice_id:
universe_ref:
unweighted_n:
weighted_n_raw:
weighted_n:
effective_n:
```

Los campos aplicables dependerán de la estructura.

Las definiciones establecidas en M2, M3 y M4 no se reinterpretan aquí.

En particular:

`unweighted_n`

continúa siendo respondent count según el universo/aplicabilidad correspondiente.

`weighted_n_raw`

y

`weighted_n`

continúan siguiendo B1/M3.

`effective_n`

continúa siendo exclusivamente el diagnóstico Kish aprobado y no reemplaza bases descriptivas ni inferenciales.

---

## 9. RESPONDENT VS MENTION DENOMINATORS

M5 debe preservar explícitamente la separación cerrada en M4.

Un denominador respondent-level y un denominador mention-level **no pueden compartir identidad aunque numéricamente coincidan accidentalmente**.

Canonical Results debe poder representar como mínimo la semántica del denominator/base.

Por ejemplo:

```text
RESPONDENT
MENTION
VALID_CATEGORY
APPLICABLE_RESPONDENT
```

o referencias equivalentes al ledger producido por M4.

No debe reconstruirse el tipo de base observando la métrica o el label.

La autoridad procede del contrato Core/M4.

---

## 10. VALUE CONTRACT

Cada resultado analítico debe existir como un registro largo independiente.

Grain conceptual:

```yaml
value_id:
question_id:
structure_type:
row_member_id:
column_member_id:
category_id:
slice_id:
metric_id:
formula_id:
base_id:
numerator:
denominator:
estimate:
unit:
status:
```

No todos los campos aplican a todas las estructuras, pero la combinación de IDs debe identificar inequívocamente una observación analítica.

`estimate` es el resultado oficial.

`numerator` y `denominator`, cuando sean metodológicamente aplicables, permiten trazabilidad y QA.

No son campos destinados a que el renderer vuelva a calcular `estimate`.

---

## 11. UNIT CONTRACT

La unidad debe ser explícita.

Como mínimo M5 debe distinguir semánticamente resultados como:

`count`

`proportion`

`percent`

`mean`

`score`

`rank`

y otras unidades futuras aprobadas.

Un renderer no debe decidir que `0.52` significa 52% porque conoce la pregunta.

Debe saberlo mediante el contrato.

---

## 12. FORMULA PROVENANCE

Todo valor debe identificar el cálculo determinístico que lo produjo.

Por ello:

`metric_id`

y

`formula_id`

son conceptos distintos.

`metric_id` identifica la métrica solicitada/configurada.

`formula_id` identifica la implementación metodológica/versionada usada por Core.

Esto permitirá saber posteriormente no sólo que un valor era `MEAN`, sino qué regla canónica lo produjo.

No se define una nueva metodología en M5.

Se registra la metodología ya autorizada.

---

## 13. NULL / EMPTY / UNSUPPORTED / ERROR

M5 no debe permitir que todos los estados problemáticos se representen mediante una celda vacía.

Un valor puede necesitar estados estructurados como:

```text
OK
EMPTY_BASE
UNSUPPORTED
ERROR
```

La distinción es crítica.

`EMPTY_BASE` significa que no existe base suficiente para producir matemáticamente el resultado.

`UNSUPPORTED` significa que EXPLORA V1 no tiene autoridad/metodología para producirlo.

`ERROR` significa que una ejecución esperada falló.

`null` no debe utilizarse como sustituto silencioso de estas semánticas.

---

## 14. SIGNIFICANCE CONTRACT

Significance debe almacenarse separada de `values`.

No debe convertirse en letras incrustadas dentro de `estimate`, labels de columnas o strings como:

`42% A`

El Canonical Result debe conservar las comparaciones pairwise oficiales producidas conforme a B2.

Conceptualmente:

```yaml
comparison_id:
question_id:
metric_id:
row/category scope:
slice_a:
slice_b:
test_id:
confidence_level:
p_value:
adjusted_p_value:
decision:
status:
```

Sólo deberán aparecer comparaciones que Core tenga autoridad para producir.

Los dominios declarados `UNSUPPORTED V1` por B2 continúan siendo `UNSUPPORTED`.

M5 no amplía significance.

Las letras A/B/C son presentación derivada de relaciones pairwise ya oficiales; no son la verdad estadística primaria.

---

## 15. WARNINGS CONTRACT

Warnings deben ser datos estructurados.

Como mínimo necesitan:

```text
code
severity
scope
related IDs
blocking
message
evidence/details
```

Un warning puede aplicar a:

`run`

`question`

`row`

`cell`

`metric`

o posteriormente a un renderer.

No debe existir una situación donde una advertencia metodológicamente relevante solamente aparezca como texto libre debajo de una gráfica.

---

## 16. QA CONTRACT

Canonical Results debe transportar evidencia suficiente de QA para distinguir:

```text
PASS
PASS_WITH_WARNINGS
FAIL
REVIEW_REQUIRED
```

Un Canonical Result con `FAIL` puede existir como artefacto interno de diagnóstico.

Eso no lo convierte en resultado oficial liberable.

La liberación productiva requiere cumplimiento del release gate correspondiente.

Una excepción humana, si se permite por las políticas ya aprobadas, debe quedar explícitamente versionada y trazable.

No debe eliminar la evidencia original del problema.

---

## 17. IMMUTABILITY

Un Canonical Result liberado es inmutable.

Si cambia cualquiera de los elementos que afectan el resultado:

dataset, Project Spec, Question/Structure/Universe/Weight/Metric/Significance Spec, Core, reglas o feature flags relevantes,

se ejecuta un nuevo run.

No se actualiza silenciosamente el anterior.

---

## 18. DETERMINISTIC RECONSTRUCTION

Éste debe ser un acceptance criterion fundamental de M5.

Partiendo del mismo:

dataset fingerprint + released specs + Core version + ruleset + feature flags

debe poder reconstruirse el mismo Canonical Result dentro de las tolerancias numéricas definidas por tests.

La reconstrucción debe comprobar identidad y semántica, no simplemente comparar una tabla visual.

---

## 19. ORDERING

Canonical Results puede almacenar claves de orden semántico, por ejemplo:

`question_order`

`row_order`

`category_order`

cuando ese orden forma parte del significado/configuración.

No debe almacenar:

coordenadas de Excel, pixel positions, Plotly traces, width de columnas, CSS o posiciones físicas.

Orden semántico pertenece al contrato.

Layout pertenece al renderer.

---

## 20. LABELS

Los joins analíticos deben utilizar IDs estables.

Los labels pueden almacenarse como metadata o resolverse desde Specs.

Nunca deben ser utilizados como primary key analítica.

Cambiar:

`Ciudad de México`

por:

`CDMX`

no debe crear una nueva celda estadística si el `member_id` es el mismo.

---

## 21. PHYSICAL PERSISTENCE BOUNDARY

M5 debe congelar el **schema lógico**, no decidir todavía que la única implementación válida sea:

SQLite,

Parquet,

JSON,

o cualquier combinación específica.

La persistencia física puede definirse mediante una decisión de implementación posterior, siempre que conserve exactamente la semántica canónica.

Por lo tanto M5 no autoriza rediseñar el SQLite productivo actual.

---

## 22. LEGACY COMPATIBILITY

Durante M5 deben coexistir:

```text
result_contract = reportresult_legacy
result_contract = canonical_v1
```

`reportresult_legacy` sigue siendo el comportamiento productivo mientras no exista autorización de migración.

`canonical_v1` debe poder ejecutarse en validación/dual-run sin obligar todavía a Web a consumirlo.

Una ejecución oficial no debe mezclar silenciosamente celdas Legacy y Canonical dentro del mismo resultado.

---

## 23. RELATIONSHIP WITH REPORTRESULT

`ReportResult` no desaparece en M5.

El contrato debe permitir que inicialmente funcione como:

compatibility/output object

mientras Canonical Results se construye como nueva autoridad analítica.

La dirección futura correcta es:

```text
Canonical Results
       ↓
renderer/adaptor
       ↓
ReportResult-compatible presentation
```

y no:

```text
ReportResult.table
       ↓
reverse engineering
       ↓
Canonical Results
```

---

## 24. RELATIONSHIP WITH M4

M5 debe consumir la representación normalizada producida por M4.

No debe volver a inferir:

RU/RM, GRID, LOOP, selected state, applicability, duplicates, exclusives, denominator type o category validity.

Si M5 detecta una inconsistencia en un output M4, debe generar QA/error.

No debe corregirla semánticamente.

---

## 25. RELATIONSHIP WITH M3

M5 registra los resultados y las bases de weight execution.

No implementa ni modifica:

normalization,

trimming,

capping,

missing handling,

zero/negative behavior,

Kish effective N,

ni ninguna otra política B1/M3.

Debe conservar exactamente lo que Core produjo bajo el Weight Contract.

---

## 26. RELATIONSHIP WITH M2

`Universe Spec` continúa siendo autoridad sobre elegibilidad analítica.

M5 registra qué universo/base originó cada resultado.

No vuelve a decidir quién pertenece a la base.

---

## 27. RELATIONSHIP WITH B2

M5 transporta significance.

No redefine significance.

Cualquier método no autorizado en `SIGNIFICANCE_POLICY_CANONICAL.md` debe continuar explícitamente como no soportado.

---

## 28. RELATIONSHIP WITH WEB AND EXCEL

M5 no migra ningún renderer.

Pero debe cerrar el contrato necesario para que M6 pueda hacer:

```text
Web → Canonical Results
```

y M7 posteriormente:

```text
Excel → mismos Canonical Results
```

Dos renderers pueden producir apariencias diferentes.

No pueden producir valores distintos para el mismo `value_id`.

---

## 29. REQUIRED M5 INVARIANTS

Para cerrar el contrato propongo congelar estas invariantes:

1. Un resultado oficial posee un único `result_run_id`.
2. Released Canonical Results son inmutables.
3. Analytical identity usa IDs, no labels.
4. Cada `value` referencia una base explícita cuando la métrica la requiere.
5. Respondent denominators y mention denominators nunca se confunden.
6. `estimate` no se recalcula en renderers.
7. Significance se almacena aparte de values.
8. Warnings y QA son estructurados.
9. `null`, `EMPTY_BASE`, `UNSUPPORTED` y `ERROR` no son equivalentes.
10. Weight semantics provienen exclusivamente de M3/B1.
11. Universe semantics provienen exclusivamente de M2.
12. Structure/applicability semantics provienen exclusivamente de M4.
13. Significance semantics provienen exclusivamente de B2.
14. No existe renderer-specific analytical calculation dentro del contrato.
15. El schema lógico es independiente de la tecnología física de persistencia.
16. Un cambio material de inputs/configuración/reglas produce un nuevo run.
17. Un run FAIL puede conservarse para diagnóstico, pero no liberarse como oficial.
18. LEGACY continúa siendo default hasta un gate posterior.
19. M5 no cambia resultados productivos Legacy.
20. M5 debe permitir comparación determinística Legacy ↔ Canonical antes de M6.

---

## 30. VALIDATION REQUIRED FOR IMPLEMENTATION

Cuando posteriormente se autorice Codex, M5 deberá demostrar al menos:

totales; banners; filtros; combinaciones de slices; RU; RM respondent%; RM mention%; GRID\_RM; GRID\_ESCALA; LOOP structures soportadas por M4; weighted/unweighted execution conforme a M3; metric values; significance soportada por B2; unsupported significance; empty bases; denominator identity; warning propagation; QA propagation; manifest/provenance; schema validation; serialization/deserialization; deterministic reconstruction; dual-run contra Legacy; y ausencia de numerical deltas no explicados.

Los benchmarks GRID/LOOP que todavía tienen warnings de evidencia productiva no deben transformarse artificialmente en una regla universal para aprobar M5.

---

## 31. OUT OF SCOPE

Para evitar expansión accidental, quedan fuera de M5:

Web renderer migration, Excel renderer, VBA, Visual Spec implementation, dashboard redesign, nueva significance methodology, nueva weight methodology, nuevas métricas no aprobadas, cambios a NG, cambio de Project Spec semántico, reemplazo del SQLite productivo, removal de Legacy y optimización de performance que altere semántica.

---

## 32. ACCEPTANCE GATE PROPUESTO

M5 sólo debería declararse `CONTRACT READY` cuando podamos responder **YES** a estas cinco preguntas:

**Authority:** ¿Canonical Results es inequívocamente la única fuente de verdad numérica para un run canónico?

**Identity:** ¿cada run, slice, base, value y comparison puede identificarse sin depender de labels o layouts?

**Semantics:** ¿bases, weights, structures y significance conservan exactamente las autoridades ya congeladas en M2/M3/M4/B2?

**Traceability:** ¿un valor oficial puede rastrearse hasta proyecto, dataset, configuración, reglas, versión de Core y QA?

**Renderer independence:** ¿Web y Excel podrían consumir el mismo resultado sin tener que recalcular nada?

Si las cinco respuestas son YES y no aparecen contradicciones bloqueantes, el siguiente estado sería:

`M5 CONTRACT READY`

y sólo después:

`M5 CODEX READY = YES`

No autorizaría todavía Codex con este texto por sí solo. Primero conviene cerrar las decisiones de schema que aún admiten dos implementaciones válidas, especialmente **identidad exacta de** **`base_id`****/****`value_id`****, modelo de denominator reference, granularidad de QA/warnings y manifest mínimo obligatorio**. Ésas son las decisiones que debemos resolver en este chat antes del gate de implementación.

---

# APPENDIX — FINAL SCHEMA CLOSURE

El cierre queda consistente con el contrato M5 y resuelve las tensiones entre identidad de ejecución, identidad semántica, fingerprint determinístico y estados de QA/significance. Mantengo M2/M3/M4 y B1/B2/B3 como autoridades aguas arriba; M5 sólo ensambla y publica la verdad analítica renderer-neutral.

# M5 — FINAL SCHEMA CLOSURE

## M5 FINAL CONTRACT STATUS

**CONTRACT READY**

El schema lógico de M5 queda suficientemente cerrado para implementación incremental.

M5 define `CanonicalResult` como la representación analítica autoritativa posterior a Core. `CanonicalResult` no es `ReportResult`, y Web/Excel no podrán recalcular universes, denominators, weights, metrics, significance ni decisiones de QA.

Estado resultante:

`M5 CONTRACT READY = YES`

`M5 CODEX READY = YES`

`M5 IMPLEMENTATION AUTHORIZED = NO`

La implementación requiere autorización humana explícita posterior a este cierre.

No se autoriza M6.

---

## RESULT\_RUN\_ID DECISION

### DECISION — FROZEN V1

`result_run_id` identifica una ejecución concreta e inmutable.

Reglas:

- obligatorio;
- único por ejecución;
- una nueva ejecución siempre genera un nuevo `result_run_id`;
- dos ejecuciones con inputs idénticos siguen teniendo distintos `result_run_id`;
- no es un content hash;
- no puede reutilizarse para una reejecución;
- una corrida histórica nunca cambia de contenido.

Por tanto:

`execution identity != analytical equivalence identity`

La equivalencia analítica corresponde a `result_fingerprint`, no a `result_run_id`.

---

## RESULT\_FINGERPRINT DECISION

### DECISION — REQUIRED V1

`result_fingerprint` es obligatorio.

Debe representar de forma determinística el contenido analítico y metodológico del Canonical Result.

Dos ejecuciones distintas:

`result_run_id = A`

`result_run_id = B`

pueden producir:

`result_fingerprint = X`

si sus resultados canónicos son determinísticamente equivalentes.

### Canonical fingerprint input

Debe incorporar conceptualmente:

- dataset fingerprint;
- released Spec identities, versions y hashes;
- B1/B2/B3 versions/hashes;
- Analytics Core version;
- ruleset version;
- relevant feature flags;
- canonical request identity;
- canonical result schema version;
- canonical bases;
- canonical values;
- significance relations;
- deterministic QA/release state;
- deterministic provenance.

Debe excluir:

- `result_run_id`;
- execution timestamp;
- packaging timestamp;
- renderer metadata;
- insertion order;
- otros datos volátiles sin semántica analítica.

### Important identity rule

Los IDs de registros que sean run-scoped, como `base_id`, `value_id`, `comparison_id` o `qa_id`, no deben provocar fingerprints diferentes entre dos ejecuciones equivalentes.

Para el fingerprint se canonicaliza su **semantic identity payload**, no su identificador técnico dependiente de la corrida.

Esto resuelve la coexistencia de:

`unique execution IDs`

con:

`stable analytical fingerprint`.

---

## SLICE\_ID DECISION

### DECISION — FROZEN V1

`slice_id` representa una identidad analítica de slice.

No depende de labels.

Su identidad debe derivarse de una representación normalizada de:

- banner dimension IDs;
- banner member IDs;
- filter IDs;
- filter values;
- Total/member status;
- analytical slice configuration.

El orden visual de los banners no modifica el `slice_id` salvo que ese orden forme parte explícita de la configuración analítica.

Ejemplo:

`Male / CDMX`

y

`CDMX / Male`

son el mismo slice si representan exactamente la misma combinación semántica.

Cambiar:

`Ciudad de México`

por:

`CDMX`

tampoco cambia el slice cuando el member ID es el mismo.

---

## BASE\_ID DECISION

### DECISION — FROZEN V1

`base_id` identifica un denominator analítico exacto dentro de una ejecución.

Debe considerar, cuando aplique:

- `result_run_id`;
- `question_id`;
- `structure_id`;
- `slice_id`;
- `universe_ref`;
- `denominator_unit`;
- `denominator_ref`;
- `denominator_scope_id`;
- row/entity ID;
- column/option ID;
- loop instance ID;
- active weight reference.

Labels quedan excluidos.

Invariante:

**dos denominadores semánticamente diferentes nunca pueden compartir** **`base_id`****.**

Por tanto:

`RESPONDENT != MENTION`

aunque ambos produzcan exactamente:

`N = 100`.

Esto preserva directamente la separación cerrada por M4.

---

## DENOMINATOR REFERENCE DECISION

### DECISION — FROZEN V1

M5 nunca reconstruye denominators.

Cada Base mantiene referencia explícita a la autoridad/primitiva M4 que originó su denominator cuando corresponda.

Campos conceptuales obligatorios:

`denominator_unit`

`denominator_ref`

`denominator_scope_id`

`universe_ref`

`denominator_ref` es una identidad/referencia.

**No es el N numérico.**

El valor numérico pertenece al Base/primitives.

M4 conserva autoridad sobre:

- membership;
- applicability;
- valid category;
- respondent vs mention;
- structural states;
- option/row/loop scope.

M5 registra el resultado de esa autoridad y no vuelve a inferirla.

---

## BASE OBJECT V1

Base queda congelado conceptualmente con:

- `base_id`;
- `question_id`;
- `structure_id`;
- `slice_id`;
- row/entity ID cuando aplique;
- column/option ID cuando aplique;
- loop instance ID cuando aplique;
- `universe_ref`;
- `denominator_unit`;
- `denominator_ref`;
- `denominator_scope_id`;
- `unweighted_n`;
- `weighted_n_raw`;
- `weighted_n`;
- `effective_n`;
- active weight ID/ref;
- base status;
- `qa_refs`;
- provenance refs.

M5 no recalcula:

`unweighted_n`

`weighted_n_raw`

`weighted_n`

`effective_n`

Los consume según M3.

---

## VALUE\_ID DECISION

### DECISION — FROZEN V1

`value_id` identifica una celda **analítica**, nunca una celda visual.

Su identidad considera:

- `result_run_id`;
- `question_id`;
- `structure_id`;
- row/entity ID;
- column/option/category ID;
- loop instance ID cuando aplique;
- `slice_id`;
- `metric_id`;
- `formula_id`;
- `formula_version`;
- `base_id`.

Cambios de:

- label;
- display order no semántico;
- renderer;
- worksheet;
- chart;
- CSS;
- Excel coordinates;

no producen un nuevo `value_id`.

---

## VALUE RECORD V1

Value queda congelado con:

- `value_id`;
- analytical IDs;
- `metric_id`;
- `formula_id`;
- `formula_version`;
- `base_id`;
- numerator cuando aplique;
- denominator numeric primitive cuando aplique;
- `estimate`;
- `unit`;
- `value_status`;
- significance relation refs;
- `qa_refs`;
- provenance refs;
- semantic order metadata cuando forme parte de la configuración.

`estimate` es el valor analítico oficial.

Numerator y denominator existen para trazabilidad y QA.

No constituyen permiso para que Web, Excel o exports recalculen `estimate`.

---

## VALUE STATUS DECISION

### DECISION — FROZEN V1

No se utilizará un status universal para value, significance, QA y release.

`ValueStatus V1` queda:

`OK`

`NO_VALID_BASE`

`UNSUPPORTED`

`INELIGIBLE`

`ERROR`

### Important correction

`NOT_TESTED` **NO pertenece a ValueStatus**.

Es un concepto de significance.

Del mismo modo:

`REVIEW_REQUIRED`

y

`FAIL`

no son ValueStatus; pertenecen al QA/release model.

Esto evita justamente el colapso de vocabularios que M5 debe impedir.

Se congela además:

`NO_VALID_BASE != 0`

`UNSUPPORTED != NOT_TESTED`

`INELIGIBLE != NOT_SIGNIFICANT`

`ERROR != UNSUPPORTED`

El término canónico V1 será:

`NO_VALID_BASE`

No se mantendrá un segundo alias `EMPTY_BASE`.

---

## NUMERIC NULL RULE

### DECISION — FROZEN V1

Cuando:

`value_status != OK`

M5 no fabrica un número.

Ejemplo:

`NO_VALID_BASE`

produce:

`estimate = null`

nunca:

`estimate = 0`.

Un cero real y válido se representa:

`value_status = OK`

`estimate = 0`

JSON V1 prohíbe valores numéricos:

`NaN`

`Infinity`

`-Infinity`

Deben transformarse en:

structured status + `null`

según la causa correspondiente.

---

## PERCENT / PROPORTION DECISION

### DECISION — FROZEN V1

Las métricas porcentuales canónicas se almacenan como proporción 0–1.

Ejemplo:

`estimate = 0.52`

`unit = PROPORTION`

Renderer:

`52%`

No se permite que la misma métrica aparezca arbitrariamente unas veces como:

`0.52`

y otras como:

`52`.

`PERCENT` 0–100 sólo podrá existir como unidad diferente cuando una fórmula canónica aprobada produzca semánticamente esa escala.

No será la representación normal de porcentajes de frecuencia.

---

## QA EVENT MODEL DECISION

### DECISION — SINGLE STRUCTURED QA EVENT MODEL

QA será una colección estructurada independiente.

Cada QA event debe contener como mínimo:

- `qa_id`;
- `qa_domain`;
- `code`;
- severity/state;
- `blocking`;
- `scope_type`;
- related IDs;
- `message`;
- structured details/evidence;
- source component;
- applicable policy/rule version.

Domains mínimos:

`UNIVERSE`

`WEIGHT`

`STRUCTURE`

`METRIC`

`STATISTICAL`

`RESULT`

`RELEASE`

Scopes soportados:

- run;
- question;
- structure;
- slice;
- base;
- value;
- significance comparison.

Los domain-specific statuses de M2/M3/M4/B1/B2/B3 no se reemplazan por este modelo.

QA Event los transporta/referencia sin perder su semántica original.

---

## WARNING MODEL DECISION

### DECISION — WARNING IS QA EVENT

No existirán dos fuentes paralelas:

`warnings[]`

y

`qa[]`

para la misma evidencia.

Un warning es un QA event con severity equivalente a:

`WARN`.

Bases, Values, Comparisons y el run pueden contener:

`qa_refs`

o índices derivados de warnings para facilidad de consumo.

Pero la evidencia vive una sola vez.

No se replica físicamente el mismo warning en cientos de values.

---

## SIGNIFICANCE IDENTITY DECISION

### DECISION — FROZEN V1

`comparison_id` identifica una relación estadística pairwise canónica.

Su semantic identity incorpora:

- question;
- metric;
- analytical row/category scope;
- comparison family;
- left slice/member;
- right slice/member;
- test ID;
- test version.

Para tests no direccionales de B2 se utilizará canonical pair ordering.

Conceptualmente:

`pair(A,B) == pair(B,A)`

La identidad del pair se construye ordenando sus operandos por sus IDs canónicos.

La dirección del efecto, cuando aplique, es un atributo del resultado:

`direction`

no una segunda comparación.

No deben existir simultáneamente:

`A_vs_B`

y

`B_vs_A`

para representar el mismo test two-sided.

Las letras A/B/C continúan siendo presentation tokens derivados, nunca la autoridad estadística.

---

## SIGNIFICANCE STATUS DECISION

M5 no crea una segunda metodología.

Debe consumir o mapear inequívocamente el vocabulario B2.

Semánticas obligatorias:

`NOT_REQUESTED`

`UNSUPPORTED`

`INELIGIBLE`

`TESTED_NOT_SIGNIFICANT`

`TESTED_SIGNIFICANT`

Si B2 utiliza nombres de enum distintos, los tokens canónicos de B2 prevalecen.

M5 debe conservar una equivalencia uno-a-uno con estas cinco semánticas.

Especialmente:

`UNSUPPORTED != NOT_REQUESTED`

`INELIGIBLE != TESTED_NOT_SIGNIFICANT`

`no letter != not significant`.

Weighted significance continúa:

`UNSUPPORTED V1`.

NPS puede tener:

`ValueStatus = OK`

y simultáneamente significance:

`UNSUPPORTED`

sin contradicción.

---

## MANIFEST REQUIRED FIELDS

### REQUIRED V1

El manifest debe contener:

- `canonical_result_schema_version`;
- `serialization_version`;
- `result_run_id`;
- `result_fingerprint`;
- `project_id`;
- project version;
- dataset fingerprint;
- Project Spec version/hash;
- Question Spec versions/hashes usadas;
- Structure Spec versions/hashes usadas;
- Universe Spec versions/hashes usadas;
- Metric Spec versions/hashes usadas;
- Weight Spec versions/hashes usadas;
- Significance Spec versions/hashes usadas;
- B1 version/hash;
- B2 version/hash;
- B3 version/hash;
- Analytics Core version;
- ruleset version;
- execution mode;
- relevant feature flags;
- `request_id`;
- `request_fingerprint`;
- execution timestamp;
- `computation_status`;
- aggregate `qa_release_status`;
- `releasable`;
- slice count;
- base count;
- value count;
- comparison count;
- QA event count;
- optional `supersedes_result_run_id`.

Un campo no aplicable debe representarse explícitamente como `null` / not-used según schema.

No puede simplemente desaparecer creando ambigüedad.

La trazabilidad completa de Project, dataset, Specs, policies, Core y execution está explícitamente requerida por el contrato M5.

---

## REQUEST IDENTITY DECISION

Request snapshot tendrá:

`request_id`

y:

`request_fingerprint`.

`request_fingerprint` usa representación normalizada de:

- question IDs;
- metric refs;
- banner configuration;
- filters;
- weight overrides;
- compatibility profile;
- relevant execution options.

Labels no afectan request fingerprint.

---

## SERIALIZATION DECISION

### DECISION — JSON-COMPATIBLE REQUIRED V1

M5 requiere una representación interoperable JSON-compatible.

Esto no obliga a persistencia física JSON.

Requirements:

- UTF-8;
- stable field names;
- explicit null;
- no NaN/Infinity;
- versioned schema;
- deterministic ordering;
- analytical semantic round-trip lossless.

Posteriormente podrán existir:

- SQLite;
- Parquet;
- database records;
- APIs;

si preservan exactamente el mismo contrato.

M5 no autoriza rediseñar el SQLite productivo.

---

## DETERMINISTIC ORDERING DECISION

La serialización canónica deberá ordenar determinísticamente:

- slices;
- bases;
- values;
- comparisons;
- QA events.

El orden deberá derivarse de IDs y/o semantic-order keys aprobadas.

Python insertion order no es autoridad.

Un cambio en el orden accidental de construcción no puede alterar:

`result_fingerprint`.

---

## PRECISION DECISION

### DECISION — FULL CORE PRECISION

M5 conserva la precisión numérica producida por Core.

No aplica presentation rounding.

En particular no se redondean para display dentro de Canonical Results:

- weighted\_n;
- effective\_n;
- means;
- standard deviations;
- proportions;
- scores;
- p-values;
- adjusted p-values.

Floating tests utilizarán tolerancias explícitas cuando matemáticamente corresponda.

El renderer es responsable únicamente del formato visible.

Ejemplo:

Canonical:

`0.523746128`

Renderer:

`52.4%`

sin cambiar el valor canónico.

---

## METRIC EXECUTION SCOPE V1

### DECISION — FROZEN V1

M5 puede ensamblar/ejecutar únicamente fórmulas determinísticas aprobadas en Metric Specs sobre primitives autorizados de M2/M3/M4.

Scope V1:

`COUNT`

`FREQUENCY / PROPORTION`

`MEAN`

`STANDARD_DEVIATION`

`TOP_BOX`

`BOTTOM_BOX`

y otras box derivations sólo cuando estén explícitamente definidas en Metric Spec;

`NPS_DESCRIPTIVE`

`RM_RESPONDENT_PROPORTION`

`RM_MENTION_PROPORTION`

approved scale metrics.

Para:

`LOOP_NUMERICO`

se permiten métricas numéricas solamente cuando exista un Metric Spec aprobado y una fórmula registrada compatible.

No quedan autorizados por inferencia:

- nuevas métricas;
- custom formulas libres;
- renderer-calculated metrics;
- weighted significance;
- una fórmula desconocida encontrada en configuración.

La separación entre M4 primitives y final metric values queda congelada como parte del límite de M5.

---

## FORMULA REGISTRY DECISION

### DECISION — REQUIRED MINIMUM V1 REGISTRY

M5 necesita un Formula Registry explícito para todas las fórmulas V1 que ejecute.

Cada entry debe declarar:

`formula_id`

`formula_version`

input requirements

denominator requirements

supported structures

supported weight modes

significance compatibility.

No se permiten fórmulas identificadas mediante texto libre.

### Unknown vs unsupported

Se congela esta diferencia:

**Unknown** **`formula_id`**

→ contract/configuration error
→ blocking QA
→ no silent execution
→ run no releasable.

**Known formula, unsupported para esa structure/weight combination**

→ `value_status = UNSUPPORTED`
→ QA estructurado según aplique.

Esto evita transformar una mala configuración en un resultado silenciosamente vacío.

El registry completo puede ampliarse en futuros milestones, pero las fórmulas utilizadas por M5 V1 deben estar registradas/versionadas desde M5.

---

## RELEASE MODEL DECISION

### DECISION — THREE SEPARATE CONCEPTS

Se congelan:

`computation_status`

`qa_release_status`

`releasable`

### ComputationStatus

Semántica mínima:

`COMPLETE`

`PARTIAL`

`FAILED`

Describe si la ejecución pudo producir el package solicitado.

No describe aprobación metodológica.

### QAReleaseStatus

Utiliza:

`PASS`

`PASS_WITH_WARNINGS`

`REVIEW_REQUIRED`

`FAIL`

Describe la evaluación de QA/release.

### releasable

Boolean determinístico derivado del release gate/B3.

No es editable libremente.

Un run puede ser:

`computation_status = COMPLETE`

pero:

`qa_release_status = REVIEW_REQUIRED`

y:

`releasable = false`.

La existencia de números nunca implica que puedan liberarse.

Sólo un run que cumpla B3 y el release gate aplicable puede marcar:

`releasable = true`.

---

## IMMUTABILITY DECISION

### DECISION — ABSOLUTE AFTER EMISSION

Un CanonicalResult emitido nunca se modifica in-place.

Cambios en:

- dataset;
- Project Spec;
- Question Spec;
- Universe Spec;
- Structure Spec;
- Metric Spec;
- Weight Spec;
- Significance Spec;
- policy;
- formula;
- Core;
- ruleset;
- relevant feature flags;

generan un nuevo:

`result_run_id`.

Puede registrarse opcionalmente:

`supersedes_result_run_id`

para establecer lineage.

El resultado anterior permanece intacto y auditable.

---

## LEGACY COMPARISON DECISION

### DECISION — DUAL-RUN REQUIRED BEFORE M6

M5 debe soportar comparación:

`LEGACY`

vs

`CANONICAL_V1`

Las diferencias se clasifican exclusivamente como:
