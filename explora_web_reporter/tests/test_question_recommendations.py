import sqlite3

import pandas as pd
import pytest

from src.reporter.question_recommendations import recommend_question


def database(tmp_path, kind, *, bounds=True, unit='evaluacion', repeated=True):
    path = tmp_path / 'study.db'
    with sqlite3.connect(path) as conn:
        pd.DataFrame([{'pregunta_id': 'arbitrary', 'tipo_pregunta': kind,
                       'unidad_analisis': unit, 'pregunta_padre': '',
                       'tipo_eje_fila': ''}]).to_sql('preguntas', conn, index=False)
        pd.DataFrame({'id_respondente': ['r1', 'r2', 'r3'],
                      'id_persona': ['x', 'x' if repeated else 'z', 'y'],
                      'id_original': ['x', 'x' if repeated else 'z', 'y']}).to_sql('respondentes', conn, index=False)
        # Observed values alone must never define box thresholds.
        pd.DataFrame({'pregunta_id': ['arbitrary'] * 3, 'valor': [3, 4, 5],
                      'escala_min': [1 if bounds else None] * 3,
                      'escala_max': [9 if bounds else None] * 3}).to_sql('escalas_long', conn, index=False)
    return path


@pytest.mark.parametrize('kind,expected', [
    ('RU', ('n', '%')), ('Escala JAR', ('n', '%')), ('NPS', ('NPS',)),
    ('Numérica', ('Media', 'Desviación estándar')),
    ('RM', ('n', 'RM % Respondentes', 'RM % Menciones')),
    ('GRID_RM', ('% respondentes', 'Menciones')),
])
def test_declared_type_drives_suggestion(tmp_path, kind, expected):
    result = recommend_question(database(tmp_path, kind), 'arbitrary')
    assert result.calculations == expected


def test_scale_uses_stored_bounds_not_observed_extremes(tmp_path):
    path = database(tmp_path, 'Escala', bounds=False)
    result = recommend_question(path, 'arbitrary')
    assert result.calculations == ('Media', 'Desviación estándar')
    assert any('límites' in text for text in result.warnings)
    with sqlite3.connect(path) as conn:
        conn.execute('UPDATE escalas_long SET escala_min=1, escala_max=9')
    assert 'Top2Box' in recommend_question(path, 'arbitrary').calculations


def test_jar_does_not_invent_grouping_or_recommend_boxes(tmp_path):
    result = recommend_question(database(tmp_path, 'Escala JAR'), 'arbitrary')
    assert any('códigos' in text and 'penalización' in text for text in result.warnings)
    assert 'Top2Box' not in result.calculations


def test_unknown_type_and_missing_question_require_review(tmp_path):
    path = database(tmp_path, 'Unspecified')
    assert not recommend_question(path, 'arbitrary').calculations
    assert not recommend_question(path, 'not-present').calculations


def test_repeated_person_warning_and_person_base_are_explicit(tmp_path):
    result = recommend_question(database(tmp_path, 'RU', unit='persona'), 'arbitrary')
    assert 'Unidad: personas' in result.base
    assert any('varias evaluaciones' in text for text in result.warnings)
    assert any('consistentes' in text for text in result.warnings)


def test_rm_missing_eligible_universe_warns(tmp_path):
    result = recommend_question(database(tmp_path, 'RM'), 'arbitrary')
    assert 'total de menciones' in result.base
    assert any('elegibilidad' in text for text in result.warnings)


def test_invalid_identity_never_suggests_pairing(tmp_path):
    path = database(tmp_path, 'RU')
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE respondentes SET id_persona='generated'")
    result = recommend_question(path, 'arbitrary')
    assert any('identificador de persona verificable' in text for text in result.warnings)
    assert not any('varias evaluaciones' in text for text in result.warnings)


def test_axis_and_valid_base_rule_are_shown_without_changing_database(tmp_path):
    path = database(tmp_path, 'Escala', repeated=False)
    with sqlite3.connect(path) as conn:
        conn.execute('ALTER TABLE preguntas ADD COLUMN base_valida TEXT')
        conn.execute("UPDATE preguntas SET tipo_eje_fila='Momento', base_valida='answer_key = 2'")
    before = path.read_bytes()
    result = recommend_question(path, 'arbitrary')
    assert any('Momento' in text for text in result.warnings)
    assert any('answer_key = 2' in text for text in result.warnings)
    assert not any('varias evaluaciones' in text for text in result.warnings)
    assert path.read_bytes() == before


def test_missing_unit_requests_review_instead_of_assuming_people(tmp_path):
    result = recommend_question(database(tmp_path, 'RU', unit=None), 'arbitrary')
    assert 'Unidad: evaluaciones' in result.base
    assert any('unidad no está declarada' in text for text in result.warnings)


@pytest.mark.parametrize('kind', ['RU', 'Escala', 'Escala JAR', 'RM', 'NPS', 'Numérica'])
def test_recommendation_is_invariant_to_project_names_ids_and_row_order(tmp_path, kind):
    path = database(tmp_path, kind)
    expected = recommend_question(path, 'arbitrary')
    new_id = "ítem ' sin sufijo / β"
    with sqlite3.connect(path) as conn:
        conn.execute('UPDATE preguntas SET pregunta_id=?', (new_id,))
        conn.execute('UPDATE escalas_long SET pregunta_id=?', (new_id,))
        conn.execute("UPDATE respondentes SET id_persona='person_' || id_persona, id_original='person_' || id_original")
        reordered = pd.read_sql_query('SELECT * FROM escalas_long ORDER BY rowid DESC', conn)
        reordered.to_sql('escalas_long', conn, if_exists='replace', index=False)
    renamed = tmp_path / 'Proyecto independiente κ.db'
    path.rename(renamed)
    assert recommend_question(renamed, new_id) == expected


@pytest.mark.parametrize('low,high', [(1, float('inf')), (float('-inf'), 9), (9, 1), (1, 1)])
def test_invalid_scale_definitions_do_not_suggest_boxes(tmp_path, low, high):
    path = database(tmp_path, 'Escala')
    with sqlite3.connect(path) as conn:
        conn.execute('UPDATE escalas_long SET escala_min=?, escala_max=?', (low, high))
    assert 'Top2Box' not in recommend_question(path, 'arbitrary').calculations


def test_conflicting_bounds_for_one_item_require_review(tmp_path):
    path = database(tmp_path, 'Escala')
    with sqlite3.connect(path) as conn:
        conn.execute('ALTER TABLE escalas_long ADD COLUMN variable TEXT')
        conn.execute("UPDATE escalas_long SET variable='physical_item'")
        conn.execute('UPDATE escalas_long SET escala_max=5 WHERE rowid=1')
    result = recommend_question(path, 'arbitrary')
    assert 'Top2Box' not in result.calculations
    assert any('contradictorios' in warning for warning in result.warnings)


def test_unknown_unit_is_not_silently_approved(tmp_path):
    result = recommend_question(database(tmp_path, 'RU', unit='hogar'), 'arbitrary')
    assert any('no reconocida: hogar' in warning for warning in result.warnings)


def test_missing_person_table_is_reported(tmp_path):
    path = database(tmp_path, 'RU')
    with sqlite3.connect(path) as conn:
        conn.execute('DROP TABLE respondentes')
    assert any('Falta la tabla' in warning for warning in recommend_question(path, 'arbitrary').warnings)


def test_rm_eligibility_is_checked_for_selected_question(tmp_path):
    path = database(tmp_path, 'RM')
    with sqlite3.connect(path) as conn:
        pd.DataFrame({'pregunta_id': ['another_question'], 'id_respondente': ['r1']}).to_sql('bases_multirrespuesta', conn, index=False)
    assert any('elegibilidad' in warning for warning in recommend_question(path, 'arbitrary').warnings)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE bases_multirrespuesta SET pregunta_id='arbitrary'")
    assert not any('elegibilidad' in warning for warning in recommend_question(path, 'arbitrary').warnings)
