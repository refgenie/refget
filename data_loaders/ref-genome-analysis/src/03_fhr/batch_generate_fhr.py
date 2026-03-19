#!/usr/bin/env python3
"""Batch-generate FHR metadata for all VGP vertebrate genomes.

Reads the inventory CSV, extracts unique GCA accessions for vertebrate genomes,
and fetches FHR metadata from NCBI for each. Skips accessions that already have
an FHR file in the output directory, so it's safe to re-run.

Usage:
    python batch_generate_fhr.py --inventory /path/to/inventory.csv --output-dir /path/to/fhr_metadata/
    python batch_generate_fhr.py --inventory /path/to/inventory.csv --output-dir /path/to/fhr_metadata/ --group vertebrates
"""

import argparse
import csv
import re
import sys
import os
import time

from genomeark_to_fhr import process_accession


def main():
    parser = argparse.ArgumentParser(description="Batch-generate FHR metadata from inventory CSV")
    parser.add_argument("--inventory", required=True, help="Path to refgenomes_inventory.csv")
    parser.add_argument("--output-dir", required=True, help="Output directory for .fhr.json files")
    parser.add_argument("--group", default="vertebrates", help="Filter by group column (default: vertebrates)")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N accessions")
    parser.add_argument("--skip-genomeark", action="store_true", help="Skip GenomeArk YAML fetch (faster)")
    args = parser.parse_args()

    # Read inventory and extract unique accessions for the target group
    with open(args.inventory, newline="") as f:
        rows = list(csv.DictReader(f))

    accessions = set()
    for row in rows:
        if row.get("group", "").strip() != args.group:
            continue
        acc = row.get("accession", "").strip()
        if not acc:
            m = re.search(r'(GCA_\d+(?:\.\d+)?)', row.get("filename", ""))
            if m:
                acc = m.group(1)
        if acc:
            accessions.add(acc)

    accessions = sorted(accessions)
    if args.limit:
        accessions = accessions[:args.limit]

    # Check which ones already exist
    os.makedirs(args.output_dir, exist_ok=True)
    existing = {f.replace(".fhr.json", "") for f in os.listdir(args.output_dir) if f.endswith(".fhr.json")}
    todo = [a for a in accessions if a not in existing]

    print(f"Group: {args.group}", file=sys.stderr)
    print(f"Total accessions: {len(accessions)}", file=sys.stderr)
    print(f"Already done: {len(accessions) - len(todo)}", file=sys.stderr)
    print(f"To process: {len(todo)}", file=sys.stderr)

    if not todo:
        print("Nothing to do!", file=sys.stderr)
        return

    n_ok = 0
    n_fail = 0
    t_start = time.time()

    for i, acc in enumerate(todo, 1):
        output_path = os.path.join(args.output_dir, f"{acc}.fhr.json")
        ok = False
        for attempt in range(3):
            try:
                print(f"[{i}/{len(todo)}] ", end="", file=sys.stderr)
                process_accession(acc, output_path)
                n_ok += 1
                ok = True
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 5 * (attempt + 1)
                    print(f"[{i}/{len(todo)}] {acc}: rate limited, waiting {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                else:
                    print(f"[{i}/{len(todo)}] {acc}: FAILED ({e})", file=sys.stderr)
                    n_fail += 1
                    break

        # Throttle to ~3 requests/sec (NCBI + GenomeArk = 2 requests per accession)
        time.sleep(0.3)

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed:.0f}s: {n_ok} OK, {n_fail} failed out of {len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()
