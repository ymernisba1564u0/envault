"""CLI commands for profile pinning."""

from __future__ import annotations

import click

from envault.pin import pin_profile, unpin_profile, is_pinned, list_pinned


@click.group("pin")
def pin_cmd() -> None:
    """Pin or unpin profiles to protect them from accidental changes."""


@pin_cmd.command("on")
@click.argument("profile")
def pin_on_cmd(profile: str) -> None:
    """Pin a profile."""
    try:
        pins = pin_profile(profile)
        click.echo(f"Profile '{profile}' is now pinned.")
        click.echo("Pinned profiles: " + ", ".join(pins))
    except FileNotFoundError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@pin_cmd.command("off")
@click.argument("profile")
def pin_off_cmd(profile: str) -> None:
    """Unpin a profile."""
    pins = unpin_profile(profile)
    click.echo(f"Profile '{profile}' is now unpinned.")
    if pins:
        click.echo("Pinned profiles: " + ", ".join(pins))
    else:
        click.echo("No profiles are currently pinned.")


@pin_cmd.command("status")
@click.argument("profile")
def pin_status_cmd(profile: str) -> None:
    """Show whether a profile is pinned."""
    if is_pinned(profile):
        click.echo(f"Profile '{profile}' is PINNED.")
    else:
        click.echo(f"Profile '{profile}' is not pinned.")


@pin_cmd.command("list")
def pin_list_cmd() -> None:
    """List all pinned profiles."""
    pins = list_pinned()
    if not pins:
        click.echo("No profiles are currently pinned.")
    else:
        for name in pins:
            click.echo(name)
