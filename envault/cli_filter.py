"""CLI commands for filtering env vars within a profile."""
from __future__ import annotations

from pathlib import Path

import click

from envault.env_filter import FilterError, filter_profile, write_filtered


@click.group("filter")
def filter_cmd() -> None:
    """Filter env vars in a profile by key or value pattern."""


@filter_cmd.command("show")
@click.argument("profile")
@click.option("--key", "key_pattern", default=None, help="Glob pattern for key names.")
@click.option("--value", "value_pattern", default=None, help="Regex pattern for values.")
@click.option("--invert", is_flag=True, default=False, help="Return non-matching vars.")
@click.option("--base-dir", default=None, hidden=True)
def show_cmd(
    profile: str,
    key_pattern: str | None,
    value_pattern: str | None,
    invert: bool,
    base_dir: str | None,
) -> None:
    """Print filtered env vars to stdout."""
    bd = Path(base_dir) if base_dir else Path.home()
    try:
        result = filter_profile(profile, bd, key_pattern, value_pattern, invert)
    except FilterError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if not result.matched:
        click.echo("No matching variables found.")
        return
    for k, v in result.matched.items():
        click.echo(f"{k}={v}")


@filter_cmd.command("extract")
@click.argument("profile")
@click.argument("dest")
@click.option("--key", "key_pattern", default=None, help="Glob pattern for key names.")
@click.option("--value", "value_pattern", default=None, help="Regex pattern for values.")
@click.option("--invert", is_flag=True, default=False, help="Extract non-matching vars.")
@click.option("--base-dir", default=None, hidden=True)
def extract_cmd(
    profile: str,
    dest: str,
    key_pattern: str | None,
    value_pattern: str | None,
    invert: bool,
    base_dir: str | None,
) -> None:
    """Write filtered vars into a new encrypted profile DEST."""
    bd = Path(base_dir) if base_dir else Path.home()
    try:
        result = filter_profile(profile, bd, key_pattern, value_pattern, invert)
        out = write_filtered(profile, bd, result, dest)
    except FilterError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(f"Wrote {len(result.matched)} var(s) to profile '{dest}' ({out}).")
