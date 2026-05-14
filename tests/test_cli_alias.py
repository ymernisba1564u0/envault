"""Tests for envault.cli_alias."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_alias import alias_cmd
from envault.profiles import _profile_dir


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    """Patch profile dir and create dummy profiles."""
    profile_dir = _profile_dir(tmp_path)
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "production.age").write_bytes(b"fake")
    (profile_dir / "staging.age").write_bytes(b"fake")
    monkeypatch.chdir(tmp_path)
    # Patch _profile_dir used inside alias module
    import envault.alias as alias_mod
    import envault.profiles as profiles_mod
    monkeypatch.setattr(alias_mod, "_profile_dir", lambda base=None: profile_dir)
    monkeypatch.setattr(profiles_mod, "_profile_dir", lambda base=None: profile_dir)
    return tmp_path


def test_add_creates_alias(runner, isolated):
    result = runner.invoke(alias_cmd, ["add", "prod", "production"])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "production" in result.output


def test_add_fails_for_missing_profile(runner, isolated):
    result = runner.invoke(alias_cmd, ["add", "ghost", "nonexistent"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_add_duplicate_fails(runner, isolated):
    runner.invoke(alias_cmd, ["add", "prod", "production"])
    result = runner.invoke(alias_cmd, ["add", "prod", "staging"])
    assert result.exit_code == 1
    assert "already maps" in result.output


def test_remove_alias(runner, isolated):
    runner.invoke(alias_cmd, ["add", "prod", "production"])
    result = runner.invoke(alias_cmd, ["remove", "prod"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_missing_alias_fails(runner, isolated):
    result = runner.invoke(alias_cmd, ["remove", "nope"])
    assert result.exit_code == 1


def test_resolve_known_alias(runner, isolated):
    runner.invoke(alias_cmd, ["add", "prod", "production"])
    result = runner.invoke(alias_cmd, ["resolve", "prod"])
    assert result.exit_code == 0
    assert "production" in result.output


def test_resolve_unknown_returns_identity(runner, isolated):
    result = runner.invoke(alias_cmd, ["resolve", "staging"])
    assert result.exit_code == 0
    assert "staging" in result.output


def test_list_empty(runner, isolated):
    result = runner.invoke(alias_cmd, ["list"])
    assert result.exit_code == 0
    assert "No aliases" in result.output


def test_list_shows_entries(runner, isolated):
    runner.invoke(alias_cmd, ["add", "prod", "production"])
    runner.invoke(alias_cmd, ["add", "stage", "staging"])
    result = runner.invoke(alias_cmd, ["list"])
    assert "prod" in result.output
    assert "stage" in result.output
