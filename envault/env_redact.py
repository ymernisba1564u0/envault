"""Redact sensitive values from a decrypted .env profile for safe display."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import decrypt_file
from envault.export import parse_env_bytes
from envault.keystore import load_private_key
from envault.profiles import profile_path

# Keys whose values are always fully redacted regardless of pattern matching.
_SENSITIVE_PATTERNS = (
    "secret",
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "auth",
    "credential",
    "cert",
    "signing",
)

REDACTED_PLACEHOLDER = "***REDACTED***"
_PARTIAL_VISIBLE = 4  # characters visible at start for partial mode


@dataclass
class RedactResult:
    profile: str
    pairs: Dict[str, str] = field(default_factory=dict)
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True

    def render(self) -> str:
        lines = []
        for key, value in self.pairs.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(pat in lower for pat in _SENSITIVE_PATTERNS)


def _redact_value(value: str, partial: bool) -> str:
    if not partial or len(value) <= _PARTIAL_VISIBLE:
        return REDACTED_PLACEHOLDER
    return value[:_PARTIAL_VISIBLE] + "..." + REDACTED_PLACEHOLDER


def redact_profile(
    profile: str,
    base_dir: Optional[Path] = None,
    partial: bool = False,
    extra_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Decrypt *profile* and return a RedactResult with sensitive values masked."""
    path = profile_path(profile, base_dir=base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile}")

    private_key = load_private_key(base_dir=base_dir)
    raw = decrypt_file(path, private_key)
    pairs = parse_env_bytes(raw)

    sensitive_set = set(k.upper() for k in (extra_keys or []))
    result_pairs: Dict[str, str] = {}
    redacted: List[str] = []

    for key, value in pairs.items():
        if _is_sensitive(key) or key.upper() in sensitive_set:
            result_pairs[key] = _redact_value(value, partial)
            redacted.append(key)
        else:
            result_pairs[key] = value

    return RedactResult(profile=profile, pairs=result_pairs, redacted_keys=sorted(redacted))
