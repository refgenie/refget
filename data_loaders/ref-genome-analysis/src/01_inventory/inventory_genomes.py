#!/usr/bin/env python3
"""
Inventory all FASTA files in the brickyard refgenomes directory.

Walks the brickyard directory tree, extracts structured metadata from paths
and filenames, cross-references against the PEP project, and produces a
master CSV inventory.

Zero non-stdlib dependencies.

Usage:
    python inventory_genomes.py
    python inventory_genomes.py --dry-run --no-pep
    python inventory_genomes.py --root /tmp/mock_brickyard --dry-run --no-pep
"""

import argparse
import csv
import json
import os
import os.path
import pathlib
import re
import sys
import urllib.error
import urllib.request

BRICKYARD_ROOT = os.environ["BRICK_ROOT"]
PEP_URL = "https://pephub-api.databio.org/api/v1/projects/donaldcampbelljr/human_mouse_fasta_brickyard/samples?tag=default"
OUTPUT_FILE = os.environ.get("INVENTORY_CSV", os.path.join(BRICKYARD_ROOT, "refgenomes_inventory.csv"))
FASTA_EXTENSIONS = {".fa", ".fa.gz", ".fna", ".fna.gz", ".fasta", ".fasta.gz"}
ACCESSION_PATTERN = re.compile(r"(GC[AF]_\d+\.\d+)")


def fetch_pep_samples():
    """Fetch PEP samples from the PEPHub API.

    Returns a dict mapping absolute fasta path to sample_name.
    Falls back to an empty dict if the API is unreachable.
    """
    try:
        with urllib.request.urlopen(PEP_URL) as response:
            data = json.loads(response.read().decode("utf-8"))
        lookup = {}
        for item in data.get("items", []):
            fasta_path = item.get("fasta", "")
            sample_name = item.get("sample_name", "")
            if fasta_path:
                lookup[fasta_path] = sample_name
        print(f"Fetched {len(lookup)} PEP samples.", file=sys.stderr)
        return lookup
    except urllib.error.URLError as e:
        print(f"Warning: Could not fetch PEP samples: {e}", file=sys.stderr)
        return {}


def walk_fasta_files(root):
    """Walk the directory tree and yield absolute paths of FASTA files."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if any(name.endswith(ext) for ext in FASTA_EXTENSIONS):
                yield os.path.join(dirpath, name)


def extract_metadata(filepath, root):
    """Extract structured metadata from a FASTA file path.

    Returns a dict with: path, filename, accession, group, source, build.
    """
    filename = os.path.basename(filepath)
    match = ACCESSION_PATTERN.search(filename)
    accession = match.group(1) if match else ""

    rel = os.path.relpath(filepath, root)
    parts = pathlib.PurePosixPath(rel).parts
    # parts[0] = group, parts[1] = source, parts[2] = build (or subdir), parts[-1] = filename
    group = parts[0] if len(parts) > 1 else ""
    source = parts[1] if len(parts) > 2 else ""
    build = parts[2] if len(parts) > 3 else ""

    return {
        "path": filepath,
        "filename": filename,
        "accession": accession,
        "group": group,
        "source": source,
        "build": build,
    }


def add_pep_info(record, pep_lookup):
    """Add PEP sample name to a record if it exists in the lookup."""
    record["pep_sample_name"] = pep_lookup.get(record["path"], "")


def write_inventory(records, output_path):
    """Write the inventory records to a CSV file."""
    fieldnames = ["path", "filename", "accession", "group", "source", "build", "pep_sample_name"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Inventory FASTA files in the brickyard refgenomes directory."
    )
    parser.add_argument(
        "--root",
        default=BRICKYARD_ROOT,
        help=f"Root directory to scan (default: {BRICKYARD_ROOT})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=f"Output CSV path (default: <root>/refgenomes_inventory.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the first 10 rows to stdout instead of writing CSV.",
    )
    parser.add_argument(
        "--no-pep",
        action="store_true",
        help="Skip PEP fetching (useful for offline HPC nodes).",
    )
    args = parser.parse_args()

    root = args.root
    output_path = args.output if args.output else os.path.join(root, "refgenomes_inventory.csv")

    # Step 1: Fetch PEP samples
    if args.no_pep:
        pep_lookup = {}
        print("Skipping PEP fetch (--no-pep).", file=sys.stderr)
    else:
        pep_lookup = fetch_pep_samples()

    # Step 2: Walk and collect FASTA files
    print(f"Scanning {root} ...", file=sys.stderr)
    records = []
    for filepath in walk_fasta_files(root):
        record = extract_metadata(filepath, root)
        add_pep_info(record, pep_lookup)
        records.append(record)

    # Step 3: Sort for deterministic output
    records.sort(key=lambda r: r["path"])

    # Step 4: Output
    if args.dry_run:
        fieldnames = ["path", "filename", "accession", "group", "source", "build", "pep_sample_name"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        for row in records[:10]:
            writer.writerow(row)
    else:
        write_inventory(records, output_path)

    # Step 5: Summary stats
    total = len(records)
    with_accession = sum(1 for r in records if r["accession"])
    in_pep = sum(1 for r in records if r["pep_sample_name"])
    unique_groups = len({r["group"] for r in records if r["group"]})
    unique_sources = len({r["source"] for r in records if r["source"]})

    print(f"\nSummary:", file=sys.stderr)
    print(f"  Total FASTA files: {total}", file=sys.stderr)
    print(f"  Files with accessions: {with_accession}", file=sys.stderr)
    print(f"  Files in PEP: {in_pep}", file=sys.stderr)
    print(f"  Unique groups: {unique_groups}", file=sys.stderr)
    print(f"  Unique sources: {unique_sources}", file=sys.stderr)


if __name__ == "__main__":
    main()
