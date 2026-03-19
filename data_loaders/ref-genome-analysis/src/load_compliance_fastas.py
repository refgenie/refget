#!/usr/bin/env python3
"""
Load GA4GH seqcol compliance test FASTAs into all RefgetStores.

These small synthetic FASTAs are required for the compliance suite to pass.
They live in the refget repo at test_fasta/*.fa.

Usage:
    source env/on-cluster.env
    python src/load_compliance_fastas.py
    python src/load_compliance_fastas.py --store $VGP_STORE_PATH   # single store
"""

import argparse
import os
from pathlib import Path

# Compliance FASTAs are in the refget repo
REFGET_REPO = os.environ.get("REFGET_REPO", os.path.join(os.environ.get("DEPLOY_DIR", ""), "refget"))
TEST_FASTA_DIR = os.path.join(REFGET_REPO, "test_fasta")

COMPLIANCE_FASTAS = [
    "base.fa",
    "different_names.fa",
    "different_order.fa",
    "pair_swap.fa",
    "subset.fa",
    "swap_wo_coords.fa",
]


def load_compliance_fastas(store_path: str, fasta_dir: str):
    from refget.store import RefgetStore

    store = RefgetStore.on_disk(store_path)
    store.set_quiet(True)

    print(f"Store: {store_path}")
    loaded = 0
    for fa in COMPLIANCE_FASTAS:
        path = os.path.join(fasta_dir, fa)
        if not os.path.exists(path):
            print(f"  {fa}: NOT FOUND at {path}")
            continue
        meta, was_new = store.add_sequence_collection_from_fasta(path)
        status = "added" if was_new else "exists"
        print(f"  {fa}: {meta.digest} ({status})")
        loaded += 1

    print(f"  {loaded}/{len(COMPLIANCE_FASTAS)} loaded\n")


def main():
    parser = argparse.ArgumentParser(description="Load compliance FASTAs into RefgetStores")
    parser.add_argument("--store", help="Load into a single store (path)")
    parser.add_argument("--fasta-dir", default=TEST_FASTA_DIR, help="Directory containing test FASTAs")
    args = parser.parse_args()

    if not os.path.isdir(args.fasta_dir):
        print(f"Error: FASTA directory not found: {args.fasta_dir}")
        print("Set REFGET_REPO or DEPLOY_DIR, or pass --fasta-dir")
        return

    print(f"Compliance FASTAs from: {args.fasta_dir}\n")

    if args.store:
        load_compliance_fastas(args.store, args.fasta_dir)
    else:
        # Load into all stores from env vars
        for var in ["VGP_STORE_PATH", "REF_STORE_PATH", "PANGENOME_STORE_PATH"]:
            path = os.environ.get(var)
            if path and os.path.isdir(path):
                load_compliance_fastas(path, args.fasta_dir)
            elif path:
                print(f"  {var}={path} (not found, skipping)")


if __name__ == "__main__":
    main()
