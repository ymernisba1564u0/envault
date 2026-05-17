"""Tests for envault.env_redact."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file, generate_keypair
from envault.env_redact import (
    REDACTED_PLACEHOLDER,
    RedactResult,
    _is_sensitive,
    redact_profile,
)
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path


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
    encrypt_file(content.encode(), path, pub_key)
    return path


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_detects_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_detects_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_detects_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_ignores_plain_key():
    assert _is_sensitive("APP_NAME") is False


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_Secret") is True


# ---------------------------------------------------------------------------
# redact_profile
# ---------------------------------------------------------------------------

def test_redact_masks_sensitive_values(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "APP_NAME=myapp\nDB_PASSWORD=supersecret\n", base, pub)
    result = redact_profile("prod", base_dir=base)
    assert result.pairs["APP_NAME"] == "myapp"
    assert result.pairs["DB_PASSWORD"] == REDACTED_PLACEHOLDER


def test_redact_result_lists_redacted_keys(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "GITHUB_TOKEN=abc123\nPORT=8080\n", base, pub)
    result = redact_profile("prod", base_dir=base)
    assert "GITHUB_TOKEN" in result.redacted_keys
    assert "PORT" not in result.redacted_keys


def test_redact_partial_shows_prefix(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "API_KEY=mysecretvalue\n", base, pub)
    result = redact_profile("prod", base_dir=base, partial=True)
    assert result.pairs["API_KEY"].startswith("myse")
    assert REDACTED_PLACEHOLDER in result.pairs["API_KEY"]


def test_redact_extra_keys_are_masked(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "CUSTOM_FIELD=hidden\nOTHER=visible\n", base, pub)
    result = redact_profile("prod", base_dir=base, extra_keys=["CUSTOM_FIELD"])
    assert result.pairs["CUSTOM_FIELD"] == REDACTED_PLACEHOLDER
    assert result.pairs["OTHER"] == "visible"


def test_redact_missing_profile_raises(base, setup_keys):
    with pytest.raises(FileNotFoundError, match="Profile not found"):
        redact_profile("nonexistent", base_dir=base)


def test_redact_result_render_output(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "APP=hello\nSECRET_KEY=xyz\n", base, pub)
    result = redact_profile("prod", base_dir=base)
    rendered = result.render()
    assert "APP=hello" in rendered
    assert f"SECRET_KEY={REDACTED_PLACEHOLDER}" in rendered


def test_redact_result_ok_is_true(base, setup_keys):
    _, pub = setup_keys
    _write_profile("prod", "X=1\n", base, pub)
    result = redact_profile("prod", base_dir=base)
    assert result.ok is True
