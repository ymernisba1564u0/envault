"""Register the access sub-command group with the main CLI.

This module is imported by envault/cli.py to attach `access_cmd` to the
top-level `cli` group without modifying the existing cli.py file.

Usage (in cli.py)::

    from envault.cli_access_register import register
    register(cli)
"""

from __future__ import annotations

import click

from envault.cli_access import access_cmd


def register(cli: click.Group) -> None:
    """Attach the *access* command group to *cli*."""
    cli.add_command(access_cmd)
