from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.builder.analytic_db_builder import build_analytic_database
from src.builder.variables_builder import build_variables
from src.database.dashboard_config import apply_dashboard_configuration
from src.export.datamap_exporter import save_final_datamap
from src.export.excel_exporter import export_revision_excel
from src.readers.spss_reader import (
    get_missing_ranges,
    get_missing_values,
    get_value_labels,
)
from src.reporter.frequency_profile import build_frequency_profile
from src.utils.constants import (
    DATAMAP_FINAL_FILENAME,
    REVISION_EXCEL_FILENAME,
    SQLITE_FILENAME,
)
from src.utils.file_utils import file_bytes
from src.utils.session_paths import session_file
from src.utils.variable_safety import banner_filter_exclusion_reason


def render() -> None:
    st.subheader("Crear base analítica")
    df_spss = st.session_state.get("df_spss")
    meta_spss = st.session_state.get("meta_spss")
    datamap = st.session_state.get("review_datamap")
    sheets = st.session_state.get("datamap_sheets", {})

    if df_spss is None or meta_spss is None or datamap is None:
        st.info("Carga y revisa los archivos antes de construir la base.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Casos de entrada", f"{len(df_spss):,}")
    c2.metric("Variables SPSS", f"{len(df_spss.columns):,}")
    c3.metric("Filas Datamap", f"{len(datamap):,}")

    db_path = st.session_state.get("db_path")
    if st.button("Construir base analítica", type="primary"):
        try:
            with st.spinner(
                "Construyendo tablas y SQLite para el reporteador..."
            ):
                result = build_analytic_database(
                    df_spss=df_spss,
                    meta_spss=meta_spss,
                    datamap_df=datamap,
                    datamap_sheets=sheets,
                    db_path=session_file("db", SQLITE_FILENAME),
                    excel_path=session_file(
                        "exports", REVISION_EXCEL_FILENAME
                    ),
                    export_revision=False,
                )
            st.session_state.db_path = result["db_path"]
            st.session_state.pop("revision_excel_path", None)
            st.session_state.analytic_tables = result["tables"]
            db_path = result["db_path"]
            st.success("Base analítica creada correctamente.")
        except Exception as exc:
            st.error(f"No fue posible crear la base: {exc}")

    tables = st.session_state.get("analytic_tables")
    if tables:
        summary_columns = st.columns(4)
        summary_columns[0].metric(
            "Casos", len(tables.get("respondentes", []))
        )
        summary_columns[1].metric(
            "Preguntas", len(tables.get("preguntas", []))
        )
        summary_columns[2].metric(
            "Variables", len(tables.get("variables", []))
        )
        summary_columns[3].metric(
            "Recomendaciones",
            len(tables.get("recomendaciones_reporteador", [])),
        )
        with st.expander(
            "Detalle técnico de la base", expanded=False
        ):
            counts = pd.DataFrame(
                [
                    {
                        "Componente": name,
                        "Registros": (
                            len(frame)
                            if frame is not None
                            else 0
                        ),
                    }
                    for name, frame in tables.items()
                ]
            )
            st.dataframe(
                counts,
                hide_index=True,
                width="stretch",
            )

    if db_path is not None and Path(db_path).exists():
        current_db_path = Path(db_path)
        st.download_button(
            "Descargar base analítica completa",
            data=file_bytes(current_db_path),
            file_name=current_db_path.name,
            mime="application/x-sqlite3",
            key="download_built_analytic_database",
            type="primary",
        )
        _render_revision_excel_export(tables, sheets)
        _render_dashboard_configuration(
            db_path=current_db_path,
            df_spss=df_spss,
            meta_spss=meta_spss,
            datamap=st.session_state.get(
                "review_datamap", datamap
            ),
            sheets=sheets,
        )


def _render_dashboard_configuration(
    db_path,
    df_spss: pd.DataFrame,
    meta_spss,
    datamap: pd.DataFrame,
    sheets: dict[str, pd.DataFrame],
) -> None:
    st.divider()
    st.markdown("### Configurar banners y filtros")
    st.caption(
        "Marca las variables que estarán disponibles para comparar "
        "o filtrar. Una variable puede cumplir ambos roles."
    )

    candidates = _configuration_candidates(
        df_spss, meta_spss, datamap
    )
    if candidates.empty:
        st.info(
            "No hay variables seguras disponibles para configurar "
            "como banner o filtro."
        )
        return
    preview_variable = st.selectbox(
        "Vista previa de frecuencias",
        options=candidates["variable"].tolist(),
        format_func=lambda variable: _variable_display(
            candidates, variable
        ),
        key="dashboard_config_preview",
    )
    if preview_variable:
        _render_frequency_preview(
            preview_variable, df_spss, meta_spss
        )

    editor = st.data_editor(
        candidates,
        width="stretch",
        height=520,
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "variable",
            "label",
            "clasificacion_analitica",
            "tipo_spss",
            "valores_unicos",
            "observacion",
        ],
        column_order=[
            "variable",
            "label",
            "clasificacion_analitica",
            "tipo_spss",
            "valores_unicos",
            "es_banner",
            "es_filtro",
            "observacion",
        ],
        column_config={
            "variable": st.column_config.TextColumn(
                "Variable", width="small"
            ),
            "label": st.column_config.TextColumn(
                "Label", width="large"
            ),
            "clasificacion_analitica": (
                st.column_config.TextColumn(
                    "Clasificación", width="medium"
                )
            ),
            "tipo_spss": st.column_config.TextColumn(
                "Tipo", width="small"
            ),
            "valores_unicos": st.column_config.NumberColumn(
                "Valores únicos", format="%d", width="small"
            ),
            "es_banner": st.column_config.CheckboxColumn(
                "Banner", width="small"
            ),
            "es_filtro": st.column_config.CheckboxColumn(
                "Filtro", width="small"
            ),
            "observacion": st.column_config.TextColumn(
                "Observación", width="medium"
            ),
        },
        key="dashboard_config_editor",
    )

    banner_count = int(editor["es_banner"].fillna(False).sum())
    filter_count = int(editor["es_filtro"].fillna(False).sum())
    m1, m2 = st.columns(2)
    m1.metric("Banners seleccionados", banner_count)
    m2.metric("Filtros seleccionados", filter_count)

    if st.button(
        "Aplicar configuración",
        type="primary",
        key="apply_dashboard_configuration",
    ):
        banners = editor.loc[
            editor["es_banner"].fillna(False), "variable"
        ].astype(str)
        filters = editor.loc[
            editor["es_filtro"].fillna(False), "variable"
        ].astype(str)
        try:
            with st.spinner("Actualizando la base analítica..."):
                result = apply_dashboard_configuration(
                    db_path=db_path,
                    df_spss=df_spss,
                    meta_spss=meta_spss,
                    datamap_df=datamap,
                    banner_variables=banners,
                    filter_variables=filters,
                )
        except Exception as exc:
            st.error(
                "No fue posible aplicar la configuración: "
                f"{exc}"
            )
            return

        st.session_state.review_datamap = result["datamap"]
        st.session_state.analytic_tables = result["tables"]
        final_datamap_path = session_file(
            "processed", DATAMAP_FINAL_FILENAME
        )
        export_errors = []
        with st.spinner("Actualizando Datamap final..."):
            try:
                save_final_datamap(
                    final_datamap_path,
                    sheets,
                    result["datamap"],
                    df_spss=df_spss,
                    meta_spss=meta_spss,
                )
                st.session_state.datamap_final_path = (
                    final_datamap_path
                )
            except Exception as exc:
                export_errors.append(f"Datamap: {exc}")
            st.session_state.pop("revision_excel_path", None)

        st.success(
            "Configuración aplicada. El reporteador ya "
            "puede usar los nuevos banners y filtros."
        )
        if export_errors:
            st.warning(
                "La base se actualizó, pero hubo problemas al "
                "regenerar archivos: "
                + " | ".join(export_errors)
            )


def _render_revision_excel_export(
    tables: dict[str, pd.DataFrame] | None,
    sheets: dict[str, pd.DataFrame],
) -> None:
    if not tables:
        return
    revision_path = st.session_state.get("revision_excel_path")
    current_path = Path(revision_path) if revision_path else None
    if current_path is not None and current_path.exists():
        st.download_button(
            "Descargar Excel técnico de revisión",
            data=file_bytes(current_path),
            file_name=current_path.name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            key="download_revision_excel_after_build",
        )
        return

    st.caption(
        "El Excel técnico de revisión se puede generar aparte; "
        "incluye BD_Pivot y puede tardar más."
    )
    if st.button(
        "Generar Excel técnico de revisión",
        key="generate_revision_excel_after_build",
    ):
        path = session_file("exports", REVISION_EXCEL_FILENAME)
        try:
            with st.spinner(
                "Generando Excel técnico de revisión..."
            ):
                export_revision_excel(
                    path, tables, datamap_sheets=sheets
                )
            st.session_state.revision_excel_path = path
            st.success("Excel técnico de revisión generado.")
            st.rerun()
        except Exception as exc:
            st.error(
                "No fue posible generar el Excel técnico: "
                f"{exc}"
            )


def _configuration_candidates(
    df_spss: pd.DataFrame,
    meta_spss,
    datamap: pd.DataFrame,
) -> pd.DataFrame:
    variables = build_variables(df_spss, meta_spss, datamap)
    result = variables[
        [
            "variable",
            "label",
            "clasificacion_analitica",
            "tipo_spss",
            "valores_unicos",
            "es_banner",
            "es_filtro",
        ]
    ].copy()
    result["observacion"] = result.apply(
        lambda row: _configuration_warning(row, df_spss), axis=1
    )
    safe = result["observacion"].fillna("").eq("")
    return result.loc[safe].reset_index(drop=True)


def _configuration_warning(
    row: pd.Series, df_spss: pd.DataFrame
) -> str:
    safety_reason = banner_filter_exclusion_reason(
        df_spss, row.get("variable")
    )
    if safety_reason:
        return safety_reason
    unique = int(row.get("valores_unicos") or 0)
    classification = str(
        row.get("clasificacion_analitica") or ""
    )
    if unique == 0:
        return "Sin datos válidos"
    if unique == 1:
        return "Sin variación"
    if row.get("tipo_spss") == "text" and unique > 50:
        return "Texto con alta cardinalidad"
    if unique > 50:
        return "Alta cardinalidad"
    if classification in {
        "Variable técnica",
        "Control de calidad",
        "No usar en dashboard",
        "Abierta",
    }:
        return "Revisar antes de usar"
    return ""


def _variable_display(
    candidates: pd.DataFrame, variable: str
) -> str:
    selected = candidates.loc[
        candidates["variable"].astype(str).eq(str(variable))
    ]
    if selected.empty:
        return str(variable)
    label = str(selected.iloc[0].get("label") or "").strip()
    return f"{variable} — {label}" if label else str(variable)


def _render_frequency_preview(
    variable: str,
    df_spss: pd.DataFrame,
    meta_spss,
) -> None:
    table, summary = build_frequency_profile(
        df_spss[variable],
        value_labels=get_value_labels(meta_spss, variable),
        missing_values=get_missing_values(meta_spss, variable),
        missing_ranges=get_missing_ranges(meta_spss, variable),
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Casos válidos", f"{summary.valid:,}")
    c2.metric(
        "Categorías", f"{summary.observed_categories:,}"
    )
    c3.metric(
        "Códigos sin etiqueta", f"{summary.unlabeled_codes:,}"
    )
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        height=min(350, 38 + max(len(table), 1) * 35),
        column_config={
            "Frecuencia": st.column_config.NumberColumn(
                format="%d"
            ),
            "% válido": st.column_config.NumberColumn(
                format="%.1f%%"
            ),
        },
    )
