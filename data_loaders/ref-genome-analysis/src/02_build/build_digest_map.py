#!/usr/bin/env python3
"""
Build a complete digest_map.csv from the inventory CSV.

For each FASTA in the inventory, reads the seqcol digest from the .rgsi cache
file next to it (instant — just reads the first line). Falls back to computing
the digest with digest_fasta() if no .rgsi exists.

Outputs: $STAGING/digest_map.csv with columns:
    path, filename, digest, n_sequences, group

Usage:
    python src/02_build/build_digest_map.py
    python src/02_build/build_digest_map.py --dry-run
"""

import argparse
import csv
import os
import re
import sys
import time

BRICK_ROOT = os.environ["BRICK_ROOT"]
STAGING = os.environ.get("STAGING", os.path.join(BRICK_ROOT, "refget_staging"))
INVENTORY_CSV = os.environ.get("INVENTORY_CSV", os.path.join(BRICK_ROOT, "refgenomes_inventory.csv"))
OUTPUT_CSV = os.path.join(STAGING, "digest_map.csv")

# Pattern to strip FASTA extensions and get the RGSI path
FASTA_EXTS = re.compile(r'\.(fa|fasta|fna)(\.gz)?$')


def rgsi_path_for(fasta_path: str) -> str:
    """Get the .rgsi cache path for a FASTA file."""
    return FASTA_EXTS.sub('.rgsi', fasta_path)


def read_rgsi_digest(rgsi_path: str) -> tuple[str, int] | None:
    """Read seqcol digest and sequence count from an .rgsi file.

    Returns (digest, n_sequences) or None if file doesn't exist or is malformed.
    """
    if not os.path.exists(rgsi_path):
        return None
    digest = None
    n_sequences = 0
    with open(rgsi_path) as f:
        for line in f:
            if line.startswith("##seqcol_digest="):
                digest = line.strip().split("=", 1)[1]
            elif not line.startswith("#"):
                n_sequences += 1
    if digest:
        return digest, n_sequences
    return None


def build_digest_map(inventory_path: str, output_path: str, dry_run: bool = False):
    with open(inventory_path) as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f"Inventory: {total} FASTAs from {inventory_path}")

    if dry_run:
        # Just count how many have .rgsi files
        have_rgsi = sum(1 for r in rows if os.path.exists(rgsi_path_for(r["path"])))
        print(f"FASTAs with .rgsi cache: {have_rgsi}/{total}")
        print("--dry-run: stopping here.")
        return

    results = []
    from_cache = 0
    skipped = 0
    t0 = time.time()

    for i, row in enumerate(rows, 1):
        fasta_path = row["path"]
        group = row.get("group", "")
        filename = row.get("filename", os.path.basename(fasta_path))

        # Try .rgsi cache first
        rgsi = rgsi_path_for(fasta_path)
        cached = read_rgsi_digest(rgsi)
        if cached:
            digest, n_sequences = cached
            from_cache += 1
            results.append({
                "path": fasta_path,
                "filename": filename,
                "digest": digest,
                "n_sequences": n_sequences,
                "group": group,
            })
            print(f"  [{i}/{total}] (cache) {group}/{filename} -> {digest}")
            continue

        # No cache — skip (these FASTAs were never successfully loaded)
        print(f"  [{i}/{total}] NO CACHE: {group}/{filename}", file=sys.stderr)
        skipped += 1

    elapsed = time.time() - t0

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "filename", "digest", "n_sequences", "group"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone in {elapsed:.1f}s")
    print(f"  Written:    {len(results)} entries to {output_path}")
    print(f"  From cache: {from_cache}")
    print(f"  No cache:   {skipped}")

    # Summary by group
    from collections import Counter
    group_counts = Counter(r["group"] for r in results)
    print(f"\nBy group:")
    for group, count in sorted(group_counts.items(), key=lambda x: -x[1]):
        print(f"  {group}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Build complete digest_map.csv from inventory.")
    parser.add_argument("--inventory", default=INVENTORY_CSV)
    parser.add_argument("--output", default=OUTPUT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    build_digest_map(args.inventory, args.output, args.dry_run)


if __name__ == "__main__":
    main()
