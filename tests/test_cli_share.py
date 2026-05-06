"""Tests for the share CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_share import share_cmd
from envault.crypto import generate_keypair, encrypt_data
from envault.keystore import save_keypair
from envault.profiles import profile_path, ensure_profile_dir


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path: Path):
    """Return a base directory with a keypair and a sample profile."""
    pub, priv = generate_keypair()
    save_keypair(pub, priv, base=tmp_path)

    plaintext = b"TOKEN=abc\nSECRET=xyz\n"
    ciphertext = encrypt_data(plaintext, pub)
    ensure_profile_dir(base=tmp_path)
    profile_path("dev", base=tmp_path).write_bytes(ciphertext)

    return tmp_path, pub, priv, plaintext


def test_send_creates_bundle(runner, isolated):
    base, pub, priv, _ = isolated
    recipient_pub, _ = generate_keypair()
    result = runner.invoke(share_cmd, ["send", "dev", recipient_pub, "--base", str(base)])
    assert result.exit_code == 0
    assert "share bundle written to" in result.output.lower()


def test_send_fails_for_missing_profile(runner, isolated):
    base, pub, priv, _ = isolated
    recipient_pub, _ = generate_keypair()
    result = runner.invoke(share_cmd, ["send", "nope", recipient_pub, "--base", str(base)])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_receive_prints_env_vars(runner, isolated):
    base, pub, priv, plaintext = isolated
    recipient_pub, recipient_priv = generate_keypair()

    # Create share bundle
    runner.invoke(share_cmd, ["send", "dev", recipient_pub, "--base", str(base)])

    # Switch to recipient keys
    save_keypair(recipient_pub, recipient_priv, base=base, force=True)

    bundle = base / "shared" / "dev.share.json"
    result = runner.invoke(share_cmd, ["receive", str(bundle), "--base", str(base)])
    assert result.exit_code == 0
    assert "TOKEN" in result.output
    assert "SECRET" in result.output


def test_receive_dotenv_format(runner, isolated):
    base, pub, priv, _ = isolated
    recipient_pub, recipient_priv = generate_keypair()

    runner.invoke(share_cmd, ["send", "dev", recipient_pub, "--base", str(base)])
    save_keypair(recipient_pub, recipient_priv, base=base, force=True)

    bundle = base / "shared" / "dev.share.json"
    result = runner.invoke(
        share_cmd, ["receive", str(bundle), "--format", "dotenv", "--base", str(base)]
    )
    assert result.exit_code == 0
    assert "TOKEN=" in result.output
