"""Copy individual key-value pairs between encrypted profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path, profile_exists


@dataclass
class CopyError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class CopyResult:
    source: str
    destination: str
    keys_copied: List[str] = field(default_factory=list)
    keys_skipped: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.keys_copied)


def copy_keys(
    source_profile: str,
    dest_profile: str,
    keys: List[str],
    *,
    overwrite: bool = False,
    base_dir: Optional[Path] = None,
) -> CopyResult:
    """Copy *keys* from *source_profile* into *dest_profile*.

    If *overwrite* is False (default) existing keys in the destination are
    left unchanged and reported in ``CopyResult.keys_skipped``.
    """
    if not profile_exists(source_profile, base_dir=base_dir):
        raise CopyError(f"Source profile '{source_profile}' does not exist.")
    if not profile_exists(dest_profile, base_dir=base_dir):
        raise CopyError(f"Destination profile '{dest_profile}' does not exist.")

    priv = load_private_key(base_dir=base_dir)
    pub = load_public_key(base_dir=base_dir)

    src_path = profile_path(source_profile, base_dir=base_dir)
    dst_path = profile_path(dest_profile, base_dir=base_dir)

    src_vars = parse_env_bytes(decrypt_file(src_path, priv))
    dst_vars = parse_env_bytes(decrypt_file(dst_path, priv))

    result = CopyResult(source=source_profile, destination=dest_profile)

    for key in keys:
        if key not in src_vars:
            raise CopyError(f"Key '{key}' not found in source profile '{source_profile}'.")
        if key in dst_vars and not overwrite:
            result.keys_skipped.append(key)
            continue
        dst_vars[key] = src_vars[key]
        result.keys_copied.append(key)

    if result.keys_copied:
        updated = "\n".join(to_dotenv_lines(dst_vars)).encode()
        encrypt_file(updated, dst_path, pub)

    return result
