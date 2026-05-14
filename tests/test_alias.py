"""Tests for envault.alias."""

from __future__ import annotations

import pytest

from envault.alias import (
    AliasError,
    _alias_file,
    add_alias,
    list_aliases,
    remove_alias,
    resolve_alias,
)
from envault.profiles import _profile_dir


@pytest.fixture()
def base(tmp_path):
    """Return a tmp_path with a dummy profile pre-created."""
    profile_dir = _profile_dir(tmp_path)
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "production.age").write_bytes(b"fake")
    (profile_dir / "staging.age").write_bytes(b"fake")
    return tmp_path


def test_add_alias_creates_file(base):
    add_alias("prod", "production", base)
    assert _alias_file(base).exists()


def test_add_alias_maps_correctly(base):
    add_alias("prod", "production", base)
    result = list_aliases(base)
    assert result == [{"alias": "prod", "profile": "production"}]


def test_add_alias_deduplicates_raises(base):
    add_alias("prod", "production", base)
    with pytest.raises(AliasError, match="already maps"):
        add_alias("prod", "staging", base)


def test_add_alias_missing_profile_raises(base):
    with pytest.raises(AliasError, match="does not exist"):
        add_alias("ghost", "nonexistent", base)


def test_remove_alias_deletes_entry(base):
    add_alias("prod", "production", base)
    remove_alias("prod", base)
    assert list_aliases(base) == []


def test_remove_alias_missing_raises(base):
    with pytest.raises(AliasError, match="does not exist"):
        remove_alias("nope", base)


def test_resolve_alias_returns_profile(base):
    add_alias("prod", "production", base)
    assert resolve_alias("prod", base) == "production"


def test_resolve_alias_identity_for_unknown(base):
    assert resolve_alias("staging", base) == "staging"


def test_list_aliases_sorted(base):
    add_alias("zz", "staging", base)
    add_alias("aa", "production", base)
    names = [e["alias"] for e in list_aliases(base)]
    assert names == ["aa", "zz"]


def test_list_aliases_empty_when_no_file(base):
    assert list_aliases(base) == []


def test_multiple_aliases_independent(base):
    add_alias("prod", "production", base)
    add_alias("stage", "staging", base)
    assert len(list_aliases(base)) == 2
