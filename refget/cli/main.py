"""
Main Typer application for the refget CLI.

This module defines the main CLI app and registers all command groups.
"""

import typer
from typing import Optional

from refget._version import __version__

app = typer.Typer(
    name="refget",
    help="GA4GH refget CLI - reference sequence access and management",
    no_args_is_help=True,
)

# Import and register command groups
from refget.cli import config, fasta, store, seqcol, admin

app.add_typer(config.app, name="config", help="Configuration management")
app.add_typer(fasta.app, name="fasta", help="FASTA file utilities")
app.add_typer(store.app, name="store", help="RefgetStore operations")
app.add_typer(seqcol.app, name="seqcol", help="Sequence collection API")
app.add_typer(admin.app, name="admin", help="Admin/database operations")


def version_callback(value: bool):
    if value:
        typer.echo(f"refget {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version and exit."
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
