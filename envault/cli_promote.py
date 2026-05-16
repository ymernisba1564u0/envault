"""CLI commands for the promote feature."""
from __future__ import annotations

import click

from envault.env_promote import PromoteError, promote_profile


@click.group("promote")
def promote_cmd() -> None:
    """Promote a profile to another environment tier."""


@promote_cmd.command("run")
@click.argument("source")
@click.argument("destination")
@click.option(
    "--allow",
    multiple=True,
    metavar="KEY",
    help="Only promote these keys (repeatable). Omit to promote all keys.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the destination profile if it already exists.",
)
def run_cmd(
    source: str,
    destination: str,
    allow: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Promote SOURCE profile into DESTINATION.

    Example:

      envault promote run staging production --allow DB_URL --allow SECRET_KEY
    """
    try:
        result = promote_profile(
            source,
            destination,
            allow=list(allow) if allow else None,
            overwrite=overwrite,
        )
    except PromoteError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(str(result))
    if result.skipped_keys:
        click.echo("  Skipped keys  : " + ", ".join(result.skipped_keys))
