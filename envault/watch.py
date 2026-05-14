"""Watch a .env file for changes and automatically re-encrypt into a profile."""

import hashlib
import time
from pathlib import Path
from typing import Callable, Optional

from envault.crypto import encrypt_file
from envault.keystore import load_public_key
from envault.profiles import profile_path, ensure_profile_dir
from envault.audit import record_event


def _file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def watch_file(
    env_file: Path,
    profile: str,
    base_dir: Optional[Path] = None,
    interval: float = 2.0,
    on_change: Optional[Callable[[str], None]] = None,
    _stop_after: int = -1,
) -> None:
    """Poll *env_file* every *interval* seconds and re-encrypt on change.

    Args:
        env_file:    Path to the plain-text .env file to watch.
        profile:     Target profile name to encrypt into.
        base_dir:    Root directory for keystore / profiles (defaults to ~).
        interval:    Polling interval in seconds.
        on_change:   Optional callback invoked with the profile name after each
                     successful re-encryption.
        _stop_after: Internal test hook — stop after this many iterations
                     (negative means run forever).
    """
    if not env_file.exists():
        raise FileNotFoundError(f"Watch target not found: {env_file}")

    pub_key = load_public_key(base_dir=base_dir)
    ensure_profile_dir(base_dir=base_dir)
    dest = profile_path(profile, base_dir=base_dir)

    last_hash = ""
    iterations = 0

    while True:
        current_hash = _file_hash(env_file)
        if current_hash != last_hash:
            encrypt_file(env_file, dest, pub_key)
            record_event(
                "watch_reencrypt",
                profile,
                detail=str(env_file),
                base_dir=base_dir,
            )
            last_hash = current_hash
            if on_change:
                on_change(profile)

        iterations += 1
        if _stop_after >= 0 and iterations >= _stop_after:
            break

        time.sleep(interval)
