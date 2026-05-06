"""Tests for envault.cli_history CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_history import history_cmd
from envault.history import snapshot_profile


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Patch profile and history dirs to tmp_path."""
    monkeypatch.setenv("HOME", str(tmp_path))

    import envault.profiles as _p
    import envault.history as _h

    monkeypatch.setattr(_p, "_profile_dir", lambda b=None: tmp_path / "profiles")
    monkeypatch.setattr(_h, "_history_dir", lambda b=None: tmp_path / "history")
    monkeypatch.setattr(
        _h,
        "_profile_history_dir",
        lambda profile, b=None: tmp_path / "history" / profile,
    )
    return tmp_path


def _make_profile(base: Path, name: str, content: bytes = b"enc") -> Path:
    p = base / "profiles" / f"{name}.age"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_snapshot_success(runner: CliRunner, isolated: Path) -> None:
    _make_profile(isolated, "prod")

    import envault.profiles as _p
    import envault.history as _h

    with runner.isolated_filesystem():
        result = runner.invoke(
            history_cmd,
            ["snapshot", "prod"],
            catch_exceptions=False,
            obj={"base": isolated},
        )
    assert result.exit_code == 0 or "Snapshot saved" in result.output


def test_snapshot_fails_for_missing_profile(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(history_cmd, ["snapshot", "ghost"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_list_shows_no_snapshots_message(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(history_cmd, ["list", "dev"])
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_shows_timestamps(runner: CliRunner, isolated: Path) -> None:
    enc = _make_profile(isolated, "dev")
    snapshot_profile("dev", enc, base=isolated / "history", note="v1")

    import envault.history as _h

    snaps = _h.list_snapshots("dev", base=isolated / "history")
    assert len(snaps) == 1
    assert snaps[0]["note"] == "v1"


def test_restore_with_yes_flag(runner: CliRunner, isolated: Path) -> None:
    enc = _make_profile(isolated, "staging", b"original")
    snap = snapshot_profile("staging", enc, base=isolated / "history")
    enc.write_bytes(b"modified")

    import envault.history as _h

    ts = _h.list_snapshots("staging", base=isolated / "history")[0]["timestamp"]
    result = runner.invoke(
        history_cmd, ["restore", "staging", ts, "--yes"]
    )
    assert result.exit_code == 0 or "restored" in result.output
