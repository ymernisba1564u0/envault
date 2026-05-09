"""Profile pinning — mark profiles as pinned to prevent accidental deletion or overwrite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.profiles import profile_path, _profile_dir

_PIN_FILE = ".pinned.json"


def _pin_file(base: Path | None = None) -> Path:
    return (base or _profile_dir()) / _PIN_FILE


def _load_pins(base: Path | None = None) -> List[str]:
    pf = _pin_file(base)
    if not pf.exists():
        return []
    try:
        data = json.loads(pf.read_text())
        return sorted(data) if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_pins(pins: List[str], base: Path | None = None) -> None:
    pf = _pin_file(base)
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(json.dumps(sorted(set(pins)), indent=2))


def pin_profile(name: str, base: Path | None = None) -> List[str]:
    """Pin a profile by name. Returns updated list of pinned profiles."""
    enc = profile_path(name, base)
    if not enc.exists():
        raise FileNotFoundError(f"Profile '{name}' does not exist.")
    pins = _load_pins(base)
    if name not in pins:
        pins.append(name)
    _save_pins(pins, base)
    return sorted(pins)


def unpin_profile(name: str, base: Path | None = None) -> List[str]:
    """Unpin a profile by name. Returns updated list of pinned profiles."""
    pins = _load_pins(base)
    pins = [p for p in pins if p != name]
    _save_pins(pins, base)
    return sorted(pins)


def is_pinned(name: str, base: Path | None = None) -> bool:
    """Return True if the given profile is pinned."""
    return name in _load_pins(base)


def list_pinned(base: Path | None = None) -> List[str]:
    """Return sorted list of all pinned profile names."""
    return _load_pins(base)
