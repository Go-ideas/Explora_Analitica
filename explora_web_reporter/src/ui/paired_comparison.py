from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.database.db_reader import read_table
from src.reporter.filters import config_entries, filter_choices
from src.reporter.paired_comparison import PairedCondition, compare_paired


def render_paired_comparison(db_path: Path, questions: pd.DataFrame) -> None:
    with st.expander('Comparar las mismas personas entre productos o tiempos'):
        st.info('Usa este panel cuando las mismas personas respondieron en ambas condiciones. Solo se comparan personas con ambas respuestas válidas. Si son grupos distintos, esta comparación no corresponde.')
        st.caption('Comparación histórica sin ponderación. Define aquí las dos condiciones; los filtros de la tabla anterior no se aplican a este panel.')
        candidates = questions[questions.tipo_pregunta_reporter.isin(['Escala','NPS','RM'])]
        if candidates.empty:
            st.info('No hay preguntas de escala o RM para comparar.')
            return
        labels = {str(row.pregunta_id): str(row.texto_pregunta) for _,row in candidates.iterrows()}
        columns=st.columns(2)
        conditions=[]
        entries=pd.concat([config_entries(db_path,'banner'),config_entries(db_path,'filtro')],ignore_index=True)
        variables=list(dict.fromkeys(entries.get('variable',pd.Series(dtype=str)).astype(str)))
        for index, column in enumerate(columns):
            side='A' if index==0 else 'B'
            with column:
                st.markdown(f'**Condición {side}**')
                question=st.selectbox(f'Pregunta {side}',list(labels),format_func=lambda key: f'{key} | {labels[key]}',key=f'paired_question_{side}')
                variable=st.selectbox(f'Filtrar condición {side}', ['']+variables,format_func=lambda value:value or 'Sin filtro',key=f'paired_filter_{side}')
                filters={}
                if variable:
                    choices=filter_choices(db_path,variable)
                    choice=st.selectbox(f'Valor {side}',choices,format_func=lambda value:value.display,key=f'paired_value_{side}_{variable}') if choices else None
                    if choice is None:
                        st.warning('El filtro no tiene valores disponibles.')
                        return
                    filters[variable]=[choice.value]
                conditions.append(PairedCondition(question,filters))
        metric=st.selectbox('Qué comparar',['Media','Top2Box','BottomBox','Selección RM'],key='paired_metric')
        option=None
        if metric=='Selección RM':
            options=read_table(db_path,'opciones')
            options=options[options.pregunta_id.eq(conditions[0].question_id)].dropna(subset=['codigo']).drop_duplicates('codigo')
            options=options[pd.to_numeric(options.codigo,errors='coerce').ne(0)]
            if options.empty:
                st.info('La primera condición no tiene opciones declaradas.')
                return
            option_labels=dict(zip(options.codigo,options.label))
            option=st.selectbox('Opción RM',list(option_labels),format_func=lambda code:f'{code} | {option_labels[code]}',key='paired_option')
        policy=st.selectbox('Si una persona tiene varias evaluaciones en una condición',
            ['reject','person_mean'] if metric=='Media' else ['reject'],
            format_func=lambda value:'Pedir que se filtre una sola evaluación' if value=='reject' else 'Usar la media por persona en cada condición',key=f'paired_policy_{metric}')
        st.caption('No se elige una evaluación al azar: filtra una por persona o, para Media, selecciona explícitamente la media por persona. La tabla final informa cuántos pares completos se pudieron comparar.')
        settings=st.columns(2)
        confidence=settings[0].selectbox('Confianza de la comparación pareada',[.90,.95,.99],index=1,format_func=lambda value:f'{value:.0%}',key='paired_confidence')
        minimum=int(settings[1].number_input('Mínimo de personas con ambas respuestas',min_value=2,value=30,step=1,key='paired_minimum'))
        signature=json.dumps([str(db_path),db_path.stat().st_mtime_ns,[{'question':c.question_id,'filters':c.filters} for c in conditions],metric,option,policy,confidence,minimum],sort_keys=True,default=str)
        if st.button('Calcular comparación pareada',key='paired_calculate'):
            st.session_state.pop('paired_comparison_result',None)
            try:
                result=compare_paired(db_path,*conditions,metric=metric,option_code=option,duplicate_policy=policy,confidence=confidence,min_pairs=minimum)
                st.session_state['paired_comparison_result']=(signature,result)
            except (ValueError,KeyError) as exc:
                st.error(f'No se pudo comparar: {exc}')
        saved=st.session_state.get('paired_comparison_result')
        if saved and saved[0]==signature:
            result=saved[1]
            st.dataframe(result.table,hide_index=True)
            st.write(f"Método: {result.config['Método']}. Valores binarios expresados como proporciones de 0 a 1.")
            st.download_button('Descargar comparación pareada',result.excel_bytes(),file_name='Comparacion_Pareada.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key='paired_download',on_click='ignore')
            for note in result.notes:
                st.caption(note)
