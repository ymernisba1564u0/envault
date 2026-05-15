"""Tests for envault.access (ACL management)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.access import (
    AccessError,
    grant_access,
    revoke_access,
    list_access,
    has_access,
    clear_access,
    _acl_file,
)
from envault.profiles import ensure_profile_dir


KEY_A = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq8lka"
KEY_B = "age1zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzrcz4"


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    ensure_profile_dir(tmp_path)
    # Create a dummy profile file so profile_exists returns True.
    (tmp_path / ".envault" / "profiles" / "dev.age").write_bytes(b"dummy")
    return tmp_path


def _make_profile(base: Path, name: str) -> None:
    (base / ".envault" / "profiles" / f"{name}.age").write_bytes(b"dummy")


def test_grant_creates_acl_file(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    assert _acl_file(base).exists()


def test_grant_returns_sorted_keys(base: Path) -> None:
    grant_access(base, "dev", KEY_B)
    result = grant_access(base, "dev", KEY_A)
    assert result == sorted([KEY_A, KEY_B])


def test_grant_deduplicates(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    result = grant_access(base, "dev", KEY_A)
    assert result.count(KEY_A) == 1


def test_grant_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(AccessError, match="does not exist"):
        grant_access(base, "ghost", KEY_A)


def test_revoke_removes_key(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    grant_access(base, "dev", KEY_B)
    remaining = revoke_access(base, "dev", KEY_A)
    assert KEY_A not in remaining
    assert KEY_B in remaining


def test_revoke_nonexistent_key_is_noop(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    remaining = revoke_access(base, "dev", KEY_B)
    assert KEY_A in remaining


def test_revoke_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(AccessError):
        revoke_access(base, "ghost", KEY_A)


def test_list_access_empty_when_no_acl(base: Path) -> None:
    assert list_access(base, "dev") == []


def test_has_access_false_before_grant(base: Path) -> None:
    assert not has_access(base, "dev", KEY_A)


def test_has_access_true_after_grant(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    assert has_access(base, "dev", KEY_A)


def test_clear_access_removes_profile_entry(base: Path) -> None:
    _make_profile(base, "prod")
    grant_access(base, "dev", KEY_A)
    grant_access(base, "prod", KEY_B)
    clear_access(base, "dev")
    assert list_access(base, "dev") == []
    assert list_access(base, "prod") == [KEY_B]


def test_acl_file_is_valid_json(base: Path) -> None:
    grant_access(base, "dev", KEY_A)
    data = json.loads(_acl_file(base).read_text())
    assert "dev" in data
