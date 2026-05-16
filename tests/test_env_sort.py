"""Tests for envault.env_sort."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file
from envault.env_sort import SortError, sort_profile
from envault.export import parse_env_bytes
from envault.crypto import decrypt_file
from envault.keystore import load_private_key, load_public_key, save_keypair
from envault.crypto import generate_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    monkeypatch.setattr("envault.env_sort.profile_path", lambda n, base_dir=None: profile_path(n, base_dir=base_dir or tmp_path))
    monkeypatch.setattr("envault.env_sort.profile_exists", lambda n, base_dir=None: profile_path(n, base_dir=base_dir or tmp_path).exists())
    priv, pub = generate_keypair()
    save_keypair(priv, pub)
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    return tmp_path


def _write_profile(name: str, content: str, base: Path, pub: str) -> Path:
    ensure_profile_dir(base_dir=base)
    path = profile_path(name, base_dir=base)
    encrypt_file(content.encode(), path, pub)
    return path


def _read_keys(name: str, base: Path, priv: str) -> list[str]:
    path = profile_path(name, base_dir=base)
    raw = decrypt_file(path, priv)
    return [k for k, _ in parse_env_bytes(raw)]


def test_sort_already_sorted(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ALPHA=1\nBETA=2\nZETA=3\n", base, pub)
    result = sort_profile("prod", base_dir=base)
    assert not result.changed
    assert result.sorted_order == ["ALPHA", "BETA", "ZETA"]


def test_sort_reorders_keys(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ZETA=3\nALPHA=1\nBETA=2\n", base, pub)
    result = sort_profile("prod", base_dir=base)
    assert result.changed
    assert result.sorted_order == ["ALPHA", "BETA", "ZETA"]
    assert _read_keys("prod", base, priv) == ["ALPHA", "BETA", "ZETA"]


def test_sort_reverse(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ALPHA=1\nBETA=2\nZETA=3\n", base, pub)
    result = sort_profile("prod", base_dir=base, reverse=True)
    assert result.changed
    assert result.sorted_order == ["ZETA", "BETA", "ALPHA"]


def test_sort_dry_run_does_not_write(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ZETA=3\nALPHA=1\n", base, pub)
    sort_profile("prod", base_dir=base, dry_run=True)
    # File should still have original order
    assert _read_keys("prod", base, priv) == ["ZETA", "ALPHA"]


def test_sort_missing_profile_raises(base: Path):
    with pytest.raises(SortError, match="does not exist"):
        sort_profile("ghost", base_dir=base)


def test_sort_result_str_changed(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ZETA=3\nALPHA=1\n", base, pub)
    result = sort_profile("prod", base_dir=base)
    assert "sorted" in str(result).lower()


def test_sort_result_str_unchanged(base: Path, monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setattr("envault.env_sort.load_private_key", lambda: priv)
    monkeypatch.setattr("envault.env_sort.load_public_key", lambda: pub)
    _write_profile("prod", "ALPHA=1\nBETA=2\n", base, pub)
    result = sort_profile("prod", base_dir=base)
    assert "already sorted" in str(result)
