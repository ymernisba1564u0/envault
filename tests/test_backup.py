"""Tests for envault.backup"""

from __future__ import annotations

import zipfile
import json
from pathlib import Path

import pytest

from envault.backup import backup_profiles, restore_profiles, BackupError
from envault.crypto import generate_keypair, encrypt_file
from envault.keystore import save_keypair
from envault.profiles import profile_path, _profile_dir


@pytest.fixture()
def base(tmp_path: Path):
    return tmp_path


@pytest.fixture()
def setup_keys(base):
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base_dir=base)
    return pub, priv


def _write_profile(name: str, base: Path, pub: str) -> Path:
    env_bytes = f"KEY_{name.upper()}=value\n".encode()
    dest = profile_path(name, base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    encrypt_file(env_bytes, dest, pub)
    return dest


def test_backup_creates_zip(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    out = base / "backup.zip"
    names = backup_profiles(out, base_dir=base)
    assert out.exists()
    assert names == ["prod"]


def test_backup_zip_contains_age_and_manifest(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    _write_profile("staging", base, pub)
    out = base / "backup.zip"
    backup_profiles(out, base_dir=base)
    with zipfile.ZipFile(out) as zf:
        entries = zf.namelist()
    assert "prod.age" in entries
    assert "staging.age" in entries
    assert "manifest.json" in entries


def test_backup_manifest_lists_profiles(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("dev", base, pub)
    out = base / "backup.zip"
    backup_profiles(out, base_dir=base)
    with zipfile.ZipFile(out) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert "dev" in manifest["profiles"]
    assert "created_at" in manifest


def test_backup_selected_profiles_only(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    _write_profile("dev", base, pub)
    out = base / "backup.zip"
    names = backup_profiles(out, base_dir=base, profiles=["prod"])
    assert names == ["prod"]
    with zipfile.ZipFile(out) as zf:
        assert "prod.age" in zf.namelist()
        assert "dev.age" not in zf.namelist()


def test_backup_raises_for_missing_profile(base, setup_keys):
    pub, _ = setup_keys
    out = base / "backup.zip"
    with pytest.raises(BackupError, match="ghost"):
        backup_profiles(out, base_dir=base, profiles=["ghost"])


def test_backup_raises_when_no_profiles(base):
    out = base / "backup.zip"
    with pytest.raises(BackupError, match="No profiles"):
        backup_profiles(out, base_dir=base)


def test_restore_recreates_profiles(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    out = base / "backup.zip"
    backup_profiles(out, base_dir=base)

    # Remove original
    profile_path("prod", base).unlink()

    restored = restore_profiles(out, base_dir=base)
    assert "prod" in restored
    assert profile_path("prod", base).exists()


def test_restore_raises_if_overwrite_false(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    out = base / "backup.zip"
    backup_profiles(out, base_dir=base)

    with pytest.raises(BackupError, match="already exists"):
        restore_profiles(out, base_dir=base, overwrite=False)


def test_restore_overwrites_when_flag_set(base, setup_keys):
    pub, _ = setup_keys
    _write_profile("prod", base, pub)
    out = base / "backup.zip"
    backup_profiles(out, base_dir=base)

    restored = restore_profiles(out, base_dir=base, overwrite=True)
    assert "prod" in restored


def test_restore_raises_for_missing_archive(base):
    with pytest.raises(BackupError, match="not found"):
        restore_profiles(base / "nonexistent.zip", base_dir=base)
