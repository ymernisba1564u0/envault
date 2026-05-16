"""CLI commands for diffing a profile against a historical snapshot."""

from __future__ import annotations

import sys

import click

from envault.env_snapshot_diff import diff_snapshot
from envault.history import list_snapshots


@click.group("snapshot-diff")
def snapshot_diff_cmd() -> None:
    """Compare a profile against a historical snapshot."""


@snapshot_diff_cmd.command("run")
@click.argument("profile")
@click.argument("snapshot_id")
@click.option("--exit-code", is_flag=True, help="Exit 1 if differences found.")
def run_cmd(profile: str, snapshot_id: str, exit_code: bool) -> None:
    """Diff PROFILE against SNAPSHOT_ID."""
    try:
        result = diff_snapshot(profile, snapshot_id)
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)

    click.echo(result.summary())

    if exit_code and not result.ok:
        sys.exit(1)


@snapshot_diff_cmd.command("latest")
@click.argument("profile")
@click.option("--exit-code", is_flag=True, help="Exit 1 if differences found.")
def latest_cmd(profile: str, exit_code: bool) -> None:
    """Diff PROFILE against its most recent snapshot."""
    snapshots = list_snapshots(profile)
    if not snapshots:
        click.echo(f"No snapshots found for profile '{profile}'.", err=True)
        sys.exit(2)

    latest = snapshots[-1]["id"]
    try:
        result = diff_snapshot(profile, latest)
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)

    click.echo(result.summary())

    if exit_code and not result.ok:
        sys.exit(1)
