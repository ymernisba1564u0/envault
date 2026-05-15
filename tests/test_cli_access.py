"""Tests for envault.cli_access CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_access import access_cmd
from envault.profiles import ensure_profile_dir


KEY_A = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq8lka"
KEY_B = "age1zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzrcz4"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    ensure_profile_dir(tmp_path)
    (tmp_path / ".envault" / "profiles" / "dev.age").write_bytes(b"dummy")
    # Patch _profile_dir so the CLI resolves paths relative to tmp_path.
    import envault.access as _access_mod
    import envault.profiles as _prof_mod
    monkeypatch.setattr(_prof_mod, "_profile_dir", lambda: tmp_path / ".envault" / "profiles")
    monkeypatch.setattr(_access_mod, "_profile_dir", lambda: tmp_path / ".envault" / "profiles")
    return tmp_path


def test_grant_success(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(access_cmd, ["grant", "dev", KEY_A])
    assert result.exit_code == 0
    assert KEY_A in result.output


def test_grant_fails_for_missing_profile(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(access_cmd, ["grant", "ghost", KEY_A])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_revoke_success(runner: CliRunner, isolated: Path) -> None:
    runner.invoke(access_cmd, ["grant", "dev", KEY_A])
    result = runner.invoke(access_cmd, ["revoke", "dev", KEY_A])
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_list_empty(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(access_cmd, ["list", "dev"])
    assert result.exit_code == 0
    assert "No access" in result.output


def test_list_shows_keys(runner: CliRunner, isolated: Path) -> None:
    runner.invoke(access_cmd, ["grant", "dev", KEY_A])
    runner.invoke(access_cmd, ["grant", "dev", KEY_B])
    result = runner.invoke(access_cmd, ["list", "dev"])
    assert result.exit_code == 0
    assert KEY_A in result.output
    assert KEY_B in result.output


def test_clear_removes_all(runner: CliRunner, isolated: Path) -> None:
    runner.invoke(access_cmd, ["grant", "dev", KEY_A])
    runner.invoke(access_cmd, ["clear", "dev"])
    result = runner.invoke(access_cmd, ["list", "dev"])
    assert "No access" in result.output
