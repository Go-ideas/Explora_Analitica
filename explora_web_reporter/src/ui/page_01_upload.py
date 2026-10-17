from __future__ import annotations

import pandas as pd
import streamlit as st

from src.readers.datamap_reader import (
    datamap_summary,
    get_review_source_sheet,
    normalize_review_datamap,
    read_datamap,
)
from src.readers.spss_reader import read_spss
from src.structure.grid_loop_detector import (
    enrich_datamap_with_spss_structure,
)
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
                    review = enrich_datamap_with_spss_structure(
                        review=review,
                        df_spss=df_spss,
                        meta_spss=meta_spss,
                        datamap_sheets=sheets,
                    )
                st.session_state.df_spss = df_spss
                st.session_state.meta_spss = meta_spss
                st.session_state.spss_summary = spss_summary
                st.session_state.datamap_sheets = sheets
                st.session_state.review_datamap = review
                st.session_state.spss_path = spss_path
                st.session_state.datamap_path = datamap_path
                st.session_state.grid_loop_structures = (
                    review.attrs.get("grid_loop_structures")
                )
                st.success("Archivos procesados correctamente.")
                st.info("Siguiente paso: abre 2. Revisar Datamap y revisa las preguntas, identificadores y exclusiones.")
                if (
                    st.session_state.grid_loop_structures is not None
                    and not st.session_state.grid_loop_structures.empty
                ):
                    st.warning(
                        "Se detectaron estructuras GRID/LOOP automáticamente. "
                        "Revísalas en Datamap > Estructuras detectadas."
                    )
            except Exception as exc:
                st.error(
                    f"No fue posible procesar los archivos: {exc}"
                )

    _render_summary()


def _reset_project_state() -> None:
    for key in list(st.session_state):
        if key.startswith(('report_', 'paired_', 'current_', 'canonical_')):
            del st.session_state[key]
    for key in [
        "db_path",
        "revision_excel_path",
        "datamap_final_path",
        "analytic_tables",
        "current_report",
        "significance_report",
        "saved_reports",
        "review_datamap",
        "datamap_sheets",
        "grid_loop_structures",
        "df_spss",
        "meta_spss",
        "spss_summary",
        "spss_path",
        "datamap_path",
        "datamap_review_saved",
        "project_download",
        "project_restored_message",
        "failed_analysis_binding",
        "pending_analysis_binding",
        "last_execution_error",
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
    c1.metric("Filas / evaluaciones", f"{len(df_spss):,}")
    c2.metric("Variables", f"{len(df_spss.columns):,}")
    summary = datamap_summary(sheets)
    c3.metric("Hojas Datamap", len(sheets))
    c4.metric("QA del archivo", summary.get("qa_status") or "No informado")
    _render_person_summary(df_spss, review)
    st.caption(
        "Revisión del Datamap: "
        + ("guardada; no implica certificación metodológica." if st.session_state.get("datamap_review_saved")
           else "pendiente de guardar en 2. Revisar Datamap.")
    )
    if not summary.get("qa_status"):
        st.info("El archivo no informa un estatus QA. Cero riesgos registrados no equivale a una validación completa.")

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

    risks = summary.get("risk_counts", {})
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Riesgos críticos", risks.get("criticos", 0))
    r2.metric("Riesgos altos", risks.get("altos", 0))
    r3.metric("Riesgos medios", risks.get("medios", 0))
    r4.metric("Riesgos bajos", risks.get("bajos", 0))


def _render_person_summary(df: pd.DataFrame, review: pd.DataFrame | None) -> None:
    """Count people only from an explicitly declared, complete identifier."""
    if review is None or "variable_id_persona" not in review:
        st.caption("Personas únicas: sin identificador de persona declarado en el Datamap; no se infieren a partir del número de filas.")
        return
    declared = review["variable_id_persona"].dropna().astype(str).str.strip()
    declared = declared[declared.ne("")].unique()
    if len(declared) != 1 or declared[0] not in df:
        st.warning("No se puede confirmar el número de personas: revisa variable_id_persona en el Datamap.")
        return
    values = df[declared[0]]
    normalized = values.astype(str).str.strip()
    if values.isna().any() or normalized.str.casefold().isin({"", "nan", "none", "null"}).any():
        st.warning("El identificador de persona contiene valores vacíos; revisa el Datamap antes de contar personas.")
        return
    st.metric("Personas únicas", f"{normalized.nunique():,}")
    st.caption(f"Identificador declarado: {declared[0]}. Una persona puede aportar varias evaluaciones; cada tabla indica su unidad y base válida.")
