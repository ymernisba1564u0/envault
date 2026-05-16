"""Tests for envault.cli_sort."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_sort import sort_cmd
from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    priv, pub = generate_keypair()
    save_keypair(priv, pub)
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    monkeypatch.setattr(
        "envault.env_sort.profile_path",
        lambda n, base_dir=None: profile_path(n, base_dir=base_dir or tmp_path),
    )
    monkeypatch.setattr(
        "envault.env_sort.profile_exists",
        lambda n, base_dir=None: profile_path(n, base_dir=base_dir or tmp_path).exists(),
    )
    return tmp_path, priv, pub


def _make_profile(name: str, content: str, base: Path, pub: str) -> None:
    ensure_profile_dir(base_dir=base)
    encrypt_file(content.encode(), profile_path(name, base_dir=base), pub)


def test_run_sorts_profile(runner: CliRunner, isolated):
    base, priv, pub = isolated
    _make_profile("prod", "ZETA=3\nALPHA=1\nBETA=2\n", base, pub)
    result = runner.invoke(sort_cmd, ["run", "prod"])
    assert result.exit_code == 0
    assert "sorted" in result.output.lower()


def test_run_already_sorted(runner: CliRunner, isolated):
    base, priv, pub = isolated
    _make_profile("prod", "ALPHA=1\nBETA=2\nZETA=3\n", base, pub)
    result = runner.invoke(sort_cmd, ["run", "prod"])
    assert result.exit_code == 0
    assert "already sorted" in result.output


def test_run_dry_run_shows_order(runner: CliRunner, isolated):
    base, priv, pub = isolated
    _make_profile("prod", "ZETA=3\nALPHA=1\n", base, pub)
    result = runner.invoke(sort_cmd, ["run", "prod", "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert "ALPHA" in result.output


def test_run_missing_profile_exits_one(runner: CliRunner, isolated):
    result = runner.invoke(sort_cmd, ["run", "ghost"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_run_reverse_flag(runner: CliRunner, isolated):
    base, priv, pub = isolated
    _make_profile("prod", "ALPHA=1\nBETA=2\nZETA=3\n", base, pub)
    result = runner.invoke(sort_cmd, ["run", "prod", "--reverse"])
    assert result.exit_code == 0
    assert "sorted" in result.output.lower()
