"""
RefgetStore operations for the refget CLI.

Commands for managing local and remote RefgetStores, including
adding, pulling, and exporting sequence collections.

Commands:
    init        - Initialize local store
    add         - Import FASTA to local store
    list        - List collections or sequences in store
    get         - Get collection or sequence by digest
    pull        - Pull collection from remote
    export      - Export collection as FASTA
    fai         - Generate .fai from digest
    chrom-sizes - Generate chrom.sizes from digest
    stats       - Store statistics
"""

import os
import tempfile
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Iterator, List, Optional

import typer

from refget.cli.config_manager import get_remote_stores, get_seqcol_servers, get_store_path
from refget.cli.output import (
    EXIT_FILE_NOT_FOUND,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    check_dependency,
    print_error,
    print_json,
)


class StorageModeChoice(str, Enum):
    """Storage mode choices for CLI."""

    encoded = "encoded"
    raw = "raw"


@contextmanager
def _temp_file_path(suffix: str = ".fa") -> Iterator[str]:
    """Context manager that yields a temp file path and cleans up on exit."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)


app = typer.Typer(
    name="store",
    help="RefgetStore operations",
    no_args_is_help=True,
)


def _get_store_path(path: Optional[Path]) -> Path:
    """Get the store path from CLI arg or config."""
    if path is not None:
        return path.expanduser().resolve()
    return get_store_path()


def _get_collection_digests(store) -> set:
    """Get the set of collection digest strings from a store."""
    return {meta.digest for meta in store.list_collections()}


def _load_store(path: Optional[Path], must_exist: bool = True, remote: Optional[str] = None):
    """
    Load a RefgetStore from local path or remote server.

    Args:
        path: Optional path override (uses config if None)
        must_exist: If True, error if store doesn't exist
        remote: Optional remote store URL (overrides path)

    Returns:
        RefgetStore instance
    """
    check_dependency("gtars", "store", "store")
    from refget.store import RefgetStore

    # Remote store takes precedence
    if remote:
        cache_path = _get_store_path(path) / ".remote_cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        return RefgetStore.open_remote(str(cache_path), remote)

    store_path = _get_store_path(path)

    if must_exist:
        if not store_path.exists():
            print_error(f"Store not found at {store_path}", EXIT_FILE_NOT_FOUND)
        if not RefgetStore.store_exists(str(store_path)):
            # Empty directory - use on_disk which handles initialization
            return RefgetStore.on_disk(str(store_path))
        return RefgetStore.open_local(str(store_path))
    else:
        # Create or load
        return RefgetStore.on_disk(str(store_path))


def _ensure_collection_loaded(store, digest: str) -> None:
    """
    Ensure a collection is loaded in the store.

    When a store is loaded from disk, collections are listed but not
    fully loaded. This triggers the lazy load by accessing a sequence.

    Args:
        store: RefgetStore instance
        digest: Collection digest to ensure is loaded
    """
    if not store.is_collection_loaded(digest):
        try:
            store.get_collection(digest)
        except Exception as e:
            print_error(f"Collection not found: {digest} ({e})", EXIT_FAILURE)


@app.command()
def init(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Path for the store (default: from config or ~/.refget/store)",
    ),
) -> None:
    """
    Initialize a local RefgetStore.

    Creates the store directory structure if it doesn't exist.
    """
    check_dependency("gtars", "store", "store")
    from refget.store import RefgetStore

    store_path = _get_store_path(path)

    # Create parent directories if needed
    store_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize the store (creates index files)
    store = RefgetStore.on_disk(str(store_path))

    print_json(
        {
            "path": str(store_path),
            "status": "initialized",
        }
    )
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def add(
    fasta: Path = typer.Argument(
        ...,
        help="Path to FASTA file to import (supports .gz)",
        exists=True,
        readable=True,
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    mode: Optional[StorageModeChoice] = typer.Option(
        None,
        "--mode",
        "-m",
        help="Storage mode override: encoded (compressed) or raw",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress output",
    ),
) -> None:
    """
    Import a FASTA file to the local store.

    Creates a sequence collection from the FASTA and stores all sequences.

    Storage modes (--mode):
        encoded - Bit-packed compression (default, ~4x smaller)
        raw     - Uncompressed ASCII (faster access, easier to inspect)

    Note: Storage mode is specified at add time, not init, because mode
    applies to how sequences are encoded - an empty store has no sequences.

    Outputs JSON: {"digest": "abc123...", "sequences": 25}
    """
    store = _load_store(path, must_exist=True)

    # Set quiet mode if requested
    store.set_quiet(quiet)

    # Override storage mode if specified
    if mode is not None:
        from refget.store import StorageMode

        if mode == StorageModeChoice.raw:
            store.set_encoding_mode(StorageMode.Raw)
        else:
            store.set_encoding_mode(StorageMode.Encoded)

    # Add the FASTA file - returns (metadata, was_new) with all info we need
    metadata, was_new = store.add_sequence_collection_from_fasta(str(fasta.resolve()))

    print_json(
        {
            "digest": metadata.digest,
            "fasta": str(fasta.resolve()),
            "sequences": metadata.n_sequences,
            "was_new": was_new,
        }
    )
    raise typer.Exit(EXIT_SUCCESS)


@app.command("list")
def list_items(
    sequences: bool = typer.Option(
        False,
        "--sequences",
        "-s",
        help="List sequences instead of collections",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    List collections or sequences in the store.

    By default, lists collections. Use --sequences to list individual sequences.

    Outputs JSON:
        Collections: {"collections": [{"digest": "..."}, ...]}
        Sequences:   {"sequences": [{"digest": "...", "name": "...", "length": N}, ...]}
    """
    store = _load_store(path, remote=remote)

    if sequences:
        items = []
        for meta in store.list_sequences():
            items.append(
                {
                    "digest": meta.sha512t24u,
                    "name": meta.name,
                    "length": meta.length,
                }
            )
        print_json({"sequences": items})
    else:
        collections = []
        for meta in store.list_collections():
            collections.append(
                {
                    "digest": meta.digest,
                }
            )
        print_json({"collections": collections})

    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def get(
    digest: str = typer.Argument(
        ...,
        help="Collection or sequence digest",
    ),
    sequence: bool = typer.Option(
        False,
        "--sequence",
        "-s",
        help="Get sequence instead of collection",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Sequence name (when getting sequence from collection)",
    ),
    start: Optional[int] = typer.Option(
        None,
        "--start",
        help="Start position for subsequence (0-based, inclusive)",
    ),
    end: Optional[int] = typer.Option(
        None,
        "--end",
        help="End position for subsequence (0-based, exclusive)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Get a collection or sequence by digest.

    By default, returns the full sequence collection with names, lengths, and sequences.
    Use --sequence to get a sequence instead.

    Examples:
        refget store get <coll_digest>                     # Get collection
        refget store get <seq_digest> -s                   # Get sequence
        refget store get <coll_digest> -s -n chr1          # Sequence by name
        refget store get <seq_digest> -s --start 0 --end 100  # Subsequence

    Outputs JSON for collections: {"names": [...], "lengths": [...], "sequences": [...]}
    Outputs raw sequence text for sequences.
    """
    store = _load_store(path, remote=remote)

    if sequence:
        # Sequence retrieval mode
        seq_data = None

        if name is not None:
            # Get sequence by collection + name
            try:
                record = store.get_sequence_by_name(digest, name)
            except KeyError as e:
                print_error(str(e), EXIT_FAILURE)
                return

            if start is not None and end is not None:
                # Get substring using the sequence digest
                try:
                    seq_data = store.get_substring(record.metadata.sha512t24u, start, end)
                except KeyError as e:
                    print_error(str(e), EXIT_FAILURE)
                    return
            elif start is not None or end is not None:
                print_error("Both --start and --end must be provided for substring", EXIT_FAILURE)
                return
            else:
                seq_data = record.decode()
        else:
            # Direct sequence lookup by digest
            if start is not None and end is not None:
                try:
                    seq_data = store.get_substring(digest, start, end)
                except KeyError as e:
                    print_error(str(e), EXIT_FAILURE)
                    return
            elif start is not None or end is not None:
                print_error("Both --start and --end must be provided for substring", EXIT_FAILURE)
                return
            else:
                try:
                    record = store.get_sequence(digest)
                    seq_data = record.decode()
                except KeyError as e:
                    print_error(str(e), EXIT_FAILURE)
                    return

        # Output raw sequence to stdout
        print(seq_data)
    else:
        # Collection retrieval mode (default)
        try:
            result = store.get_collection_level2(digest)
        except Exception:
            print_error(f"Collection not found: {digest}", EXIT_FAILURE)
            return

        print_json(result)

    raise typer.Exit(EXIT_SUCCESS)


def _find_remote_urls(remote_override: Optional[str] = None) -> List[str]:
    """
    Find remote RefgetStore URLs to try.

    Resolution order:
        1. --remote flag (direct RefgetStore URL)
        2. Configured remote_stores
        3. Configured seqcol_servers (discover RefgetStore via service-info)

    Returns:
        List of remote store URLs to try, in priority order.
    """
    if remote_override:
        return [remote_override]

    urls: List[str] = []

    # Try configured remote stores
    for store_config in get_remote_stores():
        if "url" in store_config:
            urls.append(store_config["url"])

    # Try discovering from seqcol servers' service-info
    from refget.clients import SequenceCollectionClient

    for srv in get_seqcol_servers():
        try:
            client = SequenceCollectionClient(urls=[srv["url"]], raise_errors=False)
            url = client.get_refget_store_url()
            if url and url not in urls:
                urls.append(url)
        except Exception:
            continue

    return urls


@app.command()
def pull(
    digest: Optional[str] = typer.Argument(
        None,
        help="Collection digest to pull",
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="File containing digests (one per line) for batch pull",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (default: try configured remote_stores)",
    ),
    eager: bool = typer.Option(
        False,
        "--eager",
        "-e",
        help="Pre-fetch all sequences immediately (default: lazy/on-demand)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress output",
    ),
) -> None:
    """
    Pull a collection from a remote store to local cache.

    By default, only metadata is fetched immediately. Sequence data is
    downloaded on-demand when accessed (lazy loading). Use --eager to
    pre-fetch all sequences.

    Resolution order (if --remote not specified):
        1. Check local store (already cached?)
        2. Try configured remote_stores in priority order
        3. Try seqcol_servers (discover RefgetStore via service-info)

    Use --file for batch operations with multiple digests.

    Examples:
        refget store pull ABC123 --remote https://example.com/store
        refget store pull ABC123 --eager  # Pre-fetch all sequences
        refget store pull --file digests.txt --remote https://example.com/store
    """
    check_dependency("gtars", "store", "store")
    from refget.store import RefgetStore

    # Validate arguments
    if digest is None and file is None:
        print_error("Must provide either a digest or --file", EXIT_FAILURE)
    if digest is not None and file is not None:
        print_error("Cannot specify both digest and --file", EXIT_FAILURE)

    # Collect digests to pull
    digests: List[str] = []
    if digest:
        digests.append(digest)
    elif file:
        if not file.exists():
            print_error(f"File not found: {file}", EXIT_FILE_NOT_FOUND)
        digests = [line.strip() for line in file.read_text().splitlines() if line.strip()]

    if not digests:
        print_error("No digests to pull", EXIT_FAILURE)

    # Determine remote URLs to try
    remote_urls = _find_remote_urls(remote)

    if not remote_urls:
        print_error(
            "No remote store found. Use --remote or configure remote_stores:\n"
            "  refget config add remote_store https://example.com/store",
            EXIT_FAILURE,
        )

    # Get local store path for caching
    store_path = _get_store_path(path)
    cache_path = store_path / ".remote_cache"
    cache_path.mkdir(parents=True, exist_ok=True)

    # Check local store first
    local_collections: set = set()
    if RefgetStore.store_exists(str(store_path)):
        try:
            local_store = RefgetStore.open_local(str(store_path))
            local_collections = _get_collection_digests(local_store)
        except Exception:
            pass  # Local store not available, continue with remote

    results = []
    for dig in digests:
        # Check if already in local store
        if dig in local_collections:
            results.append({"digest": dig, "status": "already_local", "source": "local"})
            continue

        # Try remote stores in order
        pulled = False
        for remote_url in remote_urls:
            try:
                # Connect to remote with local caching
                remote_store = RefgetStore.open_remote(str(cache_path), remote_url)
                remote_store.set_quiet(quiet)

                # Check if collection exists on remote
                remote_collections = _get_collection_digests(remote_store)
                if dig not in remote_collections:
                    continue  # Try next remote

                # Collection found - metadata is now cached
                result = {
                    "digest": dig,
                    "status": "pulled",
                    "source": remote_url,
                    "eager": eager,
                }

                if eager:
                    # Pre-fetch all sequences
                    coll = remote_store.get_collection(dig)
                    seq_count = 0
                    for seq in coll.sequences:
                        # Accessing the sequence triggers download and caching
                        _ = seq.decode()
                        seq_count += 1
                    result["sequences_fetched"] = seq_count

                results.append(result)
                pulled = True
                break  # Success, don't try other remotes

            except Exception as e:
                # Try next remote
                if not quiet:
                    import sys

                    print(f"Failed to pull from {remote_url}: {e}", file=sys.stderr)
                continue

        if not pulled:
            results.append(
                {
                    "digest": dig,
                    "status": "not_found",
                    "tried": remote_urls,
                }
            )

    # Output results
    if len(results) == 1:
        print_json(results[0])
    else:
        print_json({"results": results})

    # Exit with error if any failed
    failed = [r for r in results if r["status"] == "not_found"]
    if failed:
        raise typer.Exit(EXIT_FAILURE)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def export(
    digest: str = typer.Argument(
        ...,
        help="Collection digest to export",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output FASTA file path (default: stdout)",
    ),
    bed: Optional[Path] = typer.Option(
        None,
        "--bed",
        "-b",
        help="BED file for region extraction",
    ),
    names: Optional[List[str]] = typer.Option(
        None,
        "--name",
        "-n",
        help="Sequence names to include (can be repeated)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
    line_width: int = typer.Option(
        80,
        "--line-width",
        "-w",
        help="FASTA line width (default: 80)",
    ),
) -> None:
    """
    Export a collection as a FASTA file.

    Can export:
        - Full collection
        - Subset by sequence names (--name chr1 --name chr2)
        - Regions from BED file (--bed regions.bed)

    If no output file is specified, exports to stdout.
    """
    store = _load_store(path, remote=remote)

    # Ensure collection is loaded (required for export)
    _ensure_collection_loaded(store, digest)

    def _do_export(output_path: str) -> None:
        """Perform the actual export to a file path."""
        if bed is not None:
            if not bed.exists():
                print_error(f"BED file not found: {bed}", EXIT_FILE_NOT_FOUND)
            store.export_fasta_from_regions(digest, str(bed.resolve()), output_path)
        else:
            sequence_names = list(names) if names else None
            store.export_fasta(digest, output_path, sequence_names, line_width)

    if output is None:
        # Export to stdout via temp file (context manager handles cleanup)
        with _temp_file_path(suffix=".fa") as temp_path:
            _do_export(temp_path)
            with open(temp_path, "r") as f:
                print(f.read(), end="")
    else:
        # Export directly to output file
        output_path = str(output.resolve())
        _do_export(output_path)
        print_json(
            {
                "digest": digest,
                "output": output_path,
                "status": "exported",
            }
        )

    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def fai(
    digest: str = typer.Argument(
        ...,
        help="Collection digest",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Generate .fai index from a collection digest.

    Outputs samtools-compatible .fai format (tab-separated).

    Note: Byte offset columns will be placeholder values since the collection
    may not correspond to any specific FASTA file layout.
    """
    store = _load_store(path, remote=remote)

    try:
        lvl2 = store.get_collection_level2(digest)
    except Exception:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)
        return

    lines = []
    for name, length in zip(lvl2["names"], lvl2["lengths"]):
        lines.append(f"{name}\t{length}\t0\t80\t81")

    fai_content = "\n".join(lines)
    if lines:
        fai_content += "\n"

    if output is not None:
        output.write_text(fai_content)
    else:
        print(fai_content, end="")

    raise typer.Exit(EXIT_SUCCESS)


@app.command("chrom-sizes")
def chrom_sizes(
    digest: str = typer.Argument(
        ...,
        help="Collection digest",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Generate chrom.sizes from a collection digest.

    Outputs UCSC-compatible chrom.sizes format (tab-separated name/length).
    """
    store = _load_store(path, remote=remote)

    try:
        lvl2 = store.get_collection_level2(digest)
    except Exception:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)
        return

    lines = []
    for name, length in zip(lvl2["names"], lvl2["lengths"]):
        lines.append(f"{name}\t{length}")

    sizes_content = "\n".join(lines)
    if lines:
        sizes_content += "\n"

    if output is not None:
        output.write_text(sizes_content)
    else:
        print(sizes_content, end="")

    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def stats(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Display store statistics.

    Outputs JSON with storage_mode, collections, and sequences counts.

    Example output:
        {"collections": 3, "sequences": 75, "storage_mode": "Encoded"}
    """
    store = _load_store(path, remote=remote)

    stats_obj = store.stats()

    # Convert stats object to dict for JSON output
    # The stats object should have properties like collections, sequences, etc.
    stats_dict = {}
    if hasattr(stats_obj, "__iter__"):
        # If it's dict-like
        for key, value in stats_obj.items():
            stats_dict[key] = value
    elif hasattr(stats_obj, "__dict__"):
        stats_dict = vars(stats_obj)
    else:
        # Try to convert to string representation
        stats_dict = {"stats": str(stats_obj)}

    # Ensure 'collections' key exists as an integer
    # The underlying stats may use 'n_collections' as a string
    if "n_collections" in stats_dict and "collections" not in stats_dict:
        stats_dict["collections"] = int(stats_dict["n_collections"])
    elif "collections" in stats_dict:
        # Ensure it's an integer
        stats_dict["collections"] = int(stats_dict["collections"])
    else:
        # Fallback: count collections ourselves
        stats_dict["collections"] = len(store.list_collections())

    print_json(stats_dict)
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def remove(
    digest: str = typer.Argument(
        ...,
        help="Collection digest to remove",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
) -> None:
    """
    Remove a collection from the store.

    This removes the collection from the store index.
    Note: Associated sequences are not removed as they may be shared
    with other collections.
    """
    store = _load_store(path)

    removed = store.remove_collection(digest)
    if not removed:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)

    print_json(
        {
            "digest": digest,
            "status": "removed",
        }
    )
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def metadata(
    digest: str = typer.Argument(help="Collection digest"),
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Store path"
    ),
):
    """Show FHR metadata for a collection."""
    store = _load_store(path)
    fhr = store.get_fhr_metadata(digest)
    if fhr is None:
        print_error(f"No FHR metadata for collection {digest}", EXIT_FAILURE)
    import json

    print(json.dumps(fhr.to_dict(), indent=2))
    raise typer.Exit(EXIT_SUCCESS)


@app.command("metadata-set")
def metadata_set(
    digest: str = typer.Argument(help="Collection digest"),
    file: Path = typer.Argument(help="Path to FHR JSON file"),
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Store path"
    ),
):
    """Set FHR metadata for a collection from a JSON file."""
    store = _load_store(path)
    store.load_fhr_metadata(digest, str(file))
    print(f"Set FHR metadata for collection {digest}")
    raise typer.Exit(EXIT_SUCCESS)
