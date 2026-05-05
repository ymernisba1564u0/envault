"""Key rotation: re-encrypt all profiles under a new keypair."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.crypto import generate_keypair, decrypt_file, encrypt_file
from envault.keystore import save_keypair, load_private_key, load_public_key
from envault.profiles import list_profiles, profile_path
from envault.audit import record_event


def rotate_keys(
    base_dir: Optional[Path] = None,
    *,
    force: bool = False,
) -> tuple[str, str]:
    """Generate a new keypair and re-encrypt every stored profile.

    Returns the new (public_key, private_key) tuple.
    Raises RuntimeError if any profile fails to re-encrypt.
    """
    old_private = load_private_key(base_dir)
    new_public, new_private = generate_keypair()

    profiles = list_profiles(base_dir)
    reencrypted: list[str] = []

    for name in profiles:
        path = profile_path(name, base_dir)
        try:
            plaintext = decrypt_file(path, old_private)
            encrypt_file(path, plaintext, new_public)
            reencrypted.append(name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to re-encrypt profile '{name}': {exc}"
            ) from exc

    save_keypair(new_public, new_private, base_dir, overwrite=True)

    record_event(
        "rotate",
        detail={
            "profiles_reencrypted": reencrypted,
            "profile_count": len(reencrypted),
        },
        base_dir=base_dir,
    )

    return new_public, new_private
