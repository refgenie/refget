"""
Main Typer application for the refget CLI.

This module defines the main CLI app and registers all command groups.
"""

import typer
from typing import Optional

from refget._version import __version__

from refget.cli.config import app as config_app
from refget.cli.fasta import app as fasta_app
from refget.cli.store import app as store_app
from refget.cli.seqcol import app as seqcol_app
from refget.cli.admin import app as admin_app

app = typer.Typer(
    name="refget",
    help="GA4GH refget CLI - reference sequence access and management",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(config_app, name="config", help="Configuration management")
app.add_typer(fasta_app, name="fasta", help="FASTA file utilities")
app.add_typer(store_app, name="store", help="RefgetStore operations")
app.add_typer(seqcol_app, name="seqcol", help="Sequence collection API")
app.add_typer(admin_app, name="admin", help="Admin/database operations")


def version_callback(value: bool):
    if value:
        typer.echo(f"refget {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """
    GA4GH refget CLI - reference sequence access and management.

    Use 'refget <command> --help' for more information on each command.
    """
    pass


def main():
    """Entry point for the refget CLI."""
    app()


if __name__ == "__main__":
    main()
