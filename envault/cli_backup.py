"""CLI commands for backup and restore of encrypted profile archives."""

from __future__ import annotations

from pathlib import Path

import click

from envault.backup import backup_profiles, restore_profiles, BackupError


@click.group("backup")
def backup_cmd():
    """Backup and restore encrypted profile bundles."""


@backup_cmd.command("create")
@click.argument("dest", type=click.Path())
@click.option(
    "--profile",
    "profiles",
    multiple=True,
    help="Profile(s) to include (default: all).",
)
def create_cmd(dest: str, profiles: tuple):
    """Create a zip backup of encrypted profiles at DEST."""
    target = Path(dest)
    selected = list(profiles) if profiles else None
    try:
        backed_up = backup_profiles(target, profiles=selected)
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Backed up {len(backed_up)} profile(s) to {target}:")
    for name in backed_up:
        click.echo(f"  {name}")


@backup_cmd.command("restore")
@click.argument("src", type=click.Path())
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing profiles.",
)
def restore_cmd(src: str, overwrite: bool):
    """Restore encrypted profiles from a backup zip at SRC."""
    source = Path(src)
    try:
        restored = restore_profiles(source, overwrite=overwrite)
    except BackupError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Restored {len(restored)} profile(s):")
    for name in restored:
        click.echo(f"  {name}")
