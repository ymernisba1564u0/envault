"""Audit log for envault operations — records encrypt/decrypt events to a local log file."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_LOG_DIR = Path.home() / ".envault" / "logs"
_LOG_FILE = _LOG_DIR / "audit.log"


def _log_dir() -> Path:
    return _LOG_DIR


def _log_file() -> Path:
    return _LOG_FILE


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def record_event(
    action: str,
    profile: str,
    success: bool,
    detail: Optional[str] = None,
) -> None:
    """Append a single JSON-line audit entry to the log file."""
    _ensure_log_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "profile": profile,
        "success": success,
    }
    if detail:
        entry["detail"] = detail
    with _LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_events(limit: int = 50) -> list[dict]:
    """Return the most recent *limit* audit entries, newest-first."""
    if not _LOG_FILE.exists():
        return []
    lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return list(reversed(entries[-limit:]))


def clear_log() -> None:
    """Delete all audit log entries."""
    if _LOG_FILE.exists():
        _LOG_FILE.unlink()
