from __future__ import annotations

import pandas as pd
import streamlit as st

from src.readers.datamap_reader import (
    build_datamap_import_log,
    datamap_summary,
    get_review_source_sheet,
    normalize_review_datamap,
    read_datamap,
)
from src.readers.spss_reader import read_spss
from src.utils.file_utils import save_uploaded_file
from src.utils.session_paths import session_dir


def render() -> None:
    st.subheader("Estado del proyecto")
    st.caption(
        "Carga o reemplaza los archivos fuente y consulta el estado "
        "general del proyecto."
    )

    with st.container(border=True):
        st.markdown("**Archivos fuente**")
        left, right = st.columns(2)
        with left:
            sav_file = st.file_uploader(
                "Base de respuestas", type=["sav"]
            )
        with right:
            datamap_file = st.file_uploader(
                "Datamap validado", type=["xlsx"]
            )

        if st.button(
            "Procesar archivos",
            type="primary",
            disabled=not (sav_file and datamap_file),
        ):
            try:
                with st.spinner("Leyendo archivos y metadatos..."):
                    _reset_project_state()
                    raw_dir = session_dir("raw")
                    spss_path = save_uploaded_file(
                        sav_file, raw_dir
                    )
                    datamap_path = save_uploaded_file(
                        datamap_file, raw_dir
                    )
                    df_spss, meta_spss, spss_summary = (
                        read_spss(spss_path)
                    )
                    sheets = read_datamap(datamap_path)
                    _, source = get_review_source_sheet(sheets)
                    review = normalize_review_datamap(
                        source, list(df_spss.columns)
                    )
                    import_log = build_datamap_import_log(
                        sheets, review
                    )
                st.session_state.df_spss = df_spss
                st.session_state.meta_spss = meta_spss
                st.session_state.spss_summary = spss_summary
                st.session_state.datamap_sheets = sheets
                st.session_state.review_datamap = review
                st.session_state.datamap_import_log = import_log
                st.session_state.spss_path = spss_path
                st.session_state.datamap_path = datamap_path
                st.success("Archivos procesados correctamente.")
            except Exception as exc:
                st.error(
                    f"No fue posible procesar los archivos: {exc}"
                )

    _render_summary()


def _reset_project_state() -> None:
    for key in [
        "db_path",
        "revision_excel_path",
        "datamap_final_path",
        "analytic_tables",
        "current_report",
        "significance_report",
        "saved_reports",
        "review_datamap",
        "datamap_import_log",
        "datamap_sheets",
        "df_spss",
        "meta_spss",
        "spss_summary",
        "spss_path",
        "datamap_path",
    ]:
        st.session_state.pop(key, None)


def _render_summary() -> None:
    df_spss = st.session_state.get("df_spss")
    sheets = st.session_state.get("datamap_sheets")
    review = st.session_state.get("review_datamap")
    if df_spss is None or sheets is None:
        return

    st.markdown("**Resumen de carga**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casos", f"{len(df_spss):,}")
    c2.metric("Variables", f"{len(df_spss.columns):,}")
    summary = datamap_summary(sheets)
    c3.metric("Hojas Datamap", len(sheets))
    c4.metric("QA", summary.get("qa_status") or "Sin estatus")

    if isinstance(review, pd.DataFrame) and not review.empty:
        categories = {
            "Dashboard": int(review["usar_en_dashboard"].astype(bool).sum()),
            "Técnicas / excluidas": int(
                review["clasificacion_analitica"].isin(
                    [
                        "Variable técnica",
                        "Control de calidad",
                        "No usar en dashboard",
                    ]
                ).sum()
            ),
            "Banners": int(review["es_banner"].astype(bool).sum()),
            "Filtros": int(review["es_filtro"].astype(bool).sum()),
            "Ponderadores": int(
                review["es_ponderador"].astype(bool).sum()
            ),
            "Abiertas": int(
                review["clasificacion_analitica"].eq("Abierta").sum()
            ),
        }
        with st.expander("Distribución analítica"):
            st.dataframe(
                pd.DataFrame(
                    categories.items(),
                    columns=["Clasificación", "Variables"],
                ),
                hide_index=True,
                width="stretch",
            )

    _render_import_log(st.session_state.get("datamap_import_log"))

    risks = summary.get("risk_counts", {})
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Riesgos críticos", risks.get("criticos", 0))
    r2.metric("Riesgos altos", risks.get("altos", 0))
    r3.metric("Riesgos medios", risks.get("medios", 0))
    r4.metric("Riesgos bajos", risks.get("bajos", 0))


def _render_import_log(log: dict | None) -> None:
    if not log:
        return
    summary = log.get("summary", {})
    fields = log.get("fields")
    with st.expander("Log de importación del Datamap", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Hoja usada", summary.get("hoja_usada") or "Sin hoja")
        c2.metric(
            "RM_DICOTOMICA_LABEL",
            summary.get("rm_dicotomica_label_detectadas", 0),
        )
        c3.metric(
            "GRID_RM_LOOP",
            summary.get("grid_rm_loop_detectadas", 0),
        )
        st.caption(
            "Columnas detectadas: "
            f"{summary.get('columnas_detectadas') or 'Sin columnas'}"
        )
        fallback = summary.get("fallback_hoja")
        if fallback:
            st.caption(f"Fallback de hoja: {fallback}")
        missing = summary.get("columnas_faltantes")
        if missing:
            st.caption(f"Columnas faltantes: {missing}")
        if isinstance(fields, pd.DataFrame) and not fields.empty:
            st.dataframe(fields, hide_index=True, width="stretch")
