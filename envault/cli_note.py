"""CLI commands for managing per-profile notes."""

from __future__ import annotations

import click
from pathlib import Path

from envault.note import set_note, get_note, clear_note, list_notes


@click.group("note")
def note_cmd() -> None:
    """Attach or manage notes on profiles."""


@note_cmd.command("set")
@click.argument("profile")
@click.argument("text")
@click.option("--base", default=".", help="Project root directory.")
def set_cmd(profile: str, text: str, base: str) -> None:
    """Set (or replace) the note for PROFILE."""
    try:
        set_note(Path(base), profile, text)
        click.echo(f"Note saved for profile '{profile}'.")
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@note_cmd.command("get")
@click.argument("profile")
@click.option("--base", default=".", help="Project root directory.")
def get_cmd(profile: str, base: str) -> None:
    """Print the note for PROFILE."""
    note = get_note(Path(base), profile)
    if note is None:
        click.echo(f"No note found for profile '{profile}'.")
    else:
        click.echo(f"[{note['updated_at']}] {note['text']}")


@note_cmd.command("clear")
@click.argument("profile")
@click.option("--base", default=".", help="Project root directory.")
def clear_cmd(profile: str, base: str) -> None:
    """Remove the note for PROFILE."""
    removed = clear_note(Path(base), profile)
    if removed:
        click.echo(f"Note cleared for profile '{profile}'.")
    else:
        click.echo(f"No note to clear for profile '{profile}'.")


@note_cmd.command("list")
@click.option("--base", default=".", help="Project root directory.")
def list_cmd(base: str) -> None:
    """List all profiles that have notes."""
    notes = list_notes(Path(base))
    if not notes:
        click.echo("No notes found.")
        return
    for n in notes:
        click.echo(f"{n['profile']:20s}  {n['updated_at']}  {n['text']}")
