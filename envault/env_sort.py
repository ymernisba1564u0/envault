"""Sort keys within an encrypted .env profile alphabetically or by custom order."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path, profile_exists


@dataclass
class SortResult:
    profile: str
    original_order: List[str] = field(default_factory=list)
    sorted_order: List[str] = field(default_factory=list)
    changed: bool = False

    def ok(self) -> bool:
        return True

    def __str__(self) -> str:
        if not self.changed:
            return f"Profile '{self.profile}' is already sorted."
        moved = [
            f"  {k}" for k, s in zip(self.sorted_order, self.original_order) if k != s
        ]
        return (
            f"Profile '{self.profile}' sorted: "
            f"{len(self.original_order)} keys reordered."
        )


class SortError(Exception):
    def __str__(self) -> str:
        return self.args[0]


def sort_profile(
    profile: str,
    base_dir: Optional[Path] = None,
    reverse: bool = False,
    dry_run: bool = False,
) -> SortResult:
    """Sort the keys of *profile* alphabetically and re-encrypt in place.

    Args:
        profile:  Profile name.
        base_dir: Override base directory (used in tests).
        reverse:  If True, sort in descending order.
        dry_run:  If True, compute the result but do not write changes.

    Returns:
        SortResult describing what changed.

    Raises:
        SortError: If the profile does not exist.
    """
    if not profile_exists(profile, base_dir=base_dir):
        raise SortError(f"Profile '{profile}' does not exist.")

    path = profile_path(profile, base_dir=base_dir)
    priv = load_private_key()
    pub = load_public_key()

    plaintext = decrypt_file(path, priv)
    pairs = parse_env_bytes(plaintext)

    original_keys = [k for k, _ in pairs]
    sorted_pairs = sorted(pairs, key=lambda kv: kv[0].lower(), reverse=reverse)
    sorted_keys = [k for k, _ in sorted_pairs]

    changed = original_keys != sorted_keys

    if changed and not dry_run:
        lines = "".join(f"{k}={v}\n" for k, v in sorted_pairs)
        encrypt_file(lines.encode(), path, pub)

    return SortResult(
        profile=profile,
        original_order=original_keys,
        sorted_order=sorted_keys,
        changed=changed,
    )
