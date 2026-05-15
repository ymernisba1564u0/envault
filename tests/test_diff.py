"""Unit tests for envault.diff."""
import pytest

from envault.diff import diff_envs, render_diff, DiffResult


OLD_ENV = b"FOO=bar\nBAZ=qux\nKEEP=same\n"
NEW_ENV = b"FOO=changed\nNEW_KEY=hello\nKEEP=same\n"


def test_added_keys():
    result = diff_envs(OLD_ENV, NEW_ENV)
    assert "NEW_KEY" in result.added


def test_removed_keys():
    result = diff_envs(OLD_ENV, NEW_ENV)
    assert "BAZ" in result.removed


def test_changed_keys():
    result = diff_envs(OLD_ENV, NEW_ENV)
    keys = [k for k, _, _ in result.changed]
    assert "FOO" in keys


def test_changed_old_new_values():
    result = diff_envs(OLD_ENV, NEW_ENV)
    for key, old, new in result.changed:
        if key == "FOO":
            assert old == "bar"
            assert new == "changed"


def test_unchanged_keys():
    result = diff_envs(OLD_ENV, NEW_ENV)
    assert "KEEP" in result.unchanged


def test_has_changes_true():
    result = diff_envs(OLD_ENV, NEW_ENV)
    assert result.has_changes is True


def test_has_changes_false():
    result = diff_envs(OLD_ENV, OLD_ENV)
    assert result.has_changes is False


def test_render_diff_masks_values():
    result = diff_envs(OLD_ENV, NEW_ENV)
    output = render_diff(result, mask_values=True)
    assert "bar" not in output
    assert "changed" not in output
    assert "***" in output


def test_render_diff_shows_values():
    result = diff_envs(OLD_ENV, NEW_ENV)
    output = render_diff(result, mask_values=False)
    assert "bar" in output
    assert "changed" in output


def test_render_diff_no_changes():
    result = diff_envs(OLD_ENV, OLD_ENV)
    output = render_diff(result)
    assert "(no changes)" in output


def test_render_diff_prefixes():
    result = diff_envs(OLD_ENV, NEW_ENV)
    output = render_diff(result)
    assert any(line.startswith("+") for line in output.splitlines())
    assert any(line.startswith("-") for line in output.splitlines())
    assert any(line.startswith("~") for line in output.splitlines())


def test_empty_envs():
    result = diff_envs(b"", b"")
    assert not result.has_changes


def test_comments_ignored():
    a = b"# comment\nFOO=bar\n"
    b_ = b"FOO=bar\n"
    result = diff_envs(a, b_)
    assert not result.has_changes


def test_added_keys_not_in_removed_or_changed():
    """Keys that are newly added should not appear in removed or changed."""
    result = diff_envs(OLD_ENV, NEW_ENV)
    changed_keys = [k for k, _, _ in result.changed]
    assert "NEW_KEY" not in result.removed
    assert "NEW_KEY" not in changed_keys


def test_removed_keys_not_in_added_or_changed():
    """Keys that are removed should not appear in added or changed."""
    result = diff_envs(OLD_ENV, NEW_ENV)
    changed_keys = [k for k, _, _ in result.changed]
    assert "BAZ" not in result.added
    assert "BAZ" not in changed_keys
