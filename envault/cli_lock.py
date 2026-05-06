"""CLI commands for locking and unlocking envault profiles."""

from __future__ import annotations

import click

from envault.lock import is_locked, lock_profile, unlock_profile
from envault.audit import record_event


@click.group("lock")
def lock_cmd() -> None:
    """Lock or unlock a profile to prevent accidental modification."""


@lock_cmd.command("on")
@click.argument("profile")
def lock_on_cmd(profile: str) -> None:
    """Lock PROFILE (marks it read-only)."""
    try:
        lock_profile(profile)
        record_event("lock", profile, detail={"action": "locked"})
        click.echo(f"Profile '{profile}' locked.")
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc


@lock_cmd.command("off")
@click.argument("profile")
def lock_off_cmd(profile: str) -> None:
    """Unlock PROFILE (restores write access)."""
    try:
        unlock_profile(profile)
        record_event("lock", profile, detail={"action": "unlocked"})
        click.echo(f"Profile '{profile}' unlocked.")
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc


@lock_cmd.command("status")
@click.argument("profile")
def lock_status_cmd(profile: str) -> None:
    """Show the lock status of PROFILE."""
    state = "locked" if is_locked(profile) else "unlocked"
    click.echo(f"Profile '{profile}' is {state}.")
