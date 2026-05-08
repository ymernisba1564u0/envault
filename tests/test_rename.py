"""Tests for envault.rename."""

import json
from pathlib import Path

import pytest

from envault.rename import rename_profile, RenameError
from envault.profiles import profile_path, profile_exists
from envault.tag import add_tag
from envault.lock import lock_profile
from envault.history import snapshot_profile
from envault.keystore import save_keypair
from envault.crypto import generate_keypair, encrypt_file


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)
    return priv, pub


def _write_profile(name: str, base: Path, pub: str) -> Path:
    src = base / "_src.env"
    src.write_text("KEY=value\nFOO=bar\n")
    out = profile_path(name, base_dir=base)
    out.parent.mkdir(parents=True, exist_ok=True)
    encrypt_file(src, out, pub)
    return out


def test_rename_moves_encrypted_file(base, setup_keys):
    _, pub = setup_keys
    _write_profile("alpha", base, pub)
    new_path = rename_profile("alpha", "beta", base_dir=base)
    assert new_path.exists()
    assert not profile_path("alpha", base_dir=base).exists()
    assert profile_exists("beta", base_dir=base)


def test_rename_fails_for_missing_profile(base):
    with pytest.raises(RenameError, match="does not exist"):
        rename_profile("ghost", "specter", base_dir=base)


def test_rename_fails_if_target_exists(base, setup_keys):
    _, pub = setup_keys
    _write_profile("alpha", base, pub)
    _write_profile("beta", base, pub)
    with pytest.raises(RenameError, match="already exists"):
        rename_profile("alpha", "beta", base_dir=base)


def test_rename_fails_for_empty_new_name(base, setup_keys):
    _, pub = setup_keys
    _write_profile("alpha", base, pub)
    with pytest.raises(RenameError, match="must not be empty"):
        rename_profile("alpha", "   ", base_dir=base)


def test_rename_migrates_tags(base, setup_keys):
    _, pub = setup_keys
    _write_profile("alpha", base, pub)
    add_tag("alpha", "production", base_dir=base)
    rename_profile("alpha", "beta", base_dir=base)
    from envault.tag import get_tags
    assert "production" in get_tags("beta", base_dir=base)
    assert get_tags("alpha", base_dir=base) == []


def test_rename_migrates_lock_sentinel(base, setup_keys):
    _, pub = setup_keys
    _write_profile("alpha", base, pub)
    lock_profile("alpha", base_dir=base)
    rename_profile("alpha", "beta", base_dir=base)
    from envault.lock import is_locked
    assert is_locked("beta", base_dir=base)
    assert not is_locked("alpha", base_dir=base)


def test_rename_migrates_history(base, setup_keys):
    priv, pub = setup_keys
    _write_profile("alpha", base, pub)
    snapshot_profile("alpha", pub, base_dir=base)
    rename_profile("alpha", "beta", base_dir=base)
    from envault.history import _profile_history_dir, list_snapshots
    assert not _profile_history_dir("alpha", base_dir=base).exists()
    snaps = list_snapshots("beta", base_dir=base)
    assert len(snaps) == 1
