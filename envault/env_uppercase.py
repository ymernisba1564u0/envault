"""Normalize environment variable keys to UPPER_CASE within a profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from envault.crypto import decrypt_file, encrypt_file
from envault.export import parse_env_bytes, to_dotenv_lines
from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path


class UppercaseError(Exception):
    def __str__(self) -> str:  # pragma: no cover
        return self.args[0]


@dataclass
class UppercaseResult:
    profile: str
    renamed: List[Tuple[str, str]] = field(default_factory=list)  # (old, new)
    skipped: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True

    def __str__(self) -> str:
        if not self.renamed:
            return f"Profile '{self.profile}': all keys already uppercase."
        lines = [f"Profile '{self.profile}': {len(self.renamed)} key(s) renamed."]
        for old, new in self.renamed:
            lines.append(f"  {old} -> {new}")
        if self.skipped:
            lines.append(f"  Skipped (collision): {', '.join(self.skipped)}")
        return "\n".join(lines)


def uppercase_profile(
    profile: str,
    base_dir: Path | None = None,
) -> UppercaseResult:
    """Re-encrypt a profile with all keys converted to UPPER_CASE.

    If uppercasing a key would collide with an existing key, the original
    key is left unchanged and recorded in ``result.skipped``.
    """
    path = profile_path(profile, base_dir=base_dir)
    if not path.exists():
        raise UppercaseError(f"Profile '{profile}' does not exist.")

    priv = load_private_key(base_dir=base_dir)
    pub = load_public_key(base_dir=base_dir)

    raw = decrypt_file(path, priv)
    pairs = parse_env_bytes(raw)

    renamed: List[Tuple[str, str]] = []
    skipped: List[str] = []
    seen: dict[str, str] = {}

    for key, value in pairs:
        upper = key.upper()
        if upper != key:
            if upper in seen:
                skipped.append(key)
                seen[key] = value
                continue
            renamed.append((key, upper))
            seen[upper] = value
        else:
            seen[key] = value

    new_pairs = list(seen.items())
    new_content = "\n".join(to_dotenv_lines(new_pairs)).encode()
    encrypt_file(new_content, path, pub)

    return UppercaseResult(profile=profile, renamed=renamed, skipped=skipped)
