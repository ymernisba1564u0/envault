"""CLI commands for managing profile TTLs."""

from __future__ import annotations

from datetime import timezone

import click

from envault.ttl import set_ttl, clear_ttl, get_ttl, is_expired, list_ttls


@click.group("ttl")
def ttl_cmd() -> None:
    """Manage time-to-live settings for profiles."""


@ttl_cmd.command("set")
@click.argument("profile")
@click.argument("seconds", type=int)
def set_cmd(profile: str, seconds: int) -> None:
    """Set a TTL of SECONDS for PROFILE."""
    try:
        expiry = set_ttl(profile, seconds)
        click.echo(f"TTL set for '{profile}'. Expires at: {expiry.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ttl_cmd.command("clear")
@click.argument("profile")
def clear_cmd(profile: str) -> None:
    """Remove the TTL for PROFILE."""
    removed = clear_ttl(profile)
    if removed:
        click.echo(f"TTL cleared for '{profile}'.")
    else:
        click.echo(f"No TTL was set for '{profile}'.")


@ttl_cmd.command("status")
@click.argument("profile")
def status_cmd(profile: str) -> None:
    """Show TTL status for PROFILE."""
    expiry = get_ttl(profile)
    if expiry is None:
        click.echo(f"No TTL set for '{profile}'.")
        return
    expired = is_expired(profile)
    stamp = expiry.strftime("%Y-%m-%d %H:%M:%S")
    state = "EXPIRED" if expired else "active"
    click.echo(f"Profile '{profile}': expires {stamp} UTC [{state}]")


@ttl_cmd.command("list")
def list_cmd() -> None:
    """List all profiles with a TTL configured."""
    entries = list_ttls()
    if not entries:
        click.echo("No TTLs configured.")
        return
    for name, expiry in entries.items():
        expired = is_expired(name)
        stamp = expiry.strftime("%Y-%m-%d %H:%M:%S")
        state = "EXPIRED" if expired else "active"
        click.echo(f"  {name:<20} {stamp} UTC  [{state}]")
