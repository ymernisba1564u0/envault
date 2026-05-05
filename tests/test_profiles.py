"""Tests for envault.profiles"""

import pytest
from pathlib import Path
from envault.profiles import (
    profile_path,
    list_profiles,
    profile_exists,
    ensure_profile_dir,
    delete_profile,
    resolve_profile,
    DEFAULT_PROFILE,
)


@pytest.fixture
def base(tmp_path):
    return str(tmp_path)


def test_profile_path_structure(base):
    p = profile_path("dev", base)
    assert p.name == "dev.env.age"
    assert ".envault/profiles" in str(p)


def test_list_profiles_empty_when_no_dir(base):
    assert list_profiles(base) == []


def test_list_profiles_returns_sorted_names(base):
    ensure_profile_dir(base)
    for name in ("staging", "dev", "prod"):
        profile_path(name, base).touch()
    assert list_profiles(base) == ["dev", "prod", "staging"]


def test_profile_exists_false_before_creation(base):
    assert not profile_exists("dev", base)


def test_profile_exists_true_after_touch(base):
    ensure_profile_dir(base)
    profile_path("dev", base).touch()
    assert profile_exists("dev", base)


def test_ensure_profile_dir_creates_directory(base):
    d = ensure_profile_dir(base)
    assert d.exists()
    assert d.is_dir()


def test_delete_profile_removes_file(base):
    ensure_profile_dir(base)
    profile_path("dev", base).touch()
    assert delete_profile("dev", base) is True
    assert not profile_exists("dev", base)


def test_delete_profile_returns_false_if_missing(base):
    assert delete_profile("nonexistent", base) is False


def test_resolve_profile_uses_argument():
    assert resolve_profile("staging") == "staging"


def test_resolve_profile_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("ENVAULT_PROFILE", raising=False)
    assert resolve_profile(None) == DEFAULT_PROFILE


def test_resolve_profile_uses_env_var(monkeypatch):
    monkeypatch.setenv("ENVAULT_PROFILE", "prod")
    assert resolve_profile(None) == "prod"
