"""Tests for envault.crypto encryption/decryption helpers."""

from __future__ import annotations

import pytest

from envault.crypto import (
    decrypt_data,
    decrypt_file,
    encrypt_data,
    encrypt_file,
    generate_keypair,
)


@pytest.fixture()
def keypair() -> tuple[str, str]:
    """Return a freshly generated (private_key, public_key) pair."""
    return generate_keypair()


def test_generate_keypair_format(keypair):
    private_key, public_key = keypair
    assert private_key.startswith("AGE-SECRET-KEY-"), "Private key should start with AGE-SECRET-KEY-"
    assert public_key.startswith("age1"), "Public key should start with age1"


def test_generate_keypair_unique():
    pair_a = generate_keypair()
    pair_b = generate_keypair()
    assert pair_a[0] != pair_b[0], "Two generated private keys must differ"
    assert pair_a[1] != pair_b[1], "Two generated public keys must differ"


def test_roundtrip_bytes(keypair):
    private_key, public_key = keypair
    plaintext = b"DATABASE_URL=postgres://user:pass@localhost/db\nSECRET_KEY=supersecret"
    ciphertext = encrypt_data(plaintext, public_key)
    assert ciphertext != plaintext
    recovered = decrypt_data(ciphertext, private_key)
    assert recovered == plaintext


def test_encrypt_produces_different_ciphertext_each_time(keypair):
    """age uses ephemeral keys so the same plaintext yields different ciphertext."""
    _, public_key = keypair
    plaintext = b"MY_SECRET=hello"
    ct1 = encrypt_data(plaintext, public_key)
    ct2 = encrypt_data(plaintext, public_key)
    assert ct1 != ct2


def test_wrong_key_raises(keypair):
    _, public_key = keypair
    other_private, _ = generate_keypair()
    ciphertext = encrypt_data(b"secret", public_key)
    with pytest.raises(Exception):
        decrypt_data(ciphertext, other_private)


def test_encrypt_decrypt_file(tmp_path, keypair):
    private_key, public_key = keypair
    src = tmp_path / ".env"
    src.write_text("API_KEY=abc123\nDEBUG=true\n", encoding="utf-8")

    encrypted = tmp_path / ".env.age"
    encrypt_file(src, encrypted, public_key)
    assert encrypted.exists()
    assert encrypted.read_bytes() != src.read_bytes()

    decrypted = tmp_path / ".env.decrypted"
    decrypt_file(encrypted, decrypted, private_key)
    assert decrypted.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")
