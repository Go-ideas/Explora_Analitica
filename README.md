# EXPLORA WEB REPORTER

Reporteador Streamlit para cargar una base analitica SQLite ya generada por la consola de procesamiento, crear tablas y exportarlas en Excel.

## Flujo incluido

- Carga de `BD_Analitica_Explora.db`.
- Reporteador con tabla individual y generacion multiple.
- Diferencias significativas.
- Exportacion de tablas en Excel, incluyendo todas las tablas guardadas en un solo archivo.

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Publicar en Streamlit Community Cloud

1. Crea un repositorio en GitHub.
2. Sube esta carpeta completa como raiz del repositorio.
3. En Streamlit Community Cloud crea una app nueva desde ese repositorio.
4. Usa `streamlit_app.py` como archivo principal.
5. Verifica que Streamlit instale las dependencias desde `requirements.txt`.

## Archivos que si deben subirse

- `streamlit_app.py`
- `app.py`
- `requirements.txt`
- `runtime.txt`
- `.gitignore`
- `.streamlit/config.toml`
- `src/`
- `README.md`
- `DEPLOY_STREAMLIT_CLOUD.md`

## Archivo operativo que carga el usuario

El usuario final carga en la app publicada:

- `BD_Analitica_Explora.db`

Ese archivo se genera previamente en la consola local de procesamiento. No se sube a GitHub.

## Archivos que no deben subirse

No subas archivos de clientes, bases reales ni archivos generados por sesion:

- `.sav`, `.zsav`, `.por`
- `.xlsx`, `.xlsm`, `.xls` con datamaps, tabplans o entregables
- `.db`, `.sqlite`, `.sqlite3`
- `data/`
- `.streamlit/secrets.toml`

La app crea `data/` en tiempo de ejecucion. En Streamlit Cloud esa carpeta es temporal: si la app se reinicia, se debe volver a cargar `BD_Analitica_Explora.db`.
