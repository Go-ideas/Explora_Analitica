"""Explain analysis choices from stored metadata, never from question names."""
from dataclasses import dataclass
from pathlib import Path
import math

import pandas as pd

from src.database.db_reader import list_tables, read_sql
from src.reporter.analysis_unit import is_person_unit
from src.utils.text_utils import normalize_text


@dataclass(frozen=True)
class QuestionRecommendation:
    calculations: tuple[str, ...]
    reason: str
    base: str
    warnings: tuple[str, ...]


def recommend_question(db_path: Path, question_id: str) -> QuestionRecommendation:
    tables = set(list_tables(db_path))
    def question_rows(table):
        if table not in tables:
            return pd.DataFrame()
        return read_sql(db_path, f'SELECT * FROM "{table}" WHERE pregunta_id = ?', (question_id,))

    questions = question_rows('preguntas')
    if len(questions) != 1:
        return QuestionRecommendation((), 'No hay una definición única de esta pregunta.',
                                      'Requiere revisión del Datamap.', ('Revisa el tipo y la unidad de análisis.',))
    row = questions.iloc[0]
    kind = normalize_text(row.get('tipo_pregunta', ''))
    kind = {
        'ru_escala': 'escala',
        'escala_hedonica': 'escala',
        'ru_escala_hedonica': 'escala',
        'respuesta_unica': 'ru',
        'respuesta_multiple': 'rm',
    }.get(kind, kind)
    warnings = []
    person = is_person_unit(row.get('unidad_analisis', ''))
    unit = 'personas' if person else 'evaluaciones'
    base = f'Unidad: {unit}. La base válida se calcula al generar la tabla con los filtros elegidos.'
    raw_unit = row.get('unidad_analisis')
    if pd.isna(raw_unit) or not str(raw_unit).strip():
        warnings.append('La unidad no está declarada: el motor usa evaluaciones. Confirma si corresponde analizar por persona.')
    elif not person and normalize_text(raw_unit) not in {'evaluacion', 'evaluaciones', 'evaluation', 'evaluations'}:
        warnings.append(f'Unidad de análisis no reconocida: {raw_unit}. El motor usa evaluaciones; confirma o corrige la declaración antes de interpretar la base.')
    rule = row.get('base_valida', '')
    if pd.notna(rule) and str(rule).strip():
        warnings.append(f'Base válida declarada: {rule}. Revisa su implementación y los faltantes; mostrar esta regla no implica que se haya ejecutado una condición adicional.')

    if 'grid_rm' in kind or 'loop_rm' in kind:
        calculations = ('% respondentes', 'Menciones')
        reason = 'Estructura multirrespuesta por entidad declarada: conserva sus filas y opciones.'
        warnings.append('Comprueba la base válida de cada entidad; no agrupes productos o tiempos sin una regla explícita.')
    elif kind in {'rm', 'rm_codificada', 'multirrespuesta'}:
        calculations = ('n', 'RM % Respondentes', 'RM % Menciones')
        reason = 'Respuesta múltiple declarada: distingue selección de opciones y distribución de menciones.'
        base += f' RM % Respondentes usa {unit} elegibles; RM % Menciones usa el total de menciones.'
        warnings.append('Los porcentajes de selección pueden sumar más de 100%.')
        if question_rows('bases_multirrespuesta').empty:
            warnings.append('Falta la tabla de elegibilidad RM: revisa el denominador antes de interpretar porcentajes, especialmente los casos sin selecciones.')
    elif 'jar' in kind:
        calculations = ('n', '%')
        reason = 'Escala JAR declarada: comienza con la distribución de sus categorías etiquetadas.'
        warnings.append('Confirma qué códigos significan menos de lo ideal, ideal y más de lo ideal. No se inventan agrupaciones ni se calcula penalización automáticamente.')
    elif kind == 'nps':
        calculations = ('NPS',)
        reason = 'NPS declarado: utiliza la clasificación de detractores, pasivos y promotores de la escala 0–10.'
    elif kind in {'escala', 'numerica', 'numerico', 'loop_numerico', 'grid_escala'}:
        calculations = ('Distribución grid', 'Media') if kind == 'grid_escala' else ('Media', 'Desviación estándar')
        reason = 'Variable numérica o escala declarada: resume el nivel y la dispersión sin deducir su significado del texto.'
        scale = question_rows('escalas_long')
        bounded = False
        if {'escala_min', 'escala_max'}.issubset(scale.columns) and not scale.empty:
            lows = pd.to_numeric(scale.escala_min, errors='coerce')
            highs = pd.to_numeric(scale.escala_max, errors='coerce')
            bounded = bool(lows.map(math.isfinite).all() and highs.map(math.isfinite).all() and (highs > lows).all())
            # A physical item cannot have contradictory scale definitions.
            # Different explicitly defined grid items may use different bounds.
            definitions = pd.DataFrame({'low': lows, 'high': highs})
            if 'variable' in scale:
                definitions['variable'] = scale['variable']
                consistent = definitions.groupby('variable', dropna=False)[['low', 'high']].nunique(dropna=False).le(1).all().all()
            else:
                consistent = definitions.nunique(dropna=False).le(1).all()
            bounded = bounded and bool(consistent)
        if kind not in {'numerica', 'numerico', 'loop_numerico'} and bounded:
            calculations += ('Top2Box', 'BottomBox')
            warnings.append('Top2Box y BottomBox usan los extremos de la escala definida. Confirma que esos extremos tienen sentido comercial; no equivalen automáticamente a agrado o desagrado.')
        elif kind not in {'numerica', 'numerico', 'loop_numerico'}:
            warnings.append('Los límites de escala faltan, son inválidos o contradictorios: no se sugieren Top2Box ni BottomBox a partir de mínimos o máximos observados.')
    elif kind in {'ru', 'categorica', 'categorical'}:
        calculations = ('n', '%')
        reason = 'Respuesta única categórica declarada: muestra conteos y porcentajes; los códigos no se tratan como cantidades.'
    else:
        calculations = ()
        reason = 'El tipo de pregunta no tiene una recomendación automática segura.'
        warnings.append('Revisa el tipo y las reglas en el Datamap. No se deducen cálculos del nombre de la variable.')

    axis = row.get('tipo_eje_fila', '')
    if pd.notna(axis) and str(axis).strip():
        warnings.append(f'Eje de repetición declarado: {axis}. Conserva separados sus niveles; para contrastar las mismas personas utiliza el panel de comparación pareada.')
    parent = row.get('pregunta_padre', '')
    if pd.notna(parent) and str(parent).strip():
        base += f' Pregunta de origen: {parent}.'
    if 'respondentes' in tables:
        respondents = read_sql(db_path, 'SELECT * FROM respondentes')
        if {'id_persona', 'id_original'}.issubset(respondents.columns):
            ids = respondents.id_persona.astype(str).str.strip()
            original = respondents.id_original.astype(str).str.strip()
            valid = respondents.id_persona.notna().all() and not ids.str.casefold().isin({'', 'nan', 'none', 'null'}).any() and ids.eq(original).all()
            if valid and ids.duplicated().any():
                warnings.append('La base completa contiene varias evaluaciones por persona. No supongas independencia entre productos o tiempos; verifica el solapamiento después de filtrar. Para comparar las mismas personas usa el panel pareado.')
                if person:
                    warnings.append('La unidad persona requiere respuestas y atributos consistentes dentro de cada persona; el motor validará esa condición al generar la tabla.')
            elif not valid:
                warnings.append('No hay un identificador de persona verificable para recomendar comparaciones pareadas.')
        else:
            warnings.append('La base no permite comprobar la identidad de personas; revisa su identificación antes de comparar mediciones repetidas.')
    else:
        warnings.append('Falta la tabla de personas/evaluaciones: no se puede comprobar la identidad ni recomendar comparaciones pareadas.')
    return QuestionRecommendation(calculations, reason, base, tuple(warnings))
