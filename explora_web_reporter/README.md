# EXPLORA WEB REPORTER

Aplicación web en Python y Streamlit para transformar una base SPSS y un
`Datamap_Validado.xlsx` en una base analítica reutilizable, reportes dinámicos,
gráficos y pruebas de diferencias significativas.

El proyecto no depende del reporteador Excel ni de macros VBA. Toda la lógica
de preparación, tabulación, filtros, banners, ponderación y exportación se
ejecuta en Python.

## Flujo de trabajo

1. Subir la base original `.sav`.
2. Subir `Datamap_Validado.xlsx`.
3. Revisar y corregir la clasificación analítica.
4. Guardar `Datamap_Final.xlsx`.
5. Crear `BD_Analitica_Explora.db` y el Excel de revisión.
6. Seleccionar una pregunta, banner, filtro, ponderador y cálculo.
7. Generar tablas, gráficos y diferencias significativas.
8. Exportar la tabla actual o todas las tablas de la sesión.

## Funcionalidad

- Lectura de datos y metadatos SPSS con `pyreadstat`.
- Revisión editable del Datamap.
- Diez tablas analíticas en SQLite.
- Frecuencias, porcentajes, medias, Top2Box, BottomBox, NPS y RM.
- Banners múltiples en columnas con combinaciones `variable: valor | etiqueta`.
- Filtros múltiples con varios valores y lógica AND.
- Configuración editable de banners y filtros con actualización de SQLite.
- Preguntas ordenadas por cuestionario y agrupadas por sección.
- Banners y filtros recomendados con justificación comercial.
- Compatibilidad con Datamaps GPT que separan roles por variable y
  metadatos por pregunta en las hojas 08–13.
- Selección simultánea de n, %, ponderados, medias, cajas, NPS y RM.
- Orden de respuestas por Value Labels, código o frecuencia descendente.
- Significancia integrada, separada u oculta.
- Ponderadores configurados desde el Datamap.
- Gráficos automáticos con Plotly.
- Z-test de dos proporciones y Welch t-test.
- Confianza configurable al 90%, 95% o 99%.
- Base mínima configurable para significancia.
- Exportaciones Excel con título, base, configuración, tabla y notas.
- Edición y persistencia de factores/scores sugeridos.
- Procesamiento seguro de factores por rangos numéricos como
  variables derivadas disponibles para banners y filtros.

## Instalación en Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección local, normalmente
`http://localhost:8501`.

## Versión para cliente en Streamlit Community Cloud

La entrada pública para clientes es `streamlit_app.py`. Esta versión no
muestra el flujo de construcción: solo permite subir
`BD_Analitica_Explora.db`, valida que sea una base compatible y abre el
reporteador con exportación de análisis.

Para probarla localmente:

```powershell
streamlit run streamlit_app.py
```

Para publicarla en `share.streamlit.io` / Streamlit Community Cloud:

1. Sube esta carpeta a un repositorio de GitHub.
2. Crea una app nueva en Streamlit Community Cloud.
3. Selecciona como archivo principal:
   `explora_web_reporter/streamlit_app.py`.
4. Mantén `explora_web_reporter/requirements.txt` junto al archivo principal
   para que Community Cloud instale las dependencias.
5. Comparte la URL generada con el cliente.

El cliente solo necesita cargar la base SQLite generada por el builder. Cada
archivo se copia a una base temporal de sesión para que los filtros, reportes
guardados y configuraciones no afecten a otros usuarios.

## Archivos generados

- `data/processed/Datamap_Final.xlsx`
- `data/db/BD_Analitica_Explora.db`
- `data/exports/BD_Analitica_Revision.xlsx`

## Estructura

Los lectores viven en `src/readers`, la construcción de tablas en
`src/builder`, el motor analítico en `src/reporter`, las exportaciones en
`src/export` y las páginas Streamlit en `src/ui`.

Cuando una regla no puede inferirse con seguridad, el constructor conserva el
flujo y utiliza la marca `requiere_validacion` cuando corresponde.


## EXPLORA Operator Console — flujo CANONICAL

La consola operativa del flujo nuevo vive en `operator_console.py`. Esta
entrada es distinta del reporteador histórico y no calcula estadísticas por su
cuenta.

Flujo:

1. Cargar la base `.sav`.
2. Cargar `EXPLORA_PROJECT_SPEC_V1`.
3. Cargar `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`.
4. Revisar errores, warnings, ambigüedades y decisiones AI/humanas.
5. Registrar una aprobación B3 humana explícita.
6. Construir el RELEASED Package determinístico mediante el builder de Gate 47.
7. Ejecutar `CANONICAL_V1` para proyectos con output WEB.
8. Descargar package, resultados, QA y provenance.

El cuestionario y el datamap pueden cargarse como evidencia de fuente, pero Gate
48 no afirma generación automática de Project Spec desde esos documentos.

Para ejecutar localmente:

```powershell
streamlit run operator_console.py
```

Para Streamlit Community Cloud selecciona como archivo principal:

`explora_web_reporter/operator_console.py`

La consola usa almacenamiento temporal de sesión para archivos de cliente y no
los añade al repositorio. La salida Excel permanece fail-closed en esta consola
hasta integrar explícitamente el `QualifiedMaster` de M7.

### Privacidad en Streamlit Community Cloud

El repositorio es público, por lo que un despliegue nuevo puede quedar público
por defecto. Antes de subir datos reales de clientes, cambia la app a privada en
**App Settings → Sharing → Only specific people can view this app**. No utilices
la consola con datos de clientes mientras el acceso sea público.

## Datamaps, escalas y evaluaciones repetidas

La importación usa metadatos del estudio, sin reglas por nombre de archivo,
cliente, producto o pregunta. Un tipo explícito en `tipo_pregunta` tiene prioridad;
si falta, `tipo_tabla_sugerida` puede declarar Escala hedónica, Escala, JAR,
Escala 1–5, RU, RM, NPS o Cruce. Una sugerencia desconocida no se interpreta como
un tipo conocido. El texto libre de `metrica_sugerida` no define por sí solo los
límites de una escala.

| Campo del Datamap | Uso |
| --- | --- |
| `variable_id_persona` / `id_respondente` / `respondent_id_variable` | Nombre de la columna SPSS que identifica a la persona; no el valor de una persona. Debe existir y no contener IDs vacíos. |
| `unidad_analisis` / `Base_Valida_Nivel` / `analysis_unit` | `Respondente` o `Persona` para contar una vez a cada persona; las evaluaciones repetidas se conservan para unidades como evaluación de producto. |
| `tipo_eje_fila` / `Tipo_Eje_Fila` / `repetition_axis` | Eje declarado, por ejemplo Tiempo, Visita o Tienda. |
| `eje_fila_grid` / `Eje_Fila_Grid` / `repetition_value` | Etiqueta de cada ítem repetido, por ejemplo «Antes» o «Después». No se deduce de sufijos como `.1`. |
| `escala_min` / `scale_min`, `escala_max` / `scale_max` | Límites completos de la escala; tienen prioridad sobre los Value Labels. |

Los ítems escalares con un mismo `pregunta_id` y eje declarado se ofrecen como
preguntas separadas, con IDs `pregunta_padre::variable` y etiquetas del eje. Se
conservan la variable física y la pregunta padre. Si no hay eje semántico, varias
variables explícitamente escalares se separan por su nombre de variable; no se
convierten automáticamente en opciones RM. Las opciones declaradas RM mantienen
su agrupación. Los ejes incompletos, etiquetas duplicadas o IDs de pregunta en
conflicto requieren corregir el Datamap. Un eje compuesto debe identificar cada
ítem de forma única.

SQLite conserva `id_persona`, `id_evaluacion` e `id_original`; la clave histórica
`id_respondente` sigue siendo la clave de unión por fila. Al tabular una pregunta
declarada por persona se comprueba que sus respuestas sean constantes entre
evaluaciones y se cuenta una sola vez. Un banner o ponderador que cambie dentro de
una persona requiere filtrar una evaluación o revisar la unidad; no se toma una
fila arbitraria. La interfaz y el Excel indican si la base cuenta personas o
evaluaciones y muestran las personas únicas.

Las cajas se calculan con los límites declarados o los códigos numéricos
consecutivos de los Value Labels completos, nunca con extremos observados en la
muestra. Se usan los dos códigos superiores/inferiores de una escala con pasos
unitarios; escalas con codificación u orientación diferente necesitan una
recodificación explícita antes de ese cálculo. Sin una escala definida puede
calcularse la media, pero se omiten las cajas con una advertencia. El cero no se
elimina automáticamente y una escala de diez puntos no se convierte en NPS:
NPS debe estar declarado. Valores fuera de los límites declarados requieren
validación.

Si la selección contiene varias evaluaciones de una misma persona, el reporteador
no aplica pruebas de significancia para muestras independientes: informa que se
necesita un método para muestras relacionadas y conserva los descriptivos. Este
cambio no implementa tests pareados ni certifica por sí mismo una liberación
canónica. Las exclusiones `usar_en_dashboard=No` se respetan también en escalas y
multirrespuesta.

Las bases SQLite construidas previamente deben regenerarse desde los originales
y el Datamap para incorporar la identidad de persona, unidad y separación de
ítems. El modo `CANONICAL_V1` sigue requiriendo su resultado canónico explícito;
el análisis histórico de SQLite se selecciona conscientemente con `LEGACY` en
«Modo de ejecución». No hay cambio automático de motor.
