"""Tests for envault.note."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.note import set_note, get_note, clear_note, list_notes
from envault.profiles import ensure_profile_dir
from envault.crypto import generate_keypair, encrypt_data
from envault.keystore import save_keypair


@pytest.fixture()
def base(tmp_path: Path) -> Path:
    pub, priv = generate_keypair()
    save_keypair(pub, priv, tmp_path)
    ensure_profile_dir(tmp_path)
    return tmp_path


def _make_profile(base: Path, name: str) -> None:
    """Create a minimal encrypted profile so profile_exists returns True."""
    from envault.profiles import profile_path
    from envault.keystore import load_public_key
    pub = load_public_key(base)
    ciphertext = encrypt_data(b"KEY=value", pub)
    profile_path(base, name).write_bytes(ciphertext)


def test_set_note_raises_for_missing_profile(base: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        set_note(base, "ghost", "hello")


def test_set_note_creates_file(base: Path) -> None:
    _make_profile(base, "dev")
    set_note(base, "dev", "staging creds")
    note_file = base / ".envault" / "notes" / "dev.json"
    assert note_file.exists()


def test_get_note_returns_none_when_absent(base: Path) -> None:
    _make_profile(base, "dev")
    assert get_note(base, "dev") is None


def test_get_note_returns_text(base: Path) -> None:
    _make_profile(base, "dev")
    set_note(base, "dev", "my note")
    result = get_note(base, "dev")
    assert result is not None
    assert result["text"] == "my note"
    assert result["profile"] == "dev"
    assert "updated_at" in result


def test_set_note_overwrites_existing(base: Path) -> None:
    _make_profile(base, "dev")
    set_note(base, "dev", "first")
    set_note(base, "dev", "second")
    assert get_note(base, "dev")["text"] == "second"


def test_clear_note_returns_false_when_absent(base: Path) -> None:
    _make_profile(base, "dev")
    assert clear_note(base, "dev") is False


def test_clear_note_removes_file(base: Path) -> None:
    _make_profile(base, "dev")
    set_note(base, "dev", "to be removed")
    assert clear_note(base, "dev") is True
    assert get_note(base, "dev") is None


def test_list_notes_empty_when_no_notes_dir(base: Path) -> None:
    assert list_notes(base) == []


def test_list_notes_returns_all_notes(base: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        _make_profile(base, name)
        set_note(base, name, f"note for {name}")
    notes = list_notes(base)
    assert len(notes) == 3
    assert [n["profile"] for n in notes] == ["alpha", "beta", "gamma"]


def test_list_notes_sorted_by_profile_name(base: Path) -> None:
    for name in ("z_profile", "a_profile", "m_profile"):
        _make_profile(base, name)
        set_note(base, name, "x")
    profiles = [n["profile"] for n in list_notes(base)]
    assert profiles == sorted(profiles)
