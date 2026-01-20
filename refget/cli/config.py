"""
Configuration management commands for the refget CLI.

Commands:
    init    - Interactive setup wizard
    show    - View all configuration
    get     - Get specific configuration value
    set     - Set a configuration value
    add     - Add server to list
    remove  - Remove server from list
"""

from typing import Any, Dict, List, Optional

import typer

from refget.cli.output import (
    EXIT_CONFIG_ERROR,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    print_error,
    print_json,
    print_success,
)
from refget.cli.config_manager import (
    DEFAULTS,
    get_config_path,
    get_value,
    load_config,
    save_config,
    set_value,
)

app = typer.Typer(
    name="config",
    help="Configuration management",
    no_args_is_help=True,
)


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration",
    ),
) -> None:
    """
    Interactive setup wizard for refget configuration.

    Creates ~/.refget/config.toml with your preferences.
    """
    config_path = get_config_path()

    # Check if config already exists
    if config_path.exists() and not force:
        overwrite = typer.confirm(
            f"Configuration already exists at {config_path}. Overwrite?"
        )
        if not overwrite:
            typer.echo("Aborted.")
            raise typer.Exit(EXIT_FAILURE)

    # Interactive prompts
    typer.echo("Refget Configuration Setup")
    typer.echo("=" * 40)
    typer.echo()

    # Store path
    default_store_path = DEFAULTS["store"]["path"]
    store_path = typer.prompt(
        "Local store path",
        default=default_store_path,
    )

    # Seqcol server
    default_seqcol_url = DEFAULTS["seqcol_servers"][0]["url"]
    seqcol_url = typer.prompt(
        "Seqcol server URL",
        default=default_seqcol_url,
    )

    # Build config
    config: Dict[str, Any] = {
        "store": {
            "path": store_path,
        },
        "seqcol_servers": [
            {"url": seqcol_url, "name": "default"},
        ],
        "remote_stores": [],
        "sequence_servers": [],
    }

    # Try to create and save
    try:
        save_config(config)
        print_success(f"Configuration saved to {config_path}")
        raise typer.Exit(EXIT_SUCCESS)
    except ImportError as e:
        print_error(str(e), EXIT_CONFIG_ERROR)
    except OSError as e:
        print_error(f"Failed to create config: {e}", EXIT_CONFIG_ERROR)


@app.command()
def show(
    section: Optional[str] = typer.Argument(
        None,
        help="Optional section to show (store, seqcol_servers, remote_stores, admin)",
    ),
) -> None:
    """
    View all configuration or a specific section.

    Shows merged configuration from file and environment variables.
    """
    config = load_config()

    if section:
        value = get_value(config, section)
        if value is None:
            print_error(f"Section '{section}' not found", EXIT_CONFIG_ERROR)
            return  # Unreachable, but clarifies control flow
        print_json(value)
    else:
        print_json(config)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def get(
    key: str = typer.Argument(
        ...,
        help="Configuration key (dot-separated, e.g., 'store.path')",
    ),
) -> None:
    """
    Get a specific configuration value.

    Examples:
        refget config get store.path
        refget config get admin.postgres_host
    """
    config = load_config()
    value = get_value(config, key)

    if value is None:
        print_error(f"Key '{key}' not found", EXIT_FAILURE)
        return  # Unreachable, but clarifies control flow

    print_json({"value": value})
    raise typer.Exit(EXIT_SUCCESS)


@app.command("set")
def set_config(
    key: str = typer.Argument(
        ...,
        help="Configuration key (dot-separated, e.g., 'store.path')",
    ),
    value: str = typer.Argument(
        ...,
        help="Value to set",
    ),
) -> None:
    """
    Set a configuration value.

    Examples:
        refget config set store.path /path/to/store
        refget config set admin.postgres_host localhost
    """
    config = load_config()
    config = set_value(config, key, value)

    try:
        save_config(config)
        print_success(f"Set {key} = {value}")
        raise typer.Exit(EXIT_SUCCESS)
    except ImportError as e:
        print_error(str(e), EXIT_CONFIG_ERROR)
    except OSError as e:
        print_error(f"Failed to save config: {e}", EXIT_CONFIG_ERROR)


# Valid resource types and their config keys
RESOURCE_TYPE_MAP = {
    "seqcol_server": "seqcol_servers",
    "remote_store": "remote_stores",
    "sequence_server": "sequence_servers",
}


@app.command()
def add(
    resource_type: str = typer.Argument(
        ...,
        help="Resource type: seqcol_server, remote_store, or sequence_server",
    ),
    url: str = typer.Argument(
        ...,
        help="URL of the server/store to add",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Optional name for this server/store",
    ),
) -> None:
    """
    Add a server or store to the configuration.

    Examples:
        refget config add seqcol_server https://example.com/seqcol --name myserver
        refget config add remote_store s3://bucket/store/ --name primary
    """
    # Validate resource type
    if resource_type not in RESOURCE_TYPE_MAP:
        valid_types = ", ".join(RESOURCE_TYPE_MAP.keys())
        print_error(
            f"Invalid resource type '{resource_type}'.\n"
            f"Valid types: {valid_types}",
            EXIT_CONFIG_ERROR,
        )
        return  # Unreachable, but clarifies control flow

    config_key = RESOURCE_TYPE_MAP[resource_type]
    config = load_config()

    # Get current list or initialize empty
    server_list: List[Dict[str, str]] = config.get(config_key, [])

    # Build new entry
    entry: Dict[str, str] = {"url": url}
    if name:
        entry["name"] = name

    # Check for duplicate URLs
    for existing in server_list:
        if existing.get("url") == url:
            print_error(f"URL '{url}' already exists in {config_key}", EXIT_CONFIG_ERROR)
            return  # Unreachable, but clarifies control flow

    # Add entry
    server_list.append(entry)
    config[config_key] = server_list

    try:
        save_config(config)
        name_str = f" ({name})" if name else ""
        print_success(f"Added {resource_type}{name_str}: {url}")
        raise typer.Exit(EXIT_SUCCESS)
    except ImportError as e:
        print_error(str(e), EXIT_CONFIG_ERROR)
    except OSError as e:
        print_error(f"Failed to save config: {e}", EXIT_CONFIG_ERROR)


@app.command()
def path() -> None:
    """
    Show the path to the configuration file.

    Displays the config file path, respecting REFGET_CONFIG env var.
    """
    config_path = get_config_path()
    typer.echo(str(config_path))
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def validate() -> None:
    """
    Validate the configuration file.

    Checks that the config file exists and is valid TOML.
    """
    config_path = get_config_path()

    if not config_path.exists():
        print_error(f"Config file not found: {config_path}", EXIT_CONFIG_ERROR)
        return  # Unreachable, but clarifies control flow

    try:
        load_config()
        print_success(f"Configuration valid: {config_path}")
    except Exception as e:
        print_error(f"Invalid configuration: {e}", EXIT_CONFIG_ERROR)
        return

    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def remove(
    resource_type: str = typer.Argument(
        ...,
        help="Resource type: seqcol_server, remote_store, or sequence_server",
    ),
    name: str = typer.Argument(
        ...,
        help="Name of the server/store to remove",
    ),
) -> None:
    """
    Remove a server or store from the configuration.

    Examples:
        refget config remove seqcol_server myserver
        refget config remove remote_store primary
    """
    # Validate resource type
    if resource_type not in RESOURCE_TYPE_MAP:
        valid_types = ", ".join(RESOURCE_TYPE_MAP.keys())
        print_error(
            f"Invalid resource type '{resource_type}'.\n"
            f"Valid types: {valid_types}",
            EXIT_CONFIG_ERROR,
        )
        return  # Unreachable, but clarifies control flow

    config_key = RESOURCE_TYPE_MAP[resource_type]
    config = load_config()

    # Get current list
    server_list: List[Dict[str, str]] = config.get(config_key, [])

    # Find and remove entry by name
    original_len = len(server_list)
    server_list = [entry for entry in server_list if entry.get("name") != name]

    if len(server_list) == original_len:
        print_error(f"No {resource_type} found with name '{name}'", EXIT_CONFIG_ERROR)
        return  # Unreachable, but clarifies control flow

    config[config_key] = server_list

    try:
        save_config(config)
        print_success(f"Removed {resource_type}: {name}")
        raise typer.Exit(EXIT_SUCCESS)
    except ImportError as e:
        print_error(str(e), EXIT_CONFIG_ERROR)
    except OSError as e:
        print_error(f"Failed to save config: {e}", EXIT_CONFIG_ERROR)
