"""Export decrypted .env profiles to shell-compatible formats."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional


_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def parse_env_bytes(data: bytes) -> Dict[str, str]:
    """Parse raw .env bytes into a key/value dictionary.

    Supports:
    - KEY=VALUE
    - KEY="VALUE"  / KEY='VALUE'
    - Blank lines and # comments are ignored.
    """
    result: Dict[str, str] = {}
    for raw_line in data.decode().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if not _VALID_KEY_RE.match(key):
            continue
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        result[key] = value
    return result


def to_export_lines(env_vars: Dict[str, str]) -> List[str]:
    """Return a list of `export KEY=VALUE` shell lines."""
    lines = []
    for key, value in env_vars.items():
        # Escape single quotes inside the value
        escaped = value.replace("'", "'\\''")
        lines.append(f"export {key}='{escaped}'")
    return lines


def to_dotenv_lines(env_vars: Dict[str, str]) -> List[str]:
    """Return a list of plain KEY=VALUE lines suitable for a .env file."""
    lines = []
    for key, value in env_vars.items():
        needs_quotes = any(c in value for c in (' ', '\t', '#', '"', "'"))
        if needs_quotes:
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f'{key}={value}')
    return lines


def render(env_vars: Dict[str, str], fmt: str = 'export') -> str:
    """Render env vars to a string in the requested format.

    Args:
        env_vars: Mapping of environment variable names to values.
        fmt: One of 'export' (default) or 'dotenv'.

    Returns:
        A newline-terminated string.

    Raises:
        ValueError: If *fmt* is not recognised.
    """
    if fmt == 'export':
        lines = to_export_lines(env_vars)
    elif fmt == 'dotenv':
        lines = to_dotenv_lines(env_vars)
    else:
        raise ValueError(f"Unknown export format: {fmt!r}. Choose 'export' or 'dotenv'.")
    return '\n'.join(lines) + ('\n' if lines else '')
