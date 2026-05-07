"""Tests for envault.env_merge."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.crypto import encrypt_file, generate_keypair
from envault.env_merge import MergeResult, merge_profiles, render_merged
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def setup_keys(base: Path):
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=str(base))
    return priv, pub


def _write_profile(name: str, content: str, pub: str, base: Path) -> None:
    ensure_profile_dir(name, base_dir=str(base))
    path = profile_path(name, base_dir=str(base))
    encrypt_file(content.encode(), str(path), pub)


def test_merge_single_profile(base, setup_keys):
    _, pub = setup_keys
    _write_profile("base", "FOO=1\nBAR=2\n", pub, base)

    result = merge_profiles(["base"], base_dir=str(base))
    assert result.ok
    assert result.merged == {"FOO": "1", "BAR": "2"}
    assert result.sources["FOO"] == "base"


def test_merge_last_wins_by_default(base, setup_keys):
    _, pub = setup_keys
    _write_profile("base", "FOO=1\nSHARED=base_val\n", pub, base)
    _write_profile("override", "SHARED=override_val\nEXTRA=3\n", pub, base)

    result = merge_profiles(["base", "override"], base_dir=str(base))
    assert result.ok
    assert result.merged["SHARED"] == "override_val"
    assert result.sources["SHARED"] == "override"
    assert result.merged["FOO"] == "1"
    assert result.merged["EXTRA"] == "3"


def test_merge_first_wins_records_conflicts(base, setup_keys):
    _, pub = setup_keys
    _write_profile("a", "KEY=from_a\n", pub, base)
    _write_profile("b", "KEY=from_b\n", pub, base)

    result = merge_profiles(["a", "b"], base_dir=str(base), last_wins=False)
    assert not result.ok
    assert len(result.conflicts) == 1
    key, first, second = result.conflicts[0]
    assert key == "KEY"
    assert first == "a"
    assert second == "b"
    assert result.merged["KEY"] == "from_a"


def test_merge_missing_profile_raises(base, setup_keys):
    with pytest.raises(FileNotFoundError, match="ghost"):
        merge_profiles(["ghost"], base_dir=str(base))


def test_render_merged_export_format(base, setup_keys):
    _, pub = setup_keys
    _write_profile("env", "Z=last\nA=first\n", pub, base)

    result = merge_profiles(["env"], base_dir=str(base))
    rendered = render_merged(result, fmt="export")
    lines = rendered.splitlines()
    assert all(line.startswith("export ") for line in lines)
    assert "export A=first" in lines
    assert "export Z=last" in lines


def test_render_merged_dotenv_format(base, setup_keys):
    _, pub = setup_keys
    _write_profile("env", "X=hello\n", pub, base)

    result = merge_profiles(["env"], base_dir=str(base))
    rendered = render_merged(result, fmt="dotenv")
    assert rendered == "X=hello"
