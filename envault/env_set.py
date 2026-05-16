"""Set, unset, and get individual keys in an encrypted profile."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from envault.profiles import profile_path, profile_exists
from envault.keystore import load_public_key, load_private_key
from envault.crypto import encrypt_file, decrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines


class EnvSetError(Exception):
    def __str__(self) -> str:
        return self.args[0]


@dataclass
class SetResult:
    profile: str
    key: str
    previous: Optional[str]
    current: Optional[str]
    action: str  # 'set' | 'unset' | 'unchanged'

    @property
    def ok(self) -> bool:
        return self.action != 'unchanged' or self.current == self.previous


def _load_vars(path: Path) -> dict[str, str]:
    """Decrypt and parse an existing profile, returning key/value pairs."""
    priv = load_private_key()
    raw = decrypt_file(path, priv)
    return parse_env_bytes(raw)


def _save_vars(path: Path, pairs: dict[str, str]) -> None:
    """Encode pairs as .env bytes and encrypt back to the profile path."""
    pub = load_public_key()
    lines = to_dotenv_lines(pairs)
    raw = "\n".join(lines).encode()
    encrypt_file(raw, path, pub)


def set_key(profile: str, key: str, value: str, base: Optional[Path] = None) -> SetResult:
    """Set *key* to *value* in *profile*. Creates the key if absent."""
    if not key or not key.replace("_", "").isalnum():
        raise EnvSetError(f"Invalid key name: {key!r}")
    if not profile_exists(profile, base=base):
        raise EnvSetError(f"Profile not found: {profile!r}")
    path = profile_path(profile, base=base)
    pairs = _load_vars(path)
    previous = pairs.get(key)
    pairs[key] = value
    action = "unchanged" if previous == value else "set"
    _save_vars(path, pairs)
    return SetResult(profile=profile, key=key, previous=previous, current=value, action=action)


def unset_key(profile: str, key: str, base: Optional[Path] = None) -> SetResult:
    """Remove *key* from *profile*. No-op if the key does not exist."""
    if not profile_exists(profile, base=base):
        raise EnvSetError(f"Profile not found: {profile!r}")
    path = profile_path(profile, base=base)
    pairs = _load_vars(path)
    previous = pairs.pop(key, None)
    action = "unset" if previous is not None else "unchanged"
    if action == "unset":
        _save_vars(path, pairs)
    return SetResult(profile=profile, key=key, previous=previous, current=None, action=action)


def get_key(profile: str, key: str, base: Optional[Path] = None) -> Optional[str]:
    """Return the value of *key* in *profile*, or None if absent."""
    if not profile_exists(profile, base=base):
        raise EnvSetError(f"Profile not found: {profile!r}")
    path = profile_path(profile, base=base)
    pairs = _load_vars(path)
    return pairs.get(key)
