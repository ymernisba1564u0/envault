"""Tests for envault.keystore key persistence helpers."""

from __future__ import annotations

import stat

import pytest

from envault.crypto import generate_keypair
from envault.keystore import (
    keypair_exists,
    load_private_key,
    load_public_key,
    save_keypair,
)


@pytest.fixture()
def key_dir(tmp_path):
    return tmp_path / "envault_keys"


@pytest.fixture()
def saved_keys(key_dir):
    private_key, public_key = generate_keypair()
    save_keypair(private_key, public_key, key_dir=key_dir)
    return private_key, public_key


def test_save_creates_directory(key_dir):
    private_key, public_key = generate_keypair()
    result = save_keypair(private_key, public_key, key_dir=key_dir)
    assert key_dir.exists()
    assert result == key_dir


def test_save_creates_both_files(key_dir, saved_keys):
    assert (key_dir / "identity.txt").exists()
    assert (key_dir / "recipient.txt").exists()


def test_identity_file_permissions(key_dir, saved_keys):
    identity_path = key_dir / "identity.txt"
    file_stat = identity_path.stat()
    mode = stat.S_IMODE(file_stat.st_mode)
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"


def test_load_private_key_roundtrip(key_dir, saved_keys):
    original_private, _ = saved_keys
    loaded = load_private_key(key_dir=key_dir)
    assert loaded == original_private


def test_load_public_key_roundtrip(key_dir, saved_keys):
    _, original_public = saved_keys
    loaded = load_public_key(key_dir=key_dir)
    assert loaded == original_public


def test_keypair_exists_true(key_dir, saved_keys):
    assert keypair_exists(key_dir=key_dir) is True


def test_keypair_exists_false(key_dir):
    assert keypair_exists(key_dir=key_dir) is False


def test_load_private_key_missing_raises(key_dir):
    with pytest.raises(FileNotFoundError, match="identity file"):
        load_private_key(key_dir=key_dir)


def test_load_public_key_missing_raises(key_dir):
    with pytest.raises(FileNotFoundError, match="recipient file"):
        load_public_key(key_dir=key_dir)
