"""Search across decrypted profile keys/values without persisting plaintext."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.crypto import decrypt_file
from envault.export import parse_env_bytes
from envault.keystore import load_private_key
from envault.profiles import list_profiles, profile_path


@dataclass
class SearchMatch:
    profile: str
    key: str
    value: str

    def __str__(self) -> str:
        return f"[{self.profile}] {self.key}={self.value}"


@dataclass
class SearchResult:
    matches: List[SearchMatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def search_profiles(
    query: str,
    *,
    keys_only: bool = False,
    profile_filter: Optional[str] = None,
    base_dir: Optional[str] = None,
) -> SearchResult:
    """Search all (or a specific) profile for keys/values matching *query*.

    Parameters
    ----------
    query:          Case-insensitive substring to search for.
    keys_only:      When True only key names are searched, not values.
    profile_filter: If given, restrict search to this single profile name.
    base_dir:       Override base directory (used in tests).
    """
    result = SearchResult()
    q = query.lower()

    try:
        private_key = load_private_key(base_dir=base_dir)
    except FileNotFoundError:
        result.errors.append("No keypair found. Run `envault init` first.")
        return result

    profiles = (
        [profile_filter]
        if profile_filter
        else list_profiles(base_dir=base_dir)
    )

    for name in profiles:
        path = profile_path(name, base_dir=base_dir)
        if not path.exists():
            result.errors.append(f"Profile '{name}' not found.")
            continue
        try:
            plaintext = decrypt_file(path, private_key)
            pairs = parse_env_bytes(plaintext)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Could not decrypt '{name}': {exc}")
            continue

        for key, value in pairs.items():
            hit = q in key.lower() or (not keys_only and q in value.lower())
            if hit:
                result.matches.append(SearchMatch(profile=name, key=key, value=value))

    return result
