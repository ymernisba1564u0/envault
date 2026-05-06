"""Profile version history: snapshot encrypted profiles with timestamps."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_HISTORY_DIR_NAME = "history"


def _history_dir(base: Optional[Path] = None) -> Path:
    root = base or Path.home() / ".envault"
    return root / _HISTORY_DIR_NAME


def _profile_history_dir(profile: str, base: Optional[Path] = None) -> Path:
    return _history_dir(base) / profile


def snapshot_profile(
    profile: str,
    encrypted_path: Path,
    base: Optional[Path] = None,
    note: str = "",
) -> Path:
    """Copy the current encrypted profile file into the history store.

    Returns the path of the newly created snapshot file.
    """
    if not encrypted_path.exists():
        raise FileNotFoundError(f"Profile file not found: {encrypted_path}")

    dest_dir = _profile_history_dir(profile, base)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_file = dest_dir / f"{ts}.age"
    shutil.copy2(encrypted_path, snapshot_file)

    meta_file = dest_dir / f"{ts}.json"
    meta = {"profile": profile, "timestamp": ts, "note": note}
    meta_file.write_text(json.dumps(meta, indent=2))

    return snapshot_file


def list_snapshots(profile: str, base: Optional[Path] = None) -> List[dict]:
    """Return a sorted list of snapshot metadata dicts (oldest first)."""
    dest_dir = _profile_history_dir(profile, base)
    if not dest_dir.exists():
        return []

    entries = []
    for meta_path in sorted(dest_dir.glob("*.json")):
        try:
            meta = json.loads(meta_path.read_text())
            meta["snapshot_file"] = str(meta_path.with_suffix(".age"))
            entries.append(meta)
        except (json.JSONDecodeError, OSError):
            continue
    return entries


def restore_snapshot(
    profile: str,
    timestamp: str,
    target_path: Path,
    base: Optional[Path] = None,
) -> None:
    """Overwrite *target_path* with the snapshot identified by *timestamp*."""
    dest_dir = _profile_history_dir(profile, base)
    snapshot_file = dest_dir / f"{timestamp}.age"
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_file}")
    shutil.copy2(snapshot_file, target_path)
