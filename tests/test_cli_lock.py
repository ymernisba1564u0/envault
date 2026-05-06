"""Tests for envault.cli_lock CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_lock import lock_cmd
from envault.profiles import profile_path, ensure_profile_dir


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patch profile and log directories to tmp_path."""
    monkeypatch.setattr("envault.profiles._profile_dir", lambda base=None: tmp_path / "profiles")
    monkeypatch.setattr("envault.lock.profile_path", lambda name, base=None: tmp_path / "profiles" / f"{name}.age")
    monkeypatch.setattr("envault.lock.profile_exists", lambda name, base=None: (tmp_path / "profiles" / f"{name}.age").exists())
    monkeypatch.setattr("envault.audit.record_event", lambda *a, **kw: None)
    profiles = tmp_path / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    return tmp_path


def _make_profile(base: Path, name: str) -> Path:
    p = base / "profiles" / f"{name}.age"
    p.write_bytes(b"fake-encrypted")
    return p


def test_lock_on_success(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "prod")
    result = runner.invoke(lock_cmd, ["on", "prod"])
    assert result.exit_code == 0
    assert "locked" in result.output


def test_lock_on_fails_for_missing_profile(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(lock_cmd, ["on", "ghost"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_lock_on_fails_if_already_locked(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "staging")
    runner.invoke(lock_cmd, ["on", "staging"])
    result = runner.invoke(lock_cmd, ["on", "staging"])
    assert result.exit_code != 0
    assert "already locked" in result.output


def test_lock_off_success(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    runner.invoke(lock_cmd, ["on", "dev"])
    result = runner.invoke(lock_cmd, ["off", "dev"])
    assert result.exit_code == 0
    assert "unlocked" in result.output


def test_lock_off_fails_if_not_locked(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    result = runner.invoke(lock_cmd, ["off", "dev"])
    assert result.exit_code != 0
    assert "not locked" in result.output


def test_lock_status_locked(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "qa")
    runner.invoke(lock_cmd, ["on", "qa"])
    result = runner.invoke(lock_cmd, ["status", "qa"])
    assert result.exit_code == 0
    assert "locked" in result.output


def test_lock_status_unlocked(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "qa")
    result = runner.invoke(lock_cmd, ["status", "qa"])
    assert result.exit_code == 0
    assert "unlocked" in result.output
