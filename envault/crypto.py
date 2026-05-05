"""Core encryption/decryption module using age encryption via pyrage."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

try:
    import pyrage
except ImportError as exc:
    raise ImportError(
        "pyrage is required for encryption. Install it with: pip install pyrage"
    ) from exc


def generate_keypair() -> tuple[str, str]:
    """Generate a new age identity (private key) and its corresponding recipient (public key).

    Returns:
        A tuple of (private_key_str, public_key_str).
    """
    identity = pyrage.x25519.Identity.generate()
    private_key = str(identity)
    public_key = str(identity.to_public())
    return private_key, public_key


def encrypt_data(plaintext: bytes, public_key: str) -> bytes:
    """Encrypt bytes using an age X25519 public key (recipient).

    Args:
        plaintext: Raw bytes to encrypt.
        public_key: age X25519 recipient string (starts with 'age1').

    Returns:
        Encrypted bytes in age binary format.
    """
    recipient = pyrage.x25519.Recipient.from_str(public_key)
    return pyrage.encrypt(plaintext, [recipient])


def decrypt_data(ciphertext: bytes, private_key: str) -> bytes:
    """Decrypt age-encrypted bytes using an X25519 private key.

    Args:
        ciphertext: age-encrypted bytes.
        private_key: age X25519 identity string (starts with 'AGE-SECRET-KEY-').

    Returns:
        Decrypted plaintext bytes.
    """
    identity = pyrage.x25519.Identity.from_str(private_key)
    return pyrage.decrypt(ciphertext, [identity])


def encrypt_file(source: Union[str, Path], dest: Union[str, Path], public_key: str) -> None:
    """Encrypt a file at *source* and write the ciphertext to *dest*."""
    source, dest = Path(source), Path(dest)
    plaintext = source.read_bytes()
    ciphertext = encrypt_data(plaintext, public_key)
    dest.write_bytes(ciphertext)


def decrypt_file(source: Union[str, Path], dest: Union[str, Path], private_key: str) -> None:
    """Decrypt an age-encrypted file at *source* and write plaintext to *dest*."""
    source, dest = Path(source), Path(dest)
    ciphertext = source.read_bytes()
    plaintext = decrypt_data(ciphertext, private_key)
    dest.write_bytes(plaintext)
