"""CLI tests for the watch command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch_cmd
from envault.crypto import generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    ensure_profile_dir(base_dir=tmp_path)
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    return tmp_path


def test_start_missing_file_shows_error(runner: CliRunner, isolated: Path) -> None:
    result = runner.invoke(watch_cmd, ["start", str(isolated / "nope.env"), "dev"])
    assert result.exit_code != 0


def test_start_encrypts_and_stops_via_keyboard_interrupt(
    runner: CliRunner, isolated: Path, tmp_path: Path
) -> None:
    """Simulate a single-iteration watch via monkeypatching."""
    import envault.cli_watch as cw

    env_file = isolated / ".env"
    env_file.write_text("CLI_KEY=hello\n")

    calls = []

    def _fake_watch(src, profile, interval, on_change, **_kw):
        on_change(profile)
        calls.append(profile)

    import unittest.mock as mock
    with mock.patch("envault.cli_watch.watch_file", side_effect=_fake_watch):
        result = runner.invoke(
            watch_cmd,
            ["start", str(env_file), "myprofile", "--interval", "0"],
        )

    assert result.exit_code == 0
    assert "myprofile" in result.output
    assert calls == ["myprofile"]


def test_start_keyboard_interrupt_exits_cleanly(
    runner: CliRunner, isolated: Path
) -> None:
    import unittest.mock as mock

    env_file = isolated / ".env"
    env_file.write_text("K=v\n")

    with mock.patch(
        "envault.cli_watch.watch_file", side_effect=KeyboardInterrupt
    ):
        result = runner.invoke(
            watch_cmd, ["start", str(env_file), "dev", "--interval", "1"]
        )

    assert result.exit_code == 0
    assert "Stopped" in result.output
