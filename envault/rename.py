"""Rename a profile (encrypted .age file + associated metadata)."""

from pathlib import Path
from typing import Optional

from envault.profiles import profile_path, profile_exists, _profile_dir
from envault.tag import _tag_file, _load_tags, _save_tags
from envault.lock import _lock_sentinel
from envault.history import _profile_history_dir
import shutil


class RenameError(Exception):
    """Raised when a profile rename operation fails."""


def rename_profile(
    old_name: str,
    new_name: str,
    *,
    base_dir: Optional[Path] = None,
) -> Path:
    """Rename *old_name* profile to *new_name*.

    Moves the encrypted file and migrates any sidecar files
    (tags, lock sentinel, history directory) atomically where possible.

    Returns the path of the newly renamed profile file.
    Raises RenameError on any validation or filesystem failure.
    """
    old_path = profile_path(old_name, base_dir=base_dir)
    new_path = profile_path(new_name, base_dir=base_dir)

    if not profile_exists(old_name, base_dir=base_dir):
        raise RenameError(f"Profile '{old_name}' does not exist.")

    if profile_exists(new_name, base_dir=base_dir):
        raise RenameError(f"Profile '{new_name}' already exists.")

    if not new_name.strip():
        raise RenameError("New profile name must not be empty.")

    # Move the primary encrypted file.
    old_path.rename(new_path)

    # Migrate tag file if present.
    old_tag = _tag_file(old_name, base_dir=base_dir)
    new_tag = _tag_file(new_name, base_dir=base_dir)
    if old_tag.exists():
        old_tag.rename(new_tag)

    # Migrate lock sentinel if present.
    old_lock = _lock_sentinel(old_name, base_dir=base_dir)
    new_lock = _lock_sentinel(new_name, base_dir=base_dir)
    if old_lock.exists():
        old_lock.rename(new_lock)

    # Migrate history directory if present.
    old_hist = _profile_history_dir(old_name, base_dir=base_dir)
    new_hist = _profile_history_dir(new_name, base_dir=base_dir)
    if old_hist.exists():
        shutil.move(str(old_hist), str(new_hist))

    return new_path
