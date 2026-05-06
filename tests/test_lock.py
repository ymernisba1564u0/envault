"""Tests for envault.lock."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from envault.lock import is_locked, lock_profile, unlock_profile, _lock_sentinel
from envault.profiles import profile_path, ensure_profile_dir


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def sample_profile(base: Path) -> str:
    ensure_profile_dir(base)
    p = profile_path("dev", base)
    p.write_bytes(b"encrypted-data")
    return "dev"


# ---------------------------------------------------------------------------
# is_locked
# ---------------------------------------------------------------------------

def test_is_locked_false_initially(base: Path, sample_profile: str) -> None:
    assert is_locked(sample_profile, base) is False


def test_is_locked_true_after_lock(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    assert is_locked(sample_profile, base) is True


# ---------------------------------------------------------------------------
# lock_profile
# ---------------------------------------------------------------------------

def test_lock_creates_sentinel(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    assert _lock_sentinel(sample_profile, base).exists()


def test_lock_makes_bundle_readonly(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    bundle = profile_path(sample_profile, base)
    mode = bundle.stat().st_mode
    assert not (mode & stat.S_IWUSR), "Bundle should not be user-writable after lock"


def test_lock_raises_if_already_locked(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    with pytest.raises(RuntimeError, match="already locked"):
        lock_profile(sample_profile, base)


def test_lock_raises_if_profile_missing(base: Path) -> None:
    ensure_profile_dir(base)
    with pytest.raises(FileNotFoundError):
        lock_profile("nonexistent", base)


# ---------------------------------------------------------------------------
# unlock_profile
# ---------------------------------------------------------------------------

def test_unlock_removes_sentinel(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    unlock_profile(sample_profile, base)
    assert not _lock_sentinel(sample_profile, base).exists()


def test_unlock_restores_write_permission(base: Path, sample_profile: str) -> None:
    lock_profile(sample_profile, base)
    unlock_profile(sample_profile, base)
    bundle = profile_path(sample_profile, base)
    mode = bundle.stat().st_mode
    assert mode & stat.S_IWUSR, "Bundle should be user-writable after unlock"


def test_unlock_raises_if_not_locked(base: Path, sample_profile: str) -> None:
    with pytest.raises(RuntimeError, match="not locked"):
        unlock_profile(sample_profile, base)


def test_unlock_raises_if_profile_missing(base: Path) -> None:
    ensure_profile_dir(base)
    with pytest.raises(FileNotFoundError):
        unlock_profile("nonexistent", base)
