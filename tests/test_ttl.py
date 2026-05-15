"""Tests for envault.ttl — TTL management for profiles."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envault.ttl import (
    clear_ttl,
    get_ttl,
    is_expired,
    list_ttls,
    set_ttl,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


def _make_profile(base: Path, name: str) -> None:
    (base / f"{name}.age").write_bytes(b"fake-encrypted-data")


# ---------------------------------------------------------------------------
# set_ttl
# ---------------------------------------------------------------------------

def test_set_ttl_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        set_ttl("ghost", 60, base_dir=base)


def test_set_ttl_raises_for_non_positive_seconds(base: Path) -> None:
    _make_profile(base, "dev")
    with pytest.raises(ValueError, match="positive"):
        set_ttl("dev", 0, base_dir=base)


def test_set_ttl_returns_future_datetime(base: Path) -> None:
    _make_profile(base, "dev")
    before = datetime.now(timezone.utc)
    expiry = set_ttl("dev", 300, base_dir=base)
    after = datetime.now(timezone.utc)
    assert expiry > before
    assert expiry <= after + timedelta(seconds=300)


def test_set_ttl_persists_to_disk(base: Path) -> None:
    _make_profile(base, "dev")
    set_ttl("dev", 120, base_dir=base)
    loaded = get_ttl("dev", base_dir=base)
    assert loaded is not None
    assert isinstance(loaded, datetime)


# ---------------------------------------------------------------------------
# get_ttl
# ---------------------------------------------------------------------------

def test_get_ttl_returns_none_when_absent(base: Path) -> None:
    assert get_ttl("no-such", base_dir=base) is None


def test_get_ttl_returns_correct_datetime(base: Path) -> None:
    _make_profile(base, "prod")
    expiry = set_ttl("prod", 3600, base_dir=base)
    assert get_ttl("prod", base_dir=base) == expiry


# ---------------------------------------------------------------------------
# clear_ttl
# ---------------------------------------------------------------------------

def test_clear_ttl_returns_false_when_absent(base: Path) -> None:
    assert clear_ttl("no-such", base_dir=base) is False


def test_clear_ttl_returns_true_and_removes_entry(base: Path) -> None:
    _make_profile(base, "staging")
    set_ttl("staging", 60, base_dir=base)
    assert clear_ttl("staging", base_dir=base) is True
    assert get_ttl("staging", base_dir=base) is None


# ---------------------------------------------------------------------------
# is_expired
# ---------------------------------------------------------------------------

def test_is_expired_false_when_no_ttl(base: Path) -> None:
    assert is_expired("any", base_dir=base) is False


def test_is_expired_false_for_future_expiry(base: Path) -> None:
    _make_profile(base, "dev")
    set_ttl("dev", 9999, base_dir=base)
    assert is_expired("dev", base_dir=base) is False


def test_is_expired_true_for_past_expiry(base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_profile(base, "old")
    set_ttl("old", 1, base_dir=base)
    # Force "now" to be far in the future.
    future = datetime.now(timezone.utc) + timedelta(days=365)
    import envault.ttl as ttl_mod
    monkeypatch.setattr(ttl_mod, "datetime",
        type("_DT", (), {"now": staticmethod(lambda tz=None: future),
                         "fromisoformat": datetime.fromisoformat})())
    assert is_expired("old", base_dir=base) is True


# ---------------------------------------------------------------------------
# list_ttls
# ---------------------------------------------------------------------------

def test_list_ttls_empty_when_none_set(base: Path) -> None:
    assert list_ttls(base_dir=base) == {}


def test_list_ttls_returns_all_entries(base: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        _make_profile(base, name)
        set_ttl(name, 60, base_dir=base)
    result = list_ttls(base_dir=base)
    assert set(result.keys()) == {"alpha", "beta", "gamma"}
    assert list(result.keys()) == sorted(result.keys())
