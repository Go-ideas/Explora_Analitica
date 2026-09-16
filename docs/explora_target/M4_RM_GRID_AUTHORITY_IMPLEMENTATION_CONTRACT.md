# M4 — RM / GRID AUTHORITY CONTRACT

**Contract status:** READY FOR HUMAN APPROVAL
**M4 implementation authorized:** NO
**Legacy default:** PRESERVED
**M2:** CLOSED / IMMUTABLE
**M3:** CLOSED / IMMUTABLE
**M5:** NOT STARTED

---

# M4 IMPLEMENTATION SCOPE

M4 establece la autoridad canónica de estructura y normalización analítica para:

- `RU`
- `RM`
- `GRID_ESCALA`
- `GRID_RM`
- `LOOP_RM`
- `LOOP_RU`
- `LOOP_NUMERICO`

M4 es responsable de determinar, exclusivamente desde contratos `RELEASED`:

- qué estructura analítica representa una pregunta;
- qué variables físicas pertenecen a esa estructura;
- qué relación parent/child existe;
- cuáles son los ejes row/entity y column/option;
- qué respondent, entity, option o cell es aplicable;
- qué significa una selección;
- qué significa una no-selección;
- qué constituye ordinary missing;
- qué constituye structural missing;
- qué cero representa una no-selección estructural;
- cuál es la unidad válida para construir cada denominador;
- cómo se normalizan RM, grids y loops antes de cualquier cálculo final.

M4 NO es un nuevo motor de reporteo.

Su producto es una representación analítica renderer-neutral suficientemente explícita para que M5 construya Canonical Results sin volver a inferir estructura.

M4 debe quedar detrás de:

`structure_authority = legacy_inference | released_spec`

El default continúa siendo:

`legacy_inference`

hasta autorización y migración posterior.

M4 no cambia resultados Legacy por defecto.

---

# STRUCTURE AUTHORITY MODEL

La precedencia canónica queda congelada así:

**Released Project Spec**
**→ Released Question Spec**
**→ Released Structure Spec**
**→ Released Universe Specs referenciados**
**→ dataset físico únicamente como evidencia/validación**

Runtime inference queda por debajo de todos ellos.

Regla central:

**RELEASED Structure/Question Specs > runtime inference**

Un detector runtime puede sugerir, validar o señalar una contradicción, pero nunca modificar la estructura utilizada por una ejecución canónica.

## Distribución de autoridad

**Question Spec** es autoridad para:

- `question_id`;
- rol analítico;
- referencia al Structure Spec;
- referencia al Universe Spec de pregunta;
- dominio/categorías cuando corresponda;
- referencias a Metric/Weight/Significance Specs;
- estado de release.

**Structure Spec** es autoridad para:

- `structure_id` y versión;
- tipo analítico;
- parent;
- row/entity axis;
- column/option axis;
- members estables de los ejes;
- variable bindings;
- category/option bindings;
- storage encoding;
- applicability adicional por row/column/cell;
- selected semantics;
- not-selected semantics;
- response completion semantics;
- structural zero semantics;
- structural missing semantics;
- duplicate policy;
- exclusive-option policy;
- loop instance identity.

**Universe Spec / M2** es autoridad exclusiva para ejecutar las expresiones de universo/applicability referenciadas.

Structure Spec decide **qué UniverseRef corresponde a qué scope**.

M2 decide **si ese UniverseRef evalúa TRUE/FALSE/FAIL/UNSUPPORTED para cada respondent**.

M4 no implementa nuevamente las expresiones de universo.

## Regla de conflicto

Si un RELEASED Question Spec y su RELEASED Structure Spec contienen campos que deberían ser consistentes y no coinciden:

`FAIL`

No se utiliza heurística para escoger uno.

## Release authority

Sólo:

`release_state = RELEASED`

puede ser autoridad canónica.

`DRAFT`, `REVIEW`, candidatos ambiguos o estructuras inferidas no pueden producir ejecución canónica oficial.

Un Project Spec debe fijar las versiones exactas que consume.

---

# PHYSICAL VS ANALYTICAL STRUCTURE

M4 congela una separación explícita.

**Physical storage structure** describe cómo está codificada la información:

- una variable;
- múltiples columnas binarias;
- slots de menciones;
- una variable por row;
- matriz entity × option;
- variables repetidas;
- registros long;
- otras representaciones explícitamente declaradas.

**Analytical structure** describe qué significa:

- RU;
- RM;
- GRID\_ESCALA;
- GRID\_RM;
- LOOP\_RM;
- LOOP\_RU;
- LOOP\_NUMERICO.

No existe una relación automática entre número de variables y tipo analítico.

Por tanto:

`multiple physical variables != automatically RM`

y:

`entity × option naming pattern != automatically GRID_RM`

Los sufijos de variables, labels, cantidad de columnas, missing patterns o value labels pueden ser evidencia de QA/importación, pero no autoridad en `released_spec`.

Los bindings RELEASED son los que conectan almacenamiento físico y estructura analítica.

---

# RU CONTRACT

Una RU canónica produce para cada respondent exactamente uno de estos estados analíticos relevantes:

`VALID_CATEGORY`

`ORDINARY_MISSING`

`STRUCTURAL_MISSING`

`INVALID_OUT_OF_DOMAIN`

## Valid response

Una respuesta es válida cuando:

- el respondent pertenece al universo M2 correspondiente;
- las reglas adicionales de applicability aplican;
- el valor físico se encuentra vinculado explícitamente a un `category_id` permitido;
- ese código no está declarado como missing.

## Ordinary missing

El respondent es aplicable, pero no existe una respuesta válida.

Incluye los missing codes que el RELEASED Question/Structure Spec declare como ordinary/user/system missing.

Ordinary missing no forma parte del denominador válido salvo que una categoría originalmente considerada missing haya sido convertida explícitamente en una categoría analítica RELEASED.

## Structural missing

La observación no debía existir analíticamente porque el respondent/cell no era aplicable.

No es una respuesta omitida.

## Denominator

Para frecuencia/% RU:

`denominator = applicable respondents with VALID_CATEGORY`

No incluye:

- M2-excluded;
- structural missing;
- ordinary missing;
- invalid/out-of-domain.

## Category identity

La identidad es `category_id`, no el texto visible.

Los raw codes se vinculan a un category ID estable.

Labels son presentación.

## Unknown/out-of-domain

Un valor no missing observado que no pueda mapearse a una categoría RELEASED:

`FAIL` para la ejecución canónica de la pregunta afectada.

No se convierte automáticamente en:

- Other;
- Missing;
- 0;
- categoría nueva.

---

# RM CONTRACT

La unidad analítica básica de RM es:

`respondent × option`

y, para estructuras más complejas:

`respondent × entity/row × option`

Cada unidad debe quedar normalizada en uno de estos estados:

`SELECTED`

`NOT_SELECTED`

`ORDINARY_MISSING`

`STRUCTURAL_MISSING`

o un estado explícito de dato inválido para QA.

Las siguientes identidades quedan congeladas:

`NOT_SELECTED != MISSING`

`NOT_SELECTED != NOT_APPLICABLE`

`MISSING != STRUCTURAL_MISSING`

## Respondent-level applicability

Determina si el respondent pertenece a la estructura/pregunta.

Su punto de partida es M2.

## Option-level applicability

Determina si una opción específica es válida para ese respondent.

Puede incluir UniverseRefs RELEASED de column/cell scope.

## SELECTED

Requiere evidencia compatible con los bindings y `selected_values` RELEASED.

No puede inferirse exclusivamente del label.

## NOT\_SELECTED

Sólo puede producirse si:

1. el respondent/option es aplicable; y
2. existe evidencia determinística de que la respuesta es válida; y
3. la opción no fue seleccionada según el encoding RELEASED.

Ejemplos válidos:

- dummy declarado `1=selected`, `0=not_selected`;
- set de slots respondido válidamente donde Structure Spec declara que las opciones no mencionadas representan `NOT_SELECTED`;
- representación sparse cuya completion rule RELEASED garantiza que la ausencia de la opción significa no-selección.

La mera ausencia de una fila en una tabla long NO es evidencia suficiente.

## Response completion

Las estructuras sparse/slot deben declarar una regla explícita de completion.

Como mínimo debe distinguir:

- conjunto respondido;
- conjunto totalmente missing;
- código explícito de ninguna opción;
- selección válida parcial/completa según diseño.

`all slots missing` no puede transformarse automáticamente en una respuesta válida con cero selecciones.

## Exclusivas

La exclusividad utiliza `category_id`/`option_id` RELEASED.

Nunca substrings como:

`ninguna`

`no aplica`

u otros hints textuales.

Si una opción declarada exclusiva aparece simultáneamente con otra selección, Canonical M4 preserva la evidencia original y genera QA.

No elimina silenciosamente una opción para corregir el dato.

Para V1, una violación de exclusividad no resuelta bloquea el resultado oficial afectado.

## Duplicados

El Structure Spec debe declarar:

`keep`

`deduplicate_by_category`

o

`error`

La política afecta menciones.

Nunca altera que un respondent cuente como máximo una vez por option en RM respondent %.

---

# RM RESPONDENT % CONTRACT

Para opción `o`:

`numerator(o) = unique respondents with state SELECTED for o`

`denominator(o) = unique respondents for whom o is applicable and whose response state for o is metric-valid`

Los estados que forman el denominador son:

`SELECTED`

-

`NOT_SELECTED`

No forman denominador:

`ORDINARY_MISSING`

`STRUCTURAL_MISSING`

`OUT_OF_UNIVERSE`

`INVALID`

Por tanto:

`RM respondent % = selected unique respondents / valid eligible respondents`

Un respondent cuenta máximo una vez por opción.

## Consecuencia importante

Un respondent que esté válidamente en la pregunta y tenga todas las opciones en estado `NOT_SELECTED` debe permanecer en la base.

Este contrato corrige específicamente el riesgo AS-IS donde respondents zero-only pueden desaparecer si la base se reconstruye únicamente desde filas seleccionadas de `multirrespuesta_long`.

## Denominator by option

Si la applicability cambia por opción:

`denominator(option A)`

puede ser diferente de:

`denominator(option B)`

No existe obligación de utilizar una base RM común cuando Structure Spec indique applicabilities distintas.

## Zero denominator

Si el denominador válido es 0:

el resultado no es `0%`.

Debe quedar como:

`NO_VALID_BASE`

o equivalente estructurado para consumo posterior por M5.

---

# RM MENTION % CONTRACT

RM mention % usa como unidad una **mención válida**, no un respondent.

Una mención válida es un evento de selección que:

- pertenece a un respondent aplicable;
- pertenece a una opción aplicable;
- está permitido por los bindings RELEASED;
- pasa la política de duplicados;
- no corresponde a structural missing;
- no contiene un option/category desconocido.

Para opción `o`:

`numerator_mentions(o) = valid mention events of o`

El denominador es:

`total valid mention events in the explicitly declared mention-denominator scope`

Por tanto:

`RM mention % = mentions of option / total valid mentions in scope`

`NOT_SELECTED` no genera menciones.

Un respondent puede aportar múltiples menciones al denominador.

Una misma opción puede producir más de una mención del mismo respondent únicamente cuando la estructura lo permite y:

`duplicate_policy = keep`

Con:

`deduplicate_by_category`

un respondent-option aporta como máximo una mención dentro del scope correspondiente.

## Mention denominator scope

No puede quedar implícito.

Structure/Metric configuration debe identificar el scope, por ejemplo:

- parent RM;
- entity/row dentro de GRID\_RM;
- repeated instance;
- otro grupo analítico RELEASED.

Especialmente en GRID/LOOP:

no se permite asumir automáticamente que todas las entities comparten un único denominator de menciones.

## Distinción obligatoria

`respondent %`

y

`mention %`

son métricas diferentes.

No pueden reutilizar silenciosamente el mismo denominator.

---

# STRUCTURAL ZERO RULE

Para M4, structural zero significa:

**la unidad respondent-option/cell es aplicable, la respuesta está suficientemente definida como válida y la opción no fue seleccionada.**

Semánticamente corresponde a:

`NOT_SELECTED`

Structural zero puede provenir de:

- un `0` físico declarado explícitamente como not-selected;
- una representación sparse que Structure Spec autorice convertir determinísticamente a not-selected.

No puede deducirse únicamente de:

- encontrar un `0`;
- encontrar un missing;
- no encontrar una fila;
- sparse columns;
- sufijos de variables;
- nombres de variables;
- patrones observados en los datos.

## Regla de precedencia

En RM/Grid/Loop:

los valores físicos declarados como `not_selected_values` son mappings hacia el estado analítico `NOT_SELECTED`.

`structural_zero` no debe convertirse en una segunda semántica competidora.

Es una propiedad/origen del estado de no-selección.

Un `0` RU puede perfectamente ser una categoría válida si el Question Spec lo declara así.

Por tanto:

`raw value 0 != automatically structural zero`

---

# STRUCTURAL MISSING RULE

Structural missing significa:

**la unidad analítica no aplica.**

Puede ocurrir a nivel de:

- respondent;
- row/entity;
- option/column;
- cell;
- repeated instance.

Se deriva exclusivamente de applicabilities RELEASED evaluadas por M2 y compuestas por M4.

Structural missing:

`!= ordinary missing`

`!= unanswered`

`!= not selected`

`!= zero`

`!= invalid value`

No forma parte de numeradores ni denominadores.

M4 debe conservarlo explícitamente para QA y trazabilidad.

La ausencia de un dato físico no demuestra structural missing.

---

# GRID CONTRACT

## GRID\_ESCALA

Estructura analítica:

`respondent × row/entity → categorical/numeric scale response`

Debe declarar:

- stable `row_id/entity_id`;
- shared or explicitly bound scale domain;
- variable binding para cada row/entity;
- question applicability;
- row applicability;
- cualquier column/cell applicability aplicable;
- valid categories;
- missing semantics.

La base descriptiva de cada row se construye con respondents:

- aplicables a esa row;
- con respuesta válida para esa métrica.

Una row sin respuesta porque no aplicaba es structural missing.

Una row aplicable pero no respondida es ordinary missing.

La similitud de value labels entre varias variables no convierte por sí sola esas variables en GRID\_ESCALA.

## GRID\_RM

Unidad:

`respondent × row/entity × option`

Cada cell recibe la misma máquina de estados RM:

`SELECTED`

`NOT_SELECTED`

`ORDINARY_MISSING`

`STRUCTURAL_MISSING`

La applicability efectiva de una cell es la composición de:

`question applicability`

AND

`row applicability`

AND

`column applicability`

AND

`cell applicability`

usando exclusivamente masks producidos por M2 desde UniverseRefs RELEASED.

La base puede variar por:

- entity;
- option;
- cell.

No se fuerza una base común.

## Physical mapping

Los bindings RELEASED identifican explícitamente:

- variable física;
- row/entity member;
- column/option member.

M4 no parsea un nombre como `Q10_3_7` para descubrir row=3/option=7 en canonical execution.

Ese parsing puede existir únicamente en import-assist/QA.

## Missing physical binding

Si una variable requerida por un binding RELEASED no existe en el dataset:

`FAIL`

No se busca automáticamente una variable de nombre parecido.

---

# LOOP CONTRACT

Un loop necesita tres identidades diferentes cuando correspondan:

`respondent_id`

`entity_id`

`loop_instance_id`

`entity_id` representa la entidad semántica.

`loop_instance_id` representa la ocurrencia específica dentro del loop.

No deben tratarse como equivalentes.

## Parent relation

Todo loop debe mantener una relación explícita con su parent question/structure.

## LOOP\_RM

Unidad normalizada:

`respondent × loop_instance × option`

y, cuando exista entity semántica:

`respondent × entity × loop_instance × option`

Estados y denominadores siguen RM.

## LOOP\_RU

Unidad normalizada:

`respondent × loop_instance`

Cada instance aplicable debe tener:

- una categoría válida;
- ordinary missing;
- structural missing;
- invalid.

## LOOP\_NUMERICO

Unidad:

`respondent × loop_instance`

El valor debe conservarse como numeric valid o estado missing/applicability correspondiente.

M4 no define todavía nuevas fórmulas numéricas.

## Denominator identity

Para loops deben mantenerse al menos:

- número de respondents únicos;
- número de instances aplicables;
- número de instances válidas.

M4 no colapsa automáticamente instances a respondent level.

El Metric Spec posterior debe indicar qué unidad requiere.

## Independence

Dos instances del mismo respondent NO se consideran estadísticamente independientes.

M4 debe exponer esa dependencia en metadata/QA para evitar que capas posteriores la ignoren.

---

# M2 DEPENDENCY RULES

M2 permanece autoridad exclusiva de Universe execution.

M4:

- consume masks M2;
- no cambia masks;
- no reevalúa el AST/DSL;
- no inventa UniverseRefs;
- no convierte missing observado en Universe;
- no reemplaza un `FAIL`;
- no reemplaza un `UNSUPPORTED`;
- no hace fuzzy lookup de Universe IDs.

El orden conceptual permanece:

`M2 Universe`

→ `scope applicability`

→ `M4 response-state normalization`

→ `metric-valid denominator`

Cuando Structure Spec declara row/column/cell UniverseRefs, esos refs deben pasar por M2.

M4 únicamente compone sus resultados.

Si no existe una regla adicional para row/column/cell:

significa:

`no additional restriction`

No significa:

`infer from observed missing`.

`zero eligible respondents` sigue siendo una ejecución válida con base 0 cuando M2 ejecutó correctamente.

No se busca una base alternativa.

---

# M3 DEPENDENCY RULES

M3 no define estructura.

M4 debe resolver primero:

- applicability;
- analytical unit;
- response state;
- metric-valid membership.

Sólo después puede M3 definir contribución ponderada.

Orden obligatorio:

`M2 Universe`

→ `M4 Structure/applicability/metric-valid denominator`

→ `M3 weight contribution`

Consecuencias:

- un weight nunca convierte a alguien en applicable;
- un weight nunca convierte missing en selected/not-selected;
- un weight nunca descubre row/entity/option;
- `weight=0` no elimina al respondent de la estructura ni de los conteos unweighted correspondientes;
- invalid weight handling permanece exactamente como lo cerró M3;
- no se normalizan weights;
- no trimming/capping;
- no sustitución silenciosa por weight=1;
- `effective_n` Kish continúa siendo diagnóstico/QA únicamente.

La normalización estructural M4 debe producir exactamente los mismos estados con weighted mode ON u OFF.

Esto debe probarse explícitamente.

---

# B2 COMPATIBILITY RULES

M4 no ejecuta significance.

Únicamente entrega metadata suficiente para que B2 pueda decidir elegibilidad posteriormente.

## Potencialmente elegible

RM respondent % de:

**la misma opción**

comparada entre:

**grupos independientes de respondents**

puede ser candidata a los métodos B2 soportados.

Esto no significa automáticamente que el test se ejecute.

B2 deberá seguir comprobando todas sus condiciones canónicas.

## UNSUPPORTED V1

`RM mention significance`

permanece:

`UNSUPPORTED V1`

Comparaciones:

`option A vs option B within the same respondents`

permanecen:

`UNSUPPORTED V1`

Loops/repeated/panel:

no permiten asumir independencia entre instances.

Significance basada directamente en repeated instances queda:

`UNSUPPORTED V1`

salvo que en el futuro exista una metodología B2 explícitamente aprobada.

Weighted significance continúa:

`UNSUPPORTED V1`

M4 no cambia esta política.

---

# LEGACY MIGRATION PLAN

| Inteligencia actualTratamiento M4                               |                                                                                                                             |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `src/structure/grid_loop_detector.py`                           | **KEEP LEGACY + WRAP** como evidencia/import-assist/QA. **DEPRECATE LATER** como autoridad runtime.                         |
| Detección GRID/LOOP por value labels/contexto/patrones          | **DO NOT MIGRATE** como autoridad canónica.                                                                                 |
| `rm_long_builder.py::build_rm_long()`                           | **KEEP LEGACY** para Legacy/parity. La normalización equivalente se **MOVE TO CORE** pero reescrita para bindings RELEASED. |
| Detección RM por `tipo_pregunta/tipo_calculo` strings           | **KEEP LEGACY / DO NOT MIGRATE** como regla canónica.                                                                       |
| Detección dummy por subset `{0,1}`                              | **KEEP LEGACY**; en Core requiere selected/not-selected mappings explícitos.                                                |
| Opción RM obtenida del sufijo de variable                       | **DO NOT MIGRATE** como autoridad.                                                                                          |
| Slot RM: cualquier non-missing como mención                     | **WRAP/VALIDATE**; sólo se mueve a Core cuando Structure Spec declara ese encoding.                                         |
| `deduplicate_rm()`                                              | **KEEP LEGACY**; el mecanismo genérico se **MOVE TO CORE** gobernado por `duplicate_policy`.                                |
| `remove_exclusive_combinations()` por texto                     | **DO NOT MIGRATE**. Legacy puede conservarlo para parity; canonical usa IDs explícitos y QA, sin mutación silenciosa.       |
| `grid_loop_long_builder.py`                                     | **KEEP LEGACY**. El concepto de normalización se **MOVE TO CORE** basado en Structure Spec.                                 |
| `respuestas_grid_loop.base_valida/missing_estructural`          | **WRAP** como evidencia legacy; no sustituye M2/M4.                                                                         |
| `tabulator._apply_grid_rm_metadata()`                           | **KEEP LEGACY**, **DEPRECATE LATER**, **DO NOT MIGRATE** como canonical fallback.                                           |
| `rm_summary()`                                                  | **KEEP LEGACY** para regression. Denominator semantics canonical pasan a M4.                                                |
| `_grid_loop_rm_summary()`                                       | **KEEP LEGACY** para regression. No es autoridad canonical.                                                                 |
| `escalas_long_builder.py`                                       | **KEEP LEGACY**. Binding GRID\_ESCALA/response normalization se mueve conceptualmente a Core; métricas quedan fuera de M4.  |
| `variables`, `grids`, `grid_items`, `preguntas` legacy metadata | **WRAP** como import/evidence. Sólo un RELEASED Spec se vuelve autoridad.                                                   |
| Existing SQLite response tables                                 | **KEEP LEGACY** como input/compatibilidad. No se convierten por sí mismas en Structure authority.                           |

No debe eliminarse ninguna ruta Legacy durante M4.

---

# CANONICAL OUTPUT REQUIREMENTS

M4 debe producir un objeto conceptual renderer-neutral, por ejemplo:

`StructureExecutionResult`

El nombre concreto de implementación puede variar, pero su contrato lógico no.

Debe contener dos niveles.

## A. Normalized analytical records

Cada registro debe poder conservar, cuando corresponda:

- project/spec execution identity;
- `respondent_id`;
- `question_id`;
- `structure_id`;
- `structure_version`;
- `structure_type`;
- `parent_id`;
- `row_id/entity_id`;
- `column_id/option_id`;
- `loop_instance_id`;
- physical `variable_ref`;
- category/option binding;
- raw evidence reference cuando sea necesaria para QA;
- applicability state;
- response state;
- `selected`;
- `not_selected`;
- structural-zero provenance;
- `structural_missing`;
- `ordinary_missing`;
- invalid/out-of-domain state;
- metric-valid eligibility;
- denominator unit;
- source/release provenance.

No todos los campos aplican a todas las estructuras.

## B. Structure/denominator ledger

Debe permitir representar por scope:

- structure identity;
- metric identity;
- respondent denominator;
- option/entity denominator;
- valid respondent count;
- applicable respondent count;
- valid instance count;
- valid mention count;
- selected count;
- not-selected/structural-zero count;
- ordinary missing count;
- structural missing count;
- invalid count;
- zero-base status;
- dependency/repeated-observation flags;
- QA;
- traceability.

## Boundary with M5

M4 puede producir los numerator/denominator primitives y counts necesarios para demostrar que la estructura fue ejecutada correctamente.

M4 NO produce todavía:

- HTML;
- tables de presentación;
- Plotly;
- Excel ranges;
- Canonical Results persistence final;
- significance letters;
- Web formatting.

M5 transforma las primitivas analíticas autorizadas en Canonical Results.

---

# FILES / AREAS EXPECTED TO CHANGE

Cuando M4 sea autorizado, el cambio debe concentrarse en la nueva capa Core y contratos.

Áreas esperadas:

`src/contracts/`

para completar/reforzar:

- Structure Spec model;
- axis/member models;
- variable/category bindings;
- response-state vocabulary;
- applicability references;
- release validation;
- duplicate/exclusive policy;
- storage encoding;
- loop instance identity.

`src/analytics_core/`

para incorporar componentes renderer-neutral de:

- Structure resolution;
- released-spec authority;
- response normalization;
- RM normalization;
- Grid normalization;
- Loop normalization;
- denominator eligibility;
- QA/provenance.

Tests nuevos bajo las áreas de tests Core/contracts.

Puede incorporarse un adapter de compatibilidad para convertir metadata Legacy en **evidence/candidate structures**, pero el resultado del adapter no será RELEASED automáticamente.

M4 no requiere rediseñar SQLite.

---

# FILES / AREAS PROTECTED

Durante M4 deben permanecer sin cambio funcional incidental:

M2 Universe implementation.

M3 Weight implementation.

B1 canonical policy.

B2 canonical policy.

B3 canonical policy.

`WEIGHT_POLICY_CANONICAL.md`

`SIGNIFICANCE_POLICY_CANONICAL.md`

`AI_RELEASE_POLICY_CANONICAL.md`

Web/UI.

Excel.

EXPLORA NG.

SQLite production schema.

Significance runtime.

Visual/reporting behavior.

Legacy debe seguir siendo default.

En particular, las rutas actuales:

`src/reporter/**`

y los builders productivos Legacy de RM/Grid/Scale no deben ser reescritos para activar canonical behavior por defecto.

Si Codex necesita un adapter, wrapper o parity hook, no puede alterar el resultado Legacy existente.

No se deben retirar durante M4:

`grid_loop_detector`

`rm_long_builder`

`grid_loop_long_builder`

ni los fallbacks actuales.

Su retiro pertenece a una etapa de deprecación posterior, tras regresión aprobada.

---

# TEST MATRIX

| CasoComportamiento obligatorio   |                                                                                                                                          |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| RU simple                        | Categorías RELEASED se normalizan correctamente; denominator = valid applicable responses.                                               |
| RU ordinary missing              | Aplicable + missing se excluye del valid denominator y queda registrado como missing.                                                    |
| RU structural missing            | No entra al denominator y queda diferenciado de ordinary missing.                                                                        |
| RU out-of-domain                 | Observación no missing desconocida produce FAIL canónico.                                                                                |
| RM respondent %                  | Numerator unique selected respondents; denominator selected + not-selected válidos.                                                      |
| RM all-zero válido               | Respondent permanece en denominator cuando 0 está declarado como not-selected.                                                           |
| RM all-missing                   | No se convierte automáticamente en all-zero/not-selected.                                                                                |
| RM mention %                     | Numerator/denominator se construyen con mention events y scope explícito.                                                                |
| RM duplicate keep                | Repetición puede aumentar mentions pero nunca respondent numerator >1 por option.                                                        |
| RM deduplicate                   | Duplicate option del mismo respondent se reduce según policy.                                                                            |
| RM duplicate error               | Produce QA/FAIL según contrato.                                                                                                          |
| Option not selected              | Estado distinto de missing y not applicable.                                                                                             |
| Structural missing               | Cell no aplicable jamás se convierte en 0.                                                                                               |
| Ordinary missing                 | Aplicable sin respuesta no se convierte en structural missing.                                                                           |
| Out-of-universe                  | M4 no reincorpora respondent excluido por M2.                                                                                            |
| Row applicability                | Bases varían correctamente por row/entity.                                                                                               |
| Column applicability             | Bases varían correctamente por option/column.                                                                                            |
| Cell applicability               | Cell false produce structural missing sólo para esa cell.                                                                                |
| GRID\_ESCALA                     | Rows/scale/bindings RELEASED gobiernan estructura; detector no puede cambiarla.                                                          |
| GRID\_RM                         | Estados respondent×entity×option y denominators cell-specific correctos.                                                                 |
| LOOP\_RM                         | Conserva respondent/entity/instance/option identity.                                                                                     |
| LOOP\_RU                         | Cada instance conserva su respuesta/applicability individual.                                                                            |
| LOOP\_NUMERICO                   | Cada instance mantiene numeric state y denominator validity sin asumir independencia.                                                    |
| Repeated dependency              | Resultado incluye flag de dependencia; no se vuelve significance-eligible por conteo de instances.                                       |
| Unknown structure                | No ejecución canónica silenciosa.                                                                                                        |
| Ambiguous structure              | No puede llegar a RELEASED sin resolución.                                                                                               |
| Released structure               | Es autoridad aunque heurística Legacy sugiera otra clasificación.                                                                        |
| Non-released structure           | Canonical execution se bloquea.                                                                                                          |
| Missing physical binding         | FAIL; no fuzzy replacement.                                                                                                              |
| Detector disagreement            | RELEASED Spec gana; disagreement queda en QA.                                                                                            |
| Exclusive violation              | Fuente se conserva; no se elimina opción por label.                                                                                      |
| M2 mask invariance               | Antes/después de M4, el mask M2 debe ser byte/logically equivalent.                                                                      |
| M2 FAIL propagation              | M4 no busca una ruta alternativa.                                                                                                        |
| M2 UNSUPPORTED propagation       | M4 no convierte el caso en supported.                                                                                                    |
| M3 weight independence           | Weighted ON/OFF produce idéntica clasificación estructural y denominator membership unweighted.                                          |
| Weight zero                      | No cambia selected/not-selected/applicability; sólo contribución ponderada.                                                              |
| Invalid weights                  | Se aplica exactamente M3, sin reparación M4.                                                                                             |
| Legacy parity                    | Cuando las semánticas Legacy y RELEASED son equivalentes, no debe haber delta numérico.                                                  |
| Known structural-zero correction | Donde Legacy pierde respondents zero-only, el delta canónico debe quedar identificado como **INTENDED CORRECTION**, no forzado a parity. |
| Zero denominator                 | Produce NO\_VALID\_BASE/null, nunca 0% fabricado.                                                                                        |
| Traceability                     | Todo resultado M4 permite identificar Project/Question/Structure/Universe versions y execution mode.                                     |

---

# ACCEPTANCE CRITERIA

M4 sólo podrá considerarse implementado y cerrarse cuando se demuestre:

1. `released_spec` nunca utiliza runtime classification como fallback.
2. Todas las estructuras soportadas tienen bindings y response semantics explícitas.
3. RM respondent % conserva respondents válidos con cero selecciones.
4. Ordinary missing, structural missing y not-selected están separados en toda la ejecución.
5. RM respondent denominator y mention denominator son independientes y auditables.
6. GRID\_RM permite row/column/cell applicability sin reconstruirla desde missing observado.
7. LOOP mantiene repeated-instance identity y no declara independencia estadística.
8. M2 masks no cambian.
9. M3 weight resolution/application no cambia.
10. Weight no afecta structure classification ni unweighted denominator membership.
11. B2 no se implementa ni amplía.
12. Weighted significance sigue `UNSUPPORTED V1`.
13. Legacy sigue siendo default.
14. Legacy numerical behavior no cambia cuando se ejecuta `legacy_inference`.
15. Dual run identifica por separado:

- parity;
- intended corrections;
- regression;
- unsupported comparisons.

16. No existe auto-corrección textual de exclusivas en canonical mode.
17. No existe inference de row/option por variable suffix durante canonical execution.
18. Un RELEASED Structure Spec contradictorio con el dataset produce QA/FAIL, no reinterpretación.
19. Un non-RELEASED Structure Spec no produce resultado oficial.
20. Todos los tests anteriores pasan junto con la regression suite existente.
21. No existen cambios incidentales en M2, M3, Web, Excel, NG, SQLite o significance.
22. El output de M4 es renderer-neutral y puede ser consumido posteriormente por M5.

---

# BLOCKERS

## Contract blockers

**NONE**, siempre que este contrato sea aprobado como la resolución humana de M4.

Las ambigüedades principales quedaron resueltas aquí:

- not-selected versus missing;
- structural zero;
- structural missing;
- RM respondent denominator;
- RM mention denominator;
- scope de applicability;
- loops y repeated identity;
- released-spec authority;
- precedence frente a runtime inference.

## Implementation/validation warnings

Existe una advertencia importante, pero no bloquea el inicio técnico:

el AS-IS auditado no encontró bases SQLite productivas que materializaran de forma confirmada:

`grids`

`grid_items`

`respuestas_grid_loop`

`estructuras_detectadas`

Por ello, los fixtures sintéticos son suficientes para desarrollar el Core M4, pero **no son suficientes por sí solos para declarar posteriormente que GRID\_RM/LOOP\_RM están validados en producción**.

Antes de cierre final de M4 deberá existir al menos una de estas dos evidencias:

- benchmark real trazado con Grid/Loop; o
- aprobación humana explícita de que esa capacidad queda validada únicamente a nivel contractual/unitario y continúa marcada como pendiente de benchmark productivo.

Esto es una condición de cierre/validación, no una razón para convertir heurísticas Legacy en autoridad.

---

# CODEX READY YES/NO

**CODEX READY: YES — CONTRACTUALLY**

El contrato está suficientemente determinado para que Codex pueda implementar M4 sin tomar decisiones metodológicas nuevas.

Pero:

**M4 IMPLEMENTATION AUTHORIZED: NO**

Este documento no constituye la autorización de inicio.

La autorización debe ser una decisión humana separada.

Una vez autorizada, Codex deberá recibir este contrato como especificación congelada y no deberá reinterpretar:

- M2;
- M3;
- B1;
- B2;
- B3;
- denominadores RM;
- structural zero/missing;
- release authority;
- scope de M4.

**M5 remains NOT AUTHORIZED.**

El punto más importante que cambia respecto al comportamiento Legacy es el RM con respondents válidos de “cero selecciones”: en canonical M4 esos respondents ya no pueden desaparecer de la base sólo porque `multirrespuesta_long` no tenga una fila seleccionada. Ese delta deberá tratarse como una corrección metodológica intencional, no como un fallo de parity.
