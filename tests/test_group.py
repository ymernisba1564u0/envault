"""Tests for envault.group and envault.cli_group."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.group import (
    GroupError,
    add_to_group,
    group_members,
    list_groups,
    profile_groups,
    remove_from_group,
    _group_file,
)
from envault.cli_group import group_cmd


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base(tmp_path: Path) -> Path:
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    return profiles


def _make_profile(base: Path, name: str) -> None:
    (base / f"{name}.age").write_bytes(b"fake")


# ---------------------------------------------------------------------------
# Unit tests — group module
# ---------------------------------------------------------------------------

def test_add_creates_group_file(base):
    _make_profile(base, "prod")
    add_to_group("production", "prod", base)
    assert _group_file(base).exists()


def test_add_returns_sorted_members(base):
    _make_profile(base, "prod")
    _make_profile(base, "alpha")
    add_to_group("g1", "prod", base)
    members = add_to_group("g1", "alpha", base)
    assert members == ["alpha", "prod"]


def test_add_deduplicates(base):
    _make_profile(base, "prod")
    add_to_group("g1", "prod", base)
    members = add_to_group("g1", "prod", base)
    assert members.count("prod") == 1


def test_add_raises_for_missing_profile(base):
    with pytest.raises(GroupError, match="does not exist"):
        add_to_group("g1", "ghost", base)


def test_remove_from_group(base):
    _make_profile(base, "prod")
    _make_profile(base, "staging")
    add_to_group("g1", "prod", base)
    add_to_group("g1", "staging", base)
    remaining = remove_from_group("g1", "prod", base)
    assert "prod" not in remaining
    assert "staging" in remaining


def test_remove_deletes_empty_group(base):
    _make_profile(base, "prod")
    add_to_group("g1", "prod", base)
    remove_from_group("g1", "prod", base)
    assert "g1" not in list_groups(base)


def test_remove_raises_if_not_member(base):
    _make_profile(base, "prod")
    add_to_group("g1", "prod", base)
    with pytest.raises(GroupError, match="not in group"):
        remove_from_group("g1", "ghost", base)


def test_list_groups_empty(base):
    assert list_groups(base) == []


def test_list_groups_sorted(base):
    for name in ["z", "a", "m"]:
        _make_profile(base, name)
        add_to_group(name, name, base)
    assert list_groups(base) == ["a", "m", "z"]


def test_group_members_unknown_group(base):
    assert group_members("nonexistent", base) == []


def test_profile_groups(base):
    _make_profile(base, "prod")
    add_to_group("g1", "prod", base)
    add_to_group("g2", "prod", base)
    assert profile_groups("prod", base) == ["g1", "g2"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    monkeypatch.setattr("envault.group._profile_dir", lambda: profiles)
    monkeypatch.setattr("envault.profiles._profile_dir", lambda: profiles)
    return profiles


def test_cli_add_success(runner, isolated):
    (isolated / "dev.age").write_bytes(b"x")
    result = runner.invoke(group_cmd, ["add", "mygroup", "dev"])
    assert result.exit_code == 0
    assert "Added" in result.output


def test_cli_add_fails_missing_profile(runner, isolated):
    result = runner.invoke(group_cmd, ["add", "mygroup", "ghost"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_list_no_groups(runner, isolated):
    result = runner.invoke(group_cmd, ["list"])
    assert result.exit_code == 0
    assert "No groups" in result.output


def test_cli_members_empty(runner, isolated):
    result = runner.invoke(group_cmd, ["members", "unknown"])
    assert result.exit_code == 0
    assert "no members" in result.output
