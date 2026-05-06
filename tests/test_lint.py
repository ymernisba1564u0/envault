"""Tests for envault.lint."""

import pytest

from envault.lint import lint_env_bytes, LintResult, LintIssue


def _lint(text: str) -> LintResult:
    return lint_env_bytes(text.encode())


def test_clean_file_returns_ok():
    result = _lint("FOO=bar\nBAZ=qux\n")
    assert result.ok


def test_blank_lines_and_comments_ignored():
    result = _lint("# comment\n\nFOO=bar\n")
    assert result.ok


def test_missing_equals_flagged():
    result = _lint("NODIVIDER\n")
    assert not result.ok
    assert any("Missing '='" in i.message for i in result.issues)


def test_empty_key_flagged():
    result = _lint("=value\n")
    assert not result.ok
    assert any("Empty key" in i.message for i in result.issues)


def test_invalid_key_with_hyphen_flagged():
    result = _lint("MY-KEY=value\n")
    assert not result.ok
    assert any("Invalid key" in i.message for i in result.issues)


def test_key_starting_with_digit_flagged():
    result = _lint("1BAD=value\n")
    assert not result.ok
    assert any("Invalid key" in i.message for i in result.issues)


def test_unclosed_double_quote_flagged():
    result = _lint('FOO="unclosed\n')
    assert not result.ok
    assert any("Unclosed double-quote" in i.message for i in result.issues)


def test_unclosed_single_quote_flagged():
    result = _lint("FOO='unclosed\n")
    assert not result.ok
    assert any("Unclosed single-quote" in i.message for i in result.issues)


def test_properly_quoted_values_ok():
    result = _lint('FOO="hello world"\nBAR=\'baz\'\n')
    assert result.ok


def test_key_with_spaces_flagged():
    result = _lint("MY KEY=value\n")
    assert not result.ok
    assert any("spaces" in i.message for i in result.issues)


def test_multiple_issues_collected():
    result = _lint("NODIVIDER\n=empty\nBAD-KEY=x\n")
    assert len(result.issues) >= 3


def test_issue_str_contains_line_number():
    result = _lint("NODIVIDER\n")
    assert "Line 1" in str(result.issues[0])


def test_result_str_ok_message():
    result = _lint("FOO=bar\n")
    assert str(result) == "No issues found."


def test_result_str_shows_count():
    result = _lint("NODIVIDER\n=empty\n")
    assert "issue(s) found" in str(result)


def test_lint_file(tmp_path):
    from envault.lint import lint_file
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAD-KEY=x\n")
    result = lint_file(str(env_file))
    assert not result.ok
    assert any("Invalid key" in i.message for i in result.issues)
