"""Tests for envault.export."""

import pytest

from envault.export import parse_env_bytes, render, to_export_lines, to_dotenv_lines


# ---------------------------------------------------------------------------
# parse_env_bytes
# ---------------------------------------------------------------------------

def test_parse_simple_pairs():
    data = b"KEY=value\nSECRET=abc123\n"
    result = parse_env_bytes(data)
    assert result == {"KEY": "value", "SECRET": "abc123"}


def test_parse_ignores_comments_and_blanks():
    data = b"# comment\n\nFOO=bar\n"
    result = parse_env_bytes(data)
    assert result == {"FOO": "bar"}


def test_parse_strips_double_quotes():
    data = b'DB_URL="postgres://localhost/db"\n'
    result = parse_env_bytes(data)
    assert result["DB_URL"] == "postgres://localhost/db"


def test_parse_strips_single_quotes():
    data = b"TOKEN='my-secret-token'\n"
    result = parse_env_bytes(data)
    assert result["TOKEN"] == "my-secret-token"


def test_parse_ignores_invalid_keys():
    data = b"123INVALID=oops\nVALID_KEY=ok\n"
    result = parse_env_bytes(data)
    assert "123INVALID" not in result
    assert result["VALID_KEY"] == "ok"


def test_parse_ignores_lines_without_equals():
    data = b"NOEQUALS\nKEY=val\n"
    result = parse_env_bytes(data)
    assert "NOEQUALS" not in result
    assert result["KEY"] == "val"


# ---------------------------------------------------------------------------
# to_export_lines
# ---------------------------------------------------------------------------

def test_export_lines_format():
    lines = to_export_lines({"FOO": "bar"})
    assert lines == ["export FOO='bar'"]


def test_export_lines_escapes_single_quotes():
    lines = to_export_lines({"MSG": "it's alive"})
    assert lines == ["export MSG='it'\\''s alive'"]


# ---------------------------------------------------------------------------
# to_dotenv_lines
# ---------------------------------------------------------------------------

def test_dotenv_lines_plain_value():
    lines = to_dotenv_lines({"KEY": "simple"})
    assert lines == ["KEY=simple"]


def test_dotenv_lines_quotes_value_with_spaces():
    lines = to_dotenv_lines({"KEY": "hello world"})
    assert lines == ['KEY="hello world"']


def test_dotenv_lines_escapes_double_quotes():
    lines = to_dotenv_lines({"KEY": 'say "hi"'})
    assert '\\"' in lines[0]


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def test_render_export_format():
    output = render({"A": "1", "B": "2"}, fmt='export')
    assert "export A='1'" in output
    assert "export B='2'" in output
    assert output.endswith('\n')


def test_render_dotenv_format():
    output = render({"A": "1"}, fmt='dotenv')
    assert "A=1" in output


def test_render_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown export format"):
        render({"A": "1"}, fmt='json')


def test_render_empty_dict_returns_empty_string():
    assert render({}) == ''
