"""Tests for envault.compare."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.compare import CompareResult, compare_profiles, render_compare
from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVAULT_BASE_DIR", str(base))
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=base)
    return priv, pub


def _write_profile(name: str, env: dict, base: Path, pub: str) -> None:
    ensure_profile_dir(base_dir=base)
    raw = "\n".join(f"{k}={v}" for k, v in env.items()).encode()
    path = profile_path(name, base_dir=base)
    encrypt_file(raw, path, pub)


def test_compare_identical_profiles(base, setup_keys):
    _, pub = setup_keys
    env = {"KEY": "val", "PORT": "8080"}
    _write_profile("a", env, base, pub)
    _write_profile("b", env, base, pub)

    result = compare_profiles("a", "b", base_dir=base)

    assert result.ok
    assert result.in_both_same == ["KEY", "PORT"]
    assert result.only_in_left == []
    assert result.only_in_right == []
    assert result.in_both_different == []


def test_compare_disjoint_profiles(base, setup_keys):
    _, pub = setup_keys
    _write_profile("a", {"ALPHA": "1"}, base, pub)
    _write_profile("b", {"BETA": "2"}, base, pub)

    result = compare_profiles("a", "b", base_dir=base)

    assert not result.ok
    assert result.only_in_left == ["ALPHA"]
    assert result.only_in_right == ["BETA"]
    assert result.in_both_same == []
    assert result.in_both_different == []


def test_compare_different_values(base, setup_keys):
    _, pub = setup_keys
    _write_profile("a", {"KEY": "old"}, base, pub)
    _write_profile("b", {"KEY": "new"}, base, pub)

    result = compare_profiles("a", "b", base_dir=base)

    assert not result.ok
    assert result.in_both_different == ["KEY"]
    assert result.in_both_same == []


def test_coverage_full_overlap(base, setup_keys):
    _, pub = setup_keys
    env = {"A": "1", "B": "2"}
    _write_profile("x", env, base, pub)
    _write_profile("y", env, base, pub)

    result = compare_profiles("x", "y", base_dir=base)
    assert result.coverage() == pytest.approx(1.0)


def test_coverage_no_overlap(base, setup_keys):
    _, pub = setup_keys
    _write_profile("x", {"A": "1"}, base, pub)
    _write_profile("y", {"B": "2"}, base, pub)

    result = compare_profiles("x", "y", base_dir=base)
    assert result.coverage() == pytest.approx(0.0)


def test_missing_profile_raises(base, setup_keys):
    _, pub = setup_keys
    _write_profile("exists", {"K": "v"}, base, pub)

    with pytest.raises(FileNotFoundError):
        compare_profiles("exists", "ghost", base_dir=base)


def test_render_compare_ok(base, setup_keys):
    _, pub = setup_keys
    env = {"DB": "postgres"}
    _write_profile("p", env, base, pub)
    _write_profile("q", env, base, pub)

    result = compare_profiles("p", "q", base_dir=base)
    output = render_compare(result)

    assert "Comparing" in output
    assert "100%" in output
    assert "identical" in output.lower()


def test_render_compare_differences(base, setup_keys):
    _, pub = setup_keys
    _write_profile("p", {"A": "1", "B": "old"}, base, pub)
    _write_profile("q", {"B": "new", "C": "3"}, base, pub)

    result = compare_profiles("p", "q", base_dir=base)
    output = render_compare(result)

    assert "Only in 'p'" in output
    assert "Only in 'q'" in output
    assert "Different values" in output
