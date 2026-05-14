"""Profile alias management — map short names to profile names."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.profiles import _profile_dir


def _alias_file(base: Optional[Path] = None) -> Path:
    return _profile_dir(base) / ".aliases.json"


def _load_aliases(base: Optional[Path] = None) -> Dict[str, str]:
    f = _alias_file(base)
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def _save_aliases(aliases: Dict[str, str], base: Optional[Path] = None) -> None:
    f = _alias_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(aliases, indent=2, sort_keys=True))


class AliasError(Exception):
    pass


def add_alias(alias: str, profile: str, base: Optional[Path] = None) -> Dict[str, str]:
    """Map *alias* to *profile*. Raises AliasError if alias already exists."""
    from envault.profiles import profile_exists

    if not profile_exists(profile, base):
        raise AliasError(f"Profile '{profile}' does not exist.")
    aliases = _load_aliases(base)
    if alias in aliases:
        raise AliasError(
            f"Alias '{alias}' already maps to '{aliases[alias]}'. Use remove first."
        )
    aliases[alias] = profile
    _save_aliases(aliases, base)
    return aliases


def remove_alias(alias: str, base: Optional[Path] = None) -> Dict[str, str]:
    """Remove *alias*. Raises AliasError if it does not exist."""
    aliases = _load_aliases(base)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' does not exist.")
    del aliases[alias]
    _save_aliases(aliases, base)
    return aliases


def resolve_alias(name: str, base: Optional[Path] = None) -> str:
    """Return the profile name for *name*, resolving an alias if necessary."""
    aliases = _load_aliases(base)
    return aliases.get(name, name)


def list_aliases(base: Optional[Path] = None) -> List[Dict[str, str]]:
    """Return sorted list of {alias, profile} dicts."""
    aliases = _load_aliases(base)
    return [{"alias": k, "profile": v} for k, v in sorted(aliases.items())]
