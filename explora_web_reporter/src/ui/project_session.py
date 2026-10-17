from pathlib import Path
from uuid import uuid4

import streamlit as st
from src.utils.privacy import download_button

from src.export.project_archive import create_project_archive, restore_project_archive
from src.readers.datamap_reader import read_datamap, get_review_source_sheet, normalize_review_datamap
from src.readers.spss_reader import read_spss
from src.structure.grid_loop_detector import enrich_datamap_with_spss_structure
from src.utils.session_paths import session_dir


def render_project_session() -> None:
    with st.expander('Guardar o recuperar proyecto'):
        st.caption('El archivo conserva la base, los análisis guardados y las selecciones del reporteador. Contiene datos del estudio; guárdalo en una ubicación de acceso restringido.')
        db_value = st.session_state.get('db_path')
        include_source = st.checkbox('Incluir SAV y Datamap para poder reconstruir', value=True, key='project_include_sources')
        datamap = st.session_state.get('datamap_final_path') or st.session_state.get('datamap_path')
        source = st.session_state.get('spss_path')
        if include_source and not (datamap and source and Path(datamap).is_file() and Path(source).is_file()):
            st.caption('No están disponibles ambas fuentes (SAV y Datamap). Se incluirán las que existan; podrás retomar el análisis, pero para reconstruir necesitarás las fuentes que falten.')
        if st.button('Preparar archivo de proyecto', disabled=not db_value, key='project_prepare'):
            try:
                st.session_state['project_download'] = create_project_archive(
                    Path(db_value), dict(st.session_state),
                    datamap=Path(datamap) if include_source and datamap else None,
                    source=Path(source) if include_source and source else None,
                )
            except Exception as exc:
                st.session_state.pop('project_download', None)
                st.error(f'No se pudo preparar el proyecto: {exc}')
        if st.session_state.get('project_download'):
            download_button('Descargar proyecto para retomarlo', st.session_state['project_download'],
                               file_name='Explora_Proyecto.zip', mime='application/zip', key='project_download_button', on_click='ignore')
            st.caption('Es una copia del momento en que pulsaste Preparar. Si cambias la configuración o guardas otra tabla, prepara un archivo nuevo. Los resultados canónicos deben vincularse de nuevo; no se restaura su estado de aprobación.')
        uploaded = st.file_uploader('Recuperar proyecto de EXPLORA (.zip)', type=['zip'], key='project_restore_upload')
        if st.button('Recuperar proyecto', disabled=uploaded is None, key='project_restore'):
            try:
                restored = restore_project_archive(uploaded.getvalue(), session_dir('restored') / uuid4().hex)
                source_state = {}
                if restored['datamap_path'] and restored['spss_path']:
                    df, meta, summary = read_spss(restored['spss_path'])
                    sheets = read_datamap(restored['datamap_path'])
                    _, raw = get_review_source_sheet(sheets)
                    review = enrich_datamap_with_spss_structure(
                        normalize_review_datamap(raw, list(df.columns)), df, meta, sheets)
                    source_state = {'df_spss': df, 'meta_spss': meta, 'spss_summary': summary,
                                    'datamap_sheets': sheets, 'review_datamap': review}
                for key in list(st.session_state):
                    if key.startswith(('report_', 'paired_', 'current_', 'canonical_')) or key in {
                        'db_path', 'saved_reports', 'analytic_tables', 'df_spss', 'meta_spss',
                        'spss_summary', 'datamap_sheets', 'review_datamap', 'datamap_path',
                        'datamap_final_path', 'spss_path', 'revision_excel_path', 'grid_loop_structures',
                        'datamap_review_saved', 'failed_analysis_binding', 'pending_analysis_binding',
                        'last_execution_error', 'project_download'}:
                        del st.session_state[key]
                controls = restored.pop('controls')
                st.session_state.update(restored)
                st.session_state.update(source_state)
                st.session_state.update(controls)
                st.session_state['project_navigation'] = '4. Reporteador'
                st.session_state['project_restored_message'] = 'Proyecto recuperado. Revisa las selecciones y pulsa Generar tabla para recalcular el análisis actual.'
                st.rerun()
            except Exception as exc:
                st.error(f'No se pudo recuperar el proyecto: {exc}. La sesión anterior se conserva si no se completó la lectura.')
        message = st.session_state.get('project_restored_message')
        if message:
            st.success(message)
