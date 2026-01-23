"""
RefgetStore operations for the refget CLI.

Commands for managing local and remote RefgetStores, including
adding, pulling, and exporting sequence collections.

Commands:
    init        - Initialize local store
    add         - Import FASTA to local store
    list        - List collections in store
    pull        - Pull collection from remote
    export      - Export collection as FASTA
    seq         - Get sequence/subsequence
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

from refget.cli.config_manager import get_store_path
from refget.cli.output import (
    EXIT_FILE_NOT_FOUND,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    check_dependency,
    not_implemented,
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


def _load_store(path: Optional[Path], must_exist: bool = True, server: Optional[str] = None):
    """
    Load a RefgetStore from local path or remote server.

    Args:
        path: Optional path override (uses config if None)
        must_exist: If True, error if store doesn't exist
        server: Optional remote server URL (overrides path)

    Returns:
        RefgetStore instance
    """
    check_dependency("gtars", "store", "store")
    from refget.store import RefgetStore

    # Remote store takes precedence
    if server:
        cache_path = _get_store_path(path) / ".remote_cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        return RefgetStore.load_remote(str(cache_path), server)

    store_path = _get_store_path(path)

    if must_exist:
        if not store_path.exists():
            print_error(f"Store not found at {store_path}", EXIT_FILE_NOT_FOUND)
        # Check if rgstore.json exists - if not, it's an empty store that needs on_disk
        # The store uses rgstore.json as its manifest file
        rgstore_path = store_path / "rgstore.json"
        if not rgstore_path.exists():
            # Empty store - use on_disk which handles initialization
            return RefgetStore.on_disk(str(store_path))
        return RefgetStore.load_local(str(store_path))
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
        # Get collection metadata to find a sequence name
        meta = store.get_collection_metadata(digest)
        if meta is None:
            print_error(f"Collection not found: {digest}", EXIT_FAILURE)
        # Force load by accessing a sequence (any sequence will do)
        # We use sequence_records to get the first sequence name
        try:
            for rec in store.sequence_records():
                # Get just one to force load
                _ = store.get_sequence_by_collection_and_name(digest, rec.metadata.name)
                break
        except (KeyError, AttributeError, StopIteration):
            # Collection may not have sequences yet, or wasn't properly saved.
            # This is acceptable - the caller will handle missing data downstream.
            pass


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

    print_json({
        "path": str(store_path),
        "status": "initialized",
    })
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

    print_json({
        "digest": metadata.digest,
        "fasta": str(fasta.resolve()),
        "sequences": metadata.n_sequences,
        "was_new": was_new,
    })
    raise typer.Exit(EXIT_SUCCESS)


@app.command("list")
def list_collections(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    List collections in the store.

    Outputs JSON: {"collections": [{"digest": "...", "sequences": N}, ...]}
    """
    store = _load_store(path, server=server)

    collections = []
    for digest in store.list_collections():
        collections.append({
            "digest": digest,
        })

    print_json({
        "collections": collections,
    })
    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def get(
    digest: str = typer.Argument(
        ...,
        help="Collection digest to retrieve",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Get a collection by digest.

    Returns the full sequence collection with names, lengths, and sequences.

    Outputs JSON: {"names": [...], "lengths": [...], "sequences": [...]}
    """
    store = _load_store(path, server=server)

    # Check if collection exists
    if digest not in store.list_collections():
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)
        return  # Unreachable, but clarifies control flow

    # Ensure collection is loaded
    _ensure_collection_loaded(store, digest)

    # Get collection data
    names = []
    lengths = []
    sequences = []

    for coll in store.collections():
        if coll.digest == digest:
            for seq in coll.sequences:
                m = seq.metadata
                names.append(m.name)
                lengths.append(m.length)
                sequences.append("SQ." + m.sha512t24u)
            break

    if not names:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)
        return  # Unreachable, but clarifies control flow

    print_json({
        "names": names,
        "lengths": lengths,
        "sequences": sequences,
    })
    raise typer.Exit(EXIT_SUCCESS)


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
) -> None:
    """
    Pull a collection from a remote store.

    Resolution order:
        1. Check local store (already cached?)
        2. Try configured remote_stores in priority order
        3. Try configured seqcol_servers (query service-info for RefgetStore URL)
        4. Fail with helpful message

    Use --file for batch operations with multiple digests.
    """
    not_implemented("store pull")


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
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
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
    store = _load_store(path, server=server)

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
        print_json({
            "digest": digest,
            "output": output_path,
            "status": "exported",
        })

    raise typer.Exit(EXIT_SUCCESS)


@app.command()
def seq(
    digest: str = typer.Argument(
        ...,
        help="Sequence digest or collection digest",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Sequence name (when using collection digest)",
    ),
    start: Optional[int] = typer.Option(
        None,
        "--start",
        "-s",
        help="Start position (0-based, inclusive)",
    ),
    end: Optional[int] = typer.Option(
        None,
        "--end",
        "-e",
        help="End position (0-based, exclusive)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Get a sequence or subsequence.

    Examples:
        refget store seq <seq_digest>                          # Full sequence
        refget store seq <seq_digest> --start 100 --end 200    # Subsequence
        refget store seq <coll_digest> --name chr1             # By name
        refget store seq <coll_digest> --name chr1 -s 100 -e 200
    """
    store = _load_store(path, server=server)

    sequence = None

    if name is not None:
        # Get sequence by collection + name
        record = store.get_sequence_by_collection_and_name(digest, name)
        if record is None:
            print_error(f"Sequence '{name}' not found in collection {digest}", EXIT_FAILURE)
        if start is not None and end is not None:
            # Get substring using the sequence digest
            sequence = store.get_substring(record.metadata.sha512t24u, start, end)
        elif start is not None or end is not None:
            print_error("Both --start and --end must be provided for substring", EXIT_FAILURE)
        else:
            # Use decode() to get the sequence string (handles encoded mode)
            sequence = record.decode()
    else:
        # Direct sequence lookup by digest
        if start is not None and end is not None:
            sequence = store.get_substring(digest, start, end)
        elif start is not None or end is not None:
            print_error("Both --start and --end must be provided for substring", EXIT_FAILURE)
        else:
            record = store.get_sequence_by_id(digest)
            if record is None:
                print_error(f"Sequence not found: {digest}", EXIT_FAILURE)
            # Use decode() to get the sequence string (handles encoded mode)
            sequence = record.decode()

    # Output raw sequence to stdout
    print(sequence)
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
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Generate .fai index from a collection digest.

    Outputs samtools-compatible .fai format (tab-separated).

    Note: Byte offset columns will be placeholder values since the collection
    may not correspond to any specific FASTA file layout.
    """
    store = _load_store(path, server=server)

    # Ensure collection is loaded
    _ensure_collection_loaded(store, digest)

    lines = []

    # Find the collection and get its sequences
    for coll in store.collections():
        if coll.digest == digest:
            for seq in coll.sequences:
                m = seq.metadata
                # FAI format: name, length, offset, linebases, linewidth
                # Since we don't have a specific FASTA file, offset is 0
                # Using default line width of 80
                lines.append(f"{m.name}\t{m.length}\t0\t80\t81")
            break

    if not lines:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)

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
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Generate chrom.sizes from a collection digest.

    Outputs UCSC-compatible chrom.sizes format (tab-separated name/length).
    """
    store = _load_store(path, server=server)

    # Ensure collection is loaded
    _ensure_collection_loaded(store, digest)

    lines = []

    # Find the collection and get its sequences
    for coll in store.collections():
        if coll.digest == digest:
            for seq in coll.sequences:
                m = seq.metadata
                lines.append(f"{m.name}\t{m.length}")
            break

    if not lines:
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)

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
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Display store statistics.

    Outputs JSON with storage_mode, collections, and sequences counts.

    Example output:
        {"collections": 3, "sequences": 75, "storage_mode": "Encoded"}
    """
    store = _load_store(path, server=server)

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


def _remove_collection_from_store(store_path: Path, digest: str) -> bool:
    """
    Remove a collection from the store by manipulating store files.

    gtars RefgetStore doesn't provide a remove_collection method, so we
    implement it by modifying the collections index file directly.

    Args:
        store_path: Path to the store directory
        digest: Collection digest to remove

    Returns:
        True if removed, False if not found
    """
    # Validate digest to prevent path traversal
    if "/" in digest or "\\" in digest or ".." in digest:
        return False

    # Remove from collections index (TSV file)
    collections_idx = store_path / "collections.rgci"
    if collections_idx.exists():
        lines = collections_idx.read_text().splitlines()
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("#") or not line.strip():
                new_lines.append(line)
            elif line.startswith(digest + "\t"):
                found = True  # Skip this line (remove it)
            else:
                new_lines.append(line)
        if found:
            collections_idx.write_text("\n".join(new_lines) + "\n" if new_lines else "")

    # Remove the collection's .rgsi file
    collection_file = store_path / "collections" / f"{digest}.rgsi"
    if collection_file.exists():
        collection_file.unlink()

    return True


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
    store_path = _get_store_path(path)

    # Check if collection exists
    if digest not in store.list_collections():
        print_error(f"Collection not found: {digest}", EXIT_FAILURE)

    # Remove the collection by manipulating store files
    _remove_collection_from_store(store_path, digest)

    print_json({
        "digest": digest,
        "status": "removed",
    })
    raise typer.Exit(EXIT_SUCCESS)
