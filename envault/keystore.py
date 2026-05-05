"""Manage persistence of age identity keys on the local filesystem."""

from __future__ import annotations

import os
import stat
from pathlib import Path

DEFAULT_KEY_DIR = Path.home() / ".config" / "envault"
IDENTITY_FILENAME = "identity.txt"
RECIPIENT_FILENAME = "recipient.txt"


def _key_dir(key_dir: Path | None = None) -> Path:
    return Path(key_dir) if key_dir else DEFAULT_KEY_DIR


def save_keypair(private_key: str, public_key: str, key_dir: Path | None = None) -> Path:
    """Persist a keypair to *key_dir*, creating the directory if needed.

    The private key file is written with mode 0o600 (owner read/write only).

    Returns:
        The directory where keys were saved.
    """
    directory = _key_dir(key_dir)
    directory.mkdir(parents=True, exist_ok=True)

    identity_path = directory / IDENTITY_FILENAME
    identity_path.write_text(private_key + "\n", encoding="utf-8")
    identity_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    recipient_path = directory / RECIPIENT_FILENAME
    recipient_path.write_text(public_key + "\n", encoding="utf-8")

    return directory


def load_private_key(key_dir: Path | None = None) -> str:
    """Load the private key from *key_dir*.

    Raises:
        FileNotFoundError: If the identity file does not exist.
    """
    path = _key_dir(key_dir) / IDENTITY_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"No identity file found at {path}. Run 'envault init' to create one."
        )
    return path.read_text(encoding="utf-8").strip()


def load_public_key(key_dir: Path | None = None) -> str:
    """Load the public key (recipient) from *key_dir*.

    Raises:
        FileNotFoundError: If the recipient file does not exist.
    """
    path = _key_dir(key_dir) / RECIPIENT_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"No recipient file found at {path}. Run 'envault init' to create one."
        )
    return path.read_text(encoding="utf-8").strip()


def keypair_exists(key_dir: Path | None = None) -> bool:
    """Return True if both identity and recipient files exist in *key_dir*."""
    directory = _key_dir(key_dir)
    return (directory / IDENTITY_FILENAME).exists() and (directory / RECIPIENT_FILENAME).exists()
