"""Tests for envault.watch."""

import json
import time
from pathlib import Path

import pytest

from envault.crypto import generate_keypair, decrypt_file
from envault.keystore import save_keypair, load_public_key
from envault.profiles import ensure_profile_dir, profile_path
from envault.watch import watch_file, _file_hash
from envault.audit import read_events


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    ensure_profile_dir(base_dir=tmp_path)
    return tmp_path


def _env_file(tmp_path: Path, content: str = "KEY=value\n") -> Path:
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_file_hash_changes_on_content_change(tmp_path: Path) -> None:
    f = _env_file(tmp_path, "A=1\n")
    h1 = _file_hash(f)
    f.write_text("A=2\n")
    h2 = _file_hash(f)
    assert h1 != h2


def test_file_hash_stable_for_same_content(tmp_path: Path) -> None:
    f = _env_file(tmp_path, "STABLE=yes\n")
    assert _file_hash(f) == _file_hash(f)


def test_watch_raises_for_missing_file(base: Path) -> None:
    with pytest.raises(FileNotFoundError):
        watch_file(base / "nonexistent.env", "dev", base_dir=base, _stop_after=1)


def test_watch_encrypts_on_first_run(base: Path, tmp_path: Path) -> None:
    src = _env_file(tmp_path, "DB=postgres\n")
    dest = profile_path("prod", base_dir=base)

    watch_file(src, "prod", base_dir=base, interval=0, _stop_after=1)

    assert dest.exists()


def test_watch_decryptable_content(base: Path, tmp_path: Path) -> None:
    src = _env_file(tmp_path, "SECRET=abc123\n")
    out = tmp_path / "decrypted.env"

    watch_file(src, "ci", base_dir=base, interval=0, _stop_after=1)

    from envault.keystore import load_private_key
    priv = load_private_key(base_dir=base)
    dest = profile_path("ci", base_dir=base)
    decrypt_file(dest, out, priv)

    assert b"SECRET=abc123" in out.read_bytes()


def test_watch_calls_on_change_callback(base: Path, tmp_path: Path) -> None:
    src = _env_file(tmp_path, "X=1\n")
    called_with = []

    watch_file(
        src, "staging", base_dir=base, interval=0,
        on_change=lambda p: called_with.append(p), _stop_after=1,
    )

    assert called_with == ["staging"]


def test_watch_records_audit_event(base: Path, tmp_path: Path) -> None:
    src = _env_file(tmp_path, "AUDIT=yes\n")
    watch_file(src, "audit_prof", base_dir=base, interval=0, _stop_after=1)

    events = read_events(base_dir=base)
    assert any(e["event"] == "watch_reencrypt" for e in events)


def test_watch_no_double_encrypt_without_change(base: Path, tmp_path: Path) -> None:
    src = _env_file(tmp_path, "SAME=value\n")
    calls = []

    # Two iterations; content unchanged after first encrypt.
    watch_file(
        src, "stable", base_dir=base, interval=0,
        on_change=lambda p: calls.append(p), _stop_after=2,
    )

    # on_change should only fire once (first iteration detects new hash).
    assert len(calls) == 1
