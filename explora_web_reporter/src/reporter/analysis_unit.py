from __future__ import annotations

import pandas as pd

from src.utils.text_utils import normalize_text


def is_person_unit(value: object) -> bool:
    return normalize_text(value) in {'persona', 'respondente', 'person', 'respondent'}


def person_unit_data(
    respondents: pd.DataFrame,
    selected: pd.DataFrame,
    sources: list[pd.DataFrame],
    attributes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, list[pd.DataFrame]]:
    """Collapse declared person-level data only after verifying its invariance.

    Row keys remain untouched in storage. This view is built for the current
    question, with filters already applied, so no arbitrary product row defines
    a person's banner or weight.
    """
    if 'id_persona' not in respondents:
        return respondents, selected, sources
    lookup = respondents.set_index('id_respondente')['id_persona']
    converted = []
    for source in sources:
        if source.empty:
            converted.append(source.copy())
            continue
        work = source.copy()
        work['id_respondente'] = work['id_respondente'].map(lookup)
        if work['id_respondente'].isna().any():
            raise ValueError('Hay respuestas sin vínculo con su persona de origen.')
        variable = next((c for c in ('variable', 'variable_origen') if c in work), None)
        values = [c for c in ('codigo_respuesta', 'valor', 'respuesta_texto') if c in work]
        if variable and values:
            distinct = work[['id_respondente', variable, *values]].drop_duplicates()
            if distinct.duplicated(['id_respondente', variable]).any():
                raise ValueError(
                    'Una pregunta declarada por persona tiene respuestas diferentes entre evaluaciones. '
                    'Revise su unidad de análisis o declare el eje de repetición.'
                )
        converted.append(work.drop_duplicates(
            subset=[column for column in work if column != 'ponderador']
        ).reset_index(drop=True))
    for column in dict.fromkeys(attributes):
        if column in selected and selected.groupby('id_persona')[column].nunique(dropna=False).gt(1).any():
            raise ValueError(
                f'El banner o ponderador {column} cambia dentro de una persona. '
                'Filtre una evaluación o revise la unidad de análisis antes de comparar.'
            )

    def collapse(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.drop_duplicates('id_persona').copy()
        result['id_respondente'] = result['id_persona']
        return result.reset_index(drop=True)

    return collapse(respondents), collapse(selected), converted
