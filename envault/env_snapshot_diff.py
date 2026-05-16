"""Compare a profile's current state against a historical snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import decrypt_file
from envault.export import parse_env_bytes
from envault.history import _profile_history_dir
from envault.keystore import load_private_key
from envault.profiles import profile_path


@dataclass
class SnapshotDiffResult:
    profile: str
    snapshot_id: str
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [f"Snapshot diff for '{self.profile}' vs snapshot '{self.snapshot_id}':"]
        for k, v in sorted(self.added.items()):
            lines.append(f"  + {k}={v}")
        for k, v in sorted(self.removed.items()):
            lines.append(f"  - {k}={v}")
        for k, (old, new) in sorted(self.changed.items()):
            lines.append(f"  ~ {k}: {old!r} -> {new!r}")
        if self.ok:
            lines.append("  (no changes)")
        return "\n".join(lines)


def _load_vars(path: Path, private_key: str) -> Dict[str, str]:
    raw = decrypt_file(path, private_key)
    return parse_env_bytes(raw)


def diff_snapshot(
    profile: str,
    snapshot_id: str,
    base_dir: Optional[Path] = None,
) -> SnapshotDiffResult:
    """Diff the current profile against a named snapshot."""
    private_key = load_private_key(base_dir=base_dir)

    current_path = profile_path(profile, base_dir=base_dir)
    if not current_path.exists():
        raise FileNotFoundError(f"Profile '{profile}' not found.")

    snap_dir = _profile_history_dir(profile, base_dir=base_dir)
    snap_file = snap_dir / f"{snapshot_id}.age"
    if not snap_file.exists():
        raise FileNotFoundError(f"Snapshot '{snapshot_id}' not found for profile '{profile}'.")

    old_vars = _load_vars(snap_file, private_key)
    new_vars = _load_vars(current_path, private_key)

    result = SnapshotDiffResult(profile=profile, snapshot_id=snapshot_id)

    all_keys = set(old_vars) | set(new_vars)
    for key in all_keys:
        if key in old_vars and key not in new_vars:
            result.removed[key] = old_vars[key]
        elif key in new_vars and key not in old_vars:
            result.added[key] = new_vars[key]
        elif old_vars[key] != new_vars[key]:
            result.changed[key] = (old_vars[key], new_vars[key])
        else:
            result.unchanged.append(key)

    return result
