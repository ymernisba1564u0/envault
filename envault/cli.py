"""Main CLI entry-point for envault."""
import click

from envault.keystore import save_keypair, keypair_exists, load_public_key
from envault.crypto import generate_keypair, encrypt_file, decrypt_file
from envault.profiles import profile_path, list_profiles, profile_exists, ensure_profile_dir
from envault.export import render, parse_env_bytes
from envault.audit import record_event
from envault.cli_rotate import rotate_cmd
from envault.cli_share import share_cmd
from envault.cli_diff import diff_cmd


@click.group()
def cli():
    """envault — encrypted .env manager."""


@cli.command("init")
@click.option("--force", is_flag=True, default=False, help="Overwrite existing keypair.")
def init_cmd(force: bool):
    """Generate a new age keypair."""
    if keypair_exists() and not force:
        raise click.ClickException("Keypair already exists. Use --force to overwrite.")
    pub, priv = generate_keypair()
    save_keypair(pub, priv)
    record_event("init", detail={"force": force})
    click.echo(f"Keypair generated. Public key: {pub}")


@cli.command("encrypt")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--profile", default="default", show_default=True)
def encrypt_cmd(env_file: str, profile: str):
    """Encrypt an .env file into a named profile."""
    ensure_profile_dir()
    pub = load_public_key()
    dest = profile_path(profile)
    encrypt_file(env_file, pub, dest)
    record_event("encrypt", detail={"profile": profile, "source": env_file})
    click.echo(f"Encrypted '{env_file}' -> profile '{profile}'.")


@cli.command("decrypt")
@click.option("--profile", default="default", show_default=True)
@click.option("--export", "export_format", type=click.Choice(["export", "dotenv", "raw"]), default="raw")
def decrypt_cmd(profile: str, export_format: str):
    """Decrypt a named profile and print to stdout."""
    if not profile_exists(profile):
        raise click.ClickException(f"Profile '{profile}' not found.")
    from envault.keystore import load_private_key
    priv = load_private_key()
    raw = decrypt_file(profile_path(profile), priv)
    record_event("decrypt", detail={"profile": profile})
    pairs = parse_env_bytes(raw)
    click.echo(render(pairs, fmt=export_format))


@cli.command("profiles")
def profiles_cmd():
    """List available profiles."""
    names = list_profiles()
    if not names:
        click.echo("No profiles found.")
    for name in names:
        click.echo(name)


@cli.command("verify")
@click.option("--profile", default=None, help="Verify a single profile.")
def verify_cmd(profile: str):
    """Verify integrity of encrypted profiles."""
    from envault.verify import verify_profile, verify_all
    if profile:
        result = verify_profile(profile)
        status = "OK" if result.ok else f"FAIL ({result.reason})"
        click.echo(f"{profile}: {status}")
        if not result.ok:
            raise SystemExit(1)
    else:
        results = verify_all()
        any_fail = False
        for name, result in results.items():
            status = "OK" if result.ok else f"FAIL ({result.reason})"
            click.echo(f"{name}: {status}")
            if not result.ok:
                any_fail = True
        if any_fail:
            raise SystemExit(1)


cli.add_command(rotate_cmd, name="rotate")
cli.add_command(share_cmd, name="share")
cli.add_command(diff_cmd, name="diff")
