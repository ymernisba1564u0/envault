"""Tests for envault.cli_compare."""

from __future__ import annotations

from pathlib import Path

import json
import pytest
from click.testing import CliRunner

from envault.cli_compare import compare_cmd
from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    return tmp_path, pub


def _make_profile(name: str, env: dict, base: Path, pub: str) -> None:
    ensure_profile_dir(base_dir=base)
    raw = "\n".join(f"{k}={v}" for k, v in env.items()).encode()
    encrypt_file(raw, profile_path(name, base_dir=base), pub)


def test_profiles_identical_exits_zero(runner, isolated):
    base, pub = isolated
    _make_profile("dev", {"KEY": "val"}, base, pub)
    _make_profile("staging", {"KEY": "val"}, base, pub)

    result = runner.invoke(compare_cmd, ["profiles", "dev", "staging"])

    assert result.exit_code == 0
    assert "identical" in result.output.lower()


def test_profiles_different_exits_one(runner, isolated):
    base, pub = isolated
    _make_profile("dev", {"KEY": "old"}, base, pub)
    _make_profile("staging", {"KEY": "new"}, base, pub)

    result = runner.invoke(compare_cmd, ["profiles", "dev", "staging"])

    assert result.exit_code == 1
    assert "Different values" in result.output


def test_profiles_json_output(runner, isolated):
    base, pub = isolated
    _make_profile("a", {"X": "1"}, base, pub)
    _make_profile("b", {"X": "1", "Y": "2"}, base, pub)

    result = runner.invoke(compare_cmd, ["profiles", "a", "b", "--json"])

    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["left"] == "a"
    assert data["right"] == "b"
    assert "Y" in data["only_in_right"]
    assert "coverage" in data


def test_missing_profile_shows_error(runner, isolated):
    base, pub = isolated
    _make_profile("real", {"K": "v"}, base, pub)

    result = runner.invoke(compare_cmd, ["profiles", "real", "ghost"])

    assert result.exit_code == 1
    assert "Error" in result.output
