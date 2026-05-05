"""CLI sub-command: envault rotate — rotate encryption keys."""

from __future__ import annotations

import click

from envault.keystore import keypair_exists
from envault.rotate import rotate_keys


@click.command("rotate")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt.",
)
@click.pass_context
def rotate_cmd(ctx: click.Context, force: bool) -> None:  # noqa: FBT001
    """Rotate the encryption keypair and re-encrypt all profiles."""
    base_dir = ctx.obj.get("base_dir") if ctx.obj else None

    if not keypair_exists(base_dir):
        raise click.ClickException(
            "No keypair found. Run 'envault init' first."
        )

    if not force:
        click.confirm(
            "This will generate a new keypair and re-encrypt all profiles. "
            "Continue?",
            abort=True,
        )

    try:
        new_pub, _ = rotate_keys(base_dir)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("Keys rotated successfully.")
    click.echo(f"New public key: {new_pub}")
