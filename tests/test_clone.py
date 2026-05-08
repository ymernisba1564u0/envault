"""Tests for envault.clone."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.clone import clone_profile, CloneError
from envault.profiles import profile_path, profile_exists
from envault.tag import add_tag, list_tags


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    return tmp_path


def _write_profile(name: str, base: Path, content: bytes = b"AGE-SECRET") -> Path:
    path = profile_path(name, base_dir=base)
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_clone_creates_destination_file(base: Path) -> None:
    _write_profile("prod", base, b"encrypted-bytes")
    dst = clone_profile("prod", "staging", base_dir=base)
    assert dst.exists()
    assert dst.read_bytes() == b"encrypted-bytes"


def test_clone_returns_destination_path(base: Path) -> None:
    _write_profile("prod", base)
    result = clone_profile("prod", "staging", base_dir=base)
    assert result == profile_path("staging", base_dir=base)


def test_clone_source_still_exists(base: Path) -> None:
    _write_profile("prod", base)
    clone_profile("prod", "staging", base_dir=base)
    assert profile_exists("prod", base_dir=base)


def test_clone_copies_tags_by_default(base: Path) -> None:
    _write_profile("prod", base)
    add_tag("prod", "live", base_dir=base)
    add_tag("prod", "reviewed", base_dir=base)
    clone_profile("prod", "staging", base_dir=base)
    assert list_tags("staging", base_dir=base) == ["live", "reviewed"]


def test_clone_skips_tags_when_disabled(base: Path) -> None:
    _write_profile("prod", base)
    add_tag("prod", "live", base_dir=base)
    clone_profile("prod", "staging", base_dir=base, copy_tags=False)
    assert list_tags("staging", base_dir=base) == []


def test_clone_no_tags_on_source_is_fine(base: Path) -> None:
    _write_profile("prod", base)
    # No tags added — should not raise
    clone_profile("prod", "staging", base_dir=base)
    assert list_tags("staging", base_dir=base) == []


# ---------------------------------------------------------------------------
# Error-path tests
# ---------------------------------------------------------------------------

def test_clone_raises_if_source_missing(base: Path) -> None:
    with pytest.raises(CloneError, match="Source profile 'ghost' does not exist"):
        clone_profile("ghost", "copy", base_dir=base)


def test_clone_raises_if_destination_exists(base: Path) -> None:
    _write_profile("prod", base)
    _write_profile("staging", base)
    with pytest.raises(CloneError, match="Destination profile 'staging' already exists"):
        clone_profile("prod", "staging", base_dir=base)


def test_clone_error_str(base: Path) -> None:
    err = CloneError("something went wrong")
    assert str(err) == "something went wrong"
