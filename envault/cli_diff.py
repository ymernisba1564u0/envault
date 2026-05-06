"""CLI commands for diffing two env profiles or a profile against a plain file."""
import click

from envault.crypto import decrypt_file
from envault.keystore import load_private_key
from envault.profiles import profile_path, profile_exists
from envault.diff import diff_envs, render_diff


@click.group("diff")
def diff_cmd():
    """Compare env profiles or files."""


@diff_cmd.command("profiles")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--show-values", is_flag=True, default=False, help="Show actual values (not masked).")
def diff_profiles_cmd(profile_a: str, profile_b: str, show_values: bool):
    """Diff two encrypted profiles by name."""
    for name in (profile_a, profile_b):
        if not profile_exists(name):
            raise click.ClickException(f"Profile '{name}' does not exist.")

    priv = load_private_key()
    raw_a = decrypt_file(profile_path(profile_a), priv)
    raw_b = decrypt_file(profile_path(profile_b), priv)

    result = diff_envs(raw_a, raw_b)
    click.echo(render_diff(result, mask_values=not show_values))
    if result.has_changes:
        raise SystemExit(1)


@diff_cmd.command("file")
@click.argument("profile")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--show-values", is_flag=True, default=False, help="Show actual values (not masked).")
def diff_file_cmd(profile: str, env_file: str, show_values: bool):
    """Diff an encrypted profile against a plain .env file."""
    if not profile_exists(profile):
        raise click.ClickException(f"Profile '{profile}' does not exist.")

    priv = load_private_key()
    raw_profile = decrypt_file(profile_path(profile), priv)

    with open(env_file, "rb") as fh:
        raw_file = fh.read()

    result = diff_envs(raw_profile, raw_file)
    click.echo(render_diff(result, mask_values=not show_values))
    if result.has_changes:
        raise SystemExit(1)
