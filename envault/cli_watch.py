"""CLI commands for the watch feature."""

import click
from pathlib import Path

from envault.watch import watch_file


@click.group("watch")
def watch_cmd() -> None:
    """Watch a .env file and auto-encrypt on change."""


@watch_cmd.command("start")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("profile")
@click.option(
    "--interval",
    "-i",
    default=2.0,
    show_default=True,
    help="Polling interval in seconds.",
)
def start_cmd(env_file: str, profile: str, interval: float) -> None:
    """Watch ENV_FILE and re-encrypt into PROFILE on every change.

    Press Ctrl-C to stop watching.
    """
    src = Path(env_file)
    click.echo(f"Watching {src} → profile '{profile}' (interval={interval}s)")
    click.echo("Press Ctrl-C to stop.")

    def _notify(p: str) -> None:
        click.echo(f"[envault] Change detected — re-encrypted → {p}")

    try:
        watch_file(src, profile, interval=interval, on_change=_notify)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nStopped watching.")
