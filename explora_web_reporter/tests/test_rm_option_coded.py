from types import SimpleNamespace

import pandas as pd
import pytest

from src.builder.analytic_db_builder import build_analytic_database
from src.database.db_reader import read_table
from src.readers.datamap_reader import normalize_review_datamap
from src.reporter.tabulator import generate_report


def build(tmp_path, *, all_zero=False, fmt='codigo_por_opcion', unit='Evaluación', string_labels=False):
    df = pd.DataFrame({'case':['A','B','C','D','E'],
                       'benefit_a':[10,0,0,None,0], 'benefit_b':[0,20,0,None,20],
                       'group':[1,1,2,2,2], 'weight':[1.,2.,3.,4.,5.]})
    if all_zero: df.loc[df.benefit_a.notna(),'benefit_a']=0; df.loc[df.benefit_b.notna(),'benefit_b']=0
    dm = normalize_review_datamap(pd.DataFrame([
        {'variable':'benefit_a','pregunta_id':'BEN','tipo_pregunta':'RM', 'formato_rm':fmt,
         'codigo_opcion_rm':10,'id_respondente':'case','unidad_analisis':unit,'usar_en_dashboard':True},
        {'variable':'benefit_b','pregunta_id':'BEN','tipo_pregunta':'RM', 'formato_rm':fmt,
         'codigo_opcion_rm':20,'id_respondente':'case','unidad_analisis':unit,'usar_en_dashboard':True},
        {'variable':'group','tipo_pregunta':'RU','es_banner':True,'es_filtro':True,'usar_en_dashboard':True},
        {'variable':'weight','clasificacion_analitica':'Ponderador','es_ponderador':True},
    ]),list(df))
    labels = {'10':'A','20':'B'} if string_labels else {10:'A',20:'B'}
    meta = SimpleNamespace(variable_value_labels={c:labels for c in ['benefit_a','benefit_b']},column_names_to_labels={})
    db=tmp_path/'rm.db'
    build_analytic_database(df,meta,dm,db_path=db,export_revision=False)
    return db


@pytest.mark.parametrize('string_labels',[False,True])
def test_zero_is_not_a_mention_and_zero_selection_stays_in_base(tmp_path,string_labels):
    db=build(tmp_path,string_labels=string_labels)
    mentions=read_table(db,'multirrespuesta_long')
    assert len(mentions)==3 and set(mentions.respuesta_label)=={'A','B'}
    r=generate_report(db,'BEN',calculations=['RM % Respondentes','RM % Menciones','Menciones'])
    assert r.base==4 and r.person_base==4
    summary=r.summary.set_index('respuesta')
    assert summary.at['A','pct_respondentes']==.25
    assert summary.at['B','pct_respondentes']==.5
    assert summary.at['A','pct_menciones']==pytest.approx(1/3)


def test_option_bases_follow_banners_filters_and_weights(tmp_path):
    db=build(tmp_path)
    r=generate_report(db,'BEN',banner=['group'],ponderador='weight',calculations=['RM % Respondentes','% ponderado'])
    a=r.summaries['rm'].query("respuesta=='A' and banner=='Total'").iloc[0]
    assert a.base==4 and a.base_ponderada==11
    assert a.pct_respondentes_ponderado==pytest.approx(1/11)
    # The second group includes the evaluation with no selected options.
    second=r.summaries['rm'][r.summaries['rm'].banner.eq('2')]
    assert second.base.iloc[0]==2
    filtered=generate_report(db,'BEN',filters={'group':[2]},calculations=['RM % Respondentes'])
    assert filtered.base==2 and filtered.summary.pct_respondentes.iloc[0]==.5


def test_all_zero_options_keep_valid_base_without_fabricating_mentions(tmp_path):
    db=build(tmp_path,all_zero=True)
    r=generate_report(db,'BEN',calculations=['RM % Respondentes'])
    assert r.base==4 and r.summary.empty
    assert read_table(db,'multirrespuesta_long').empty


@pytest.mark.parametrize('selected_code',[1,10])
def test_explicit_mentions_can_retain_a_labelled_zero_category(tmp_path,selected_code):
    df=pd.DataFrame({'slot_a':[0,selected_code], 'slot_b':[20,0]})
    dm=normalize_review_datamap(pd.DataFrame({'variable':list(df),'pregunta_id':['M','M'],
        'tipo_pregunta':['RM','RM'],'formato_rm':['menciones','menciones'],'usar_en_dashboard':[True,True]}))
    labels={0:'Neutral',selected_code:'A',20:'B'}
    meta=SimpleNamespace(variable_value_labels={c:labels for c in df},column_names_to_labels={})
    db=tmp_path/'mentions.db'
    build_analytic_database(df,meta,dm,db_path=db,export_revision=False)
    assert 'Neutral' in set(read_table(db,'multirrespuesta_long').respuesta_label)


@pytest.mark.parametrize('bad_values', [[10,11], [10,'invalid']])
def test_option_coded_unknown_states_require_validation(tmp_path,bad_values):
    df=pd.DataFrame({'option':bad_values})
    dm=normalize_review_datamap(pd.DataFrame([{'variable':'option','pregunta_id':'B','tipo_pregunta':'RM',
        'formato_rm':'codigo_por_opcion','codigo_opcion_rm':10,'usar_en_dashboard':True}]))
    meta=SimpleNamespace(variable_value_labels={'option':{10:'A'}},column_names_to_labels={})
    with pytest.raises(ValueError,match='RM'):
        build_analytic_database(df,meta,dm,db_path=tmp_path/'invalid.db',export_revision=False)


def test_option_axis_uses_numeric_code_and_authoritative_label_without_suffix_guessing(tmp_path):
    df=pd.DataFrame({'arbitrary_name':[0,12,0]})
    dm=normalize_review_datamap(pd.DataFrame([{'variable':'arbitrary_name','pregunta_id':'B','tipo_pregunta':'RM',
        'Tipo_Eje_Fila':'Opción RM','usar_en_dashboard':True}]))
    meta=SimpleNamespace(variable_value_labels={'arbitrary_name':{12:'Beneficio',25:'Otro beneficio'}},column_names_to_labels={})
    db=tmp_path/'axis.db'
    build_analytic_database(df,meta,dm,db_path=db,export_revision=False)
    r=generate_report(db,'B',calculations=['RM % Respondentes'])
    assert r.base==3 and r.summary.pct_respondentes.iloc[0]==pytest.approx(1/3)
    assert r.summary.respuesta.iloc[0]=='Beneficio'


def test_unobserved_option_requires_explicit_code_instead_of_inventing_it(tmp_path):
    df=pd.DataFrame({'option':[0,0]})
    dm=normalize_review_datamap(pd.DataFrame([{'variable':'option','pregunta_id':'B','tipo_pregunta':'RM',
        'formato_rm':'codigo_por_opcion','usar_en_dashboard':True}]))
    meta=SimpleNamespace(variable_value_labels={'option':{12:'A',25:'B'}},column_names_to_labels={})
    with pytest.raises(ValueError,match='Declare codigo_opcion_rm'):
        build_analytic_database(df,meta,dm,db_path=tmp_path/'unknown.db',export_revision=False)


def test_blank_option_cells_are_missing_not_zero_selection(tmp_path):
    df=pd.DataFrame({'option':['12','0','  ',None]})
    dm=normalize_review_datamap(pd.DataFrame([{'variable':'option','pregunta_id':'B','tipo_pregunta':'RM',
        'formato_rm':'codigo_por_opcion','codigo_opcion_rm':12,'usar_en_dashboard':True}]))
    meta=SimpleNamespace(variable_value_labels={'option':{12:'A'}},column_names_to_labels={})
    db=tmp_path/'blank.db'
    build_analytic_database(df,meta,dm,db_path=db,export_revision=False)
    r=generate_report(db,'B',calculations=['RM % Respondentes'])
    assert r.base==2 and r.summary.pct_respondentes.iloc[0]==.5
