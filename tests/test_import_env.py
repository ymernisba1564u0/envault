"""Tests for envault.import_env and envault.cli_import."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_import import import_cmd
from envault.crypto import decrypt_file
from envault.import_env import import_env_file, parse_import_source
from envault.keystore import load_private_key, save_keypair
from envault.crypto import generate_keypair


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base(tmp_path: Path) -> Path:
    priv, pub = generate_keypair()
    save_keypair(priv, pub, base_dir=tmp_path)
    return tmp_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# parse_import_source
# ---------------------------------------------------------------------------

def test_parse_plain_pairs() -> None:
    text = "FOO=bar\nBAZ=qux"
    pairs, skipped = parse_import_source(text)
    assert pairs == {"FOO": "bar", "BAZ": "qux"}
    assert skipped == []


def test_parse_export_syntax() -> None:
    text = "export FOO=bar\nexport BAZ=qux"
    pairs, skipped = parse_import_source(text)
    assert pairs == {"FOO": "bar", "BAZ": "qux"}


def test_parse_strips_quotes() -> None:
    pairs, _ = parse_import_source('KEY="hello world"\nOTHER=\'value\'')
    assert pairs["KEY"] == "hello world"
    assert pairs["OTHER"] == "value"


def test_parse_skips_comments_and_blanks() -> None:
    text = "# comment\n\nFOO=1"
    pairs, skipped = parse_import_source(text)
    assert list(pairs.keys()) == ["FOO"]
    assert skipped == []


def test_parse_records_unrecognised_lines() -> None:
    text = "FOO=1\nnot-valid-line"
    pairs, skipped = parse_import_source(text)
    assert "FOO" in pairs
    assert "not-valid-line" in skipped


# ---------------------------------------------------------------------------
# import_env_file
# ---------------------------------------------------------------------------

def test_import_creates_encrypted_profile(base: Path, tmp_path: Path) -> None:
    src = tmp_path / "sample.env"
    src.write_text("SECRET=abc123\nPORT=8080\n")

    count, skipped = import_env_file(src, "prod", base_dir=base)

    assert count == 2
    assert skipped == []
    from envault.profiles import profile_path
    assert profile_path("prod", base).exists()


def test_import_encrypted_content_is_decryptable(base: Path, tmp_path: Path) -> None:
    src = tmp_path / "vars.env"
    src.write_text("TOKEN=secret\n")
    import_env_file(src, "ci", base_dir=base)

    from envault.profiles import profile_path
    priv = load_private_key(base_dir=base)
    plaintext = decrypt_file(profile_path("ci", base), priv)
    assert b"TOKEN=secret" in plaintext


def test_import_raises_if_profile_exists(base: Path, tmp_path: Path) -> None:
    src = tmp_path / "a.env"
    src.write_text("X=1")
    import_env_file(src, "dev", base_dir=base)

    with pytest.raises(FileExistsError):
        import_env_file(src, "dev", base_dir=base, overwrite=False)


def test_import_overwrite_replaces_profile(base: Path, tmp_path: Path) -> None:
    src = tmp_path / "b.env"
    src.write_text("X=1")
    import_env_file(src, "dev", base_dir=base)

    src.write_text("X=2\nY=3")
    count, _ = import_env_file(src, "dev", base_dir=base, overwrite=True)
    assert count == 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_import_file_success(base: Path, tmp_path: Path, runner: CliRunner) -> None:
    src = tmp_path / "env.env"
    src.write_text("API_KEY=xyz")
    result = runner.invoke(
        import_cmd, ["file", str(src), "staging", "--base-dir", str(base)]
    )
    assert result.exit_code == 0
    assert "Imported 1 variable" in result.output


def test_cli_import_file_exists_no_overwrite(base: Path, tmp_path: Path, runner: CliRunner) -> None:
    src = tmp_path / "env.env"
    src.write_text("A=1")
    runner.invoke(import_cmd, ["file", str(src), "prod", "--base-dir", str(base)])
    result = runner.invoke(
        import_cmd, ["file", str(src), "prod", "--base-dir", str(base)]
    )
    assert result.exit_code != 0
    assert "already exists" in result.output
