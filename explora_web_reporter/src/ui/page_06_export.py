from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.export.report_exporter import report_to_excel_bytes
from src.export.project_exporter import (
    executive_export_bytes,
    saved_reports_export_bytes,
    technical_export_bytes,
)
from src.reporter.report_store import (
    delete_report_snapshots,
    saved_reports_summary,
)
from src.utils.file_utils import file_bytes
from src.utils.filename import safe_filename
from src.web_canonical.export import (
    internal_qa_export_bytes,
    official_released_export_bytes,
)
from src.web_canonical.models import CanonicalWebProjection


def render() -> None:
    st.subheader("Exportar")
    st.caption(
        "Elige una salida ejecutiva para presentar resultados o "
        "una salida técnica para auditoría."
    )
    current = st.session_state.get("current_report")
    saved_reports = st.session_state.get("saved_reports", [])
    message = st.session_state.pop(
        "_saved_reports_message", None
    )
    if message:
        st.success(message)
    executive_tab, technical_tab = st.tabs(
        ["Exportación ejecutiva", "Exportación técnica"]
    )

    with executive_tab:
        canonical_projection = st.session_state.get(
            "current_canonical_projection"
        )
        if isinstance(canonical_projection, CanonicalWebProjection):
            is_releasable = bool(
                canonical_projection.release.get("releasable")
            )
            st.download_button(
                (
                    "Descargar resultado oficial canónico"
                    if is_releasable
                    else "Descargar QA interna canónica"
                ),
                data=(
                    official_released_export_bytes(canonical_projection)
                    if is_releasable
                    else internal_qa_export_bytes(canonical_projection)
                ),
                file_name=safe_filename(
                    canonical_projection.result_run_id,
                    (
                        "Canonical_Official_Released_Projection.csv"
                        if is_releasable
                        else "Canonical_Internal_QA_Projection.csv"
                    ),
                ),
                mime="text/csv",
                type="primary",
            )
            if is_releasable:
                st.caption(
                    "Export oficial liberado con value_id, base_id "
                    "y result_run_id. No recalcula valores analíticos."
                )
            else:
                st.warning(
                    "El resultado canónico no es liberable; la "
                    "exportación disponible es sólo QA interna."
                )
        elif current is not None:
            st.download_button(
                "Descargar análisis ejecutivo",
                data=executive_export_bytes(current),
                file_name=(
                    safe_filename(
                        current.question_id,
                        "Analisis_Ejecutivo_Explora.zip",
                    )
                ),
                mime="application/zip",
                type="primary",
            )
            st.caption(
                "Incluye tabla, configuración, notas y el gráfico "
                "interactivo cuando está disponible."
            )
            st.download_button(
                "Descargar solo la tabla en Excel",
                data=report_to_excel_bytes(current),
                file_name=(
                    safe_filename(
                        current.question_id,
                        "Reporte_Explora.xlsx",
                    )
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
        else:
            st.info(
                "Genera una tabla en el Reporteador para habilitar "
                "la exportación ejecutiva."
            )
        st.divider()
        st.markdown("### Análisis guardados")
        if saved_reports:
            st.download_button(
                "Exportar todas las tablas y gráficos guardados",
                data=saved_reports_export_bytes(saved_reports),
                file_name="Analisis_Guardados_Explora.zip",
                mime="application/zip",
                type="primary",
            )
            st.caption(
                "El paquete incluye un Excel y un gráfico por "
                "análisis, además de un libro con todas las tablas."
            )
            summary = pd.DataFrame(
                saved_reports_summary(saved_reports)
            )
            edited = st.data_editor(
                summary,
                hide_index=True,
                width="stretch",
                column_order=[
                    "Eliminar",
                    "Nombre",
                    "Pregunta",
                    "Sección",
                    "Guardado",
                ],
                disabled=[
                    "Nombre",
                    "Pregunta",
                    "Sección",
                    "Guardado",
                    "_id",
                ],
                column_config={
                    "Eliminar": st.column_config.CheckboxColumn(
                        "Eliminar", width="small"
                    ),
                    "Nombre": st.column_config.TextColumn(
                        width="large"
                    ),
                    "Pregunta": st.column_config.TextColumn(
                        width="small"
                    ),
                },
                key="saved_reports_editor",
            )
            selected_ids = (
                edited.loc[
                    edited["Eliminar"].fillna(False), "_id"
                ]
                .astype(str)
                .tolist()
            )
            if st.button(
                "Eliminar seleccionados",
                disabled=not selected_ids,
                key="delete_saved_reports",
            ):
                st.session_state.saved_reports = (
                    delete_report_snapshots(
                        saved_reports, selected_ids
                    )
                )
                st.session_state._saved_reports_message = (
                    f"Se eliminaron {len(selected_ids)} "
                    "análisis guardados."
                )
                st.rerun()

            names = {
                str(entry.get("id")): str(
                    entry.get("name") or "Análisis"
                )
                for entry in saved_reports
            }
            selected_id = st.selectbox(
                "Descargar un análisis individual",
                list(names),
                format_func=names.get,
                key="individual_saved_report",
            )
            selected_entry = next(
                entry
                for entry in saved_reports
                if str(entry.get("id")) == selected_id
            )
            st.download_button(
                "Descargar análisis seleccionado",
                data=executive_export_bytes(
                    selected_entry["report"]
                ),
                file_name=(
                    safe_filename(
                        selected_entry["report"].question_id,
                        "Analisis_Explora.zip",
                    )
                ),
                mime="application/zip",
                key="download_individual_saved_report",
            )
        else:
            st.info(
                "Todavía no hay análisis guardados. Usa "
                "“Guardar tabla y gráfico” en el Reporteador."
            )

    files = [
        (
            "BD_Analitica_Explora.db",
            _session_path("db_path"),
            "application/x-sqlite3",
        ),
        (
            "BD_Analitica_Revision.xlsx",
            _session_path("revision_excel_path"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "Datamap_Final.xlsx",
            _session_path("datamap_final_path"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ]

    with technical_tab:
        available = [
            (name, path) for name, path, _ in files if path.exists()
        ]
        if available:
            st.download_button(
                "Descargar paquete técnico completo",
                data=technical_export_bytes(
                    available,
                    tables=st.session_state.get("analytic_tables"),
                ),
                file_name="Explora_Exportacion_Tecnica.zip",
                mime="application/zip",
                type="primary",
            )
            st.caption(
                "Incluye Datamap completo, recomendaciones, "
                "configuración, factores, riesgos y base analítica."
            )
        for name, path, mime in files:
            if path.exists():
                st.download_button(
                    name,
                    data=file_bytes(path),
                    file_name=path.name,
                    mime=mime,
                    key=f"export_{path.name}",
                )
            else:
                st.caption(f"{name}: todavía no disponible.")


def _session_path(key: str) -> Path:
    value = st.session_state.get(key)
    return Path(value) if value else Path("__no_session_file__")
