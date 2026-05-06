"""Tests for envault.template — template rendering with env var substitution."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.crypto import encrypt_file, generate_keypair
from envault.keystore import save_keypair
from envault.profiles import ensure_profile_dir, profile_path
from envault.template import (
    TemplateRenderError,
    load_env_vars,
    render_template,
    render_template_file,
)


@pytest.fixture()
def base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    priv, pub = generate_keypair()
    save_keypair(priv, pub)
    return tmp_path


@pytest.fixture()
def sample_profile(base: Path) -> str:
    """Create an encrypted 'default' profile with two variables."""
    ensure_profile_dir(base_dir=base)
    env_bytes = b"APP_HOST=localhost\nAPP_PORT=8080\nSECRET_KEY=hunter2\n"
    from envault.keystore import load_public_key

    pub = load_public_key()
    path = profile_path("default", base)
    encrypt_file(env_bytes, path, pub)
    return "default"


# ---------------------------------------------------------------------------
# render_template unit tests (no I/O)
# ---------------------------------------------------------------------------


def test_render_template_dollar_brace_syntax():
    result = render_template("host=${APP_HOST}", {"APP_HOST": "localhost"})
    assert result == "host=localhost"


def test_render_template_bare_dollar_syntax():
    result = render_template("port=$PORT", {"PORT": "9000"})
    assert result == "port=9000"


def test_render_template_multiple_vars():
    tmpl = "${A} and ${B}"
    result = render_template(tmpl, {"A": "foo", "B": "bar"})
    assert result == "foo and bar"


def test_render_template_strict_raises_on_missing():
    with pytest.raises(TemplateRenderError, match="MISSING_VAR"):
        render_template("value=${MISSING_VAR}", {}, strict=True)


def test_render_template_non_strict_leaves_placeholder():
    result = render_template("value=${MISSING_VAR}", {}, strict=False)
    assert result == "value=${MISSING_VAR}"


def test_render_template_no_placeholders():
    result = render_template("plain text", {"UNUSED": "x"})
    assert result == "plain text"


# ---------------------------------------------------------------------------
# load_env_vars integration tests
# ---------------------------------------------------------------------------


def test_load_env_vars_returns_dict(base: Path, sample_profile: str):
    env = load_env_vars(sample_profile, base_dir=base)
    assert env["APP_HOST"] == "localhost"
    assert env["APP_PORT"] == "8080"
    assert env["SECRET_KEY"] == "hunter2"


def test_load_env_vars_missing_profile_raises(base: Path):
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        load_env_vars("nonexistent", base_dir=base)


# ---------------------------------------------------------------------------
# render_template_file integration tests
# ---------------------------------------------------------------------------


def test_render_template_file_substitutes_vars(base: Path, sample_profile: str, tmp_path: Path):
    tmpl = tmp_path / "config.tmpl"
    tmpl.write_text("host=${APP_HOST}\nport=${APP_PORT}\n")
    result = render_template_file(tmpl, sample_profile, base_dir=base)
    assert "host=localhost" in result
    assert "port=8080" in result


def test_render_template_file_writes_output(base: Path, sample_profile: str, tmp_path: Path):
    tmpl = tmp_path / "nginx.conf.tmpl"
    tmpl.write_text("listen ${APP_PORT};\n")
    out = tmp_path / "out" / "nginx.conf"
    render_template_file(tmpl, sample_profile, output_path=out, base_dir=base)
    assert out.exists()
    assert "listen 8080;" in out.read_text()
