"""Lint .env files for common issues before encryption."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class LintIssue:
    line_number: int
    line: str
    message: str

    def __str__(self) -> str:
        return f"  Line {self.line_number}: {self.message!r} -> {self.line!r}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.ok:
            return "No issues found."
        lines = [f"{len(self.issues)} issue(s) found:"]
        lines.extend(str(i) for i in self.issues)
        return "\n".join(lines)


def lint_env_bytes(data: bytes) -> LintResult:
    """Lint raw .env file bytes and return a LintResult."""
    result = LintResult()
    text = data.decode("utf-8", errors="replace")

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(lineno, raw, "Missing '=' separator"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.issues.append(LintIssue(lineno, raw, "Empty key"))
            continue

        if not key.replace("_", "").isalnum() or key[0].isdigit():
            result.issues.append(
                LintIssue(lineno, raw, f"Invalid key name '{key}'")
            )

        if value.startswith('"') and not value.endswith('"'):
            result.issues.append(
                LintIssue(lineno, raw, "Unclosed double-quote in value")
            )
        elif value.startswith("'") and not value.endswith("'"):
            result.issues.append(
                LintIssue(lineno, raw, "Unclosed single-quote in value")
            )

        if " " in key:
            result.issues.append(
                LintIssue(lineno, raw, f"Key '{key}' contains spaces")
            )

    return result


def lint_file(path: str) -> LintResult:
    """Lint a .env file on disk."""
    with open(path, "rb") as fh:
        data = fh.read()
    return lint_env_bytes(data)
