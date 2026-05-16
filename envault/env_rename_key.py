"""Rename a key within an encrypted profile without changing its value."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path, profile_exists


class RenameKeyError(Exception):
    def __str__(self) -> str:
        return self.args[0]


@dataclass
class RenameKeyResult:
    profile: str
    old_key: str
    new_key: str
    value: str
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return not self.skipped


def rename_key(
    profile: str,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
    base_dir: Optional[Path] = None,
) -> RenameKeyResult:
    """Rename *old_key* to *new_key* inside *profile*.

    Raises RenameKeyError if the profile does not exist, old_key is absent,
    or new_key already exists and *overwrite* is False.
    """
    if not profile_exists(profile, base_dir=base_dir):
        raise RenameKeyError(f"Profile '{profile}' does not exist.")

    priv = load_private_key(base_dir=base_dir)
    pub = load_public_key(base_dir=base_dir)
    path = profile_path(profile, base_dir=base_dir)

    raw = decrypt_file(path, priv)
    pairs = parse_env_bytes(raw)

    keys = [k for k, _ in pairs]

    if old_key not in keys:
        raise RenameKeyError(f"Key '{old_key}' not found in profile '{profile}'.")

    if new_key in keys and not overwrite:
        raise RenameKeyError(
            f"Key '{new_key}' already exists in profile '{profile}'. "
            "Use --overwrite to replace it."
        )

    updated: list[tuple[str, str]] = []
    captured_value = ""
    for k, v in pairs:
        if k == old_key:
            captured_value = v
            updated.append((new_key, v))
        elif k == new_key and overwrite:
            # skip the old occurrence of new_key so we don't duplicate
            continue
        else:
            updated.append((k, v))

    new_raw = "\n".join(to_dotenv_lines(updated)).encode()
    encrypt_file(new_raw, path, pub)

    return RenameKeyResult(
        profile=profile,
        old_key=old_key,
        new_key=new_key,
        value=captured_value,
    )
