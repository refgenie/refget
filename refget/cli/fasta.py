"""
FASTA file utility commands for the refget CLI.

Standalone utilities that work directly on FASTA files without requiring
a store or server.

Commands:
    index       - Generate ALL derived files at once
    digest      - Compute seqcol digest (top-level)
    seqcol      - Compute full seqcol JSON
    fai         - Compute FAI index
    chrom-sizes - Compute chrom.sizes
    rgsi        - Compute .rgsi (RefgetStore sequence index)
    rgci        - Compute .rgci (RefgetStore collection index)
    stats       - File statistics
"""

import json
from pathlib import Path
from typing import Optional

import typer

from refget.cli.output import (
    EXIT_FILE_NOT_FOUND,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    print_error,
    print_json,
    print_success,
    suppress_stdout,
)

app = typer.Typer(
    name="fasta",
    help="FASTA file utilities",
    no_args_is_help=True,
)


@app.command()
def index(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory (default: same as input file)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output result as JSON",
    ),
) -> None:
    """
    Generate ALL derived files from a FASTA file.

    For genome.fa, creates:
        - genome.fa.fai       (FASTA index, samtools-compatible)
        - genome.seqcol.json  (Sequence collection JSON)
        - genome.chrom.sizes  (Chromosome sizes)
        - genome.rgsi         (RefgetStore sequence index)
        - genome.rgci         (RefgetStore collection index)

    Prints the seqcol digest to stdout.
    """
    from gtars.refget import compute_fai, digest_fasta

    try:
        # Determine output directory
        out_dir = output_dir if output_dir else file.parent
        base_name = file.name

        # Compute seqcol digest (suppress verbose gtars output)
        with suppress_stdout():
            sc = digest_fasta(str(file))

        # Build seqcol JSON (level 2)
        names = [s.metadata.name for s in sc.sequences]
        lengths = [s.metadata.length for s in sc.sequences]
        sequences = [s.metadata.sha512t24u for s in sc.sequences]
        seqcol_data = {
            "names": names,
            "lengths": lengths,
            "sequences": sequences,
        }

        # Compute FAI (suppress verbose gtars output)
        with suppress_stdout():
            fai_records = compute_fai(str(file))
        fai_lines = []
        for r in fai_records:
            fai_meta = r.fai
            fai_lines.append(
                f"{r.name}\t{r.length}\t{fai_meta.offset}\t{fai_meta.line_bases}\t{fai_meta.line_bytes}"
            )
        fai_content = "\n".join(fai_lines) + "\n"

        # Build chrom.sizes
        chrom_sizes_lines = [f"{n}\t{length}" for n, length in zip(names, lengths)]
        chrom_sizes_content = "\n".join(chrom_sizes_lines) + "\n"

        # Write files
        fai_path = out_dir / f"{base_name}.fai"
        seqcol_path = (
            out_dir
            / f"{base_name.replace('.fa', '.seqcol.json').replace('.fasta', '.seqcol.json')}"
        )
        chrom_sizes_path = (
            out_dir
            / f"{base_name.replace('.fa', '.chrom.sizes').replace('.fasta', '.chrom.sizes')}"
        )

        # Handle .gz suffix
        if base_name.endswith(".gz"):
            seqcol_path = (
                out_dir
                / f"{base_name[:-3].replace('.fa', '.seqcol.json').replace('.fasta', '.seqcol.json')}"
            )
            chrom_sizes_path = (
                out_dir
                / f"{base_name[:-3].replace('.fa', '.chrom.sizes').replace('.fasta', '.chrom.sizes')}"
            )

        with open(fai_path, "w") as f:
            f.write(fai_content)

        with open(seqcol_path, "w") as f:
            json.dump(seqcol_data, f, indent=2)

        with open(chrom_sizes_path, "w") as f:
            f.write(chrom_sizes_content)

        # Write RGSI file
        stem = base_name
        for ext in [".fa.gz", ".fasta.gz", ".fa", ".fasta"]:
            if stem.endswith(ext):
                stem = stem[: -len(ext)]
                break
        rgsi_path = out_dir / f"{stem}.rgsi"
        sc.write_rgsi(str(rgsi_path))

        # Write RGCI file
        rgci_path = out_dir / f"{stem}.rgci"
        with open(rgci_path, "w") as f:
            meta = sc.metadata
            f.write(
                "#digest\tn_sequences\tnames_digest\tsequences_digest"
                "\tlengths_digest\tname_length_pairs_digest"
                "\tsorted_name_length_pairs_digest\tsorted_sequences_digest\n"
            )
            f.write(
                f"{meta.digest}\t{meta.n_sequences}\t{meta.names_digest}"
                f"\t{meta.sequences_digest}\t{meta.lengths_digest}"
                f"\t{meta.name_length_pairs_digest or ''}"
                f"\t{meta.sorted_name_length_pairs_digest or ''}"
                f"\t{meta.sorted_sequences_digest or ''}\n"
            )

        files_created = [
            str(fai_path), str(seqcol_path), str(chrom_sizes_path),
            str(rgsi_path), str(rgci_path),
        ]

        if json_output:
            print_json(
                {
                    "digest": sc.digest,
                    "file": str(file),
                    "files_created": files_created,
                }
            )
        else:
            print(sc.digest)

        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def digest(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
    ),
) -> None:
    """
    Compute the seqcol digest (top-level) of a FASTA file.

    Outputs JSON: {"digest": "abc123...", "file": "genome.fa"}
    """
    from gtars.refget import digest_fasta

    if not file.exists():
        print_error(f"File not found: {file}", EXIT_FILE_NOT_FOUND)

    try:
        # Suppress verbose gtars output
        with suppress_stdout():
            sc = digest_fasta(str(file))
        print_json({"digest": sc.digest, "file": file.name})
        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def seqcol(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    level: int = typer.Option(
        2,
        "--level",
        "-l",
        help="Seqcol level: 1 (digests only) or 2 (full arrays)",
        min=1,
        max=2,
    ),
) -> None:
    """
    Compute the full seqcol JSON from a FASTA file.

    Level 1 returns attribute digests only.
    Level 2 (default) returns full arrays (names, lengths, sequences).
    """
    from gtars.refget import digest_fasta

    try:
        # Suppress verbose gtars output
        with suppress_stdout():
            sc = digest_fasta(str(file))

        if level == 1:
            # Level 1: Return only attribute digests
            result = {
                "names": sc.lvl1.names_digest,
                "lengths": sc.lvl1.lengths_digest,
                "sequences": sc.lvl1.sequences_digest,
            }
        else:
            # Level 2: Return full arrays
            names = [s.metadata.name for s in sc.sequences]
            lengths = [s.metadata.length for s in sc.sequences]
            sequences = [s.metadata.sha512t24u for s in sc.sequences]
            result = {
                "names": names,
                "lengths": lengths,
                "sequences": sequences,
            }

        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            print_success(f"Wrote seqcol to {output}")
        else:
            print_json(result)

        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def fai(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
) -> None:
    """
    Compute FAI index from a FASTA file.

    Outputs samtools-compatible .fai format (tab-separated).

    Note: For .gz files, byte offsets are unavailable (cannot seek in
    compressed streams), but name/length data is still generated.
    """
    from gtars.refget import compute_fai

    try:
        # Suppress verbose gtars output
        with suppress_stdout():
            fai_records = compute_fai(str(file))

        # Build FAI format lines: name, length, offset, line_bases, line_bytes
        lines = []
        for r in fai_records:
            fai_meta = r.fai
            line = f"{r.name}\t{r.length}\t{fai_meta.offset}\t{fai_meta.line_bases}\t{fai_meta.line_bytes}"
            lines.append(line)

        content = "\n".join(lines)

        if output:
            with open(output, "w") as f:
                f.write(content + "\n")
            print_success(f"Wrote FAI index to {output}")
        else:
            print(content)

        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command("chrom-sizes")
def chrom_sizes(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
) -> None:
    """
    Compute chrom.sizes from a FASTA file.

    Outputs UCSC-compatible chrom.sizes format (tab-separated name/length).
    """
    from gtars.refget import digest_fasta

    try:
        # Suppress verbose gtars output
        with suppress_stdout():
            sc = digest_fasta(str(file))

        # Build chrom.sizes format: name\tlength
        lines = []
        for s in sc.sequences:
            m = s.metadata
            lines.append(f"{m.name}\t{m.length}")

        content = "\n".join(lines)

        if output:
            with open(output, "w") as f:
                f.write(content + "\n")
            print_success(f"Wrote chrom.sizes to {output}")
        else:
            print(content)

        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def rgsi(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: <input>.rgsi)",
    ),
) -> None:
    """
    Compute .rgsi (RefgetStore sequence index) from a FASTA file.

    The .rgsi is a TSV index file containing collection-level digest headers
    and per-sequence metadata (name, length, alphabet, digests). Used by
    RefgetStore for efficient collection storage and as a FASTA digest cache.
    """
    from gtars.refget import digest_fasta

    try:
        # Determine output path
        if output is None:
            # Replace FASTA extensions with .rgsi
            stem = file.name
            for ext in [".fa.gz", ".fasta.gz", ".fa", ".fasta"]:
                if stem.endswith(ext):
                    stem = stem[: -len(ext)]
                    break
            output = file.parent / f"{stem}.rgsi"

        # Digest the FASTA file
        with suppress_stdout():
            sc = digest_fasta(str(file))

        # Write RGSI file using gtars binding
        sc.write_rgsi(str(output))

        print_success(f"Wrote RGSI index to {output}")
        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def rgci(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: <input>.rgci)",
    ),
) -> None:
    """
    Compute .rgci (RefgetStore collection index) from a FASTA file.

    The .rgci is a TSV index file listing collection metadata (digest,
    sequence count, and level 1 digests). Used by RefgetStore as a
    master index of all collections.
    """
    from gtars.refget import digest_fasta

    try:
        # Determine output path
        if output is None:
            stem = file.name
            for ext in [".fa.gz", ".fasta.gz", ".fa", ".fasta"]:
                if stem.endswith(ext):
                    stem = stem[: -len(ext)]
                    break
            output = file.parent / f"{stem}.rgci"

        # Digest the FASTA file
        with suppress_stdout():
            sc = digest_fasta(str(file))

        meta = sc.metadata

        # Write RGCI file (matches store.rs write_collections_rgci format)
        with open(output, "w") as f:
            # Header
            f.write(
                "#digest\tn_sequences\tnames_digest\tsequences_digest"
                "\tlengths_digest\tname_length_pairs_digest"
                "\tsorted_name_length_pairs_digest\tsorted_sequences_digest\n"
            )
            # Single collection row
            f.write(
                f"{meta.digest}\t{meta.n_sequences}\t{meta.names_digest}"
                f"\t{meta.sequences_digest}\t{meta.lengths_digest}"
                f"\t{meta.name_length_pairs_digest or ''}"
                f"\t{meta.sorted_name_length_pairs_digest or ''}"
                f"\t{meta.sorted_sequences_digest or ''}\n"
            )

        print_success(f"Wrote RGCI index to {output}")
        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def stats(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON instead of table",
    ),
) -> None:
    """
    Display statistics for a FASTA file.

    Shows: sequence count, total length, N50, min/max/mean sequence length.
    """
    from gtars.refget import digest_fasta

    try:
        # Suppress verbose gtars output
        with suppress_stdout():
            sc = digest_fasta(str(file))

        # Extract lengths
        lengths = [s.metadata.length for s in sc.sequences]
        num_sequences = len(lengths)
        total_length = sum(lengths)
        min_length = min(lengths) if lengths else 0
        max_length = max(lengths) if lengths else 0
        mean_length = total_length / num_sequences if num_sequences > 0 else 0

        # Calculate N50
        sorted_lengths = sorted(lengths, reverse=True)
        cumsum = 0
        n50 = 0
        half_total = total_length / 2
        for length in sorted_lengths:
            cumsum += length
            if cumsum >= half_total:
                n50 = length
                break

        stats_data = {
            "file": str(file),
            "digest": sc.digest,
            "sequences": num_sequences,
            "total_length": total_length,
            "min_length": min_length,
            "max_length": max_length,
            "mean_length": round(mean_length, 2),
            "n50": n50,
        }

        if json_output:
            print_json(stats_data)
        else:
            # Pretty table output
            print(f"File:           {file}")
            print(f"Digest:         {sc.digest}")
            print(f"Sequences:      {num_sequences}")
            print(f"Total length:   {total_length:,}")
            print(f"Min length:     {min_length:,}")
            print(f"Max length:     {max_length:,}")
            print(f"Mean length:    {mean_length:,.2f}")
            print(f"N50:            {n50:,}")

        raise typer.Exit(EXIT_SUCCESS)
    except OSError as e:
        print_error(f"Error processing FASTA file: {e}", EXIT_FAILURE)


@app.command()
def validate(
    file: Path = typer.Argument(
        ...,
        help="Path to FASTA file (supports .gz)",
        exists=True,
        readable=True,
    ),
) -> None:
    """
    Validate a FASTA file format.

    Returns exit code 0 if valid, non-zero if invalid.
    """
    import gzip

    try:
        # Determine if file is gzipped
        is_gzipped = str(file).endswith(".gz")
        opener = gzip.open if is_gzipped else open
        mode = "rt" if is_gzipped else "r"

        has_sequence = False
        in_sequence = False
        line_num = 0

        with opener(file, mode) as f:
            for line in f:
                line_num += 1
                line = line.strip()

                if not line:
                    continue

                if line.startswith(">"):
                    # Header line
                    if len(line) < 2:
                        print(f"Invalid header at line {line_num}: empty header")
                        raise typer.Exit(EXIT_FAILURE)
                    in_sequence = True
                    has_sequence = True
                elif in_sequence:
                    # Sequence line - check for valid characters
                    valid_chars = set("ACGTUNacgtunRYSWKMBDHVryswkmbdhv.-")
                    invalid = set(line) - valid_chars
                    if invalid:
                        print(f"Invalid characters at line {line_num}: {invalid}")
                        raise typer.Exit(EXIT_FAILURE)
                else:
                    # Line before any header
                    print(f"Invalid FASTA: content before first header at line {line_num}")
                    raise typer.Exit(EXIT_FAILURE)

        if not has_sequence:
            # Empty file or no sequences - still valid, just empty
            print("Valid FASTA (empty)")
        else:
            print("Valid FASTA")

        raise typer.Exit(EXIT_SUCCESS)

    except gzip.BadGzipFile:
        print("Invalid gzip file")
        raise typer.Exit(EXIT_FAILURE)
    except OSError as e:
        print(f"Error reading file: {e}")
        raise typer.Exit(EXIT_FAILURE)
