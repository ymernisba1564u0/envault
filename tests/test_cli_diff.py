"""Integration tests for the diff CLI commands."""
import os
import pytest
from click.testing import CliRunner

from envault.cli_diff import diff_cmd
from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import profile_path, ensure_profile_dir


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    pub, priv = generate_keypair()
    save_keypair(pub, priv)
    ensure_profile_dir()
    return tmp_path, pub


def _make_profile(name: str, content: bytes, pub: str):
    path = profile_path(name)
    encrypt_file(content, pub, path)


def test_diff_profiles_no_changes(runner, isolated):
    _, pub = isolated
    _make_profile("a", b"FOO=bar\n", pub)
    _make_profile("b", b"FOO=bar\n", pub)
    result = runner.invoke(diff_cmd, ["profiles", "a", "b"])
    assert result.exit_code == 0
    assert "(no changes)" in result.output


def test_diff_profiles_with_changes(runner, isolated):
    _, pub = isolated
    _make_profile("a", b"FOO=bar\n", pub)
    _make_profile("b", b"FOO=changed\nNEW=val\n", pub)
    result = runner.invoke(diff_cmd, ["profiles", "a", "b"])
    assert result.exit_code == 1


def test_diff_profiles_missing_profile(runner, isolated):
    _, pub = isolated
    _make_profile("a", b"FOO=bar\n", pub)
    result = runner.invoke(diff_cmd, ["profiles", "a", "ghost"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_diff_file_no_changes(runner, isolated, tmp_path):
    _, pub = isolated
    _make_profile("a", b"FOO=bar\n", pub)
    plain = tmp_path / "plain.env"
    plain.write_bytes(b"FOO=bar\n")
    result = runner.invoke(diff_cmd, ["file", "a", str(plain)])
    assert result.exit_code == 0
    assert "(no changes)" in result.output


def test_diff_file_with_changes(runner, isolated, tmp_path):
    _, pub = isolated
    _make_profile("a", b"FOO=bar\n", pub)
    plain = tmp_path / "plain.env"
    plain.write_bytes(b"FOO=different\n")
    result = runner.invoke(diff_cmd, ["file", "a", str(plain)])
    assert result.exit_code == 1
