"""Portable project snapshots: SQLite plus typed JSON, never executable objects."""
from dataclasses import fields
from hashlib import sha256
from io import BytesIO, StringIO
import json
import math
from numbers import Integral, Real
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import numpy as np
import plotly.io as pio
from plotly.graph_objects import Figure

from src.database.validation import validate_reporter_database
from src.reporter.filters import FilterChoice
from src.reporter.tabulator import ReportResult


MAX_BYTES = 512 * 1024 * 1024
MEMBERS = {'database.db', 'state.json', 'source.sav', 'datamap.xlsx'}
CONTROL = re.compile(
    r'report_(?:question|banners|filter_variables|weight|banner_mode|response_order|'
    r'confidence|min_base|significance_display|execution_mode|calculations_.+_v2|filter_values_.+)'
    r'|paired_(?:question_[AB]|filter_[AB]|value_[AB]_.+|metric|option|policy_.+|confidence|minimum)'
)


def encode(value):
    if isinstance(value, pd.DataFrame):
        table = json.loads(value.to_json(orient='table', date_format='iso', double_precision=15))
        # Pandas' JSON writer rounds tiny probabilities to zero. Preserve the
        # original finite floats using Python's round-trip JSON representation.
        for column in value.columns:
            for record, cell in zip(table['data'], value[column].tolist()):
                if isinstance(cell, Real) and not isinstance(cell, (bool, Integral)) and math.isfinite(cell):
                    record[str(column)] = float(cell)
        return {'__type__': 'frame', 'value': json.dumps(table, ensure_ascii=False, allow_nan=False)}
    if isinstance(value, np.generic):
        return encode(value.item())
    if isinstance(value, Figure):
        return {'__type__': 'figure', 'value': pio.to_json(value)}
    if isinstance(value, FilterChoice):
        return {'__type__': 'choice', 'value': encode(value.value), 'display': value.display}
    if isinstance(value, ReportResult):
        return {'__type__': 'report', 'value': {f.name: encode(getattr(value, f.name)) for f in fields(ReportResult)}}
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): encode(item) for key, item in value.items()}
    raise ValueError(f'Tipo no portable en la configuración: {type(value).__name__}')


def decode(value):
    if isinstance(value, list):
        return [decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    kind = value.get('__type__')
    if kind == 'frame':
        return pd.read_json(StringIO(value['value']), orient='table', precise_float=True)
    if kind == 'figure':
        return pio.from_json(value['value'])
    if kind == 'choice':
        return FilterChoice(decode(value['value']), str(value['display']))
    if kind == 'report':
        return ReportResult(**{key: decode(item) for key, item in value['value'].items()})
    if kind is not None:
        raise ValueError('El proyecto contiene un tipo de configuración desconocido.')
    return {key: decode(item) for key, item in value.items()}


def create_project_archive(db_path: Path, state: dict, *, datamap: Path | None = None,
                           source: Path | None = None) -> bytes:
    validation = validate_reporter_database(db_path)
    if not validation.ok:
        raise ValueError(validation.message)
    controls = {key: value for key, value in state.items() if CONTROL.fullmatch(key)}
    saved = state.get('saved_reports', [])
    payload = {'controls': controls, 'saved_reports': saved,
               'review_saved': bool(state.get('datamap_review_saved'))}
    members = {'state.json': json.dumps(encode(payload), ensure_ascii=False, allow_nan=False).encode()}
    # SQLite backup includes committed WAL data and produces a consistent copy.
    with TemporaryDirectory() as folder:
        copy = Path(folder) / 'snapshot.db'
        with sqlite3.connect(db_path) as original, sqlite3.connect(copy) as target:
            original.backup(target)
        members['database.db'] = copy.read_bytes()
    for name, path in [('datamap.xlsx', datamap), ('source.sav', source)]:
        if path is not None and path.is_file():
            members[name] = path.read_bytes()
    if sum(map(len, members.values())) > MAX_BYTES:
        raise ValueError('El proyecto supera el tamaño portátil permitido (512 MB).')
    manifest = {'format': 'EXPLORA_PROJECT', 'version': 1,
                'files': {name: sha256(content).hexdigest() for name, content in members.items()}}
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', json.dumps(manifest))
        for name, content in members.items():
            archive.writestr(name, content)
    return output.getvalue()


def restore_project_archive(content: bytes, directory: Path) -> dict:
    """Validate completely before returning session state; use a new directory."""
    if len(content) > MAX_BYTES:
        raise ValueError('El archivo de proyecto supera 512 MB.')
    with ZipFile(BytesIO(content)) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)) or not set(names).issubset(MEMBERS | {'manifest.json'}):
            raise ValueError('El proyecto contiene archivos duplicados o no permitidos.')
        if not {'manifest.json', 'database.db', 'state.json'}.issubset(names):
            raise ValueError('El proyecto está incompleto.')
        if sum(item.file_size for item in infos) > MAX_BYTES:
            raise ValueError('El proyecto descomprimido supera 512 MB.')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('format') != 'EXPLORA_PROJECT' or manifest.get('version') != 1:
            raise ValueError('Formato o versión de proyecto no compatible.')
        members = {name: archive.read(name) for name in names if name != 'manifest.json'}
    if manifest.get('files') != {name: sha256(data).hexdigest() for name, data in members.items()}:
        raise ValueError('La comprobación de integridad del proyecto falló.')
    state = decode(json.loads(members['state.json']))
    if not isinstance(state, dict) or not isinstance(state.get('controls'), dict) or not isinstance(state.get('saved_reports'), list):
        raise ValueError('La configuración del proyecto no es válida.')
    if any(not CONTROL.fullmatch(key) for key in state['controls']):
        raise ValueError('El proyecto incluye controles no permitidos.')
    if any(not isinstance(item, dict) or not isinstance(item.get('report'), ReportResult) for item in state['saved_reports']):
        raise ValueError('Los análisis guardados no son compatibles.')
    directory.mkdir(parents=True, exist_ok=False)
    try:
        for name, data in members.items():
            if name != 'state.json':
                (directory / name).write_bytes(data)
        validation = validate_reporter_database(directory / 'database.db')
        if not validation.ok:
            raise ValueError(validation.message)
    except Exception:
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()
        raise
    return {'db_path': directory / 'database.db', 'controls': state['controls'],
            'saved_reports': state['saved_reports'],
            'datamap_review_saved': bool(state.get('review_saved')),
            'datamap_path': directory / 'datamap.xlsx' if 'datamap.xlsx' in members else None,
            'spss_path': directory / 'source.sav' if 'source.sav' in members else None}
