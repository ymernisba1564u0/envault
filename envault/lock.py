"""Lock/unlock support for envault profiles.

A locked profile has its encrypted bundle marked read-only and a
.lock sentinel file placed alongside it so that accidental overwrites
are prevented without an explicit unlock step.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from envault.profiles import profile_path, profile_exists


def _lock_sentinel(profile: str, base_dir: Path | None = None) -> Path:
    """Return the path of the sentinel file for *profile*."""
    return profile_path(profile, base_dir).with_suffix(".lock")


def is_locked(profile: str, base_dir: Path | None = None) -> bool:
    """Return True when *profile* has an active lock."""
    return _lock_sentinel(profile, base_dir).exists()


def lock_profile(profile: str, base_dir: Path | None = None) -> None:
    """Lock *profile*.

    Creates a sentinel file and sets the encrypted bundle to read-only.
    Raises FileNotFoundError when the profile does not exist.
    Raises RuntimeError when the profile is already locked.
    """
    if not profile_exists(profile, base_dir):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    if is_locked(profile, base_dir):
        raise RuntimeError(f"Profile '{profile}' is already locked.")

    bundle = profile_path(profile, base_dir)
    # Make the bundle read-only
    current = bundle.stat().st_mode
    bundle.chmod(current & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))

    sentinel = _lock_sentinel(profile, base_dir)
    sentinel.touch()


def unlock_profile(profile: str, base_dir: Path | None = None) -> None:
    """Unlock *profile*.

    Removes the sentinel file and restores write permission on the bundle.
    Raises FileNotFoundError when the profile does not exist.
    Raises RuntimeError when the profile is not locked.
    """
    if not profile_exists(profile, base_dir):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    if not is_locked(profile, base_dir):
        raise RuntimeError(f"Profile '{profile}' is not locked.")

    sentinel = _lock_sentinel(profile, base_dir)
    sentinel.unlink()

    bundle = profile_path(profile, base_dir)
    current = bundle.stat().st_mode
    bundle.chmod(current | stat.S_IWUSR)
