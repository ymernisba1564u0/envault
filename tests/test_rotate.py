"""Tests for envault.rotate — key rotation logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import generate_keypair, encrypt_file
from envault.keystore import save_keypair, load_public_key, load_private_key
from envault.profiles import profile_path, ensure_profile_dir
from envault.rotate import rotate_keys


SAMPLE_ENV = b"DB_URL=postgres://localhost/db\nSECRET_KEY=hunter2\n"


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    """Isolated base directory with a keypair and two encrypted profiles."""
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base_dir=tmp_path)
    ensure_profile_dir(base_dir=tmp_path)

    for name in ("default", "staging"):
        path = profile_path(name, base_dir=tmp_path)
        encrypt_file(path, SAMPLE_ENV, pub)

    return tmp_path


def test_rotate_returns_new_keys(base: Path) -> None:
    old_pub = load_public_key(base)
    new_pub, new_priv = rotate_keys(base)

    assert new_pub != old_pub
    assert new_priv  # non-empty


def test_rotate_saves_new_keypair(base: Path) -> None:
    new_pub, _ = rotate_keys(base)
    assert load_public_key(base) == new_pub


def test_rotate_reencrypts_all_profiles(base: Path) -> None:
    from envault.crypto import decrypt_file

    new_pub, new_priv = rotate_keys(base)

    for name in ("default", "staging"):
        path = profile_path(name, base_dir=base)
        plaintext = decrypt_file(path, new_priv)
        assert plaintext == SAMPLE_ENV


def test_rotate_old_key_no_longer_decrypts(base: Path) -> None:
    from envault.crypto import decrypt_file

    old_priv = load_private_key(base)
    rotate_keys(base)

    path = profile_path("default", base_dir=base)
    with pytest.raises(Exception):
        decrypt_file(path, old_priv)


def test_rotate_no_profiles_succeeds(tmp_path: Path) -> None:
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base_dir=tmp_path)

    new_pub, new_priv = rotate_keys(tmp_path)
    assert new_pub != pub


def test_rotate_records_audit_event(base: Path) -> None:
    from envault.audit import read_events

    rotate_keys(base)
    events = read_events(base_dir=base)
    rotate_events = [e for e in events if e["event"] == "rotate"]
    assert len(rotate_events) == 1
    assert rotate_events[0]["detail"]["profile_count"] == 2
