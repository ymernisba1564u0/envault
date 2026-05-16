"""CLI commands for sorting keys inside an encrypted .env profile."""

from __future__ import annotations

import click

from envault.env_sort import SortError, sort_profile


@click.group("sort")
def sort_cmd() -> None:
    """Sort keys within an encrypted profile."""


@sort_cmd.command("run")
@click.argument("profile")
@click.option("--reverse", is_flag=True, default=False, help="Sort in descending order.")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing.",
)
def run_cmd(profile: str, reverse: bool, dry_run: bool) -> None:
    """Sort the keys of PROFILE alphabetically and re-encrypt."""
    try:
        result = sort_profile(profile, reverse=reverse, dry_run=dry_run)
    except SortError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    prefix = "[dry-run] " if dry_run else ""
    if result.changed:
        click.echo(f"{prefix}{result}")
        if dry_run:
            click.echo("New order:")
            for key in result.sorted_order:
                click.echo(f"  {key}")
    else:
        click.echo(f"{prefix}{result}")
