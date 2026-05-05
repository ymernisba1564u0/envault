"""CLI for envault — encrypt/decrypt .env files with profile support."""

import click
from pathlib import Path

from envault.crypto import encrypt_file, decrypt_file
from envault.keystore import save_keypair, load_public_key, load_private_key, keypair_exists, generate_keypair
from envault.profiles import (
    ensure_profile_dir,
    profile_path,
    profile_exists,
    list_profiles,
    delete_profile,
    resolve_profile,
)


@click.group()
def cli():
    """envault — lightweight .env encryption using age."""


@cli.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing keypair.")
def init_cmd(force):
    """Generate and store a new age keypair."""
    if keypair_exists() and not force:
        raise click.ClickException("Keypair already exists. Use --force to overwrite.")
    private_key, public_key = generate_keypair()
    save_keypair(private_key, public_key)
    click.echo(f"Keypair initialised. Public key: {public_key}")


@cli.command("encrypt")
@click.argument("env_file", default=".env")
@click.option("-p", "--profile", default=None, help="Profile name (default: 'default').")
def encrypt_cmd(env_file, profile):
    """Encrypt an .env file into a named profile."""
    profile = resolve_profile(profile)
    src = Path(env_file)
    if not src.exists():
        raise click.ClickException(f"Source file not found: {env_file}")
    public_key = load_public_key()
    ensure_profile_dir()
    dest = profile_path(profile)
    encrypt_file(src, dest, public_key)
    click.echo(f"Encrypted '{env_file}' → profile '{profile}' ({dest})")


@cli.command("decrypt")
@click.argument("output", default=".env")
@click.option("-p", "--profile", default=None, help="Profile name (default: 'default').")
@click.option("--force", is_flag=True, help="Overwrite existing output file.")
def decrypt_cmd(output, profile, force):
    """Decrypt a profile back into a .env file."""
    profile = resolve_profile(profile)
    if not profile_exists(profile):
        raise click.ClickException(f"Profile '{profile}' not found. Run 'envault encrypt' first.")
    dest = Path(output)
    if dest.exists() and not force:
        raise click.ClickException(f"'{output}' already exists. Use --force to overwrite.")
    private_key = load_private_key()
    src = profile_path(profile)
    decrypt_file(src, dest, private_key)
    click.echo(f"Decrypted profile '{profile}' → '{output}'")


@cli.command("profiles")
def profiles_cmd():
    """List available encrypted profiles."""
    names = list_profiles()
    if not names:
        click.echo("No profiles found. Run 'envault encrypt' to create one.")
    else:
        click.echo("Available profiles:")
        for name in names:
            click.echo(f"  {name}")


@cli.command("drop")
@click.argument("profile")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def drop_cmd(profile, yes):
    """Delete an encrypted profile."""
    if not yes:
        click.confirm(f"Delete profile '{profile}'?", abort=True)
    removed = delete_profile(profile)
    if removed:
        click.echo(f"Profile '{profile}' deleted.")
    else:
        raise click.ClickException(f"Profile '{profile}' not found.")
