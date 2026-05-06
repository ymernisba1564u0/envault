"""Diff two versions of a decrypted .env profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envault.export import parse_env_bytes


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _parse(raw: bytes) -> Dict[str, str]:
    return dict(parse_env_bytes(raw))


def diff_envs(old_bytes: bytes, new_bytes: bytes) -> DiffResult:
    """Compare two raw .env byte strings and return a DiffResult."""
    old = _parse(old_bytes)
    new = _parse(new_bytes)

    result = DiffResult()

    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        if key not in old:
            result.added.append(key)
        elif key not in new:
            result.removed.append(key)
        elif old[key] != new[key]:
            result.changed.append((key, old[key], new[key]))
        else:
            result.unchanged.append(key)

    return result


def render_diff(result: DiffResult, mask_values: bool = True) -> str:
    """Render a DiffResult as a human-readable string."""
    lines: List[str] = []

    def _val(v: str) -> str:
        return "***" if mask_values else v

    for key in result.added:
        lines.append(f"+ {key}")
    for key in result.removed:
        lines.append(f"- {key}")
    for key, old, new in result.changed:
        lines.append(f"~ {key}: {_val(old)} -> {_val(new)}")

    if not lines:
        lines.append("(no changes)")

    return "\n".join(lines)
