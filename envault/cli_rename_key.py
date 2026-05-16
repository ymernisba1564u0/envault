"""CLI commands for renaming a key inside an encrypted profile."""

from __future__ import annotations

import click

from envault.env_rename_key import rename_key, RenameKeyError


@click.group("rename-key")
def rename_key_cmd() -> None:
    """Rename a key inside an encrypted profile."""


@rename_key_cmd.command("run")
@click.argument("profile")
@click.argument("old_key")
@click.argument("new_key")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Replace new_key if it already exists in the profile.",
)
def run_cmd(profile: str, old_key: str, new_key: str, overwrite: bool) -> None:
    """Rename OLD_KEY to NEW_KEY inside PROFILE.

    The encrypted file is re-encrypted in place; the value is preserved.
    """
    try:
        result = rename_key(profile, old_key, new_key, overwrite=overwrite)
    except RenameKeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(
        f"Renamed '{result.old_key}' -> '{result.new_key}' "
        f"in profile '{result.profile}'."
    )
