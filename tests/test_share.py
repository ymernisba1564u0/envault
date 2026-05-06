"""Tests for envault.share — profile sharing between users."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.crypto import generate_keypair, encrypt_data
from envault.keystore import save_keypair
from envault.profiles import profile_path, ensure_profile_dir
from envault.share import share_profile, receive_share, _share_dir


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    """Generate and save a keypair for the owner."""
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base=base)
    return pub, priv


@pytest.fixture()
def sample_profile(base: Path, setup_keys):
    """Create an encrypted profile with known plaintext."""
    pub, _ = setup_keys
    plaintext = b"API_KEY=secret123\nDB_PASS=hunter2\n"
    ciphertext = encrypt_data(plaintext, pub)
    ensure_profile_dir(base=base)
    p = profile_path("staging", base=base)
    p.write_bytes(ciphertext)
    return plaintext


def test_share_profile_creates_bundle(base, setup_keys, sample_profile):
    recipient_pub, _ = generate_keypair()
    out = share_profile("staging", recipient_pub, base=base)
    assert out.exists()
    assert out.suffix == ".json"


def test_share_bundle_contains_expected_fields(base, setup_keys, sample_profile):
    recipient_pub, _ = generate_keypair()
    out = share_profile("staging", recipient_pub, base=base)
    data = json.loads(out.read_text())
    assert data["profile"] == "staging"
    assert data["recipient"] == recipient_pub
    assert "payload" in data


def test_share_bundle_stored_in_share_dir(base, setup_keys, sample_profile):
    recipient_pub, _ = generate_keypair()
    out = share_profile("staging", recipient_pub, base=base)
    assert out.parent == _share_dir(base=base)


def test_receive_share_decrypts_correctly(base, setup_keys, sample_profile):
    """Recipient can decrypt a bundle encrypted for their public key."""
    recipient_pub, recipient_priv = generate_keypair()
    bundle_path = share_profile("staging", recipient_pub, base=base)

    # Swap to recipient's keys
    save_keypair(recipient_pub, recipient_priv, base=base, force=True)

    recovered = receive_share(bundle_path, base=base)
    assert recovered == sample_profile


def test_share_profile_raises_if_profile_missing(base, setup_keys):
    recipient_pub, _ = generate_keypair()
    with pytest.raises(FileNotFoundError, match="does not exist"):
        share_profile("nonexistent", recipient_pub, base=base)


def test_share_produces_different_ciphertext_each_time(base, setup_keys, sample_profile):
    recipient_pub, _ = generate_keypair()
    out1 = share_profile("staging", recipient_pub, base=base)
    payload1 = json.loads(out1.read_text())["payload"]

    out2 = share_profile("staging", recipient_pub, base=base)
    payload2 = json.loads(out2.read_text())["payload"]

    assert payload1 != payload2
