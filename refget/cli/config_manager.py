"""
Configuration file handling for the refget CLI.

This module manages the configuration file at ~/.refget/config.toml,
environment variable overrides, and default values.

Priority: CLI flag > env var > config file > default
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore


# Default configuration
DEFAULTS = {
    "store": {
        "path": "~/.refget/store",
    },
    "remote_stores": [],
    "seqcol_servers": [
        {"url": "https://seqcolapi.databio.org", "name": "databio"},
    ],
    "sequence_servers": [],
    "admin": {
        "postgres_host": "localhost",
        "postgres_port": "5432",
        "postgres_db": "refget",
        "postgres_user": "postgres",
    },
}

# Environment variable mappings
ENV_VAR_MAPPINGS = {
    "REFGET_CONFIG": "config_path",
    "REFGET_STORE": ("store", "path"),  # Short form
    "REFGET_STORE_PATH": ("store", "path"),  # Explicit form
    "REFGET_STORE_URL": "remote_stores",  # Single URL override
    "REFGET_SEQCOL_URL": "seqcol_servers",  # Single URL override
    "REFGET_SEQUENCE_URL": "sequence_servers",  # Single URL override
    "POSTGRES_HOST": ("admin", "postgres_host"),
    "POSTGRES_PORT": ("admin", "postgres_port"),
    "POSTGRES_DB": ("admin", "postgres_db"),
    "POSTGRES_USER": ("admin", "postgres_user"),
    "POSTGRES_PASSWORD": ("admin", "postgres_password"),
}


def get_config_path() -> Path:
    """
    Get the path to the configuration file.

    Returns:
        Path to the config file, respecting REFGET_CONFIG env var.
    """
    env_path = os.environ.get("REFGET_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".refget" / "config.toml"


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file and apply environment overrides.

    Priority: env var > config file > default

    Returns:
        Configuration dictionary with all values resolved.
    """
    config = _deep_copy_dict(DEFAULTS)

    # Load from file if it exists
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "rb") as f:
            file_config = tomllib.load(f)
        config = _merge_config(config, file_config)

    # Apply environment variable overrides
    config = _apply_env_overrides(config)

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to the config file.

    Args:
        config: Configuration dictionary to save.

    Raises:
        ImportError: If tomli_w is not installed.
    """
    if tomli_w is None:
        raise ImportError(
            "tomli_w is required to save configuration.\n" "Install with: pip install tomli-w"
        )

    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def get_value(config: Dict[str, Any], key: str) -> Any:
    """
    Get a configuration value by dot-separated key.

    Args:
        config: Configuration dictionary
        key: Dot-separated key path (e.g., "store.path")

    Returns:
        The configuration value, or None if not found.
    """
    parts = key.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _coerce_value(value: str) -> Any:
    """Coerce a string value to int, bool, or keep as string."""
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def set_value(config: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """
    Set a configuration value by dot-separated key.

    Args:
        config: Configuration dictionary
        key: Dot-separated key path (e.g., "store.path")
        value: Value to set (strings are auto-coerced to int/bool if applicable)

    Returns:
        Updated configuration dictionary.
    """
    parts = key.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    # Coerce string values from CLI input
    if isinstance(value, str):
        value = _coerce_value(value)
    current[parts[-1]] = value
    return config


def get_store_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get the local RefgetStore path.

    Args:
        config: Optional config dict; if None, loads from file.

    Returns:
        Path to the local store directory.
    """
    if config is None:
        config = load_config()
    path_str = get_value(config, "store.path") or DEFAULTS["store"]["path"]
    return Path(path_str).expanduser()


def get_seqcol_servers(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Get the list of seqcol servers.

    Args:
        config: Optional config dict; if None, loads from file.

    Returns:
        List of server dicts with 'url' and optional 'name' keys.
    """
    if config is None:
        config = load_config()
    return config.get("seqcol_servers", DEFAULTS["seqcol_servers"])


def get_remote_stores(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Get the list of remote RefgetStores.

    Args:
        config: Optional config dict; if None, loads from file.

    Returns:
        List of store dicts with 'url' and optional 'name' keys.
    """
    if config is None:
        config = load_config()
    return config.get("remote_stores", DEFAULTS["remote_stores"])


def get_sequence_servers(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Get the list of sequence servers.

    Args:
        config: Optional config dict; if None, loads from file.

    Returns:
        List of server dicts with 'url' and optional 'name' keys.
    """
    if config is None:
        config = load_config()
    return config.get("sequence_servers", DEFAULTS["sequence_servers"])


def get_admin_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Get the admin/database configuration.

    Args:
        config: Optional config dict; if None, loads from file.

    Returns:
        Dict with postgres connection parameters.
    """
    if config is None:
        config = load_config()
    return config.get("admin", DEFAULTS["admin"])


def _deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Create a deep copy of a dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            # Deep copy list contents (handles lists of dicts like server configs)
            result[key] = [
                _deep_copy_dict(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[key] = value
    return result


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge override config into base config.

    Lists are replaced entirely, not merged.
    """
    result = _deep_copy_dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to config."""
    result = _deep_copy_dict(config)

    for env_var, mapping in ENV_VAR_MAPPINGS.items():
        value = os.environ.get(env_var)
        if value is None:
            continue

        if env_var == "REFGET_CONFIG":
            # This is handled separately
            continue
        elif isinstance(mapping, tuple):
            # Nested key (e.g., ("store", "path"))
            section, key = mapping
            if section not in result:
                result[section] = {}
            result[section][key] = value
        elif mapping in ("remote_stores", "seqcol_servers", "sequence_servers"):
            # Single URL override replaces the list
            result[mapping] = [{"url": value, "name": "env"}]

    return result
