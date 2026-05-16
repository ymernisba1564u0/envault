"""Tests for envault.env_rename_key."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.crypto import encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import save_keypair, load_private_key, load_public_key
from envault.crypto import generate_keypair, decrypt_file
from envault.profiles import profile_path, ensure_profile_dir
from envault.env_rename_key import rename_key, RenameKeyError
from envault.cli_rename_key import rename_key_cmd


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)
    return priv, pub


def _write_profile(name: str, pairs: list[tuple[str, str]], base: Path) -> Path:
    pub = load_public_key(base_dir=base)
    ensure_profile_dir(base_dir=base)
    path = profile_path(name, base_dir=base)
    raw = "\n".join(to_dotenv_lines(pairs)).encode()
    encrypt_file(raw, path, pub)
    return path


def _read_profile(name: str, base: Path) -> dict[str, str]:
    priv = load_private_key(base_dir=base)
    path = profile_path(name, base_dir=base)
    raw = decrypt_file(path, priv)
    return dict(parse_env_bytes(raw))


def test_rename_key_basic(base: Path, setup_keys):
    _write_profile("dev", [("OLD", "hello"), ("OTHER", "world")], base)
    result = rename_key("dev", "OLD", "NEW", base_dir=base)
    assert result.ok
    assert result.old_key == "OLD"
    assert result.new_key == "NEW"
    assert result.value == "hello"


def test_rename_key_value_preserved(base: Path, setup_keys):
    _write_profile("dev", [("FOO", "bar")], base)
    rename_key("dev", "FOO", "BAZ", base_dir=base)
    env = _read_profile("dev", base)
    assert "BAZ" in env
    assert env["BAZ"] == "bar"
    assert "FOO" not in env


def test_rename_key_old_key_absent_raises(base: Path, setup_keys):
    _write_profile("dev", [("A", "1")], base)
    with pytest.raises(RenameKeyError, match="not found"):
        rename_key("dev", "MISSING", "B", base_dir=base)


def test_rename_key_new_key_exists_raises(base: Path, setup_keys):
    _write_profile("dev", [("OLD", "1"), ("NEW", "2")], base)
    with pytest.raises(RenameKeyError, match="already exists"):
        rename_key("dev", "OLD", "NEW", base_dir=base)


def test_rename_key_overwrite_replaces(base: Path, setup_keys):
    _write_profile("dev", [("OLD", "1"), ("NEW", "2")], base)
    rename_key("dev", "OLD", "NEW", overwrite=True, base_dir=base)
    env = _read_profile("dev", base)
    assert env["NEW"] == "1"
    assert "OLD" not in env
    assert len(env) == 1


def test_rename_key_missing_profile_raises(base: Path, setup_keys):
    with pytest.raises(RenameKeyError, match="does not exist"):
        rename_key("ghost", "A", "B", base_dir=base)


# --- CLI ---

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    return tmp_path


def _make_profile(name: str, pairs: list[tuple[str, str]], base: Path) -> None:
    _write_profile(name, pairs, base)


def test_cli_run_success(runner: CliRunner, isolated: Path):
    _make_profile("dev", [("FOO", "bar")], isolated)
    result = runner.invoke(
        rename_key_cmd,
        ["run", "dev", "FOO", "BAR"],
        env={"ENVAULT_BASE_DIR": str(isolated)},
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "BAR" in result.output


def test_cli_run_missing_key_exits_one(runner: CliRunner, isolated: Path):
    _make_profile("dev", [("A", "1")], isolated)
    result = runner.invoke(
        rename_key_cmd,
        ["run", "dev", "MISSING", "B"],
        env={"ENVAULT_BASE_DIR": str(isolated)},
    )
    assert result.exit_code == 1
    assert "Error" in result.output or "Error" in (result.output + result.stderr if hasattr(result, 'stderr') else result.output)
