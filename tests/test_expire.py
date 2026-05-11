"""Tests for envault.expire — profile expiry management."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.expire import (
    clear_expiry,
    get_expiry,
    is_expired,
    list_expiring,
    set_expiry,
    _expiry_file,
)
from envault.profiles import profile_path


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def _make_profile(base: Path):
    """Helper: create a dummy encrypted profile file."""
    def _inner(name: str) -> Path:
        p = profile_path(name, base)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"dummy")
        return p
    return _inner


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_set_expiry_creates_expiry_file(_make_profile, base):
    _make_profile("prod")
    set_expiry("prod", _future(), base)
    assert _expiry_file(base).exists()


def test_set_expiry_fails_for_missing_profile(base):
    with pytest.raises(FileNotFoundError, match="prod"):
        set_expiry("prod", _future(), base)


def test_get_expiry_returns_none_when_not_set(_make_profile, base):
    _make_profile("staging")
    assert get_expiry("staging", base) is None


def test_get_expiry_returns_datetime(_make_profile, base):
    _make_profile("staging")
    exp = _future()
    set_expiry("staging", exp, base)
    result = get_expiry("staging", base)
    assert isinstance(result, datetime)
    assert abs((result - exp).total_seconds()) < 1


def test_is_expired_false_for_future(_make_profile, base):
    _make_profile("dev")
    set_expiry("dev", _future(), base)
    assert is_expired("dev", base) is False


def test_is_expired_true_for_past(_make_profile, base):
    _make_profile("dev")
    set_expiry("dev", _past(), base)
    assert is_expired("dev", base) is True


def test_is_expired_false_when_no_expiry_set(_make_profile, base):
    _make_profile("dev")
    assert is_expired("dev", base) is False


def test_clear_expiry_removes_entry(_make_profile, base):
    _make_profile("prod")
    set_expiry("prod", _future(), base)
    clear_expiry("prod", base)
    assert get_expiry("prod", base) is None


def test_clear_expiry_noop_when_not_set(base):
    # Should not raise even if profile has no expiry entry
    clear_expiry("ghost", base)


def test_list_expiring_sorted(_make_profile, base):
    for name in ("a", "b", "c"):
        _make_profile(name)
    set_expiry("c", _future(7200), base)
    set_expiry("a", _future(3600), base)
    set_expiry("b", _future(5400), base)
    result = list_expiring(base)
    names = [r[0] for r in result]
    assert names == ["a", "b", "c"]


def test_list_expiring_empty_when_no_file(base):
    assert list_expiring(base) == []
