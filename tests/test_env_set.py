"""Tests for envault.env_set (set_key, unset_key, get_key)."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.keystore import save_keypair
from envault.crypto import generate_keypair, encrypt_file
from envault.profiles import profile_path, ensure_profile_dir
from envault.env_set import set_key, unset_key, get_key, EnvSetError
from envault.cli_env_set import key_cmd


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture(autouse=True)
def setup_keys(base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVAULT_BASE", str(base))
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base=base)


def _write_profile(name: str, content: str, base: Path) -> Path:
    from envault.keystore import load_public_key
    ensure_profile_dir(base=base)
    path = profile_path(name, base=base)
    pub = load_public_key(base=base)
    encrypt_file(content.encode(), path, pub)
    return path


# ---------------------------------------------------------------------------
# set_key
# ---------------------------------------------------------------------------

def test_set_key_adds_new_key(base: Path) -> None:
    _write_profile("dev", "EXISTING=1\n", base)
    result = set_key("dev", "NEW_KEY", "hello", base=base)
    assert result.action == "set"
    assert result.previous is None
    assert result.current == "hello"
    assert get_key("dev", "NEW_KEY", base=base) == "hello"


def test_set_key_updates_existing(base: Path) -> None:
    _write_profile("dev", "FOO=old\n", base)
    result = set_key("dev", "FOO", "new", base=base)
    assert result.action == "set"
    assert result.previous == "old"
    assert get_key("dev", "FOO", base=base) == "new"


def test_set_key_unchanged_when_same_value(base: Path) -> None:
    _write_profile("dev", "FOO=same\n", base)
    result = set_key("dev", "FOO", "same", base=base)
    assert result.action == "unchanged"


def test_set_key_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(EnvSetError, match="Profile not found"):
        set_key("ghost", "K", "v", base=base)


def test_set_key_raises_for_invalid_key(base: Path) -> None:
    _write_profile("dev", "", base)
    with pytest.raises(EnvSetError, match="Invalid key"):
        set_key("dev", "bad-key!", "v", base=base)


# ---------------------------------------------------------------------------
# unset_key
# ---------------------------------------------------------------------------

def test_unset_key_removes_existing(base: Path) -> None:
    _write_profile("dev", "REMOVE_ME=yes\nKEEP=1\n", base)
    result = unset_key("dev", "REMOVE_ME", base=base)
    assert result.action == "unset"
    assert result.previous == "yes"
    assert get_key("dev", "REMOVE_ME", base=base) is None
    assert get_key("dev", "KEEP", base=base) == "1"


def test_unset_key_noop_for_absent_key(base: Path) -> None:
    _write_profile("dev", "FOO=1\n", base)
    result = unset_key("dev", "NOPE", base=base)
    assert result.action == "unchanged"


def test_unset_key_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(EnvSetError, match="Profile not found"):
        unset_key("ghost", "K", base=base)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_set_success(base: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile("dev", "A=1\n", base)
    monkeypatch.setenv("ENVAULT_BASE", str(base))
    result = runner.invoke(key_cmd, ["set", "dev", "B", "2"])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_cli_get_prints_value(base: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile("dev", "SECRET=abc\n", base)
    monkeypatch.setenv("ENVAULT_BASE", str(base))
    result = runner.invoke(key_cmd, ["get", "dev", "SECRET"])
    assert result.exit_code == 0
    assert "abc" in result.output


def test_cli_get_exits_one_for_missing_key(base: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile("dev", "A=1\n", base)
    monkeypatch.setenv("ENVAULT_BASE", str(base))
    result = runner.invoke(key_cmd, ["get", "dev", "MISSING"])
    assert result.exit_code != 0


def test_cli_unset_success(base: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile("dev", "DEL=me\n", base)
    monkeypatch.setenv("ENVAULT_BASE", str(base))
    result = runner.invoke(key_cmd, ["unset", "dev", "DEL"])
    assert result.exit_code == 0
    assert "Removed" in result.output
