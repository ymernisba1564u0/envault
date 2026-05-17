"""Tests for envault.cli_filter CLI commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_filter import filter_cmd
from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair, load_public_key
from envault.profiles import profile_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, tmp_path)
    return tmp_path


def _make_profile(name: str, vars_: dict, base: Path) -> None:
    pub = load_public_key(base)
    path = profile_path(name, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{k}={v}" for k, v in vars_.items())
    encrypt_file(content.encode(), path, pub)


def test_show_filters_by_key(runner, isolated):
    _make_profile("prod", {"DB_HOST": "db.example.com", "PORT": "5432"}, isolated)
    result = runner.invoke(
        filter_cmd, ["show", "prod", "--key", "DB_*", "--base-dir", str(isolated)]
    )
    assert result.exit_code == 0
    assert "DB_HOST=db.example.com" in result.output
    assert "PORT" not in result.output


def test_show_no_matches_prints_message(runner, isolated):
    _make_profile("prod", {"PORT": "5432"}, isolated)
    result = runner.invoke(
        filter_cmd, ["show", "prod", "--key", "MISSING_*", "--base-dir", str(isolated)]
    )
    assert result.exit_code == 0
    assert "No matching" in result.output


def test_show_missing_profile_exits_one(runner, isolated):
    result = runner.invoke(
        filter_cmd, ["show", "ghost", "--key", "*", "--base-dir", str(isolated)]
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_extract_creates_new_profile(runner, isolated):
    _make_profile("staging", {"DB_URL": "postgres://", "APP_SECRET": "abc"}, isolated)
    result = runner.invoke(
        filter_cmd,
        ["extract", "staging", "db-only", "--key", "DB_*", "--base-dir", str(isolated)],
    )
    assert result.exit_code == 0
    assert "1 var(s)" in result.output
    dest = profile_path("db-only", isolated)
    assert dest.exists()


def test_extract_invert_flag(runner, isolated):
    _make_profile("staging", {"SECRET": "x", "HOST": "h", "PORT": "p"}, isolated)
    result = runner.invoke(
        filter_cmd,
        ["extract", "staging", "public", "--key", "SECRET*", "--invert", "--base-dir", str(isolated)],
    )
    assert result.exit_code == 0
    assert "2 var(s)" in result.output
