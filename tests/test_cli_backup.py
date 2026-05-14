"""Tests for envault.cli_backup"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_backup import backup_cmd
from envault.crypto import generate_keypair, encrypt_file
from envault.keystore import save_keypair
from envault.profiles import profile_path


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base_dir=tmp_path)
    return tmp_path, pub


def _make_profile(name: str, base: Path, pub: str) -> Path:
    env_bytes = f"{name.upper()}_VAR=hello\n".encode()
    dest = profile_path(name, base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    encrypt_file(env_bytes, dest, pub)
    return dest


def test_create_success(runner, isolated):
    base, pub = isolated
    _make_profile("prod", base, pub)
    result = runner.invoke(backup_cmd, ["create", str(base / "out.zip")], env={"ENVAULT_BASE_DIR": str(base)})
    assert result.exit_code == 0
    assert "prod" in result.output
    assert (base / "out.zip").exists()


def test_create_selected_profiles(runner, isolated):
    base, pub = isolated
    _make_profile("prod", base, pub)
    _make_profile("dev", base, pub)
    out = str(base / "sel.zip")
    result = runner.invoke(
        backup_cmd,
        ["create", out, "--profile", "prod"],
        env={"ENVAULT_BASE_DIR": str(base)},
    )
    assert result.exit_code == 0
    with zipfile.ZipFile(out) as zf:
        assert "prod.age" in zf.namelist()
        assert "dev.age" not in zf.namelist()


def test_create_fails_for_missing_profile(runner, isolated):
    base, pub = isolated
    _make_profile("prod", base, pub)
    result = runner.invoke(
        backup_cmd,
        ["create", str(base / "out.zip"), "--profile", "ghost"],
        env={"ENVAULT_BASE_DIR": str(base)},
    )
    assert result.exit_code != 0
    assert "ghost" in result.output


def test_restore_success(runner, isolated):
    base, pub = isolated
    _make_profile("staging", base, pub)
    out = str(base / "bk.zip")
    runner.invoke(backup_cmd, ["create", out], env={"ENVAULT_BASE_DIR": str(base)})
    profile_path("staging", base).unlink()

    result = runner.invoke(backup_cmd, ["restore", out], env={"ENVAULT_BASE_DIR": str(base)})
    assert result.exit_code == 0
    assert "staging" in result.output
    assert profile_path("staging", base).exists()


def test_restore_fails_without_overwrite(runner, isolated):
    base, pub = isolated
    _make_profile("prod", base, pub)
    out = str(base / "bk.zip")
    runner.invoke(backup_cmd, ["create", out], env={"ENVAULT_BASE_DIR": str(base)})

    result = runner.invoke(backup_cmd, ["restore", out], env={"ENVAULT_BASE_DIR": str(base)})
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_restore_succeeds_with_overwrite(runner, isolated):
    base, pub = isolated
    _make_profile("prod", base, pub)
    out = str(base / "bk.zip")
    runner.invoke(backup_cmd, ["create", out], env={"ENVAULT_BASE_DIR": str(base)})

    result = runner.invoke(backup_cmd, ["restore", out, "--overwrite"], env={"ENVAULT_BASE_DIR": str(base)})
    assert result.exit_code == 0
