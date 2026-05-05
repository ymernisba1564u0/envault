"""Command-line interface for envault."""

import sys
from pathlib import Path

import click

from envault.crypto import encrypt_file, decrypt_file
from envault.keystore import save_keypair, load_public_key, load_private_key, keypair_exists, generate_keypair


@click.group()
def cli():
    """envault — encrypt and decrypt .env files using age encryption."""
    pass


@cli.command("init")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing keypair.")
def init_cmd(force):
    """Generate and store a new age keypair."""
    if keypair_exists() and not force:
        click.echo("Keypair already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    private_key, public_key = generate_keypair()
    save_keypair(private_key, public_key)
    click.echo(f"Keypair generated.")
    click.echo(f"Public key: {public_key}")


@cli.command("encrypt")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_file", type=click.Path(path_type=Path), default=None,
              help="Output path (default: <input>.age)")
def encrypt_cmd(input_file: Path, output_file: Path):
    """Encrypt an .env file."""
    if not keypair_exists():
        click.echo("No keypair found. Run `envault init` first.", err=True)
        sys.exit(1)

    if output_file is None:
        output_file = input_file.with_suffix(".age")

    public_key = load_public_key()
    encrypt_file(input_file, output_file, public_key)
    click.echo(f"Encrypted: {input_file} -> {output_file}")


@cli.command("decrypt")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_file", type=click.Path(path_type=Path), default=None,
              help="Output path (default: <input> without .age)")
def decrypt_cmd(input_file: Path, output_file: Path):
    """Decrypt an .age file."""
    if not keypair_exists():
        click.echo("No keypair found. Run `envault init` first.", err=True)
        sys.exit(1)

    if output_file is None:
        if input_file.suffix == ".age":
            output_file = input_file.with_suffix("")
        else:
            output_file = input_file.with_name(input_file.name + ".decrypted")

    private_key = load_private_key()
    decrypt_file(input_file, output_file, private_key)
    click.echo(f"Decrypted: {input_file} -> {output_file}")


if __name__ == "__main__":
    cli()
