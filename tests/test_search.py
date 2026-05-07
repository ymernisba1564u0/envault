"""Tests for envault.search."""

from __future__ import annotations

import pytest

from envault.crypto import encrypt_file
from envault.export import to_dotenv_lines
from envault.keystore import save_keypair
from envault.crypto import generate_keypair
from envault.profiles import ensure_profile_dir, profile_path
from envault.search import search_profiles, SearchMatch


@pytest.fixture()
def base(tmp_path):
    return tmp_path


@pytest.fixture()
def setup_keys(base):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=str(base))
    return priv, pub


def _write_profile(name: str, pairs: dict, base, pub_key: str):
    ensure_profile_dir(base_dir=str(base))
    content = "\n".join(f"{k}={v}" for k, v in pairs.items()).encode()
    path = profile_path(name, base_dir=str(base))
    encrypt_file(content, path, pub_key)


def test_search_finds_key_match(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("prod", {"DATABASE_URL": "postgres://localhost", "SECRET": "abc"}, base, pub)
    result = search_profiles("DATABASE", base_dir=str(base))
    assert result.ok
    assert any(m.key == "DATABASE_URL" for m in result.matches)


def test_search_finds_value_match(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("prod", {"DB": "postgres://myhost", "OTHER": "nope"}, base, pub)
    result = search_profiles("myhost", base_dir=str(base))
    assert result.ok
    assert any(m.key == "DB" for m in result.matches)


def test_search_keys_only_ignores_values(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("prod", {"DB": "myhost_value", "MYHOST_KEY": "something"}, base, pub)
    result = search_profiles("myhost", keys_only=True, base_dir=str(base))
    assert result.ok
    keys_found = [m.key for m in result.matches]
    assert "MYHOST_KEY" in keys_found
    assert "DB" not in keys_found


def test_search_case_insensitive(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("dev", {"Api_Token": "xyz"}, base, pub)
    result = search_profiles("api_token", base_dir=str(base))
    assert any(m.key == "Api_Token" for m in result.matches)


def test_search_profile_filter(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("dev", {"SHARED": "dev-val"}, base, pub)
    _write_profile("prod", {"SHARED": "prod-val"}, base, pub)
    result = search_profiles("SHARED", profile_filter="dev", base_dir=str(base))
    assert result.ok
    assert all(m.profile == "dev" for m in result.matches)
    assert len(result.matches) == 1


def test_search_no_keypair_returns_error(base):
    result = search_profiles("anything", base_dir=str(base))
    assert not result.ok
    assert any("init" in e for e in result.errors)


def test_search_missing_profile_records_error(base, setup_keys):
    result = search_profiles("x", profile_filter="ghost", base_dir=str(base))
    assert any("ghost" in e for e in result.errors)


def test_search_match_str(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("staging", {"FOO": "bar"}, base, pub)
    result = search_profiles("FOO", base_dir=str(base))
    assert result.matches
    assert str(result.matches[0]) == "[staging] FOO=bar"
