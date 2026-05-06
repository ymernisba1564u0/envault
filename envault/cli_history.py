"""CLI commands for profile version history."""

from __future__ import annotations

from pathlib import Path

import click

from envault.history import list_snapshots, restore_snapshot, snapshot_profile
from envault.profiles import profile_path, profile_exists


@click.group("history")
def history_cmd() -> None:
    """Manage encrypted profile snapshots."""


@history_cmd.command("snapshot")
@click.argument("profile")
@click.option("--note", default="", help="Optional note to attach to the snapshot.")
def snapshot_cmd(profile: str, note: str) -> None:
    """Create a snapshot of PROFILE's current encrypted state."""
    if not profile_exists(profile):
        click.echo(f"error: profile '{profile}' does not exist.", err=True)
        raise SystemExit(1)

    enc_path = profile_path(profile)
    snap = snapshot_profile(profile, enc_path, note=note)
    click.echo(f"Snapshot saved: {snap}")


@history_cmd.command("list")
@click.argument("profile")
def list_cmd(profile: str) -> None:
    """List all snapshots for PROFILE."""
    snapshots = list_snapshots(profile)
    if not snapshots:
        click.echo(f"No snapshots found for profile '{profile}'.")
        return

    click.echo(f"Snapshots for '{profile}':")
    for entry in snapshots:
        note_str = f"  # {entry['note']}" if entry.get("note") else ""
        click.echo(f"  {entry['timestamp']}{note_str}")


@history_cmd.command("restore")
@click.argument("profile")
@click.argument("timestamp")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def restore_cmd(profile: str, timestamp: str, yes: bool) -> None:
    """Restore PROFILE to the snapshot identified by TIMESTAMP."""
    enc_path = profile_path(profile)

    if not yes:
        click.confirm(
            f"Restore profile '{profile}' to snapshot {timestamp}? "
            "This will overwrite the current encrypted file.",
            abort=True,
        )

    restore_snapshot(profile, timestamp, enc_path)
    click.echo(f"Profile '{profile}' restored to snapshot {timestamp}.")
