"""CLI commands for importing .env files into envault profiles."""

from __future__ import annotations

from pathlib import Path

import click

from envault.import_env import import_env_file


@click.group("import")
def import_cmd() -> None:  # pragma: no cover
    """Import external .env files into envault profiles."""


@import_cmd.command("file")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("profile")
@click.option(
    "--base-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Override the envault base directory.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Replace an existing profile with the same name.",
)
def import_file_cmd(
    source: Path,
    profile: str,
    base_dir: Path | None,
    overwrite: bool,
) -> None:
    """Import SOURCE .env file into PROFILE."""
    try:
        count, skipped = import_env_file(
            source_path=source,
            profile=profile,
            base_dir=base_dir,
            overwrite=overwrite,
        )
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Import failed: {exc}") from exc

    click.echo(f"Imported {count} variable(s) into profile '{profile}'.")
    if skipped:
        click.echo(f"Skipped {len(skipped)} unrecognised line(s):")
        for line in skipped:
            click.echo(f"  {line}")
