"""CLI commands for profile alias management."""

from __future__ import annotations

import click

from envault.alias import AliasError, add_alias, list_aliases, remove_alias, resolve_alias


@click.group("alias")
def alias_cmd() -> None:
    """Manage short-name aliases for profiles."""


@alias_cmd.command("add")
@click.argument("alias")
@click.argument("profile")
def add_cmd(alias: str, profile: str) -> None:
    """Create ALIAS pointing to PROFILE."""
    try:
        add_alias(alias, profile)
        click.echo(f"Alias '{alias}' -> '{profile}' created.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_cmd.command("remove")
@click.argument("alias")
def remove_cmd(alias: str) -> None:
    """Remove ALIAS."""
    try:
        remove_alias(alias)
        click.echo(f"Alias '{alias}' removed.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_cmd.command("resolve")
@click.argument("name")
def resolve_cmd(name: str) -> None:
    """Print the profile name NAME resolves to (identity if not an alias)."""
    click.echo(resolve_alias(name))


@alias_cmd.command("list")
def list_cmd() -> None:
    """List all defined aliases."""
    entries = list_aliases()
    if not entries:
        click.echo("No aliases defined.")
        return
    for entry in entries:
        click.echo(f"{entry['alias']:20s} -> {entry['profile']}")
