"""Merge multiple .env profiles into a single resolved environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envault.crypto import decrypt_file
from envault.export import parse_env_bytes
from envault.keystore import load_private_key
from envault.profiles import profile_path, profile_exists


@dataclass
class MergeResult:
    """Result of merging one or more profiles."""

    merged: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # key -> profile name
    conflicts: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, first, second)

    @property
    def ok(self) -> bool:
        return len(self.conflicts) == 0


def merge_profiles(
    profile_names: List[str],
    base_dir: str | None = None,
    *,
    last_wins: bool = True,
) -> MergeResult:
    """Decrypt and merge multiple profiles in order.

    Parameters
    ----------
    profile_names:
        Ordered list of profile names to merge. Later profiles take
        precedence when *last_wins* is True (the default).
    base_dir:
        Optional override for the envault base directory.
    last_wins:
        When True, duplicate keys are overwritten by later profiles.
        When False, the first definition wins and conflicts are recorded.
    """
    private_key = load_private_key(base_dir=base_dir)
    result = MergeResult()

    for name in profile_names:
        if not profile_exists(name, base_dir=base_dir):
            raise FileNotFoundError(f"Profile '{name}' does not exist.")

        path = profile_path(name, base_dir=base_dir)
        raw = decrypt_file(str(path), private_key)
        pairs = parse_env_bytes(raw)

        for key, value in pairs.items():
            if key in result.merged:
                if last_wins:
                    result.merged[key] = value
                    result.sources[key] = name
                else:
                    result.conflicts.append((key, result.sources[key], name))
            else:
                result.merged[key] = value
                result.sources[key] = name

    return result


def render_merged(result: MergeResult, fmt: str = "export") -> str:
    """Render a MergeResult to a string.

    Parameters
    ----------
    fmt:
        ``'export'`` for ``export KEY=VALUE`` lines,
        ``'dotenv'`` for plain ``KEY=VALUE`` lines.
    """
    lines: List[str] = []
    for key, value in sorted(result.merged.items()):
        if fmt == "export":
            lines.append(f"export {key}={value}")
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines)
