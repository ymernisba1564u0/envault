"""Tests for envault.env_validate."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import profile_path, ensure_profile_dir
from envault.env_validate import (
    load_schema,
    validate_profile,
    validate_all,
    ValidationResult,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)
    return priv, pub


def _write_profile(name: str, content: str, base: Path, pub_key: str) -> Path:
    ensure_profile_dir(base_dir=base)
    path = profile_path(name, base_dir=base)
    encrypt_file(content.encode(), pub_key, path)
    return path


# ---------------------------------------------------------------------------
# load_schema
# ---------------------------------------------------------------------------

def test_load_schema_returns_keys(tmp_path: Path):
    schema = tmp_path / "schema.txt"
    schema.write_text("DB_URL\nSECRET_KEY\n# comment\n\nAPI_TOKEN\n")
    keys = load_schema(schema)
    assert keys == ["DB_URL", "SECRET_KEY", "API_TOKEN"]


def test_load_schema_ignores_blank_and_comments(tmp_path: Path):
    schema = tmp_path / "schema.txt"
    schema.write_text("# header\n\nONLY_KEY\n")
    keys = load_schema(schema)
    assert keys == ["ONLY_KEY"]


# ---------------------------------------------------------------------------
# validate_profile
# ---------------------------------------------------------------------------

def test_validate_profile_ok(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "DB_URL=postgres://localhost\nSECRET=abc\n", base, pub)
    result = validate_profile("prod", ["DB_URL", "SECRET"], base_dir=base)
    assert result.ok
    assert "OK" in str(result)


def test_validate_profile_missing_key(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "DB_URL=postgres://localhost\n", base, pub)
    result = validate_profile("prod", ["DB_URL", "SECRET"], base_dir=base)
    assert not result.ok
    assert len(result.issues) == 1
    assert result.issues[0].key == "SECRET"


def test_validate_profile_multiple_missing(base, setup_keys):
    _, pub = setup_keys
    _write_profile("staging", "ONLY=1\n", base, pub)
    result = validate_profile("staging", ["DB_URL", "SECRET", "API_KEY"], base_dir=base)
    missing = {i.key for i in result.issues}
    assert missing == {"DB_URL", "SECRET", "API_KEY"}


def test_validate_profile_missing_file(base, setup_keys):
    result = validate_profile("ghost", ["KEY"], base_dir=base)
    assert not result.ok
    assert result.issues[0].key == "<file>"


def test_validate_profile_str_shows_issues(base, setup_keys):
    _, pub = setup_keys
    _write_profile("dev", "A=1\n", base, pub)
    result = validate_profile("dev", ["A", "B"], base_dir=base)
    rendered = str(result)
    assert "B" in rendered
    assert "missing required key" in rendered


# ---------------------------------------------------------------------------
# validate_all
# ---------------------------------------------------------------------------

def test_validate_all_multiple_profiles(base, setup_keys):
    _, pub = setup_keys
    _write_profile("p1", "KEY=val\n", base, pub)
    _write_profile("p2", "OTHER=val\n", base, pub)
    results = validate_all(["KEY"], base_dir=base)
    names = {r.profile for r in results}
    assert names == {"p1", "p2"}
    ok_map = {r.profile: r.ok for r in results}
    assert ok_map["p1"] is True
    assert ok_map["p2"] is False


def test_validate_all_empty_when_no_profiles(base, setup_keys):
    results = validate_all(["KEY"], base_dir=base)
    assert results == []
