"""Filter env vars in a profile by key pattern or value pattern."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path


@dataclass
class FilterResult:
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return True

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"{k}={v}" for k, v in self.matched.items()]
        return "\n".join(lines)


class FilterError(Exception):
    def __str__(self) -> str:
        return self.args[0]


def _load_vars(profile: str, base_dir: Path) -> Dict[str, str]:
    priv = load_private_key(base_dir)
    path = profile_path(profile, base_dir)
    if not path.exists():
        raise FilterError(f"Profile '{profile}' not found.")
    raw = decrypt_file(path, priv)
    return dict(parse_env_bytes(raw))


def filter_profile(
    profile: str,
    base_dir: Path,
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    invert: bool = False,
) -> FilterResult:
    """Return vars matching key_pattern and/or value_pattern (glob syntax)."""
    if key_pattern is None and value_pattern is None:
        raise FilterError("At least one of key_pattern or value_pattern is required.")

    vars_ = _load_vars(profile, base_dir)
    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for k, v in vars_.items():
        key_ok = fnmatch.fnmatch(k, key_pattern) if key_pattern else True
        val_ok = bool(re.search(value_pattern, v)) if value_pattern else True
        passes = key_ok and val_ok
        if invert:
            passes = not passes
        if passes:
            matched[k] = v
        else:
            excluded[k] = v

    return FilterResult(matched=matched, excluded=excluded)


def write_filtered(
    profile: str,
    base_dir: Path,
    result: FilterResult,
    dest_profile: str,
) -> Path:
    """Write the matched vars from a FilterResult into a new profile."""
    pub = load_public_key(base_dir)
    dest = profile_path(dest_profile, base_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = to_dotenv_lines(list(result.matched.items()))
    encrypt_file(lines.encode(), dest, pub)
    return dest
