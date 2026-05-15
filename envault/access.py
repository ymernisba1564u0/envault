"""Access control: restrict which profiles a recipient key may decrypt."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.profiles import _profile_dir, profile_exists


def _acl_file(base: Path) -> Path:
    return base / ".envault" / "access.json"


def _load_acl(base: Path) -> Dict[str, List[str]]:
    f = _acl_file(base)
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def _save_acl(base: Path, acl: Dict[str, List[str]]) -> None:
    f = _acl_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(acl, indent=2, sort_keys=True))


class AccessError(Exception):
    pass


def grant_access(base: Path, profile: str, recipient_key: str) -> List[str]:
    """Grant *recipient_key* access to *profile*. Returns updated key list."""
    if not profile_exists(base, profile):
        raise AccessError(f"Profile '{profile}' does not exist.")
    acl = _load_acl(base)
    keys: List[str] = acl.get(profile, [])
    if recipient_key not in keys:
        keys.append(recipient_key)
    acl[profile] = sorted(keys)
    _save_acl(base, acl)
    return acl[profile]


def revoke_access(base: Path, profile: str, recipient_key: str) -> List[str]:
    """Revoke *recipient_key* access from *profile*. Returns updated key list."""
    if not profile_exists(base, profile):
        raise AccessError(f"Profile '{profile}' does not exist.")
    acl = _load_acl(base)
    keys: List[str] = acl.get(profile, [])
    keys = [k for k in keys if k != recipient_key]
    acl[profile] = keys
    _save_acl(base, acl)
    return acl[profile]


def list_access(base: Path, profile: str) -> List[str]:
    """Return the list of recipient keys allowed to access *profile*."""
    acl = _load_acl(base)
    return list(acl.get(profile, []))


def has_access(base: Path, profile: str, recipient_key: str) -> bool:
    """Return True if *recipient_key* is in the ACL for *profile*."""
    return recipient_key in list_access(base, profile)


def clear_access(base: Path, profile: str) -> None:
    """Remove all ACL entries for *profile*."""
    acl = _load_acl(base)
    acl.pop(profile, None)
    _save_acl(base, acl)
