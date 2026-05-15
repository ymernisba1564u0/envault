"""CLI tests for the `envault ttl` command group."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_ttl import ttl_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect profile and TTL storage to a temp directory."""
    monkeypatch.setattr("envault.ttl._profile_dir", lambda: tmp_path)
    return tmp_path


def _make_profile(base: Path, name: str) -> None:
    (base / f"{name}.age").write_bytes(b"encrypted")


# ---------------------------------------------------------------------------
# ttl set
# ---------------------------------------------------------------------------

def test_set_success(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    result = runner.invoke(ttl_cmd, ["set", "dev", "300"])
    assert result.exit_code == 0
    assert "Expires at" in result.output
    assert "dev" in result.output


def test_set_fails_for_missing_profile(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(ttl_cmd, ["set", "ghost", "60"])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_set_fails_for_zero_seconds(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    result = runner.invoke(ttl_cmd, ["set", "dev", "0"])
    assert result.exit_code == 1
    assert "positive" in result.output


# ---------------------------------------------------------------------------
# ttl clear
# ---------------------------------------------------------------------------

def test_clear_with_existing_ttl(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    runner.invoke(ttl_cmd, ["set", "dev", "120"])
    result = runner.invoke(ttl_cmd, ["clear", "dev"])
    assert result.exit_code == 0
    assert "cleared" in result.output


def test_clear_with_no_ttl(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(ttl_cmd, ["clear", "dev"])
    assert result.exit_code == 0
    assert "No TTL" in result.output


# ---------------------------------------------------------------------------
# ttl status
# ---------------------------------------------------------------------------

def test_status_no_ttl(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(ttl_cmd, ["status", "dev"])
    assert result.exit_code == 0
    assert "No TTL" in result.output


def test_status_active_ttl(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "dev")
    runner.invoke(ttl_cmd, ["set", "dev", "9999"])
    result = runner.invoke(ttl_cmd, ["status", "dev"])
    assert result.exit_code == 0
    assert "active" in result.output


# ---------------------------------------------------------------------------
# ttl list
# ---------------------------------------------------------------------------

def test_list_empty(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(ttl_cmd, ["list"])
    assert result.exit_code == 0
    assert "No TTLs" in result.output


def test_list_shows_all_profiles(runner: CliRunner, isolated: Path) -> None:
    for name in ("alpha", "beta"):
        _make_profile(isolated, name)
        runner.invoke(ttl_cmd, ["set", name, "60"])
    result = runner.invoke(ttl_cmd, ["list"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
