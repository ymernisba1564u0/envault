"""Tests for envault.history."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.history import (
    _profile_history_dir,
    list_snapshots,
    restore_snapshot,
    snapshot_profile,
)


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def enc_file(base: Path) -> Path:
    p = base / "profiles" / "dev.age"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"encrypted-content-v1")
    return p


def test_snapshot_creates_age_and_json(base: Path, enc_file: Path) -> None:
    snap = snapshot_profile("dev", enc_file, base=base)
    assert snap.exists()
    assert snap.suffix == ".age"
    meta_file = snap.with_suffix(".json")
    assert meta_file.exists()


def test_snapshot_meta_contains_expected_fields(base: Path, enc_file: Path) -> None:
    snap = snapshot_profile("dev", enc_file, base=base, note="initial")
    meta = json.loads(snap.with_suffix(".json").read_text())
    assert meta["profile"] == "dev"
    assert "timestamp" in meta
    assert meta["note"] == "initial"


def test_snapshot_copies_file_content(base: Path, enc_file: Path) -> None:
    snap = snapshot_profile("dev", enc_file, base=base)
    assert snap.read_bytes() == b"encrypted-content-v1"


def test_snapshot_missing_file_raises(base: Path, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        snapshot_profile("dev", tmp_path / "nonexistent.age", base=base)


def test_list_snapshots_empty_when_no_history(base: Path) -> None:
    assert list_snapshots("dev", base=base) == []


def test_list_snapshots_returns_sorted(base: Path, enc_file: Path) -> None:
    snapshot_profile("dev", enc_file, base=base, note="first")
    time.sleep(0.01)
    snapshot_profile("dev", enc_file, base=base, note="second")
    snaps = list_snapshots("dev", base=base)
    assert len(snaps) == 2
    assert snaps[0]["note"] == "first"
    assert snaps[1]["note"] == "second"


def test_list_snapshots_includes_snapshot_file_key(base: Path, enc_file: Path) -> None:
    snapshot_profile("dev", enc_file, base=base)
    snaps = list_snapshots("dev", base=base)
    assert "snapshot_file" in snaps[0]
    assert snaps[0]["snapshot_file"].endswith(".age")


def test_restore_overwrites_target(base: Path, enc_file: Path) -> None:
    snapshot_profile("dev", enc_file, base=base)
    ts = list_snapshots("dev", base=base)[0]["timestamp"]

    enc_file.write_bytes(b"encrypted-content-v2")
    restore_snapshot("dev", ts, enc_file, base=base)
    assert enc_file.read_bytes() == b"encrypted-content-v1"


def test_restore_missing_snapshot_raises(base: Path, enc_file: Path) -> None:
    with pytest.raises(FileNotFoundError):
        restore_snapshot("dev", "19990101T000000Z", enc_file, base=base)
