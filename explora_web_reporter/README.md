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
