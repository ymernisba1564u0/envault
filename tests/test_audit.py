"""Tests for envault.audit — audit logging module."""

import json
from pathlib import Path

import pytest

import envault.audit as audit


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    """Redirect audit log to a temporary directory for every test."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "audit.log"
    monkeypatch.setattr(audit, "_LOG_DIR", log_dir)
    monkeypatch.setattr(audit, "_LOG_FILE", log_file)
    yield log_dir, log_file


def test_record_creates_log_dir(isolated_log):
    log_dir, _ = isolated_log
    assert not log_dir.exists()
    audit.record_event("encrypt", "default", True)
    assert log_dir.exists()


def test_record_writes_valid_json(isolated_log):
    _, log_file = isolated_log
    audit.record_event("encrypt", "staging", True)
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["action"] == "encrypt"
    assert entry["profile"] == "staging"
    assert entry["success"] is True
    assert "timestamp" in entry


def test_record_optional_detail(isolated_log):
    _, log_file = isolated_log
    audit.record_event("decrypt", "prod", False, detail="key not found")
    entry = json.loads(log_file.read_text().strip())
    assert entry["detail"] == "key not found"


def test_record_no_detail_omits_key(isolated_log):
    _, log_file = isolated_log
    audit.record_event("encrypt", "default", True)
    entry = json.loads(log_file.read_text().strip())
    assert "detail" not in entry


def test_multiple_events_appended(isolated_log):
    _, log_file = isolated_log
    audit.record_event("encrypt", "dev", True)
    audit.record_event("decrypt", "dev", True)
    audit.record_event("encrypt", "prod", False)
    lines = [l for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 3


def test_read_events_empty_when_no_file(isolated_log):
    assert audit.read_events() == []


def test_read_events_returns_newest_first(isolated_log):
    audit.record_event("encrypt", "a", True)
    audit.record_event("decrypt", "b", True)
    events = audit.read_events()
    assert events[0]["profile"] == "b"
    assert events[1]["profile"] == "a"


def test_read_events_respects_limit(isolated_log):
    for i in range(10):
        audit.record_event("encrypt", f"p{i}", True)
    events = audit.read_events(limit=3)
    assert len(events) == 3


def test_read_events_limit_larger_than_total(isolated_log):
    """Requesting more events than exist should return all available events."""
    for i in range(4):
        audit.record_event("encrypt", f"p{i}", True)
    events = audit.read_events(limit=100)
    assert len(events) == 4


def test_clear_log_removes_file(isolated_log):
    _, log_file = isolated_log
    audit.record_event("encrypt", "default", True)
    assert log_file.exists()
    audit.clear_log()
    assert not log_file.exists()


def test_clear_log_noop_when_missing(isolated_log):
    # Should not raise even if file doesn't exist
    audit.clear_log()
