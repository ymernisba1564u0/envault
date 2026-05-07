"""Tests for envault.tag — profile tagging feature."""

import pytest
from pathlib import Path

from envault.tag import add_tag, remove_tag, list_tags, profiles_with_tag, _tag_file


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    """A temp directory that acts as the profile root."""
    return tmp_path


def _make_profile(base: Path, name: str) -> None:
    """Create a minimal .age file so profile_exists() returns True."""
    (base / f"{name}.age").write_bytes(b"fake-encrypted-data")


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

def test_add_tag_creates_tag_file(base):
    _make_profile(base, "dev")
    add_tag("dev", "production", base)
    assert _tag_file("dev", base).exists()


def test_add_tag_returns_sorted_list(base):
    _make_profile(base, "dev")
    add_tag("dev", "zebra", base)
    result = add_tag("dev", "alpha", base)
    assert result == ["alpha", "zebra"]


def test_add_tag_deduplicates(base):
    _make_profile(base, "dev")
    add_tag("dev", "ci", base)
    result = add_tag("dev", "ci", base)
    assert result.count("ci") == 1


def test_add_tag_raises_for_missing_profile(base):
    with pytest.raises(FileNotFoundError, match="ghost"):
        add_tag("ghost", "ci", base)


def test_add_tag_raises_for_empty_tag(base):
    _make_profile(base, "dev")
    with pytest.raises(ValueError):
        add_tag("dev", "  ", base)


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

def test_remove_tag_removes_existing(base):
    _make_profile(base, "dev")
    add_tag("dev", "ci", base)
    add_tag("dev", "staging", base)
    result = remove_tag("dev", "ci", base)
    assert "ci" not in result
    assert "staging" in result


def test_remove_tag_noop_when_absent(base):
    _make_profile(base, "dev")
    add_tag("dev", "ci", base)
    result = remove_tag("dev", "nonexistent", base)
    assert result == ["ci"]


# ---------------------------------------------------------------------------
# list_tags
# ---------------------------------------------------------------------------

def test_list_tags_empty_when_no_file(base):
    _make_profile(base, "dev")
    assert list_tags("dev", base) == []


def test_list_tags_returns_sorted(base):
    _make_profile(base, "dev")
    add_tag("dev", "z", base)
    add_tag("dev", "a", base)
    add_tag("dev", "m", base)
    assert list_tags("dev", base) == ["a", "m", "z"]


# ---------------------------------------------------------------------------
# profiles_with_tag
# ---------------------------------------------------------------------------

def test_profiles_with_tag_empty_when_no_dir(base):
    absent = base / "no_such_dir"
    assert profiles_with_tag("ci", absent) == []


def test_profiles_with_tag_finds_matching(base):
    for name in ("dev", "staging", "prod"):
        _make_profile(base, name)
    add_tag("dev", "ci", base)
    add_tag("staging", "ci", base)
    add_tag("prod", "production", base)
    assert profiles_with_tag("ci", base) == ["dev", "staging"]


def test_profiles_with_tag_returns_sorted(base):
    for name in ("z_profile", "a_profile", "m_profile"):
        _make_profile(base, name)
        add_tag(name, "shared", base)
    assert profiles_with_tag("shared", base) == ["a_profile", "m_profile", "z_profile"]
