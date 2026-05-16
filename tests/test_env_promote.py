"""Tests for envault.env_promote."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.crypto import encrypt_data
from envault.export import parse_env_bytes
from envault.keystore import load_private_key, load_public_key, save_keypair
from envault.crypto import generate_keypair, decrypt_file
from envault.profiles import profile_path, ensure_profile_dir
from envault.env_promote import PromoteError, promote_profile
from envault.cli_promote import promote_cmd


@pytest.fixture()
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    return load_private_key(base_dir=base), load_public_key(base_dir=base)


def _write_profile(name: str, pairs: dict, base: Path) -> Path:
    pub = load_public_key(base_dir=base)
    lines = "\n".join(f"{k}={v}" for k, v in pairs.items()).encode()
    ct = encrypt_data(lines, pub)
    ensure_profile_dir(base_dir=base)
    p = profile_path(name, base_dir=base)
    p.write_bytes(ct)
    return p


def test_promote_copies_all_keys(base: Path) -> None:
    _write_profile("staging", {"DB": "stg", "SECRET": "abc"}, base)
    result = promote_profile("staging", "production", base_dir=base)
    assert result.ok
    assert set(result.promoted_keys) == {"DB", "SECRET"}
    assert result.skipped_keys == []


def test_promote_destination_file_is_decryptable(base: Path) -> None:
    _write_profile("staging", {"DB": "stg", "API": "key"}, base)
    promote_profile("staging", "production", base_dir=base)
    priv = load_private_key(base_dir=base)
    dst = profile_path("production", base_dir=base)
    plain = decrypt_file(dst, priv)
    pairs = parse_env_bytes(plain)
    assert pairs["DB"] == "stg"
    assert pairs["API"] == "key"


def test_promote_with_allow_list(base: Path) -> None:
    _write_profile("staging", {"DB": "stg", "SECRET": "abc", "DEBUG": "1"}, base)
    result = promote_profile("staging", "production", allow=["DB", "SECRET"], base_dir=base)
    assert set(result.promoted_keys) == {"DB", "SECRET"}
    assert "DEBUG" in result.skipped_keys


def test_promote_skipped_key_absent_in_destination(base: Path) -> None:
    _write_profile("staging", {"DB": "stg", "DEBUG": "1"}, base)
    promote_profile("staging", "production", allow=["DB"], base_dir=base)
    priv = load_private_key(base_dir=base)
    dst = profile_path("production", base_dir=base)
    pairs = parse_env_bytes(decrypt_file(dst, priv))
    assert "DEBUG" not in pairs


def test_promote_fails_for_missing_source(base: Path) -> None:
    with pytest.raises(PromoteError, match="does not exist"):
        promote_profile("ghost", "production", base_dir=base)


def test_promote_fails_if_destination_exists_without_overwrite(base: Path) -> None:
    _write_profile("staging", {"K": "v"}, base)
    _write_profile("production", {"K": "old"}, base)
    with pytest.raises(PromoteError, match="already exists"):
        promote_profile("staging", "production", base_dir=base)


def test_promote_overwrite_replaces_destination(base: Path) -> None:
    _write_profile("staging", {"K": "new"}, base)
    _write_profile("production", {"K": "old"}, base)
    result = promote_profile("staging", "production", overwrite=True, base_dir=base)
    assert result.ok
    priv = load_private_key(base_dir=base)
    dst = profile_path("production", base_dir=base)
    pairs = parse_env_bytes(decrypt_file(dst, priv))
    assert pairs["K"] == "new"


def test_cli_promote_run(base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_profile("staging", {"X": "1"}, base)
    monkeypatch.chdir(base)
    runner = CliRunner()
    result = runner.invoke(promote_cmd, ["run", "staging", "prod"])
    assert result.exit_code == 0
    assert "Promoted" in result.output


def test_cli_promote_missing_source_exits_one(base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(base)
    runner = CliRunner()
    result = runner.invoke(promote_cmd, ["run", "nope", "prod"])
    assert result.exit_code == 1
