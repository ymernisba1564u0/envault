"""Profile grouping — assign profiles to named groups and query by group."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.profiles import profile_exists, _profile_dir


def _group_file(base: Path | None = None) -> Path:
    root = base or _profile_dir()
    return root / ".groups.json"


def _load_groups(base: Path | None = None) -> Dict[str, List[str]]:
    gf = _group_file(base)
    if not gf.exists():
        return {}
    return json.loads(gf.read_text())


def _save_groups(data: Dict[str, List[str]], base: Path | None = None) -> None:
    gf = _group_file(base)
    gf.parent.mkdir(parents=True, exist_ok=True)
    gf.write_text(json.dumps(data, indent=2))


class GroupError(Exception):
    pass


def add_to_group(group: str, profile: str, base: Path | None = None) -> List[str]:
    """Add *profile* to *group*. Returns the sorted member list."""
    if not profile_exists(profile, base):
        raise GroupError(f"profile '{profile}' does not exist")
    data = _load_groups(base)
    members = data.get(group, [])
    if profile not in members:
        members.append(profile)
    data[group] = sorted(members)
    _save_groups(data, base)
    return data[group]


def remove_from_group(group: str, profile: str, base: Path | None = None) -> List[str]:
    """Remove *profile* from *group*. Returns the remaining sorted member list."""
    data = _load_groups(base)
    members = data.get(group, [])
    if profile not in members:
        raise GroupError(f"profile '{profile}' is not in group '{group}'")
    members = [m for m in members if m != profile]
    if members:
        data[group] = sorted(members)
    else:
        data.pop(group, None)
    _save_groups(data, base)
    return data.get(group, [])


def list_groups(base: Path | None = None) -> List[str]:
    """Return sorted list of all group names."""
    return sorted(_load_groups(base).keys())


def group_members(group: str, base: Path | None = None) -> List[str]:
    """Return sorted list of profiles in *group* (empty list if unknown)."""
    return _load_groups(base).get(group, [])


def profile_groups(profile: str, base: Path | None = None) -> List[str]:
    """Return sorted list of groups that contain *profile*."""
    data = _load_groups(base)
    return sorted(g for g, members in data.items() if profile in members)
