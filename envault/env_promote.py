"""Promote (copy) a profile from one environment tier to another.

Typical usage: promote staging -> production, applying an optional
key allow-list so that only approved variables are carried over.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from envault.crypto import decrypt_file, encrypt_data
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path, profile_exists, ensure_profile_dir


@dataclass
class PromoteResult:
    source: str
    destination: str
    promoted_keys: list[str] = field(default_factory=list)
    skipped_keys: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.promoted_keys)

    def __str__(self) -> str:
        lines = [
            f"Promoted '{self.source}' -> '{self.destination}'",
            f"  Keys promoted : {len(self.promoted_keys)}",
            f"  Keys skipped  : {len(self.skipped_keys)}",
        ]
        return "\n".join(lines)


class PromoteError(Exception):
    """Raised when a promotion cannot be completed."""


def promote_profile(
    source: str,
    destination: str,
    *,
    allow: Sequence[str] | None = None,
    overwrite: bool = False,
    base_dir: Path | None = None,
) -> PromoteResult:
    """Decrypt *source*, optionally filter keys, then encrypt into *destination*.

    Parameters
    ----------
    source:
        Name of the source profile.
    destination:
        Name of the destination profile.
    allow:
        If given, only keys in this list are promoted; others are skipped.
    overwrite:
        When *False* (default) raise :class:`PromoteError` if *destination*
        already exists.
    base_dir:
        Override the default profile directory (used in tests).
    """
    if not profile_exists(source, base_dir=base_dir):
        raise PromoteError(f"Source profile '{source}' does not exist.")
    if not overwrite and profile_exists(destination, base_dir=base_dir):
        raise PromoteError(
            f"Destination profile '{destination}' already exists. "
            "Pass overwrite=True to replace it."
        )

    priv = load_private_key()
    pub = load_public_key()

    src_path = profile_path(source, base_dir=base_dir)
    plaintext = decrypt_file(src_path, priv)
    pairs = parse_env_bytes(plaintext)

    allow_set = set(allow) if allow is not None else None
    promoted: dict[str, str] = {}
    skipped: list[str] = []

    for key, value in pairs.items():
        if allow_set is None or key in allow_set:
            promoted[key] = value
        else:
            skipped.append(key)

    env_bytes = "\n".join(to_dotenv_lines(promoted)).encode()
    ensure_profile_dir(base_dir=base_dir)
    dst_path = profile_path(destination, base_dir=base_dir)
    ciphertext = encrypt_data(env_bytes, pub)
    dst_path.write_bytes(ciphertext)

    return PromoteResult(
        source=source,
        destination=destination,
        promoted_keys=list(promoted.keys()),
        skipped_keys=skipped,
    )
