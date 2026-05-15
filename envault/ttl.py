"""TTL (time-to-live) enforcement for encrypted profiles.

Allows setting a maximum age for a profile's secrets; once expired,
decryption is blocked until the profile is explicitly renewed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.profiles import _profile_dir

_TTL_FILENAME = ".ttl.json"


def _ttl_file(base_dir: Path) -> Path:
    return base_dir / _TTL_FILENAME


def _load_ttl(base_dir: Path) -> dict:
    f = _ttl_file(base_dir)
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def _save_ttl(base_dir: Path, data: dict) -> None:
    _ttl_file(base_dir).write_text(json.dumps(data, indent=2))


def set_ttl(profile: str, seconds: int, base_dir: Optional[Path] = None) -> datetime:
    """Record a TTL for *profile*; returns the computed expiry datetime (UTC)."""
    base_dir = base_dir or _profile_dir()
    if not (base_dir / f"{profile}.age").exists():
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    if seconds <= 0:
        raise ValueError("TTL must be a positive number of seconds.")
    data = _load_ttl(base_dir)
    now = datetime.now(timezone.utc)
    expiry = datetime(
        now.year, now.month, now.day,
        now.hour, now.minute, now.second,
        tzinfo=timezone.utc,
    )
    from datetime import timedelta
    expiry = expiry + timedelta(seconds=seconds)
    data[profile] = expiry.isoformat()
    _save_ttl(base_dir, data)
    return expiry


def clear_ttl(profile: str, base_dir: Optional[Path] = None) -> bool:
    """Remove TTL for *profile*. Returns True if a record existed."""
    base_dir = base_dir or _profile_dir()
    data = _load_ttl(base_dir)
    if profile not in data:
        return False
    del data[profile]
    _save_ttl(base_dir, data)
    return True


def get_ttl(profile: str, base_dir: Optional[Path] = None) -> Optional[datetime]:
    """Return the expiry datetime for *profile*, or None if no TTL is set."""
    base_dir = base_dir or _profile_dir()
    data = _load_ttl(base_dir)
    raw = data.get(profile)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def is_expired(profile: str, base_dir: Optional[Path] = None) -> bool:
    """Return True if the profile has a TTL that has already passed."""
    expiry = get_ttl(profile, base_dir)
    if expiry is None:
        return False
    return datetime.now(timezone.utc) >= expiry


def list_ttls(base_dir: Optional[Path] = None) -> dict[str, datetime]:
    """Return a mapping of profile name → expiry datetime for all TTL entries."""
    base_dir = base_dir or _profile_dir()
    data = _load_ttl(base_dir)
    return {name: datetime.fromisoformat(ts) for name, ts in sorted(data.items())}
