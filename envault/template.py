"""Template rendering: substitute env vars from a decrypted profile into a template file."""

from __future__ import annotations

import re
import string
from pathlib import Path
from typing import Dict, Optional

from envault.export import parse_env_bytes
from envault.keystore import load_private_key
from envault.profiles import profile_path, profile_exists
from envault.crypto import decrypt_file

# Matches ${VAR_NAME} or $VAR_NAME style placeholders
_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class TemplateRenderError(Exception):
    """Raised when template rendering fails due to missing variables."""


def load_env_vars(profile: str, base_dir: Optional[Path] = None) -> Dict[str, str]:
    """Decrypt a profile and return its key/value pairs as a dict."""
    if not profile_exists(profile, base_dir):
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")

    path = profile_path(profile, base_dir)
    private_key = load_private_key()
    raw = decrypt_file(path, private_key)
    return parse_env_bytes(raw)


def render_template(template_text: str, env_vars: Dict[str, str], strict: bool = True) -> str:
    """Substitute placeholders in *template_text* with values from *env_vars*.

    Supports ``${VAR}`` and ``$VAR`` syntax.  When *strict* is True any
    placeholder that has no matching key raises :class:`TemplateRenderError`.
    When *strict* is False the placeholder is left unchanged.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1) or match.group(2)
        if key in env_vars:
            return env_vars[key]
        if strict:
            missing.append(key)
            return match.group(0)
        return match.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template_text)

    if strict and missing:
        raise TemplateRenderError(
            "Template references undefined variables: " + ", ".join(sorted(set(missing)))
        )

    return result


def render_template_file(
    template_path: Path,
    profile: str,
    output_path: Optional[Path] = None,
    strict: bool = True,
    base_dir: Optional[Path] = None,
) -> str:
    """Read *template_path*, substitute vars from *profile*, optionally write to *output_path*.

    Returns the rendered string regardless of whether it is written to disk.
    """
    env_vars = load_env_vars(profile, base_dir)
    template_text = template_path.read_text(encoding="utf-8")
    rendered = render_template(template_text, env_vars, strict=strict)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    return rendered
