"""
Output formatting helpers for the refget CLI.

This module provides consistent output formatting and exit codes.
"""

import json
import os
import sys
from contextlib import contextmanager
from typing import Any, Optional

import typer

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_FILE_NOT_FOUND = 2
EXIT_NETWORK_ERROR = 3
EXIT_CONFIG_ERROR = 4


def print_json(data: Any, pretty: bool = True) -> None:
    """
    Print data as JSON to stdout.

    Args:
        data: Any JSON-serializable data
        pretty: If True, pretty-print with indentation
    """
    if pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))


def print_error(message: str, exit_code: Optional[int] = None) -> None:
    """
    Print an error message to stderr.

    Args:
        message: Error message to display
        exit_code: If provided, exit with this code
    """
    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
    if exit_code is not None:
        raise typer.Exit(code=exit_code)


def print_warning(message: str) -> None:
    """
    Print a warning message to stderr.

    Args:
        message: Warning message to display
    """
    typer.secho(f"Warning: {message}", fg=typer.colors.YELLOW, err=True)


def print_success(message: str) -> None:
    """
    Print a success message to stderr.

    Args:
        message: Success message to display
    """
    typer.secho(message, fg=typer.colors.GREEN, err=True)


def print_info(message: str) -> None:
    """
    Print an info message to stderr.

    Args:
        message: Info message to display
    """
    typer.secho(message, fg=typer.colors.BLUE, err=True)


def not_implemented(command_name: str) -> None:
    """
    Print a not implemented message and exit.

    Args:
        command_name: Name of the command that is not implemented
    """
    print_error(f"'{command_name}' is not implemented yet", EXIT_FAILURE)


def check_dependency(package: str, command_group: str, extra: str) -> None:
    """
    Check if an optional dependency is available.

    Args:
        package: Package name to import
        command_group: Name of the command group requiring this package
        extra: pip extra to install (e.g., 'store', 'admin')

    Raises:
        typer.Exit: If the dependency is not available
    """
    try:
        __import__(package)
    except ImportError:
        print_error(
            f"'{command_group}' commands require {package}.\n"
            f"Install with: pip install refget[{extra}]",
            EXIT_FAILURE,
        )


@contextmanager
def suppress_stdout():
    """
    Context manager to suppress stdout at the file descriptor level.

    This is necessary for suppressing output from libraries like gtars
    that print directly to file descriptor 1 rather than Python's sys.stdout.

    Example:
        with suppress_stdout():
            result = fasta_to_seqcol_dict(path)
    """
    # Save the original file descriptors
    original_stdout_fd = os.dup(1)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)

    try:
        # Redirect stdout to /dev/null at the file descriptor level
        os.dup2(devnull_fd, 1)
        # Also redirect Python's sys.stdout
        sys.stdout.flush()
        yield
    finally:
        # Restore stdout
        os.dup2(original_stdout_fd, 1)
        os.close(original_stdout_fd)
        os.close(devnull_fd)
