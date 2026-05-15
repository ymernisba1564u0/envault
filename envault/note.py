"""Per-profile notes: attach, read, and clear plaintext notes for a profile."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from envault.profiles import profile_path, profile_exists


def _note_file(base: Path, profile: str) -> Path:
    return base / ".envault" / "notes" / f"{profile}.json"


def _load_note(note_file: Path) -> dict:
    if not note_file.exists():
        return {}
    return json.loads(note_file.read_text())


def _save_note(note_file: Path, data: dict) -> None:
    note_file.parent.mkdir(parents=True, exist_ok=True)
    note_file.write_text(json.dumps(data, indent=2))


def set_note(base: Path, profile: str, text: str) -> None:
    """Attach or replace a note for *profile*."""
    if not profile_exists(base, profile):
        raise ValueError(f"Profile '{profile}' does not exist.")
    data = {
        "profile": profile,
        "text": text,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_note(_note_file(base, profile), data)


def get_note(base: Path, profile: str) -> Optional[dict]:
    """Return the note dict for *profile*, or None if no note exists."""
    data = _load_note(_note_file(base, profile))
    return data if data else None


def clear_note(base: Path, profile: str) -> bool:
    """Delete the note for *profile*. Returns True if a note was removed."""
    nf = _note_file(base, profile)
    if nf.exists():
        nf.unlink()
        return True
    return False


def list_notes(base: Path) -> list[dict]:
    """Return all notes, sorted by profile name."""
    notes_dir = base / ".envault" / "notes"
    if not notes_dir.exists():
        return []
    results = []
    for f in sorted(notes_dir.glob("*.json")):
        data = json.loads(f.read_text())
        if data:
            results.append(data)
    return results
