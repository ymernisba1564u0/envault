"""Profile management for envault — supports named environments (dev, staging, prod, etc.)"""

import os
from pathlib import Path

DEFAULT_PROFILE = "default"
ENVAULT_DIR = ".envault"


def _profile_dir(base_dir: str = ".") -> Path:
    return Path(base_dir) / ENVAULT_DIR / "profiles"


def profile_path(profile: str, base_dir: str = ".") -> Path:
    """Return the path to the encrypted env file for a given profile."""
    return _profile_dir(base_dir) / f"{profile}.env.age"


def list_profiles(base_dir: str = ".") -> list[str]:
    """Return a sorted list of available profile names."""
    d = _profile_dir(base_dir)
    if not d.exists():
        return []
    return sorted(
        p.stem.removesuffix(".env")
        for p in d.glob("*.env.age")
    )


def profile_exists(profile: str, base_dir: str = ".") -> bool:
    return profile_path(profile, base_dir).exists()


def ensure_profile_dir(base_dir: str = ".") -> Path:
    d = _profile_dir(base_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def delete_profile(profile: str, base_dir: str = ".") -> bool:
    """Delete a profile's encrypted file. Returns True if deleted, False if not found."""
    p = profile_path(profile, base_dir)
    if p.exists():
        p.unlink()
        return True
    return False


def resolve_profile(profile: str | None) -> str:
    """Resolve profile name, falling back to ENVAULT_PROFILE env var or 'default'."""
    if profile:
        return profile
    return os.environ.get("ENVAULT_PROFILE", DEFAULT_PROFILE)
