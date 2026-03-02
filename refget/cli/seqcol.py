"""
Sequence collection API commands for the refget CLI.

Commands for interacting with seqcol servers for comparisons,
lookups, and metadata retrieval.

Commands:
    show      - Get seqcol (local store first, then server)
    compare   - Compare two seqcols
    list      - List collections on server
    search    - Find collections by attribute digest
    attribute - Retrieve attribute array by digest
    info      - Server info/capabilities
"""

import json
from pathlib import Path
from typing import Optional

import typer

from refget.cli.config_manager import get_seqcol_servers, get_store_path
from refget.cli.output import (
    EXIT_FAILURE,
    EXIT_NETWORK_ERROR,
    EXIT_SUCCESS,
    print_error,
    print_json,
    suppress_stdout,
)

# Heavy imports moved inside functions to speed up CLI startup:
# - refget.clients (requests ~51ms)
# - refget.utils (jsonschema ~60ms)
# - refget.store (gtars ~100ms)


def _get_client(server_override: Optional[str] = None):
    """
    Get a SequenceCollectionClient configured with the appropriate server URL.

    Args:
        server_override: Optional server URL to use instead of config

    Returns:
        Configured SequenceCollectionClient
    """
    from refget.clients import SequenceCollectionClient

    if server_override:
        urls = [server_override]
    else:
        servers = get_seqcol_servers()
        urls = [s["url"] for s in servers]
    return SequenceCollectionClient(urls=urls, raise_errors=False)


def _collection_to_seqcol_dict(store, digest: str, level: int = 2) -> Optional[dict]:
    """
    Convert a RefgetStore collection to seqcol API dict format.

    Args:
        store: RefgetStore instance with the collection loaded
        digest: Collection digest
        level: 1 for attribute digests only, 2 for full arrays

    Returns:
        Seqcol dict in API format, or None if collection not found.
    """
    try:
        if level == 1:
            return store.get_collection_level1(digest)
        else:
            return store.get_collection_level2(digest)
    except Exception:
        return None


def _get_local_seqcol(digest: str, level: int = 2) -> Optional[dict]:
    """
    Try to get a seqcol from the local RefgetStore.

    Args:
        digest: Collection digest to look up
        level: 1 for attribute digests only, 2 for full arrays

    Returns:
        Seqcol dict if found locally, None otherwise.
    """
    try:
        from refget.store import RefgetStore
    except ImportError:
        # gtars not installed - can't use local store
        return None

    store_path = get_store_path()

    # Check if store exists
    if not RefgetStore.store_exists(str(store_path)):
        return None

    try:
        store = RefgetStore.open_local(str(store_path))
        store.set_quiet(True)
        return _collection_to_seqcol_dict(store, digest, level)
    except Exception:
        # Any error (store corruption, etc.) - fall back to remote
        return None


def _compute_snlp_digest(seqcol_dict: dict) -> str:
    """
    Compute the sorted_name_length_pairs digest from a seqcol dict.

    Args:
        seqcol_dict: Level 2 seqcol dict with names and lengths arrays

    Returns:
        The snlp digest (coordinate system identifier)
    """
    from refget.utils import build_sorted_name_length_pairs, canonical_str
    from refget.digests import sha512t24u_digest

    snlp_digests = build_sorted_name_length_pairs(seqcol_dict)
    return sha512t24u_digest(canonical_str(snlp_digests))


def _detect_input_type(input_str: str) -> str:
    """
    Detect the type of seqcol input.

    Args:
        input_str: Input string (file path or digest)

    Returns:
        One of: "fasta", "json", "digest"
    """
    path = Path(input_str)
    if path.exists():
        lower_name = path.name.lower()
        if lower_name.endswith((".fa", ".fasta", ".fa.gz", ".fasta.gz")):
            return "fasta"
        elif lower_name.endswith(".json"):
            return "json"
        # If file exists but doesn't match known extensions, treat as JSON
        return "json"
    # Not a file, assume it's a digest
    return "digest"


def _load_seqcol(input_str: str, client, level: int = 2) -> Optional[dict]:
    """
    Load a seqcol from various input types.

    Args:
        input_str: Input (file path or digest)
        client: SequenceCollectionClient for fetching remote digests
        level: Seqcol level for remote fetches

    Returns:
        Level 2 seqcol dict, or None on error
    """
    input_type = _detect_input_type(input_str)

    if input_type == "fasta":
        try:
            from refget.utils import fasta_to_seqcol_dict

            # Suppress stdout to hide verbose gtars output
            with suppress_stdout():
                return fasta_to_seqcol_dict(input_str)
        except ImportError:
            print_error(
                "FASTA processing requires gtars. Install with: pip install refget[store]",
                EXIT_FAILURE,
            )
            return None
        except Exception as e:
            print_error(f"Failed to process FASTA file: {e}", EXIT_FAILURE)
            return None

    elif input_type == "json":
        try:
            with open(input_str, "r") as f:
                return json.load(f)
        except Exception as e:
            print_error(f"Failed to read JSON file: {e}", EXIT_FAILURE)
            return None

    else:  # digest
        # Try local store first
        result = _get_local_seqcol(input_str, level=level)
        if result is not None:
            return result

        # Fall back to remote
        result = client.get_collection(input_str, level=level)
        if result is None:
            print_error(f"Could not fetch seqcol for digest: {input_str}", EXIT_FAILURE)
        return result


app = typer.Typer(
    name="seqcol",
    help="Sequence collection API",
    no_args_is_help=True,
)


@app.command()
def show(
    digest: str = typer.Argument(
        ...,
        help="Seqcol digest to retrieve",
    ),
    level: int = typer.Option(
        2,
        "--level",
        "-l",
        help="Seqcol level: 1 (digests only) or 2 (full arrays)",
        min=1,
        max=2,
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
) -> None:
    """
    Get a sequence collection by digest.

    Resolution order: local store -> configured seqcol_servers -> --server override

    Level 1 returns attribute digests only.
    Level 2 (default) returns full arrays.
    """
    # Try local store first
    result = _get_local_seqcol(digest, level=level)
    if result is not None:
        print_json(result)
        raise typer.Exit(EXIT_SUCCESS)

    # Fall back to remote servers
    client = _get_client(server)

    try:
        result = client.get_collection(digest, level=level)
    except ConnectionError as e:
        print_error(f"Network error: {e}", EXIT_NETWORK_ERROR)
        return

    if result is None:
        print_error(f"Seqcol not found: {digest}", EXIT_FAILURE)
        return

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def compare(
    a: str = typer.Argument(
        ...,
        help="First seqcol: digest, FASTA file, or .seqcol.json file",
    ),
    b: str = typer.Argument(
        ...,
        help="Second seqcol: digest, FASTA file, or .seqcol.json file",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress output; use exit code only (0=compatible, 1=incompatible)",
    ),
) -> None:
    """
    Compare two sequence collections.

    Accepts flexible inputs:
        - <digest>         Fetches from local store or server
        - <file.fa>        Computes seqcol on the fly
        - <file.seqcol.json>  Uses local seqcol file

    Outputs JSON comparison result with compatibility info.

    Exit codes:
        0 = compatible
        1 = incompatible
    """
    from refget.utils import compare_seqcols

    client = _get_client(server)

    # Load both seqcols
    seqcol_a = _load_seqcol(a, client, level=2)
    if seqcol_a is None:
        return  # Error already printed

    seqcol_b = _load_seqcol(b, client, level=2)
    if seqcol_b is None:
        return  # Error already printed

    # Perform comparison
    try:
        comparison_result = compare_seqcols(seqcol_a, seqcol_b)
    except Exception as e:
        print_error(f"Comparison failed: {e}", EXIT_FAILURE)
        return

    # Determine compatibility based on sorted_name_length_pairs digest match
    # Two seqcols are "compatible" if they share the same coordinate system
    # We compute snlp digest directly from the level 2 data (names + lengths arrays)
    snlp_a = _compute_snlp_digest(seqcol_a)
    snlp_b = _compute_snlp_digest(seqcol_b)
    is_compatible = snlp_a == snlp_b

    # Add compatibility flag to result
    comparison_result["compatible"] = is_compatible

    if not quiet:
        print_json(comparison_result)

    raise typer.Exit(EXIT_SUCCESS if is_compatible else EXIT_FAILURE)


@app.command("list")
def list_collections(
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Maximum number of collections to return",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Offset for pagination",
    ),
) -> None:
    """
    List collections available on the server.

    Returns a paginated list of collection digests and metadata.
    """
    client = _get_client(server)

    # Convert offset/limit to page/page_size
    page = (offset // limit) + 1 if limit > 0 else 1
    page_size = limit

    try:
        result = client.list_collections(page=page, page_size=page_size)
    except ConnectionError as e:
        print_error(f"Network error: {e}", EXIT_NETWORK_ERROR)
        return

    if result is None:
        print_error("Failed to list collections from server", EXIT_FAILURE)
        return

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


def _search_local_store(filters: dict) -> Optional[list]:
    """Search the local RefgetStore for collections matching attribute filters."""
    try:
        from refget.store import RefgetStore
    except ImportError:
        return None

    store_path = get_store_path()

    if not RefgetStore.store_exists(str(store_path)):
        return None

    try:
        store = RefgetStore.open_local(str(store_path))
        store.set_quiet(True)

        # Search each filter; results must match ALL filters (intersection)
        result_sets = []
        for attr_name, attr_digest in filters.items():
            matches = store.find_collections_by_attribute(attr_name, attr_digest)
            result_sets.append(set(matches))

        if not result_sets:
            return None

        # Intersection of all filter results
        matching = result_sets[0]
        for s in result_sets[1:]:
            matching &= s

        if not matching:
            return None

        return [{"digest": d} for d in sorted(matching)]
    except Exception:
        return None


@app.command()
def search(
    names: Optional[str] = typer.Option(
        None,
        "--names",
        help="Names array digest to search for",
    ),
    lengths: Optional[str] = typer.Option(
        None,
        "--lengths",
        help="Lengths array digest to search for",
    ),
    sequences: Optional[str] = typer.Option(
        None,
        "--sequences",
        help="Sequences array digest to search for",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
    local: bool = typer.Option(
        False,
        "--local",
        help="Search only the local store (skip remote)",
    ),
    no_local: bool = typer.Option(
        False,
        "--no-local",
        help="Skip local store and search remote only",
    ),
) -> None:
    """
    Find collections that share an attribute.

    The attribute digest is the digest of an attribute array
    (e.g., the names array digest from level 1 output).

    By default, searches the local store first, then falls back to remote.
    Use --local to search only locally, or --no-local to skip local search.

    Example workflow:
        # Get names digest from level 1
        names_digest=$(refget fasta seqcol genome.fa --level 1 | jq -r '.names')
        # Search for collections with same names
        refget seqcol search --names $names_digest
    """
    # Build filters from provided options
    filters = {}
    if names:
        filters["names"] = names
    if lengths:
        filters["lengths"] = lengths
    if sequences:
        filters["sequences"] = sequences

    if not filters:
        print_error(
            "At least one search filter required (--names, --lengths, or --sequences)",
            EXIT_FAILURE,
        )
        return

    # Try local store first (unless --no-local)
    if not no_local:
        local_results = _search_local_store(filters)
        if local_results is not None:
            print_json(local_results)
            raise typer.Exit(EXIT_SUCCESS)

        if local:
            # --local flag set but no results found locally
            print_error("No matching collections found in local store", EXIT_FAILURE)
            return

    # Fall back to remote server
    client = _get_client(server)

    try:
        result = client.list_collections(**filters)
    except ConnectionError as e:
        print_error(f"Network error: {e}", EXIT_NETWORK_ERROR)
        return

    if result is None:
        print_error("Search failed", EXIT_FAILURE)
        return

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def attribute(
    digest: str = typer.Argument(
        ...,
        help="Attribute array digest",
    ),
    attribute_name: str = typer.Option(
        "names",
        "--attribute",
        "-a",
        help="Attribute type: names, lengths, sequences, sorted_name_length_pairs",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
) -> None:
    """
    Retrieve the actual array values for an attribute digest.

    Hits the /attribute/collection/<attribute>/<digest> API endpoint.

    Returns the array values (e.g., ["chr1", "chr2", ...] for a names digest).
    """
    client = _get_client(server)

    try:
        result = client.get_attribute(attribute_name, digest)
    except ConnectionError as e:
        print_error(f"Network error: {e}", EXIT_NETWORK_ERROR)
        return

    if result is None:
        print_error(f"Attribute not found: {attribute_name}/{digest}", EXIT_FAILURE)
        return

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def info(
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server URL override",
    ),
) -> None:
    """
    Get server information and capabilities.

    Returns service-info JSON with supported features,
    available endpoints, and RefgetStore URL if available.
    """
    client = _get_client(server)

    try:
        result = client.service_info()
    except ConnectionError as e:
        print_error(f"Network error: {e}", EXIT_NETWORK_ERROR)
        return

    if result is None:
        print_error("Failed to get server info", EXIT_FAILURE)
        return

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def digest(
    file: str = typer.Argument(
        ...,
        help="Path to FASTA or .seqcol.json file",
    ),
) -> None:
    """
    Compute the seqcol digest of a file.

    Accepts either a FASTA file or a .seqcol.json file.
    Outputs JSON: {"digest": "abc123...", "file": "name"}
    """
    from refget.utils import seqcol_digest as compute_seqcol_digest

    path = Path(file)
    if not path.exists():
        print_error(f"File not found: {file}", EXIT_FAILURE)
        return

    lower_name = path.name.lower()

    # Determine file type and load seqcol
    if lower_name.endswith((".fa", ".fasta", ".fa.gz", ".fasta.gz")):
        # FASTA file - compute seqcol from FASTA
        try:
            from refget.utils import fasta_to_seqcol_dict

            # Suppress stdout to hide verbose gtars output
            with suppress_stdout():
                seqcol_data = fasta_to_seqcol_dict(file)
        except ImportError:
            print_error(
                "FASTA processing requires gtars. Install with: pip install refget[store]",
                EXIT_FAILURE,
            )
            return
        except Exception as e:
            print_error(f"Failed to process FASTA file: {e}", EXIT_FAILURE)
            return
    elif lower_name.endswith(".json"):
        # JSON file - load and compute digest
        try:
            with open(file, "r") as f:
                seqcol_data = json.load(f)
        except Exception as e:
            print_error(f"Failed to read JSON file: {e}", EXIT_FAILURE)
            return
    else:
        print_error(
            f"Unsupported file type: {file}. Expected FASTA or .seqcol.json",
            EXIT_FAILURE,
        )
        return

    # Compute digest
    try:
        digest_value = compute_seqcol_digest(seqcol_data)
    except Exception as e:
        print_error(f"Failed to compute digest: {e}", EXIT_FAILURE)
        return

    print_json({"digest": digest_value, "file": path.name})
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def validate(
    file: str = typer.Argument(
        ...,
        help="Path to .seqcol.json file to validate",
    ),
) -> None:
    """
    Validate a seqcol JSON file.

    Checks that the file is valid JSON and conforms to the seqcol schema.
    Exit code 0 = valid, non-zero = invalid.
    """
    path = Path(file)
    if not path.exists():
        print_error(f"File not found: {file}", EXIT_FAILURE)
        return

    # Load JSON
    try:
        with open(file, "r") as f:
            seqcol_data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}", EXIT_FAILURE)
        return
    except Exception as e:
        print_error(f"Failed to read file: {e}", EXIT_FAILURE)
        return

    # Validate seqcol structure
    required_attrs = ["names", "lengths", "sequences"]
    errors = []

    for attr in required_attrs:
        if attr not in seqcol_data:
            errors.append(f"Missing required attribute: {attr}")

    # Check that all arrays have the same length
    lengths = {}
    for attr in seqcol_data:
        if isinstance(seqcol_data[attr], list):
            lengths[attr] = len(seqcol_data[attr])

    if lengths:
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            errors.append(f"Array length mismatch: {dict(lengths)}")

    if errors:
        for error in errors:
            print_error(error)  # Print all errors without exiting
        raise typer.Exit(EXIT_FAILURE)

    print_json({"valid": True, "file": path.name})
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def attributes(
    file: str = typer.Argument(
        ...,
        help="Path to .seqcol.json file",
    ),
) -> None:
    """
    List attributes in a seqcol JSON file.

    Shows the attribute names and their array lengths.
    """
    path = Path(file)
    if not path.exists():
        print_error(f"File not found: {file}", EXIT_FAILURE)
        return

    # Load JSON
    try:
        with open(file, "r") as f:
            seqcol_data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}", EXIT_FAILURE)
        return
    except Exception as e:
        print_error(f"Failed to read file: {e}", EXIT_FAILURE)
        return

    # List attributes
    result = {}
    for attr, value in seqcol_data.items():
        if isinstance(value, list):
            result[attr] = {"length": len(value)}
        else:
            result[attr] = {"type": type(value).__name__}

    print_json(result)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def schema() -> None:
    """
    Show the seqcol schema definition.

    Displays the JSON schema for a valid sequence collection object.
    """
    schema_def = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Sequence Collection",
        "description": "A GA4GH Sequence Collection object",
        "type": "object",
        "required": ["names", "lengths", "sequences"],
        "properties": {
            "names": {
                "type": "array",
                "description": "Sequence names (chromosome/contig identifiers)",
                "items": {"type": "string"},
            },
            "lengths": {
                "type": "array",
                "description": "Sequence lengths in base pairs",
                "items": {"type": "integer", "minimum": 0},
            },
            "sequences": {
                "type": "array",
                "description": "GA4GH refget sequence digests (sha512t24u)",
                "items": {"type": "string"},
            },
            "sorted_name_length_pairs": {
                "type": "array",
                "description": "Sorted name-length tuples for order-invariant comparison",
                "items": {"type": "string"},
            },
        },
        "additionalProperties": True,
    }
    print_json(schema_def)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def servers() -> None:
    """
    List known seqcol servers from configuration.

    Shows servers configured in ~/.refget/config.toml or environment.
    """
    servers_list = get_seqcol_servers()
    print_json({"servers": servers_list})
    raise typer.Exit(EXIT_SUCCESS)
