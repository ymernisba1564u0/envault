"""Profile tagging — attach/remove/query string tags on encrypted profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.profiles import profile_path, profile_exists, _profile_dir


def _tag_file(profile: str, base: Path | None = None) -> Path:
    """Return the path to the JSON tag file for *profile*."""
    root = base if base is not None else _profile_dir()
    return root / f"{profile}.tags.json"


def _load_tags(profile: str, base: Path | None = None) -> List[str]:
    tf = _tag_file(profile, base)
    if not tf.exists():
        return []
    try:
        data = json.loads(tf.read_text())
        return sorted(set(str(t) for t in data)) if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_tags(profile: str, tags: List[str], base: Path | None = None) -> None:
    tf = _tag_file(profile, base)
    tf.parent.mkdir(parents=True, exist_ok=True)
    tf.write_text(json.dumps(sorted(set(tags))))


def add_tag(profile: str, tag: str, base: Path | None = None) -> List[str]:
    """Add *tag* to *profile*. Returns the updated tag list."""
    if not profile_exists(profile, base):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    tag = tag.strip()
    if not tag:
        raise ValueError("Tag must not be empty.")
    tags = _load_tags(profile, base)
    if tag not in tags:
        tags.append(tag)
    _save_tags(profile, tags, base)
    return sorted(tags)


def remove_tag(profile: str, tag: str, base: Path | None = None) -> List[str]:
    """Remove *tag* from *profile*. Returns the updated tag list."""
    tags = _load_tags(profile, base)
    tags = [t for t in tags if t != tag]
    _save_tags(profile, tags, base)
    return sorted(tags)


def list_tags(profile: str, base: Path | None = None) -> List[str]:
    """Return all tags for *profile*, sorted alphabetically."""
    return _load_tags(profile, base)


def profiles_with_tag(tag: str, base: Path | None = None) -> List[str]:
    """Return sorted list of profile names that carry *tag*."""
    root = base if base is not None else _profile_dir()
    if not root.exists():
        return []
    matches = []
    for tf in root.glob("*.tags.json"):
        profile = tf.name.replace(".tags.json", "")
        if tag in _load_tags(profile, base):
            matches.append(profile)
    return sorted(matches)
