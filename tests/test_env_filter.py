"""Tests for envault.env_filter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file
from envault.env_filter import FilterError, filter_profile, write_filtered
from envault.export import parse_env_bytes
from envault.crypto import decrypt_file
from envault.keystore import save_keypair, load_private_key, load_public_key
from envault.crypto import generate_keypair
from envault.profiles import profile_path


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base)
    return priv, pub


def _write_profile(name: str, vars_: dict, base: Path) -> None:
    pub = load_public_key(base)
    path = profile_path(name, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{k}={v}" for k, v in vars_.items())
    encrypt_file(content.encode(), path, pub)


def test_filter_by_key_pattern(base, setup_keys):
    _write_profile("dev", {"DB_HOST": "localhost", "APP_PORT": "8080", "DB_PASS": "s3cr3t"}, base)
    result = filter_profile("dev", base, key_pattern="DB_*")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PASS"}
    assert "APP_PORT" in result.excluded


def test_filter_by_value_pattern(base, setup_keys):
    _write_profile("dev", {"URL": "https://example.com", "TOKEN": "abc123", "HOST": "localhost"}, base)
    result = filter_profile("dev", base, value_pattern=r"https?://")
    assert list(result.matched.keys()) == ["URL"]


def test_filter_combined_patterns(base, setup_keys):
    _write_profile("dev", {"DB_URL": "postgres://db", "DB_PASS": "secret", "APP_URL": "http://app"}, base)
    result = filter_profile("dev", base, key_pattern="DB_*", value_pattern=r"postgres")
    assert list(result.matched.keys()) == ["DB_URL"]


def test_filter_invert(base, setup_keys):
    _write_profile("dev", {"SECRET_KEY": "abc", "PORT": "3000", "SECRET_TOKEN": "xyz"}, base)
    result = filter_profile("dev", base, key_pattern="SECRET_*", invert=True)
    assert list(result.matched.keys()) == ["PORT"]
    assert set(result.excluded.keys()) == {"SECRET_KEY", "SECRET_TOKEN"}


def test_filter_no_matches_returns_empty(base, setup_keys):
    _write_profile("dev", {"PORT": "3000"}, base)
    result = filter_profile("dev", base, key_pattern="MISSING_*")
    assert result.matched == {}
    assert result.ok is True


def test_filter_missing_profile_raises(base, setup_keys):
    with pytest.raises(FilterError, match="not found"):
        filter_profile("ghost", base, key_pattern="*")


def test_filter_no_pattern_raises(base, setup_keys):
    _write_profile("dev", {"X": "1"}, base)
    with pytest.raises(FilterError, match="At least one"):
        filter_profile("dev", base)


def test_write_filtered_creates_profile(base, setup_keys):
    _write_profile("dev", {"DB_HOST": "localhost", "APP_PORT": "8080"}, base)
    result = filter_profile("dev", base, key_pattern="DB_*")
    out = write_filtered("dev", base, result, "db-only")
    assert out.exists()
    priv = load_private_key(base)
    raw = decrypt_file(out, priv)
    pairs = dict(parse_env_bytes(raw))
    assert pairs == {"DB_HOST": "localhost"}
