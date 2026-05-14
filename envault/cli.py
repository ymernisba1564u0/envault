"""Main CLI entry-point for envault."""

import click

from envault.keystore import save_keypair, load_public_key, keypair_exists
from envault.crypto import generate_keypair, encrypt_file, decrypt_file
from envault.profiles import list_profiles, profile_path, ensure_profile_dir
from envault.export import render, parse_env_file
from envault.cli_rotate import rotate_cmd
from envault.cli_share import share_cmd
from envault.cli_diff import diff_cmd
from envault.cli_lock import lock_cmd
from envault.cli_history import history_cmd
from envault.cli_import import import_cmd
from envault.cli_pin import pin_cmd
from envault.cli_watch import watch_cmd


@click.group()
def cli() -> None:
    """envault — encrypted .env manager."""


@cli.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing keypair.")
def init_cmd(force: bool) -> None:
    """Generate a new age keypair."""
    if keypair_exists() and not force:
        raise click.ClickException(
            "Keypair already exists. Use --force to overwrite."
        )
    priv, pub = generate_keypair()
    save_keypair(priv, pub)
    click.echo("Keypair generated.")


@cli.command("encrypt")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("profile")
def encrypt_cmd(env_file: str, profile: str) -> None:
    """Encrypt ENV_FILE into PROFILE."""
    from pathlib import Path

    pub = load_public_key()
    ensure_profile_dir()
    dest = profile_path(profile)
    encrypt_file(Path(env_file), dest, pub)
    click.echo(f"Encrypted → {dest}")


@cli.command("decrypt")
@click.argument("profile")
@click.option("--format", "fmt", default="export", show_default=True,
              type=click.Choice(["export", "dotenv", "raw"]))
def decrypt_cmd(profile: str, fmt: str) -> None:
    """Decrypt PROFILE and print to stdout."""
    import tempfile
    from pathlib import Path
    from envault.keystore import load_private_key

    src = profile_path(profile)
    if not src.exists():
        raise click.ClickException(f"Profile '{profile}' not found.")

    priv = load_private_key()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".env") as tmp:
        tmp_path = Path(tmp.name)

    try:
        decrypt_file(src, tmp_path, priv)
        pairs = parse_env_file(tmp_path)
        click.echo(render(pairs, fmt))
    finally:
        tmp_path.unlink(missing_ok=True)


@cli.command("profiles")
def profiles_cmd() -> None:
    """List available profiles."""
    names = list_profiles()
    if not names:
        click.echo("No profiles found.")
    for name in names:
        click.echo(name)


@cli.command("pubkey")
def pubkey_cmd() -> None:
    """Print the current public key."""
    click.echo(load_public_key())


cli.add_command(rotate_cmd, "rotate")
cli.add_command(share_cmd, "share")
cli.add_command(diff_cmd, "diff")
cli.add_command(lock_cmd, "lock")
cli.add_command(history_cmd, "history")
cli.add_command(import_cmd, "import")
cli.add_command(pin_cmd, "pin")
cli.add_command(watch_cmd, "watch")
