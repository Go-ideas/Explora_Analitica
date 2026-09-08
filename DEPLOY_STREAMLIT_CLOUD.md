# Despliegue en Streamlit Community Cloud

Esta guia deja el reporteador listo para publicarse desde GitHub sin subir bases reales ni archivos de clientes.

## 1. Que carpeta subir

Sube a GitHub esta carpeta:

```text
explora_console_github/
```

Debe quedar como raiz del repositorio. En la raiz se tienen que ver:

```text
streamlit_app.py
requirements.txt
runtime.txt
src/
.streamlit/
```

## 2. Que no subir

No subas datos de proyecto ni archivos generados:

```text
data/
*.sav
*.zsav
*.por
*.xlsx
*.xlsm
*.xls
*.db
*.sqlite
*.sqlite3
.streamlit/secrets.toml
```

El archivo `.gitignore` ya esta configurado para excluirlos.

## 3. Crear repositorio en GitHub

Desde esta carpeta puedes ejecutar:

```bash
git init
git add .
git commit -m "Deploy Explora Streamlit reporter"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Reemplaza `TU_USUARIO` y `TU_REPOSITORIO` por los datos reales del repositorio.

Antes de hacer `git add .`, valida que no haya archivos de datos:

```bash
git status --short
```

## 4. Crear app en Streamlit Community Cloud

En Streamlit Community Cloud:

1. Selecciona el repositorio de GitHub.
2. Selecciona la rama `main`.
3. En "Main file path" usa:

```text
streamlit_app.py
```

4. Deploy.

## 5. Como usar la app publicada

La app publicada usa solo la base ya generada:

1. Cargar `BD_Analitica_Explora.db`.
2. Entrar al Reporteador.
3. Generar tablas individuales o multiples.
4. Guardar las tablas.
5. Descargar el Excel con todas las tablas guardadas.

## 6. Importante sobre la base generada

La base SQLite que genera la consola local vive en almacenamiento temporal de Streamlit Cloud despues de cargarla. No conviene subirla a GitHub porque puede contener datos confidenciales y porque cambia por proyecto.

Si mas adelante necesitas que la base quede persistente entre sesiones, agrega almacenamiento externo como Google Drive, S3, Supabase o Snowflake.
