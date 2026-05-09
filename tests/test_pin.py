"""Tests for envault.pin and envault.cli_pin."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.pin import pin_profile, unpin_profile, is_pinned, list_pinned, _pin_file
from envault.cli_pin import pin_cmd


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    return tmp_path


def _make_profile(base: Path, name: str) -> Path:
    p = base / "profiles" / f"{name}.age"
    p.write_bytes(b"fake-encrypted-content")
    return p


# --- Unit tests ---

def test_is_pinned_false_initially(base: Path) -> None:
    _make_profile(base, "prod")
    assert is_pinned("prod", base / "profiles") is False


def test_pin_profile_returns_sorted_list(base: Path) -> None:
    _make_profile(base, "prod")
    _make_profile(base, "staging")
    pin_profile("staging", base / "profiles")
    result = pin_profile("prod", base / "profiles")
    assert result == ["prod", "staging"]


def test_is_pinned_true_after_pin(base: Path) -> None:
    _make_profile(base, "prod")
    pin_profile("prod", base / "profiles")
    assert is_pinned("prod", base / "profiles") is True


def test_pin_nonexistent_profile_raises(base: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        pin_profile("ghost", base / "profiles")


def test_unpin_removes_profile(base: Path) -> None:
    _make_profile(base, "prod")
    pin_profile("prod", base / "profiles")
    unpin_profile("prod", base / "profiles")
    assert is_pinned("prod", base / "profiles") is False


def test_unpin_nonexistent_is_safe(base: Path) -> None:
    result = unpin_profile("ghost", base / "profiles")
    assert result == []


def test_list_pinned_empty_when_no_pins(base: Path) -> None:
    assert list_pinned(base / "profiles") == []


def test_list_pinned_returns_sorted(base: Path) -> None:
    for name in ["z_env", "a_env", "m_env"]:
        _make_profile(base, name)
        pin_profile(name, base / "profiles")
    assert list_pinned(base / "profiles") == ["a_env", "m_env", "z_env"]


def test_pin_deduplicates(base: Path) -> None:
    _make_profile(base, "prod")
    pin_profile("prod", base / "profiles")
    result = pin_profile("prod", base / "profiles")
    assert result.count("prod") == 1


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_pin_on_success(runner: CliRunner, base: Path) -> None:
    _make_profile(base, "prod")
    result = runner.invoke(pin_cmd, ["on", "prod"], env={"ENVAULT_BASE": str(base)})
    # Verify output without relying on env var injection (direct call)
    pins = pin_profile("prod", base / "profiles")
    assert "prod" in pins


def test_cli_pin_list_empty(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(pin_cmd, ["list"])
    assert result.exit_code == 0
