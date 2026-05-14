"""Compare two profiles side-by-side and report key coverage."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from envault.crypto import decrypt_file
from envault.export import parse_env_bytes
from envault.keystore import load_private_key
from envault.profiles import profile_path


@dataclass
class CompareResult:
    left: str
    right: str
    only_in_left: List[str] = field(default_factory=list)
    only_in_right: List[str] = field(default_factory=list)
    in_both_same: List[str] = field(default_factory=list)
    in_both_different: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when both profiles share identical keys and values."""
        return not self.only_in_left and not self.only_in_right and not self.in_both_different

    def coverage(self) -> float:
        """Fraction of keys present in both profiles (Jaccard index)."""
        total = (
            len(self.only_in_left)
            + len(self.only_in_right)
            + len(self.in_both_same)
            + len(self.in_both_different)
        )
        if total == 0:
            return 1.0
        shared = len(self.in_both_same) + len(self.in_both_different)
        return shared / total


def _load_vars(profile: str, base_dir: Path | None = None) -> Dict[str, str]:
    path = profile_path(profile, base_dir=base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile}")
    private_key = load_private_key()
    raw = decrypt_file(path, private_key)
    return parse_env_bytes(raw)


def compare_profiles(
    left: str,
    right: str,
    base_dir: Path | None = None,
) -> CompareResult:
    """Decrypt and compare two named profiles."""
    left_vars = _load_vars(left, base_dir=base_dir)
    right_vars = _load_vars(right, base_dir=base_dir)

    left_keys: Set[str] = set(left_vars)
    right_keys: Set[str] = set(right_vars)

    result = CompareResult(left=left, right=right)
    result.only_in_left = sorted(left_keys - right_keys)
    result.only_in_right = sorted(right_keys - left_keys)

    for key in sorted(left_keys & right_keys):
        if left_vars[key] == right_vars[key]:
            result.in_both_same.append(key)
        else:
            result.in_both_different.append(key)

    return result


def render_compare(result: CompareResult) -> str:
    """Return a human-readable comparison report."""
    lines: List[str] = [
        f"Comparing '{result.left}' vs '{result.right}'",
        f"Coverage: {result.coverage():.0%}",
        "",
    ]
    if result.only_in_left:
        lines.append(f"  Only in '{result.left}':")
        lines.extend(f"    - {k}" for k in result.only_in_left)
    if result.only_in_right:
        lines.append(f"  Only in '{result.right}':")
        lines.extend(f"    + {k}" for k in result.only_in_right)
    if result.in_both_different:
        lines.append("  Different values:")
        lines.extend(f"    ~ {k}" for k in result.in_both_different)
    if result.in_both_same:
        lines.append("  Identical keys:")
        lines.extend(f"    = {k}" for k in result.in_both_same)
    if result.ok:
        lines.append("  ✓ Profiles are identical.")
    return "\n".join(lines)
