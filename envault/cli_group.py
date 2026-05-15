"""CLI commands for profile grouping."""

from __future__ import annotations

import click

from envault.group import (
    GroupError,
    add_to_group,
    group_members,
    list_groups,
    profile_groups,
    remove_from_group,
)


@click.group("group")
def group_cmd() -> None:
    """Manage profile groups."""


@group_cmd.command("add")
@click.argument("group")
@click.argument("profile")
def add_cmd(group: str, profile: str) -> None:
    """Add PROFILE to GROUP."""
    try:
        members = add_to_group(group, profile)
        click.echo(f"Added '{profile}' to group '{group}'.")
        click.echo("Members: " + ", ".join(members))
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("remove")
@click.argument("group")
@click.argument("profile")
def remove_cmd(group: str, profile: str) -> None:
    """Remove PROFILE from GROUP."""
    try:
        remaining = remove_from_group(group, profile)
        click.echo(f"Removed '{profile}' from group '{group}'.")
        if remaining:
            click.echo("Remaining: " + ", ".join(remaining))
        else:
            click.echo(f"Group '{group}' is now empty and has been deleted.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("list")
def list_cmd() -> None:
    """List all groups."""
    groups = list_groups()
    if not groups:
        click.echo("No groups defined.")
    else:
        for g in groups:
            click.echo(g)


@group_cmd.command("members")
@click.argument("group")
def members_cmd(group: str) -> None:
    """List profiles in GROUP."""
    members = group_members(group)
    if not members:
        click.echo(f"Group '{group}' has no members.")
    else:
        for m in members:
            click.echo(m)


@group_cmd.command("of")
@click.argument("profile")
def of_cmd(profile: str) -> None:
    """List groups that contain PROFILE."""
    groups = profile_groups(profile)
    if not groups:
        click.echo(f"Profile '{profile}' belongs to no groups.")
    else:
        for g in groups:
            click.echo(g)
