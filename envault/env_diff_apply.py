"""Apply a diff patch to an encrypted profile, adding/updating/removing keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path, profile_exists


@dataclass
class PatchError(Exception):
    message: str

    def __str__(self) -> str:  # noqa: D105
        return self.message


@dataclass
class PatchResult:
    profile: str
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True

    @property
    def changed(self) -> bool:
        return bool(self.added or self.updated or self.removed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.updated:
            parts.append(f"~{len(self.updated)} updated")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        return ", ".join(parts) if parts else "no changes"


def apply_patch(
    profile: str,
    set_keys: Optional[Dict[str, str]] = None,
    remove_keys: Optional[List[str]] = None,
    base_dir: Optional[Path] = None,
) -> PatchResult:
    """Decrypt *profile*, mutate its key/value pairs, and re-encrypt in place.

    Args:
        profile: Name of the profile to patch.
        set_keys: Mapping of key -> value to add or update.
        remove_keys: List of keys to delete from the profile.
        base_dir: Optional override for the profiles base directory.
    """
    set_keys = set_keys or {}
    remove_keys = remove_keys or []

    if not profile_exists(profile, base_dir=base_dir):
        raise PatchError(f"Profile '{profile}' does not exist.")

    priv = load_private_key()
    pub = load_public_key()
    path = profile_path(profile, base_dir=base_dir)

    raw = decrypt_file(path, priv)
    env: Dict[str, str] = dict(parse_env_bytes(raw))

    result = PatchResult(profile=profile)

    for key, value in set_keys.items():
        if key in env:
            if env[key] != value:
                result.updated.append(key)
        else:
            result.added.append(key)
        env[key] = value

    for key in remove_keys:
        if key in env:
            del env[key]
            result.removed.append(key)

    new_content = "\n".join(to_dotenv_lines(env)).encode()
    encrypt_file(new_content, path, pub)

    return result
