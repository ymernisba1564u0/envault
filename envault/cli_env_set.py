"""CLI commands for getting/setting/unsetting individual env keys."""
import click

from envault.env_set import set_key, unset_key, get_key, EnvSetError


@click.group("key")
def key_cmd() -> None:
    """Get, set, or unset individual keys inside a profile."""


@key_cmd.command("set")
@click.argument("profile")
@click.argument("key")
@click.argument("value")
def set_cmd(profile: str, key: str, value: str) -> None:
    """Set KEY=VALUE in PROFILE."""
    try:
        result = set_key(profile, key, value)
    except EnvSetError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.action == "unchanged":
        click.echo(f"{key} is already set to that value in '{profile}'.")
    elif result.previous is None:
        click.echo(f"Added {key} to '{profile}'.")
    else:
        click.echo(f"Updated {key} in '{profile}' (was: {result.previous!r}).")


@key_cmd.command("unset")
@click.argument("profile")
@click.argument("key")
def unset_cmd(profile: str, key: str) -> None:
    """Remove KEY from PROFILE."""
    try:
        result = unset_key(profile, key)
    except EnvSetError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.action == "unchanged":
        click.echo(f"Key '{key}' was not present in '{profile}' — nothing changed.")
    else:
        click.echo(f"Removed '{key}' from '{profile}'.")


@key_cmd.command("get")
@click.argument("profile")
@click.argument("key")
def get_cmd(profile: str, key: str) -> None:
    """Print the value of KEY from PROFILE, or exit 1 if absent."""
    try:
        value = get_key(profile, key)
    except EnvSetError as exc:
        raise click.ClickException(str(exc)) from exc

    if value is None:
        raise click.ClickException(f"Key '{key}' not found in profile '{profile}'.")
    click.echo(value)
