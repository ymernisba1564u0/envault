"""Validate decrypted .env profiles against a schema of required keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.keystore import load_private_key, load_public_key
from envault.profiles import profile_path
from envault.crypto import decrypt_file
from envault.export import parse_env_bytes


@dataclass
class ValidationIssue:
    key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class ValidationResult:
    profile: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.ok:
            return f"{self.profile}: OK"
        lines = [f"{self.profile}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def load_schema(schema_path: Path) -> List[str]:
    """Read a plain-text schema file: one required key per line, # comments ignored."""
    keys: List[str] = []
    for raw in schema_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        keys.append(line)
    return keys


def validate_profile(
    profile_name: str,
    required_keys: List[str],
    base_dir: Optional[Path] = None,
) -> ValidationResult:
    """Decrypt *profile_name* and check that all *required_keys* are present."""
    result = ValidationResult(profile=profile_name)

    enc_path = profile_path(profile_name, base_dir=base_dir)
    if not enc_path.exists():
        result.issues.append(ValidationIssue("<file>", "encrypted profile not found"))
        return result

    private_key = load_private_key(base_dir=base_dir)
    raw = decrypt_file(enc_path, private_key)
    env_vars = parse_env_bytes(raw)

    for key in required_keys:
        if key not in env_vars:
            result.issues.append(ValidationIssue(key, "missing required key"))

    return result


def validate_all(
    required_keys: List[str],
    base_dir: Optional[Path] = None,
) -> List[ValidationResult]:
    """Validate every profile that exists under *base_dir*."""
    from envault.profiles import list_profiles

    return [
        validate_profile(name, required_keys, base_dir=base_dir)
        for name in list_profiles(base_dir=base_dir)
    ]
