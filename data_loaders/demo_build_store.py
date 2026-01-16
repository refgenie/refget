#!/usr/bin/env python3
"""
Build a RefgetStore from a folder of FASTA files.

Usage:
    python demo_build_store.py /path/to/fasta/folder /path/to/output/store
"""

import glob
import os
import sys

from refget.refget_store import RefgetStore


def find_fasta_files(folder: str) -> list[str]:
    """Find all FASTA files in a folder (recursively)."""
    patterns = ["*.fa", "*.fasta", "*.fa.gz", "*.fasta.gz", "*.fna", "*.fna.gz"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(folder, "**", pattern), recursive=True))
    return sorted(set(files))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    fasta_folder, store_path = sys.argv[1], sys.argv[2]
    fasta_files = find_fasta_files(fasta_folder)

    if not fasta_files:
        print(f"No FASTA files found in {fasta_folder}")
        sys.exit(1)

    print(f"Building store from {len(fasta_files)} FASTA files...")
    store = RefgetStore.on_disk(store_path)

    for fasta in fasta_files:
        store.add_sequence_collection_from_fasta(fasta)

    print(f"Done. Store at: {store_path}")
    print(f"Stats: {store.stats()}")


if __name__ == "__main__":
    main()
