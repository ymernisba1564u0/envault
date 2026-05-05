"""Tests for the envault CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from envault.cli import cli
from envault.keystore import save_keypair
from envault.crypto import generate_keypair


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Run in isolated filesystem with keystore pointing to tmp_path."""
    monkeypatch.setattr("envault.keystore._key_dir", lambda: tmp_path / ".envault")
    monkeypatch.setattr("envault.cli.generate_keypair", generate_keypair)
    return tmp_path


def test_init_creates_keypair(runner, isolated):
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert "Public key:" in result.output


def test_init_fails_if_keypair_exists(runner, isolated):
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_init_force_overwrites(runner, isolated):
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, ["init", "--force"])
    assert result.exit_code == 0
    assert "Public key:" in result.output


def test_encrypt_decrypt_roundtrip(runner, isolated, tmp_path):
    runner.invoke(cli, ["init"])

    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=hunter2\nAPI_KEY=abc123\n")

    encrypted_file = tmp_path / ".env.age"
    result = runner.invoke(cli, ["encrypt", str(env_file), "-o", str(encrypted_file)])
    assert result.exit_code == 0
    assert encrypted_file.exists()

    decrypted_file = tmp_path / ".env.decrypted"
    result = runner.invoke(cli, ["decrypt", str(encrypted_file), "-o", str(decrypted_file)])
    assert result.exit_code == 0
    assert decrypted_file.read_text() == env_file.read_text()


def test_encrypt_default_output_name(runner, isolated, tmp_path):
    runner.invoke(cli, ["init"])
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    result = runner.invoke(cli, ["encrypt", str(env_file)])
    assert result.exit_code == 0
    assert (tmp_path / ".env.age").exists()


def test_encrypt_requires_init(runner, isolated, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    result = runner.invoke(cli, ["encrypt", str(env_file)])
    assert result.exit_code == 1
    assert "envault init" in result.output
