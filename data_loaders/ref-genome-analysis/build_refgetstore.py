"""
Build a RefgetStore from the refgenomes inventory CSV.

Reads refgenomes_inventory.csv and populates a RefgetStore with all FASTA
files. No alias registration -- that is a separate, deliberate step.

Usage:
    python build_refgetstore.py [--inventory PATH] [--store-path PATH] [--output PATH] [--limit N]
"""

import argparse
import csv
import sys
import time

from refget.store import RefgetStore

STORE_PATH = "/project/shefflab/brickyard/refget_store"
INVENTORY_CSV = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refgenomes_inventory.csv"
OUTPUT_CSV = "digest_map.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Build RefgetStore from inventory CSV")
    parser.add_argument("--inventory", default=INVENTORY_CSV, help="Input inventory CSV")
    parser.add_argument("--store-path", default=STORE_PATH, help="RefgetStore path")
    parser.add_argument("--output", default=OUTPUT_CSV, help="Output digest map CSV")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N rows (for testing)")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N rows")
    return parser.parse_args()


def read_inventory(csv_path):
    """Read inventory CSV and return list of row dicts."""
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print(f"ERROR: {csv_path} appears to be empty", file=sys.stderr)
            sys.exit(1)
        if "path" not in reader.fieldnames:
            print(f"ERROR: {csv_path} missing required 'path' column", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            rows.append(row)
    return rows


def write_digest_map(output_path, results):
    """Write results to digest_map.csv."""
    fieldnames = ["path", "filename", "digest", "n_sequences", "was_new", "error"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    args = parse_args()

    inventory = read_inventory(args.inventory)
    if args.offset:
        inventory = inventory[args.offset:]
        print(f"Skipped first {args.offset} records")
    if args.limit:
        inventory = inventory[:args.limit]
        print(f"Limited to {args.limit} records")
    total = len(inventory)
    print(f"Processing {total} records from {args.inventory}")

    store = RefgetStore.on_disk(args.store_path)
    print(f"Store initialized at {args.store_path}")

    results = []
    n_success = 0
    n_failed = 0
    n_new = 0
    t_start = time.time()

    for i, row in enumerate(inventory, 1):
        fasta_path = row["path"]
        filename = row.get("filename", "")

        t0 = time.time()
        print(f"[{i}/{total}] {filename}...", end=" ", flush=True)

        try:
            meta, was_new = store.add_sequence_collection_from_fasta(fasta_path, threads=4)
            elapsed = time.time() - t0
            status = "NEW" if was_new else "exists"
            if was_new:
                n_new += 1
            print(f"{meta.digest} ({meta.n_sequences} seqs, {status}, {elapsed:.1f}s)")
            n_success += 1
            results.append({
                "path": fasta_path,
                "filename": filename,
                "digest": meta.digest,
                "n_sequences": meta.n_sequences,
                "was_new": was_new,
                "error": "",
            })
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"FAILED: {error_msg}")
            n_failed += 1
            results.append({
                "path": fasta_path,
                "filename": filename,
                "digest": "",
                "n_sequences": 0,
                "was_new": False,
                "error": error_msg,
            })

    write_digest_map(args.output, results)

    total_time = time.time() - t_start
    print(f"\nDone in {total_time:.1f}s. {n_success}/{total} succeeded, {n_new} new, {n_failed} failed.")
    print(f"Digest map written to {args.output}")
    print(f"\nStore stats: {store.stats()}")

    if n_failed > 0:
        print(f"\nFailed files:")
        for r in results:
            if r["error"]:
                print(f"  {r['filename']}: {r['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
