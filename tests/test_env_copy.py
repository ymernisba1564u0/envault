"""Tests for envault.env_copy — copy keys between profiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file
from envault.env_copy import CopyError, copy_keys
from envault.export import to_dotenv_lines, parse_env_bytes
from envault.crypto import decrypt_file
from envault.keystore import save_keypair, load_public_key, load_private_key
from envault.crypto import generate_keypair
from envault.profiles import profile_path, ensure_profile_dir


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    ensure_profile_dir(base_dir=tmp_path)
    return tmp_path


def _write_profile(name: str, vars_: dict, base: Path) -> Path:
    pub = load_public_key(base_dir=base)
    path = profile_path(name, base_dir=base)
    content = "\n".join(to_dotenv_lines(vars_)).encode()
    encrypt_file(content, path, pub)
    return path


def test_copy_keys_basic(base: Path) -> None:
    _write_profile("src", {"FOO": "bar", "BAZ": "qux"}, base)
    _write_profile("dst", {"EXISTING": "val"}, base)

    result = copy_keys("src", "dst", ["FOO"], base_dir=base)

    assert result.ok
    assert "FOO" in result.keys_copied
    assert result.keys_skipped == []

    priv = load_private_key(base_dir=base)
    dst_vars = parse_env_bytes(decrypt_file(profile_path("dst", base_dir=base), priv))
    assert dst_vars["FOO"] == "bar"
    assert dst_vars["EXISTING"] == "val"


def test_copy_multiple_keys(base: Path) -> None:
    _write_profile("src", {"A": "1", "B": "2", "C": "3"}, base)
    _write_profile("dst", {}, base)

    result = copy_keys("src", "dst", ["A", "C"], base_dir=base)

    assert sorted(result.keys_copied) == ["A", "C"]
    priv = load_private_key(base_dir=base)
    dst_vars = parse_env_bytes(decrypt_file(profile_path("dst", base_dir=base), priv))
    assert dst_vars == {"A": "1", "C": "3"}


def test_copy_skips_existing_without_overwrite(base: Path) -> None:
    _write_profile("src", {"KEY": "new_val"}, base)
    _write_profile("dst", {"KEY": "old_val"}, base)

    result = copy_keys("src", "dst", ["KEY"], base_dir=base)

    assert not result.ok
    assert "KEY" in result.keys_skipped

    priv = load_private_key(base_dir=base)
    dst_vars = parse_env_bytes(decrypt_file(profile_path("dst", base_dir=base), priv))
    assert dst_vars["KEY"] == "old_val"


def test_copy_overwrites_when_flag_set(base: Path) -> None:
    _write_profile("src", {"KEY": "new_val"}, base)
    _write_profile("dst", {"KEY": "old_val"}, base)

    result = copy_keys("src", "dst", ["KEY"], overwrite=True, base_dir=base)

    assert result.ok
    assert "KEY" in result.keys_copied

    priv = load_private_key(base_dir=base)
    dst_vars = parse_env_bytes(decrypt_file(profile_path("dst", base_dir=base), priv))
    assert dst_vars["KEY"] == "new_val"


def test_copy_raises_for_missing_source(base: Path) -> None:
    _write_profile("dst", {}, base)
    with pytest.raises(CopyError, match="Source profile"):
        copy_keys("nonexistent", "dst", ["X"], base_dir=base)


def test_copy_raises_for_missing_destination(base: Path) -> None:
    _write_profile("src", {"X": "1"}, base)
    with pytest.raises(CopyError, match="Destination profile"):
        copy_keys("src", "nonexistent", ["X"], base_dir=base)


def test_copy_raises_for_missing_key_in_source(base: Path) -> None:
    _write_profile("src", {"A": "1"}, base)
    _write_profile("dst", {}, base)
    with pytest.raises(CopyError, match="Key 'MISSING'"):
        copy_keys("src", "dst", ["MISSING"], base_dir=base)
