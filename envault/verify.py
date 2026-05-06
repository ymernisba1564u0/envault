"""Verify the integrity of encrypted profile files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import NamedTuple

from envault.crypto import decrypt_file
from envault.keystore import load_private_key
from envault.profiles import list_profiles, profile_path


class VerifyResult(NamedTuple):
    profile: str
    ok: bool
    error: str | None = None


def _sha256(data: bytes) -> str:
    """Return hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def verify_profile(profile: str, key_dir: Path | None = None) -> VerifyResult:
    """Attempt to decrypt *profile* and confirm the plaintext is valid UTF-8.

    Returns a :class:`VerifyResult` indicating success or failure.
    """
    try:
        private_key = load_private_key(key_dir=key_dir)
    except FileNotFoundError as exc:
        return VerifyResult(profile=profile, ok=False, error=f"Key not found: {exc}")

    path = profile_path(profile, base=key_dir.parent if key_dir else None)
    if not path.exists():
        return VerifyResult(profile=profile, ok=False, error="Profile file does not exist")

    try:
        plaintext = decrypt_file(path, private_key)
        plaintext.decode("utf-8")  # ensure it is valid text
    except Exception as exc:  # noqa: BLE001
        return VerifyResult(profile=profile, ok=False, error=str(exc))

    return VerifyResult(profile=profile, ok=True)


def verify_all(key_dir: Path | None = None) -> list[VerifyResult]:
    """Verify every profile known to the current key directory.

    Returns a list of :class:`VerifyResult` objects, one per profile.
    """
    base = key_dir.parent if key_dir else None
    profiles = list_profiles(base=base)
    return [verify_profile(p, key_dir=key_dir) for p in profiles]


def checksum_profile(profile: str, key_dir: Path | None = None) -> str:
    """Return the SHA-256 checksum of the *raw encrypted bytes* for *profile*.

    Raises :class:`FileNotFoundError` if the profile does not exist.
    """
    base = key_dir.parent if key_dir else None
    path = profile_path(profile, base=base)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{profile}' not found at {path}")
    return _sha256(path.read_bytes())
