"""Review prerequisites without treating missing evidence as approval."""
import math
from pathlib import Path

import pandas as pd

from src.database.db_reader import read_table
from src.database.validation import validate_reporter_database
from src.reporter.analysis_unit import is_person_unit
from src.utils.text_utils import normalize_text, truthy


def analysis_readiness(db_path: Path) -> pd.DataFrame:
    rows = []
    def add(check, ok, detail):
        rows.append({'Revisión': check, 'Estado': 'Comprobado' if ok else 'Requiere revisión', 'Detalle / acción': detail})
    validation = validate_reporter_database(db_path)
    add('Estructura de la base', validation.ok, validation.message)
    if not validation.ok:
        return pd.DataFrame(rows)
    questions = read_table(db_path, 'preguntas')
    if 'usar_en_dashboard' in questions:
        questions = questions[questions.usar_en_dashboard.apply(truthy)]
    respondents = read_table(db_path, 'respondentes')
    units = questions.get('unidad_analisis', pd.Series('', index=questions.index))
    valid_units = units.apply(lambda value: is_person_unit(value) or normalize_text(value) in {'evaluacion', 'evaluaciones', 'evaluation', 'evaluations'})
    add('Unidad de análisis', bool(valid_units.all()) and not questions.empty,
        f'{int((~valid_units).sum())} preguntas sin unidad reconocida. Revisa persona frente a evaluación en el Datamap.')
    valid_identity = False
    if {'id_persona', 'id_original'}.issubset(respondents.columns) and not respondents.empty:
        ids = respondents.id_persona.astype(str).str.strip()
        valid_identity = bool(respondents.id_persona.notna().all() and not ids.str.casefold().isin({'', 'nan', 'none', 'null'}).any() and ids.eq(respondents.id_original.astype(str).str.strip()).all())
    detail = 'Sin identificación verificable. No se pueden dar por válidas las comparaciones pareadas.'
    if valid_identity:
        detail = f'{len(respondents):,} evaluaciones; {ids.nunique():,} personas únicas. Comprueba el solapamiento de personas después de filtrar.'
    add('Identificación de personas', valid_identity, detail)
    if 'escalas_long' in validation.tables:
        scales = read_table(db_path, 'escalas_long')
        if not scales.empty:
            if {'escala_min', 'escala_max'}.issubset(scales.columns):
                low = pd.to_numeric(scales.escala_min, errors='coerce')
                high = pd.to_numeric(scales.escala_max, errors='coerce')
                good = low.map(math.isfinite) & high.map(math.isfinite) & high.gt(low)
                group = [column for column in ['pregunta_id', 'variable'] if column in scales]
                consistent = bool(scales.groupby(group, dropna=False)[['escala_min', 'escala_max']].nunique(dropna=False).le(1).all().all()) if group else False
                ok = bool(good.all()) and consistent
            else:
                ok = False
            add('Límites de escala', ok, 'Los límites deben ser finitos, ordenados y consistentes por ítem. Revisa las recomendaciones de cada pregunta; los extremos observados no definen la escala.')
    config = read_table(db_path, 'configuracion_dashboard')
    weight_names = config.loc[config.tipo_configuracion.eq('ponderador'), 'variable'].dropna().astype(str).unique() if {'tipo_configuracion', 'variable'}.issubset(config) else []
    bad_weights = []
    for name in weight_names:
        if name not in respondents:
            bad_weights.append(name)
            continue
        values = pd.to_numeric(respondents[name], errors='coerce')
        if not (values.map(math.isfinite) & values.gt(0)).all():
            bad_weights.append(name)
    add('Ponderación', not bad_weights, 'Sin ponderador configurado: análisis sin ponderación.' if not len(weight_names) else
        ('Revisa ponderadores ausentes, vacíos, no positivos o no finitos: ' + ', '.join(bad_weights) if bad_weights else 'Ponderadores numéricos positivos y finitos. Su validez metodológica requiere revisión.'))
    add('Reglas de aplicación y aprobación metodológica', False,
        'Revisa cuestionario, saltos, exclusiones y bases válidas. Estas comprobaciones automáticas no certifican la metodología ni ejecutan reglas nuevas.')
    return pd.DataFrame(rows)
