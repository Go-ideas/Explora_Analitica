import json
import os
from pathlib import Path

import pytest
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
from streamlit.runtime.media_file_storage import MediaFileKind, MediaFileStorageError

from src.utils.privacy import PrivacyManager


A, B = 'a' * 32, 'b' * 32


@pytest.fixture
def privacy(tmp_path):
    now = [1000.0]
    storage = MemoryMediaFileStorage('/media')
    guard = PrivacyManager(storage, tmp_path / 'sessions', clock=lambda: now[0], wall=lambda: now[0],
                           download_seconds=5, idle_seconds=30)
    return guard, storage, now


def register(guard, storage, owner, name):
    guard.begin(owner)
    guard.end(owner)
    file_id, deadline = guard.issue(owner, b'synthetic', 'application/octet-stream', name, 'report.bin')
    assert storage.load_and_get_id(b'synthetic', 'application/octet-stream', MediaFileKind.DOWNLOADABLE, name) == file_id
    return file_id


def test_expiry_is_enforced_on_read_even_without_background_worker(privacy):
    guard, storage, now = privacy
    file_id = register(guard, storage, A, 'random-a.bin')
    assert storage.get_file(file_id).content == b'synthetic'
    assert storage.get_file(file_id).filename == 'report.bin'
    now[0] += 5
    with pytest.raises(MediaFileStorageError):
        storage.get_file(file_id + '.bin')


def test_identical_payloads_remain_independent_and_old_links_never_revive(privacy):
    guard, storage, now = privacy
    first = register(guard, storage, A, 'nonce-a.bin')
    second = register(guard, storage, B, 'nonce-b.bin')
    assert first != second
    guard.revoke_downloads(A)
    with pytest.raises(MediaFileStorageError):
        storage.get_file(first)
    assert storage.get_file(second).content == b'synthetic'
    storage.load_and_get_id(b'synthetic', 'application/octet-stream', MediaFileKind.DOWNLOADABLE, 'nonce-a.bin')
    with pytest.raises(MediaFileStorageError):
        storage.get_file(first)


def test_purge_deletes_only_owner_files_and_cache_entries(privacy):
    guard, storage, _ = privacy
    first = register(guard, storage, A, 'first.bin')
    second = register(guard, storage, B, 'second.bin')
    (guard.path(A) / 'source.sav').write_bytes(b'data')
    (guard.path(B) / 'source.sav').write_bytes(b'other')
    cleared = []
    guard.sessions[A].caches['a'] = lambda: cleared.append(A)
    guard.sessions[B].caches['b'] = lambda: cleared.append(B)
    guard.purge(A)
    assert not guard.path(A).exists() and guard.path(B).is_dir()
    assert cleared == [A]
    with pytest.raises(MediaFileStorageError):
        storage.get_file(first)
    assert storage.get_file(second).content


def test_idle_cleanup_closes_session_but_skips_running_work(privacy):
    guard, storage, now = privacy
    closed = []
    guard.begin(A, lambda: closed.append(A))
    (guard.path(A) / 'work.db').write_bytes(b'synthetic')
    now[0] += 100
    guard.sweep()
    assert guard.path(A).exists() and closed == []
    guard.end(A)
    now[0] += 30
    guard.sweep()
    assert not guard.path(A).exists() and closed == [A]


def test_startup_sweeps_expired_directories_without_touching_other_files(privacy, tmp_path):
    guard, _, now = privacy
    old = guard.path(A)
    old.mkdir(parents=True)
    (old / '.privacy.json').write_text(json.dumps({'version': 1, 'expires_at': now[0] - 1}))
    keep = guard.path(B)
    keep.mkdir()
    (keep / '.privacy.json').write_text(json.dumps({'version': 1, 'expires_at': now[0] + 100}))
    unrelated = guard.root / 'important.db'
    unrelated.write_bytes(b'keep')
    legacy = guard.root / ('old_' + 'c' * 32 + '.db')
    legacy.write_bytes(b'synthetic legacy data')
    os.utime(legacy, (now[0] - 60, now[0] - 60))
    guard.sweep()
    assert not old.exists() and keep.exists() and unrelated.read_bytes() == b'keep'
    assert not legacy.exists()


def test_symlink_and_path_escape_are_rejected(privacy, tmp_path):
    guard, _, _ = privacy
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'keep').write_text('keep')
    guard.root.mkdir()
    (guard.root / A).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        guard.purge(A)
    with pytest.raises(ValueError):
        guard.path('../outside')
    guard.sweep()
    assert (outside / 'keep').read_text() == 'keep'


def test_deletion_failure_retains_registration_for_retry(privacy, monkeypatch):
    guard, storage, _ = privacy
    file_id = register(guard, storage, A, 'nonce.bin')
    import src.utils.privacy as module
    original = module.shutil.rmtree
    def fail(path):
        raise PermissionError('synthetic failure')
    monkeypatch.setattr(module.shutil, 'rmtree', fail)
    with pytest.raises(PermissionError):
        guard.purge(A)
    assert A in guard.sessions
    with pytest.raises(MediaFileStorageError):
        storage.get_file(file_id)
    monkeypatch.setattr(module.shutil, 'rmtree', original)
    guard.purge(A)
    assert A not in guard.sessions and not guard.path(A).exists()


def test_unsupported_framework_cannot_silently_enable_downloads(monkeypatch):
    import src.utils.privacy as module
    monkeypatch.setattr(module.st, '__version__', 'unsupported')
    with pytest.raises(RuntimeError, match='requieren Streamlit'):
        module.manager()


def test_idle_deadline_rejects_download_before_next_sweep(privacy):
    guard, storage, now = privacy
    guard.download_seconds = 100
    file_id = register(guard, storage, A, 'long-lease.bin')
    now[0] += 30
    with pytest.raises(MediaFileStorageError):
        storage.get_file(file_id)
