"""CLI commands for patching (set/remove keys in) an encrypted profile."""

from __future__ import annotations

import click

from envault.env_diff_apply import apply_patch, PatchError


@click.group("patch")
def patch_cmd() -> None:
    """Patch keys inside an encrypted profile without a full re-encrypt cycle."""


@patch_cmd.command("set")
@click.argument("profile")
@click.argument("pairs", nargs=-1, required=True, metavar="KEY=VALUE...")
def set_cmd(profile: str, pairs: tuple[str, ...]) -> None:
    """Set one or more KEY=VALUE pairs in PROFILE.

    Example: envault patch set production DB_HOST=localhost DB_PORT=5432
    """
    kv: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(
                f"Expected KEY=VALUE, got '{pair}'", param_hint="pairs"
            )
        k, _, v = pair.partition("=")
        kv[k.strip()] = v

    try:
        result = apply_patch(profile, set_keys=kv)
    except PatchError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.added:
        click.echo(f"Added   : {', '.join(sorted(result.added))}")
    if result.updated:
        click.echo(f"Updated : {', '.join(sorted(result.updated))}")
    click.echo(f"Profile '{profile}' patched — {result.summary()}.")


@patch_cmd.command("remove")
@click.argument("profile")
@click.argument("keys", nargs=-1, required=True, metavar="KEY...")
def remove_cmd(profile: str, keys: tuple[str, ...]) -> None:
    """Remove one or more KEYS from PROFILE.

    Example: envault patch remove staging LEGACY_TOKEN OLD_FLAG
    """
    try:
        result = apply_patch(profile, remove_keys=list(keys))
    except PatchError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.removed:
        click.echo(f"Removed : {', '.join(sorted(result.removed))}")
    else:
        click.echo("No matching keys found — profile unchanged.")
    click.echo(f"Profile '{profile}' patched — {result.summary()}.")
