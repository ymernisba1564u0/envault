"""Backup and restore encrypted profile bundles to/from a zip archive."""

from __future__ import annotations

import zipfile
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List

from envault.profiles import profile_path, list_profiles, _profile_dir


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""

    def __str__(self) -> str:  # pragma: no cover
        return self.args[0]


def _manifest(profiles: List[str]) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "profiles": profiles,
    }


def backup_profiles(
    dest: Path,
    base_dir: Path | None = None,
    profiles: List[str] | None = None,
) -> List[str]:
    """Write all (or selected) encrypted profiles into a zip archive at *dest*.

    Returns the list of profile names that were backed up.
    """
    available = list_profiles(base_dir)
    targets = profiles if profiles is not None else available

    missing = [p for p in targets if p not in available]
    if missing:
        raise BackupError(f"Profiles not found: {', '.join(missing)}")

    if not targets:
        raise BackupError("No profiles available to back up.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in targets:
            src = profile_path(name, base_dir)
            zf.write(src, arcname=f"{name}.age")
        zf.writestr("manifest.json", json.dumps(_manifest(targets), indent=2))

    return targets


def restore_profiles(
    src: Path,
    base_dir: Path | None = None,
    overwrite: bool = False,
) -> List[str]:
    """Extract encrypted profiles from a zip archive produced by :func:`backup_profiles`.

    Returns the list of profile names that were restored.
    """
    if not src.exists():
        raise BackupError(f"Backup file not found: {src}")

    profile_dir = _profile_dir(base_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        names = [n for n in zf.namelist() if n.endswith(".age")]
        if not names:
            raise BackupError("Archive contains no .age profile files.")

        restored: List[str] = []
        for entry in names:
            profile_name = Path(entry).stem
            dest = profile_dir / f"{profile_name}.age"
            if dest.exists() and not overwrite:
                raise BackupError(
                    f"Profile '{profile_name}' already exists. Use overwrite=True to replace."
                )
            dest.write_bytes(zf.read(entry))
            restored.append(profile_name)

    return sorted(restored)
