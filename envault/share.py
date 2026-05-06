"""Share encrypted secrets with other users via their public keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.crypto import encrypt_data, decrypt_data
from envault.keystore import load_private_key
from envault.profiles import profile_path, profile_exists


def _share_dir(base: Optional[Path] = None) -> Path:
    """Return the directory where shared bundles are stored."""
    root = base or Path.home() / ".envault"
    return root / "shared"


def share_profile(
    profile: str,
    recipient_public_key: str,
    *,
    base: Optional[Path] = None,
) -> Path:
    """Encrypt a profile's ciphertext for a recipient and write a share bundle.

    The bundle is a JSON file containing the re-encrypted payload and metadata.
    Returns the path to the written bundle file.
    """
    if not profile_exists(profile, base=base):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")

    priv_key = load_private_key(base=base)
    src = profile_path(profile, base=base)
    raw_ciphertext = src.read_bytes()

    # Decrypt with our own key first
    plaintext = decrypt_data(raw_ciphertext, priv_key)

    # Re-encrypt for the recipient
    shared_ciphertext = encrypt_data(plaintext, recipient_public_key)

    bundle = {
        "profile": profile,
        "recipient": recipient_public_key,
        "payload": shared_ciphertext.hex(),
    }

    share_dir = _share_dir(base=base)
    share_dir.mkdir(parents=True, exist_ok=True)

    out_path = share_dir / f"{profile}.share.json"
    out_path.write_text(json.dumps(bundle, indent=2))
    return out_path


def receive_share(
    bundle_path: Path,
    *,
    base: Optional[Path] = None,
) -> bytes:
    """Decrypt a share bundle using the local private key.

    Returns the raw plaintext bytes of the shared profile.
    """
    data = json.loads(bundle_path.read_text())
    payload = bytes.fromhex(data["payload"])
    priv_key = load_private_key(base=base)
    return decrypt_data(payload, priv_key)
