#!/usr/bin/env python3
"""
Register NCBI sequence and collection aliases in a RefgetStore.

Phase B of the alias registration pipeline. Reads the ncbi_alias_table.csv
(from Phase A), matches sequences to store digests, and bulk-loads aliases
via temporary TSV files.

Usage:
    python register_ncbi_aliases.py --store-path /path/to/store
    python register_ncbi_aliases.py --store-path /path/to/store --dry-run
    python register_ncbi_aliases.py --store-path /path/to/store --limit 5
"""

import argparse
import csv
import os
import sys
import tempfile
import time
from collections import defaultdict

from refget.store import RefgetStore

BRICK_ROOT = os.environ["BRICK_ROOT"]
STORE_PATH = os.environ.get("STORE_PATH", f"{BRICK_ROOT}/refget_store")
INVENTORY_CSV = os.environ.get("INVENTORY_CSV", f"{BRICK_ROOT}/refgenomes_inventory.csv")
STAGING = os.environ.get("STAGING", f"{BRICK_ROOT}/refget_staging")
ALIAS_TABLE_CSV = f"{STAGING}/ncbi_alias_table.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Register NCBI aliases in RefgetStore")
    parser.add_argument("--store-path", default=STORE_PATH, help="Path to RefgetStore")
    parser.add_argument("--alias-table", default=ALIAS_TABLE_CSV, help="Path to ncbi_alias_table.csv")
    parser.add_argument("--inventory", default=INVENTORY_CSV, help="Path to refgenomes_inventory.csv")
    parser.add_argument("--dry-run", action="store_true", help="Parse and match but don't register")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N accessions")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N accessions")
    return parser.parse_args()


def read_inventory(csv_path):
    """Read inventory CSV, return accession -> path mapping."""
    acc_to_path = {}
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            acc = row.get("accession", "").strip()
            path = row.get("path", "").strip()
            if acc and path:
                acc_to_path[acc] = path
    return acc_to_path


def read_alias_table(csv_path):
    """Read alias table CSV, return accession -> list of row dicts."""
    acc_to_rows = defaultdict(list)
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            acc = row.get("accession", "").strip()
            if acc:
                acc_to_rows[acc].append(row)
    return acc_to_rows


def write_tsv(path, pairs):
    """Write alias\tdigest pairs to a TSV file."""
    with open(path, "w") as f:
        for alias, digest in pairs:
            f.write(f"{alias}\t{digest}\n")


def main():
    args = parse_args()

    # Read inputs
    print(f"Reading inventory from {args.inventory}")
    acc_to_path = read_inventory(args.inventory)
    print(f"  {len(acc_to_path)} accessions with paths")

    print(f"Reading alias table from {args.alias_table}")
    acc_to_rows = read_alias_table(args.alias_table)
    print(f"  {len(acc_to_rows)} accessions, {sum(len(v) for v in acc_to_rows.values())} sequence rows")

    # Filter to accessions present in both
    common_accessions = sorted(set(acc_to_path) & set(acc_to_rows))
    print(f"  {len(common_accessions)} accessions in both inventory and alias table")

    if args.offset:
        common_accessions = common_accessions[args.offset:]
        print(f"  Skipped first {args.offset}")
    if args.limit:
        common_accessions = common_accessions[:args.limit]
        print(f"  Limited to {args.limit}")

    # Open store
    store = RefgetStore.on_disk(args.store_path)
    store.set_quiet(True)
    print(f"Store opened: {store.stats()}")

    # Accumulate all aliases in memory, then bulk-load at the end
    seq_aliases = {"refseq": [], "insdc": [], "ucsc": []}
    coll_aliases = {"refseq": [], "insdc": []}

    n_collections = 0
    n_matched = 0
    n_unmatched = 0
    n_skipped_files = 0
    t_start = time.time()

    for i, accession in enumerate(common_accessions, 1):
        fasta_path = acc_to_path[accession]
        alias_rows = acc_to_rows[accession]

        print(f"[{i}/{len(common_accessions)}] {accession} ({len(alias_rows)} seqs)...", end=" ", flush=True)

        # Get collection digest by loading (returns immediately if exists)
        if not os.path.exists(fasta_path):
            print("SKIP (file missing)")
            n_skipped_files += 1
            continue

        try:
            meta, was_new = store.add_sequence_collection_from_fasta(fasta_path)
        except Exception as e:
            print(f"SKIP ({e})")
            n_skipped_files += 1
            continue

        coll_digest = meta.digest
        n_collections += 1

        # Collection-level aliases from report header
        first_row = alias_rows[0]
        genbank_acc = first_row.get("genbank_assembly_accn", "").strip()
        refseq_acc = first_row.get("refseq_assembly_accn", "").strip()

        if refseq_acc:
            coll_aliases["refseq"].append((refseq_acc, coll_digest))
        if genbank_acc:
            coll_aliases["insdc"].append((genbank_acc, coll_digest))

        # Get collection's sequences to match against alias table
        level2 = store.get_collection_level2(coll_digest)
        names = level2.get("names", [])
        lengths = level2.get("lengths", [])
        sequences = level2.get("sequences", [])

        # Build name -> (seq_digest, length) lookup
        name_to_info = {}
        for name, length, seq_digest in zip(names, lengths, sequences):
            name_to_info[name] = (seq_digest, int(length))

        # Match alias table rows to store sequences
        matched_this = 0
        unmatched_this = 0
        for row in alias_rows:
            seq_name = row.get("sequence_name", "").strip()
            seq_length_str = row.get("sequence_length", "").strip()
            refseq_accn = row.get("refseq_accn", "").strip()
            genbank_accn = row.get("genbank_accn", "").strip()
            ucsc_name = row.get("ucsc_name", "").strip()

            seq_length = int(seq_length_str) if seq_length_str else None

            # Try matching by sequence_name, then refseq_accn, then genbank_accn, then ucsc_name
            seq_digest = None
            for candidate in [seq_name, refseq_accn, genbank_accn, ucsc_name]:
                if candidate and candidate in name_to_info:
                    store_digest, store_length = name_to_info[candidate]
                    if seq_length is None or store_length == seq_length:
                        seq_digest = store_digest
                        break

            if seq_digest is None:
                unmatched_this += 1
                continue

            matched_this += 1

            if refseq_accn:
                seq_aliases["refseq"].append((refseq_accn, seq_digest))
            if genbank_accn:
                seq_aliases["insdc"].append((genbank_accn, seq_digest))
            if ucsc_name:
                seq_aliases["ucsc"].append((ucsc_name, seq_digest))

        n_matched += matched_this
        n_unmatched += unmatched_this
        print(f"{coll_digest[:12]}... {matched_this}/{len(alias_rows)} matched")

    match_elapsed = time.time() - t_start

    # Summary of what was collected
    n_seq_aliases = sum(len(v) for v in seq_aliases.values())
    n_coll_aliases = sum(len(v) for v in coll_aliases.values())
    print(f"\nMatching done in {match_elapsed:.1f}s")
    print(f"  Collections: {n_collections}, skipped: {n_skipped_files}")
    print(f"  Sequences matched: {n_matched}, unmatched: {n_unmatched}")
    print(f"  Sequence aliases to register: {n_seq_aliases}")
    print(f"  Collection aliases to register: {n_coll_aliases}")

    if args.dry_run:
        print("\n[DRY RUN] Skipping alias registration.")
        return

    # Bulk-load aliases via temp TSV files
    print(f"\nRegistering aliases...")
    with tempfile.TemporaryDirectory() as tmpdir:
        for namespace, pairs in seq_aliases.items():
            if not pairs:
                continue
            tsv_path = os.path.join(tmpdir, f"seq_{namespace}.tsv")
            write_tsv(tsv_path, pairs)
            n = store.load_sequence_aliases(namespace, tsv_path)
            print(f"  sequences/{namespace}: {n} aliases loaded")

        for namespace, pairs in coll_aliases.items():
            if not pairs:
                continue
            tsv_path = os.path.join(tmpdir, f"coll_{namespace}.tsv")
            write_tsv(tsv_path, pairs)
            n = store.load_collection_aliases(namespace, tsv_path)
            print(f"  collections/{namespace}: {n} aliases loaded")

    total_elapsed = time.time() - t_start
    print(f"\nDone in {total_elapsed:.1f}s")
    print(f"  Store stats: {store.stats()}")


if __name__ == "__main__":
    main()
