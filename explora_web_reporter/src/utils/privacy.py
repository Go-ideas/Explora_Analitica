"""Expiring bearer downloads and lifecycle cleanup for the reporter apps.

The media adapter is deliberately limited to the pinned Streamlit version.
Unsupported runtimes stop rather than silently serving permanent downloads.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps, partial
from hashlib import sha256
import json
import logging
import math
from pathlib import Path
import re
import secrets
import shutil
from threading import Event, RLock, Thread
import time

import streamlit as st
from streamlit import runtime
from streamlit.runtime.media_file_storage import MediaFileKind, MediaFileStorageError
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage, _calculate_file_id
from streamlit.runtime.scriptrunner import get_script_run_ctx

from src.utils.constants import DATA_DIR

DOWNLOAD_SECONDS = 300
IDLE_SECONDS = 1800
SWEEP_SECONDS = 15
_INSTALL_LOCK = RLock()
_OWNER = re.compile(r'[0-9a-f]{32}')


@dataclass
class Session:
    expires: float
    close: object = None
    busy: int = 0
    caches: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Lease:
    owner: str
    deadline: float
    name: str


class PrivacyManager:
    def __init__(self, storage, root, *, clock=time.monotonic, wall=time.time,
                 download_seconds=DOWNLOAD_SECONDS, idle_seconds=IDLE_SECONDS):
        self.storage, self.root = storage, Path(root)
        self.clock, self.wall = clock, wall
        self.download_seconds, self.idle_seconds = download_seconds, idle_seconds
        self.lock = RLock()
        self.sessions, self.leases = {}, {}
        self.framework_owners = {}
        self.original_get = storage.get_file
        storage.get_file = self.get_file
        self.stop = Event()

    def path(self, owner):
        if not _OWNER.fullmatch(owner):
            raise ValueError('Identificador de sesión inválido.')
        path = self.root / owner
        if path.is_symlink() or path.resolve().parent != self.root.resolve():
            raise ValueError('La carpeta de sesión no es válida.')
        return path

    def _mark(self, owner):
        path = self.path(owner)
        path.mkdir(parents=True, exist_ok=True)
        temporary = path / '.privacy.tmp'
        temporary.write_text(json.dumps({'version': 1, 'expires_at': self.wall() + self.idle_seconds}))
        temporary.replace(path / '.privacy.json')

    def begin(self, owner, close=None):
        with self.lock:
            session = self.sessions.setdefault(owner, Session(self.clock() + self.idle_seconds, close))
            session.busy += 1
            session.expires = self.clock() + self.idle_seconds
            self._mark(owner)

    def end(self, owner):
        with self.lock:
            if owner in self.sessions:
                session = self.sessions[owner]
                session.busy = max(0, session.busy - 1)
                session.expires = self.clock() + self.idle_seconds
                self._mark(owner)

    def issue(self, owner, data, mime, salted_name, original_name):
        with self.lock:
            if owner not in self.sessions:
                raise ValueError('La sesión ya no está activa.')
            file_id = _calculate_file_id(data, mime, salted_name)
            deadline = self.clock() + self.download_seconds
            self.leases[file_id] = Lease(owner, deadline, original_name)
            return file_id, deadline

    def get_file(self, filename):
        file_id = Path(filename).stem
        with self.lock:
            lease = self.leases.get(file_id)
            session = self.sessions.get(lease.owner) if lease else None
            if lease and (self.clock() >= lease.deadline or session is None or
                          (not session.busy and self.clock() >= session.expires)):
                self.revoke(file_id)
                raise MediaFileStorageError('Enlace caducado.')
            media = self.original_get(filename)
            if media.kind == MediaFileKind.DOWNLOADABLE:
                if lease is None:
                    self.storage.delete_file(file_id)
                    raise MediaFileStorageError('Descarga sin vigencia registrada.')
                return media._replace(filename=lease.name)
            return media

    def revoke(self, file_id):
        with self.lock:
            self.leases.pop(file_id, None)
            self.storage.delete_file(file_id)

    def revoke_downloads(self, owner):
        with self.lock:
            for file_id, lease in list(self.leases.items()):
                if lease.owner == owner:
                    self.revoke(file_id)

    def purge(self, owner, *, close=False):
        with self.lock:
            self.revoke_downloads(owner)
            session = self.sessions.get(owner)
            callbacks = list(session.caches.values()) if session else []
            path = self.path(owner)
            if path.exists():
                shutil.rmtree(path)
        for callback in callbacks:
            callback()
        with self.lock:
            self.sessions.pop(owner, None)
        if close and session and session.close:
            session.close()

    def sweep(self):
        with self.lock:
            for file_id, lease in list(self.leases.items()):
                if self.clock() >= lease.deadline:
                    self.revoke(file_id)
            expired = [owner for owner, session in self.sessions.items()
                       if not session.busy and self.clock() >= session.expires]
            for owner, session in self.sessions.items():
                if session.busy:
                    self._mark(owner)
        for owner in expired:
            # Recheck under the same lock as begin: an action may have arrived.
            with self.lock:
                session = self.sessions.get(owner)
                if session and not session.busy and self.clock() >= session.expires:
                    self.purge(owner, close=True)
        if self.root.exists():
            for path in self.root.iterdir():
                if path.is_symlink():
                    continue
                with self.lock:
                    if path.name in self.sessions:
                        continue
                    if path.is_dir() and _OWNER.fullmatch(path.name):
                        marker = path / '.privacy.json'
                        expiry = path.stat().st_mtime + self.idle_seconds
                        if marker.exists():
                            try:
                                value = float(json.loads(marker.read_text())['expires_at'])
                                if math.isfinite(value):
                                    expiry = value
                            except (ValueError, KeyError, TypeError):
                                pass
                        if expiry <= self.wall():
                            shutil.rmtree(self.path(path.name))
                    elif path.is_file() and re.fullmatch(r'.+_[0-9a-f]{32}\.db', path.name):
                        if path.stat().st_mtime + self.idle_seconds <= self.wall():
                            path.unlink()

    def start_worker(self):
        def work():
            while not self.stop.wait(SWEEP_SECONDS):
                try:
                    self.sweep()
                except Exception:
                    logging.getLogger(__name__).warning('No se completó la limpieza temporal; se volverá a intentar.')
        Thread(target=work, name='explora-privacy', daemon=True).start()


def manager():
    if st.__version__ != '1.66.0':
        raise RuntimeError('Las descargas temporales requieren Streamlit 1.66.0. Actualiza las dependencias de EXPLORA.')
    instance = runtime.get_instance()
    storage = instance.media_file_mgr._storage
    if not isinstance(storage, MemoryMediaFileStorage):
        raise RuntimeError('Almacenamiento de descargas no compatible; descargas deshabilitadas.')
    with _INSTALL_LOCK:
        existing = getattr(storage, '_explora_privacy', None)
        if existing is None:
            existing = PrivacyManager(storage, DATA_DIR / 'sessions')
            storage._explora_privacy = existing
            if getattr(instance, '_async_objs', None) is not None:
                existing.start_worker()
        return existing


def owner_id():
    from src.utils.session_paths import session_root
    return session_root().name


@contextmanager
def privacy_run():
    if not runtime.exists():
        yield
        return
    try:
        guard = manager()
        with guard.lock:
            owner = st.session_state.get('explora_session_id')
            if owner and st.session_state.get('_privacy_started'):
                session = guard.sessions.get(owner)
                marker = guard.path(owner) / '.privacy.json'
                disk_expired = (not marker.exists() or
                                float(json.loads(marker.read_text())['expires_at']) <= guard.wall())
                if (session is None and disk_expired) or (session is not None and not session.busy and guard.clock() >= session.expires):
                    guard.purge(owner)
                    st.session_state.clear()
                    st.info('La sesión anterior caducó por inactividad. Recupera tu proyecto o vuelve a cargar los archivos.')
            owner = owner_id()
            ctx = get_script_run_ctx()
            instance = runtime.get_instance()
            framework_id = ctx.session_id
            with guard.lock:
                guard.framework_owners[framework_id] = owner
            def close():
                # Shutdown must run on Streamlit's event loop, not the sweeper thread.
                async_objects = instance._get_async_objs()
                def on_loop():
                    with guard.lock:
                        if guard.framework_owners.get(framework_id) != owner:
                            return
                        guard.framework_owners.pop(framework_id, None)
                    instance.close_session(framework_id)
                async_objects.eventloop.call_soon_threadsafe(on_loop)
            guard.begin(owner, close)
            st.session_state['_privacy_started'] = True
    except Exception:
        st.error('No se pudo activar la protección de archivos temporales. La aplicación no continuará sin ella.')
        st.stop()
    try:
        yield
    finally:
        guard.end(owner)


def clear_private_session():
    if runtime.exists():
        guard = manager()
        owner = st.session_state.get('explora_session_id')
        if owner:
            guard.purge(owner)
        ctx = get_script_run_ctx()
        if ctx:
            runtime.get_instance().uploaded_file_mgr.remove_session_files(ctx.session_id)
    st.session_state.clear()


def privacy_controls():
    st.caption('Descargas: hasta 5 minutos. Los archivos de la sesión se borran tras 30 minutos sin acciones. Descarga el proyecto para conservarlo.')
    if st.button('Renovar enlaces de descarga', key='privacy_renew'):
        manager().revoke_downloads(owner_id())
        st.session_state.pop('_download_leases', None)
        st.success('Enlaces renovados. Usa los botones de descarga actuales.')


def download_button(label, data, file_name=None, mime=None, **kwargs):
    guard, owner = manager(), owner_id()
    if owner not in guard.sessions:
        raise RuntimeError('La descarga requiere una sesión protegida.')
    cache = st.session_state.setdefault('_download_leases', {})
    key = str(kwargs.get('key') or label)
    if kwargs.get('disabled'):
        old = cache.pop(key, None)
        if old:
            guard.revoke(old[2])
        return st.button(label, disabled=True, key=kwargs.get('key'))
    mime = mime or ('text/plain' if isinstance(data, str) else 'application/octet-stream')
    content = data.encode() if isinstance(data, str) else bytes(data)
    name = file_name or 'Descarga_Explora'
    fingerprint = sha256(content).hexdigest() + mime + name
    old = cache.get(key)
    if old is None or old[0] != fingerprint or guard.clock() >= old[3] or old[2] not in guard.leases:
        if old:
            guard.revoke(old[2])
        path = Path(name)
        salted = f'{path.stem}_{secrets.token_urlsafe(24)}{path.suffix}'
        file_id, deadline = guard.issue(owner, content, mime, salted, name)
        old = (fingerprint, salted, file_id, deadline)
        cache[key] = old
    return st.download_button(label, content, file_name=old[1], mime=mime, **kwargs)


def private_cache_data(**options):
    def decorate(function):
        cached = st.cache_data(**options)(function)
        @wraps(function)
        def call(*args, **kwargs):
            if runtime.exists():
                guard = manager()
                owner = st.session_state.get('explora_session_id')
                with guard.lock:
                    if owner in guard.sessions:
                        key = (function.__module__, function.__name__, repr(args), repr(kwargs))
                        guard.sessions[owner].caches[key] = partial(cached.clear, *args, **kwargs)
            return cached(*args, **kwargs)
        call.clear = cached.clear
        return call
    return decorate
