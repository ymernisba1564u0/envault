"""Clone (duplicate) an existing encrypted profile under a new name."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from envault.profiles import profile_path, profile_exists, ensure_profile_dir
from envault.tag import _tag_file, _load_tags, _save_tags


@dataclass
class CloneError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def clone_profile(
    source: str,
    destination: str,
    *,
    base_dir: Path | None = None,
    copy_tags: bool = True,
) -> Path:
    """Duplicate *source* profile to *destination*.

    Parameters
    ----------
    source:
        Name of the existing profile to copy.
    destination:
        Name for the new profile.
    base_dir:
        Override the root directory (used in tests).
    copy_tags:
        When *True* (default) the source profile's tags are copied to the
        new profile.

    Returns
    -------
    Path
        Absolute path to the newly created ``.age`` file.

    Raises
    ------
    CloneError
        If *source* does not exist or *destination* already exists.
    """
    src_path = profile_path(source, base_dir=base_dir)
    dst_path = profile_path(destination, base_dir=base_dir)

    if not profile_exists(source, base_dir=base_dir):
        raise CloneError(f"Source profile '{source}' does not exist.")

    if profile_exists(destination, base_dir=base_dir):
        raise CloneError(f"Destination profile '{destination}' already exists.")

    ensure_profile_dir(base_dir=base_dir)
    shutil.copy2(src_path, dst_path)

    if copy_tags:
        src_tag_file = _tag_file(source, base_dir=base_dir)
        if src_tag_file.exists():
            tags = _load_tags(source, base_dir=base_dir)
            _save_tags(destination, tags, base_dir=base_dir)

    return dst_path
