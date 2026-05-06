"""Tests for envault.verify."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path
from envault.verify import VerifyResult, checksum_profile, verify_all, verify_profile


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    """Generate and save a keypair under *base*."""
    pub, priv = generate_keypair()
    key_dir = base / ".envault" / "keys"
    save_keypair(pub, priv, key_dir=key_dir)
    return pub, priv, key_dir


def _write_profile(base: Path, profile: str, content: bytes, pub_key: str) -> Path:
    ensure_profile_dir(base=base)
    path = profile_path(profile, base=base)
    encrypt_file(content, pub_key, path)
    return path


# ---------------------------------------------------------------------------
# verify_profile
# ---------------------------------------------------------------------------

def test_verify_profile_ok(base, setup_keys):
    pub, _priv, key_dir = setup_keys
    _write_profile(base, "production", b"DB_URL=postgres://localhost/db\n", pub)
    result = verify_profile("production", key_dir=key_dir)
    assert result.ok is True
    assert result.error is None
    assert result.profile == "production"


def test_verify_profile_missing_file(base, setup_keys):
    _pub, _priv, key_dir = setup_keys
    result = verify_profile("ghost", key_dir=key_dir)
    assert result.ok is False
    assert "does not exist" in (result.error or "")


def test_verify_profile_missing_key(base):
    key_dir = base / ".envault" / "keys"
    # Do NOT save any keys — key_dir is absent
    result = verify_profile("staging", key_dir=key_dir)
    assert result.ok is False
    assert result.error is not None


def test_verify_profile_returns_named_tuple(base, setup_keys):
    pub, _priv, key_dir = setup_keys
    _write_profile(base, "dev", b"KEY=value\n", pub)
    result = verify_profile("dev", key_dir=key_dir)
    assert isinstance(result, VerifyResult)


# ---------------------------------------------------------------------------
# verify_all
# ---------------------------------------------------------------------------

def test_verify_all_empty(base, setup_keys):
    _pub, _priv, key_dir = setup_keys
    results = verify_all(key_dir=key_dir)
    assert results == []


def test_verify_all_multiple_profiles(base, setup_keys):
    pub, _priv, key_dir = setup_keys
    for name in ("alpha", "beta", "gamma"):
        _write_profile(base, name, f"{name.upper()}_KEY=secret\n".encode(), pub)
    results = verify_all(key_dir=key_dir)
    assert len(results) == 3
    assert all(r.ok for r in results)


# ---------------------------------------------------------------------------
# checksum_profile
# ---------------------------------------------------------------------------

def test_checksum_returns_hex_string(base, setup_keys):
    pub, _priv, key_dir = setup_keys
    _write_profile(base, "ci", b"CI=true\n", pub)
    digest = checksum_profile("ci", key_dir=key_dir)
    assert isinstance(digest, str)
    assert len(digest) == 64  # SHA-256 hex


def test_checksum_changes_after_reencrypt(base, setup_keys):
    pub, _priv, key_dir = setup_keys
    _write_profile(base, "ci", b"CI=true\n", pub)
    first = checksum_profile("ci", key_dir=key_dir)
    # Re-encrypt (age uses random nonce, so ciphertext differs)
    _write_profile(base, "ci", b"CI=true\n", pub)
    second = checksum_profile("ci", key_dir=key_dir)
    assert first != second


def test_checksum_raises_for_missing_profile(base, setup_keys):
    _pub, _priv, key_dir = setup_keys
    with pytest.raises(FileNotFoundError):
        checksum_profile("nonexistent", key_dir=key_dir)
