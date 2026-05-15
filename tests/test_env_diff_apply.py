"""Tests for envault.env_diff_apply (apply_patch)."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file, decrypt_file
from envault.export import parse_env_bytes
from envault.keystore import save_keypair, load_private_key, load_public_key
from envault.crypto import generate_keypair
from envault.profiles import profile_path, ensure_profile_dir
from envault.env_diff_apply import apply_patch, PatchError


@pytest.fixture()
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(tmp_path))
    monkeypatch.setattr("envault.keystore._key_dir", lambda: tmp_path / ".keys")
    pub, priv = generate_keypair()
    save_keypair(pub, priv)
    return tmp_path


def _write_profile(name: str, env: dict[str, str], base: Path) -> Path:
    ensure_profile_dir(base_dir=base)
    pub = load_public_key()
    content = "\n".join(f"{k}={v}" for k, v in env.items()).encode()
    path = profile_path(name, base_dir=base)
    encrypt_file(content, path, pub)
    return path


def _read_profile(name: str, base: Path) -> dict[str, str]:
    priv = load_private_key()
    path = profile_path(name, base_dir=base)
    raw = decrypt_file(path, priv)
    return dict(parse_env_bytes(raw))


def test_patch_add_new_key(base: Path) -> None:
    _write_profile("dev", {"FOO": "bar"}, base)
    result = apply_patch("dev", set_keys={"NEW_KEY": "hello"}, base_dir=base)
    assert "NEW_KEY" in result.added
    assert _read_profile("dev", base)["NEW_KEY"] == "hello"


def test_patch_update_existing_key(base: Path) -> None:
    _write_profile("dev", {"FOO": "old"}, base)
    result = apply_patch("dev", set_keys={"FOO": "new"}, base_dir=base)
    assert "FOO" in result.updated
    assert _read_profile("dev", base)["FOO"] == "new"


def test_patch_remove_key(base: Path) -> None:
    _write_profile("dev", {"FOO": "bar", "GONE": "bye"}, base)
    result = apply_patch("dev", remove_keys=["GONE"], base_dir=base)
    assert "GONE" in result.removed
    env = _read_profile("dev", base)
    assert "GONE" not in env
    assert env["FOO"] == "bar"


def test_patch_remove_nonexistent_key_is_noop(base: Path) -> None:
    _write_profile("dev", {"FOO": "bar"}, base)
    result = apply_patch("dev", remove_keys=["DOES_NOT_EXIST"], base_dir=base)
    assert result.removed == []
    assert not result.changed


def test_patch_combined_set_and_remove(base: Path) -> None:
    _write_profile("dev", {"A": "1", "B": "2"}, base)
    result = apply_patch("dev", set_keys={"C": "3"}, remove_keys=["A"], base_dir=base)
    env = _read_profile("dev", base)
    assert "A" not in env
    assert env["B"] == "2"
    assert env["C"] == "3"
    assert result.added == ["C"]
    assert result.removed == ["A"]


def test_patch_missing_profile_raises(base: Path) -> None:
    with pytest.raises(PatchError, match="does not exist"):
        apply_patch("ghost", set_keys={"X": "1"}, base_dir=base)


def test_patch_summary_no_changes(base: Path) -> None:
    _write_profile("dev", {"FOO": "bar"}, base)
    result = apply_patch("dev", set_keys={"FOO": "bar"}, base_dir=base)
    assert result.summary() == "no changes"
    assert not result.changed


def test_patch_summary_mixed(base: Path) -> None:
    _write_profile("dev", {"A": "1", "B": "2"}, base)
    result = apply_patch(
        "dev", set_keys={"B": "99", "C": "new"}, remove_keys=["A"], base_dir=base
    )
    summary = result.summary()
    assert "+1 added" in summary
    assert "~1 updated" in summary
    assert "-1 removed" in summary
