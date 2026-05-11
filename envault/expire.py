"""Profile expiry: mark profiles with a TTL and check if they have expired."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envault.profiles import profile_path, profile_exists, _profile_dir

_EXPIRY_FILENAME = ".expiry.json"


def _expiry_file(base: Optional[Path] = None) -> Path:
    return _profile_dir(base) / _EXPIRY_FILENAME


def _load_expiry(base: Optional[Path] = None) -> dict:
    ef = _expiry_file(base)
    if not ef.exists():
        return {}
    return json.loads(ef.read_text())


def _save_expiry(data: dict, base: Optional[Path] = None) -> None:
    ef = _expiry_file(base)
    ef.parent.mkdir(parents=True, exist_ok=True)
    ef.write_text(json.dumps(data, indent=2))


def set_expiry(profile: str, expires_at: datetime, base: Optional[Path] = None) -> None:
    """Attach an expiry timestamp (UTC) to a profile."""
    if not profile_exists(profile, base):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    data = _load_expiry(base)
    data[profile] = expires_at.astimezone(timezone.utc).isoformat()
    _save_expiry(data, base)


def clear_expiry(profile: str, base: Optional[Path] = None) -> None:
    """Remove the expiry timestamp from a profile."""
    data = _load_expiry(base)
    data.pop(profile, None)
    _save_expiry(data, base)


def get_expiry(profile: str, base: Optional[Path] = None) -> Optional[datetime]:
    """Return the expiry datetime (UTC) for a profile, or None if not set."""
    data = _load_expiry(base)
    raw = data.get(profile)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def is_expired(profile: str, base: Optional[Path] = None) -> bool:
    """Return True if the profile has an expiry set and it is in the past."""
    expiry = get_expiry(profile, base)
    if expiry is None:
        return False
    return datetime.now(timezone.utc) >= expiry


def list_expiring(base: Optional[Path] = None) -> list[tuple[str, datetime]]:
    """Return all profiles with an expiry set, sorted by expiry time."""
    data = _load_expiry(base)
    result = [
        (name, datetime.fromisoformat(ts))
        for name, ts in data.items()
    ]
    return sorted(result, key=lambda x: x[1])
