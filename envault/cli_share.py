"""CLI commands for sharing encrypted profiles with other users."""

from __future__ import annotations

from pathlib import Path

import click

from envault.share import share_profile, receive_share
from envault.export import parse_env_bytes, render
from envault.audit import record_event


@click.group("share")
def share_cmd() -> None:
    """Share encrypted profiles with other users."""


@share_cmd.command("send")
@click.argument("profile")
@click.argument("recipient_public_key")
@click.option("--base", default=None, help="Override envault base directory.")
def send_cmd(profile: str, recipient_public_key: str, base: str | None) -> None:
    """Encrypt PROFILE for RECIPIENT_PUBLIC_KEY and write a share bundle."""
    base_path = Path(base) if base else None
    try:
        out = share_profile(profile, recipient_public_key, base=base_path)
        record_event("share_send", detail={"profile": profile}, base=base_path)
        click.echo(f"Share bundle written to: {out}")
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(f"Failed to create share bundle: {exc}") from exc


@share_cmd.command("receive")
@click.argument("bundle", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "fmt", default="export", type=click.Choice(["export", "dotenv"]), show_default=True)
@click.option("--base", default=None, help="Override envault base directory.")
def receive_cmd(bundle: Path, fmt: str, base: str | None) -> None:
    """Decrypt a share BUNDLE and print the contained secrets."""
    base_path = Path(base) if base else None
    try:
        plaintext = receive_share(bundle, base=base_path)
        pairs = parse_env_bytes(plaintext)
        click.echo(render(pairs, mode=fmt))
        record_event("share_receive", detail={"bundle": str(bundle)}, base=base_path)
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(f"Failed to receive share bundle: {exc}") from exc
