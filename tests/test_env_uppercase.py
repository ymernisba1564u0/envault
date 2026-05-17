"""Tests for envault.env_uppercase."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file
from envault.env_uppercase import UppercaseError, uppercase_profile
from envault.export import parse_env_bytes
from envault.crypto import decrypt_file
from envault.keystore import load_private_key, load_public_key, save_keypair
from envault.crypto import generate_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)


def _write_profile(name: str, content: str, base: Path) -> Path:
    ensure_profile_dir(base_dir=base)
    pub = load_public_key(base_dir=base)
    path = profile_path(name, base_dir=base)
    encrypt_file(content.encode(), path, pub)
    return path


def _read_profile(name: str, base: Path) -> list[tuple[str, str]]:
    priv = load_private_key(base_dir=base)
    path = profile_path(name, base_dir=base)
    raw = decrypt_file(path, priv)
    return parse_env_bytes(raw)


def test_uppercase_already_upper(base: Path, setup_keys):
    _write_profile("prod", "HOST=localhost\nPORT=5432\n", base)
    result = uppercase_profile("prod", base_dir=base)
    assert result.ok
    assert result.renamed == []
    assert result.skipped == []


def test_uppercase_renames_lowercase_keys(base: Path, setup_keys):
    _write_profile("prod", "host=localhost\nport=5432\n", base)
    result = uppercase_profile("prod", base_dir=base)
    assert len(result.renamed) == 2
    assert ("host", "HOST") in result.renamed
    assert ("port", "PORT") in result.renamed


def test_uppercase_content_is_reencrypted(base: Path, setup_keys):
    _write_profile("dev", "db_host=127.0.0.1\ndb_pass=secret\n", base)
    uppercase_profile("dev", base_dir=base)
    pairs = dict(_read_profile("dev", base))
    assert "DB_HOST" in pairs
    assert "DB_PASS" in pairs
    assert "db_host" not in pairs


def test_uppercase_skips_collision(base: Path, setup_keys):
    # 'host' would become 'HOST', but 'HOST' already exists
    _write_profile("staging", "HOST=existing\nhost=collision\n", base)
    result = uppercase_profile("staging", base_dir=base)
    assert "host" in result.skipped
    # The original uppercase key value should survive
    pairs = dict(_read_profile("staging", base))
    assert pairs.get("HOST") == "existing"


def test_uppercase_missing_profile_raises(base: Path, setup_keys):
    with pytest.raises(UppercaseError, match="does not exist"):
        uppercase_profile("ghost", base_dir=base)


def test_uppercase_str_no_changes(base: Path, setup_keys):
    _write_profile("ci", "KEY=val\n", base)
    result = uppercase_profile("ci", base_dir=base)
    assert "already uppercase" in str(result)


def test_uppercase_str_with_changes(base: Path, setup_keys):
    _write_profile("ci", "key=val\n", base)
    result = uppercase_profile("ci", base_dir=base)
    assert "1 key(s) renamed" in str(result)
    assert "key -> KEY" in str(result)
