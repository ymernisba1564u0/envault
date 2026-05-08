"""Import .env files or shell exports into an envault profile."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envault.crypto import encrypt_file
from envault.keystore import load_public_key
from envault.profiles import ensure_profile_dir, profile_path

_EXPORT_RE = re.compile(r"^export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_PLAIN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    for q in ('"', "'"):
        if value.startswith(q) and value.endswith(q) and len(value) >= 2:
            return value[1:-1]
    return value


def parse_import_source(text: str) -> Tuple[Dict[str, str], List[str]]:
    """Parse raw text into key/value pairs, returning (pairs, skipped_lines)."""
    pairs: Dict[str, str] = {}
    skipped: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = _EXPORT_RE.match(line) or _PLAIN_RE.match(line)
        if m:
            key, value = m.group(1), _strip_quotes(m.group(2).strip())
            pairs[key] = value
        else:
            skipped.append(raw_line)

    return pairs, skipped


def import_env_file(
    source_path: Path,
    profile: str,
    base_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> Tuple[int, List[str]]:
    """Import a .env / shell-export file into an envault profile.

    Returns (number_of_keys_imported, skipped_lines).
    Raises FileExistsError if the profile already exists and overwrite=False.
    """
    ensure_profile_dir(base_dir)
    dest = profile_path(profile, base_dir)

    if dest.exists() and not overwrite:
        raise FileExistsError(
            f"Profile '{profile}' already exists. Use overwrite=True to replace it."
        )

    raw = source_path.read_text(encoding="utf-8")
    pairs, skipped = parse_import_source(raw)

    # Build a clean .env byte string
    env_bytes = "\n".join(f"{k}={v}" for k, v in pairs.items()).encode()

    pub_key = load_public_key(base_dir)
    encrypt_file(env_bytes, dest, pub_key)

    return len(pairs), skipped
