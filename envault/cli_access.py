"""CLI commands for managing profile access control lists."""

from __future__ import annotations

import click

from envault.access import AccessError, grant_access, revoke_access, list_access, clear_access
from envault.profiles import _profile_dir


@click.group("access")
def access_cmd() -> None:
    """Manage recipient-key access control for profiles."""


@access_cmd.command("grant")
@click.argument("profile")
@click.argument("recipient_key")
def grant_cmd(profile: str, recipient_key: str) -> None:
    """Grant RECIPIENT_KEY access to PROFILE."""
    base = _profile_dir().parent
    try:
        keys = grant_access(base, profile, recipient_key)
        click.echo(f"Granted access to '{profile}'. Authorised keys ({len(keys)}):")
        for k in keys:
            click.echo(f"  {k}")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("revoke")
@click.argument("profile")
@click.argument("recipient_key")
def revoke_cmd(profile: str, recipient_key: str) -> None:
    """Revoke RECIPIENT_KEY access from PROFILE."""
    base = _profile_dir().parent
    try:
        keys = revoke_access(base, profile, recipient_key)
        click.echo(f"Revoked access from '{profile}'. Remaining keys: {len(keys)}")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("list")
@click.argument("profile")
def list_cmd(profile: str) -> None:
    """List recipient keys authorised for PROFILE."""
    base = _profile_dir().parent
    keys = list_access(base, profile)
    if not keys:
        click.echo(f"No access entries for '{profile}'.")
    else:
        click.echo(f"Authorised keys for '{profile}':")
        for k in keys:
            click.echo(f"  {k}")


@access_cmd.command("clear")
@click.argument("profile")
def clear_cmd(profile: str) -> None:
    """Remove all ACL entries for PROFILE."""
    base = _profile_dir().parent
    clear_access(base, profile)
    click.echo(f"Cleared all access entries for '{profile}'.")
