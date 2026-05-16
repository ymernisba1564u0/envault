"""Tests for envault.env_snapshot_diff."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file
from envault.env_snapshot_diff import diff_snapshot
from envault.history import snapshot_profile
from envault.keystore import save_keypair
from envault.crypto import generate_keypair
from envault.profiles import ensure_profile_dir


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)
    return priv, pub


def _write_profile(base: Path, name: str, pub: str, content: str) -> Path:
    ensure_profile_dir(base_dir=base)
    from envault.profiles import profile_path
    path = profile_path(name, base_dir=base)
    encrypt_file(content.encode(), path, pub)
    return path


def test_diff_no_changes(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=value\nFOO=bar\n")
    meta = snapshot_profile("dev", base_dir=base)
    result = diff_snapshot("dev", meta["id"], base_dir=base)
    assert result.ok
    assert not result.added
    assert not result.removed
    assert not result.changed
    assert set(result.unchanged) == {"KEY", "FOO"}


def test_diff_detects_added_key(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=value\n")
    meta = snapshot_profile("dev", base_dir=base)
    # Add a new key to the current profile
    _write_profile(base, "dev", pub, "KEY=value\nNEW=added\n")
    result = diff_snapshot("dev", meta["id"], base_dir=base)
    assert not result.ok
    assert "NEW" in result.added
    assert result.added["NEW"] == "added"


def test_diff_detects_removed_key(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=value\nOLD=gone\n")
    meta = snapshot_profile("dev", base_dir=base)
    _write_profile(base, "dev", pub, "KEY=value\n")
    result = diff_snapshot("dev", meta["id"], base_dir=base)
    assert not result.ok
    assert "OLD" in result.removed
    assert result.removed["OLD"] == "gone"


def test_diff_detects_changed_value(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=original\n")
    meta = snapshot_profile("dev", base_dir=base)
    _write_profile(base, "dev", pub, "KEY=updated\n")
    result = diff_snapshot("dev", meta["id"], base_dir=base)
    assert not result.ok
    assert "KEY" in result.changed
    assert result.changed["KEY"] == ("original", "updated")


def test_diff_missing_profile_raises(base, setup_keys):
    with pytest.raises(FileNotFoundError, match="Profile"):
        diff_snapshot("nonexistent", "snap-001", base_dir=base)


def test_diff_missing_snapshot_raises(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=value\n")
    with pytest.raises(FileNotFoundError, match="Snapshot"):
        diff_snapshot("dev", "no-such-snap", base_dir=base)


def test_summary_contains_profile_and_snapshot(base, setup_keys):
    priv, pub = setup_keys
    _write_profile(base, "dev", pub, "KEY=value\n")
    meta = snapshot_profile("dev", base_dir=base)
    _write_profile(base, "dev", pub, "KEY=changed\n")
    result = diff_snapshot("dev", meta["id"], base_dir=base)
    summary = result.summary()
    assert "dev" in summary
    assert meta["id"] in summary
    assert "KEY" in summary
