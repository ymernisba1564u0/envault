"""CLI surface for the compare feature."""

from __future__ import annotations

import sys

import click

from envault.compare import compare_profiles, render_compare


@click.group("compare")
def compare_cmd() -> None:
    """Compare two encrypted profiles side-by-side."""


@compare_cmd.command("profiles")
@click.argument("left")
@click.argument("right")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output result as JSON.",
)
def profiles_cmd(left: str, right: str, as_json: bool) -> None:
    """Compare LEFT profile against RIGHT profile."""
    try:
        result = compare_profiles(left, right)
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        import json

        payload = {
            "left": result.left,
            "right": result.right,
            "only_in_left": result.only_in_left,
            "only_in_right": result.only_in_right,
            "in_both_same": result.in_both_same,
            "in_both_different": result.in_both_different,
            "coverage": round(result.coverage(), 4),
            "ok": result.ok,
        }
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(render_compare(result))

    if not result.ok:
        sys.exit(1)
