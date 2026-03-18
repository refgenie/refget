#!/usr/bin/env python3
"""
Backfill sequence and collection aliases into a split store.

Matches accessions to target store collections via digest_map (path join),
then registers aliases from the NCBI alias table by matching sequence names
in level2 data. Does NOT load any FASTAs — read-only against the target store
except for alias registration.

Usage:
    source env/on-cluster.env
    python src/backfill_sequence_aliases.py --target $VGP_STORE_PATH
    python src/backfill_sequence_aliases.py --target $REF_STORE_PATH
    python src/backfill_sequence_aliases.py --target $VGP_STORE_PATH --dry-run
"""

import argparse
import csv
import os
import tempfile
import time
from collections import defaultdict

BRICK_ROOT = os.environ["BRICK_ROOT"]
STAGING = os.environ.get("STAGING", os.path.join(BRICK_ROOT, "refget_staging"))
INVENTORY_CSV = os.environ.get("INVENTORY_CSV", os.path.join(BRICK_ROOT, "refgenomes_inventory.csv"))
ALIAS_TABLE_CSV = os.path.join(STAGING, "ncbi_alias_table.csv")
DIGEST_MAP_CSV = os.path.join(STAGING, "digest_map.csv")


def get_all_collection_digests(store):
    digests = set()
    page = 0
    while True:
        result = store.list_collections(page, 1000)
        for c in result["results"]:
            digests.add(c.digest)
        if len(result["results"]) < 1000:
            break
        page += 1
    return digests


def main():
    parser = argparse.ArgumentParser(
        description="Backfill aliases into a split store from NCBI alias table."
    )
    parser.add_argument("--target", required=True, help="Target RefgetStore path")
    parser.add_argument("--alias-table", default=ALIAS_TABLE_CSV)
    parser.add_argument("--inventory", default=INVENTORY_CSV)
    parser.add_argument("--digest-map", default=DIGEST_MAP_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from refget.store import RefgetStore

    print(f"Target store: {args.target}")
    print(f"Alias table:  {args.alias_table}")
    print(f"Inventory:    {args.inventory}")
    print(f"Digest map:   {args.digest_map}")
    print(f"Dry run:      {args.dry_run}")
    print()

    # Open target store (read-only for collection lookup, then alias writes)
    store = RefgetStore.open_local(args.target)
    target_digests = get_all_collection_digests(store)
    print(f"Target has {len(target_digests)} collections")

    # Build path -> accession from inventory
    path_to_accession = {}
    with open(args.inventory, newline="") as f:
        for row in csv.DictReader(f):
            acc = row.get("accession", "").strip()
            path = row.get("path", "").strip()
            if acc and path:
                path_to_accession[path] = acc

    # Build digest -> accession via digest_map (join on path)
    digest_to_accession = {}
    with open(args.digest_map, newline="") as f:
        for row in csv.DictReader(f):
            digest = row.get("digest", "").strip()
            path = row.get("path", "").strip()
            if digest and path and path in path_to_accession:
                digest_to_accession[digest] = path_to_accession[path]

    # Filter to accessions whose digest is in the target store
    target_acc_to_digest = {}
    for digest in target_digests:
        acc = digest_to_accession.get(digest)
        if acc:
            target_acc_to_digest[acc] = digest

    print(f"Accessions in target with alias data: {len(target_acc_to_digest)}")

    # Read alias table, filtered to target accessions
    acc_to_rows = defaultdict(list)
    with open(args.alias_table, newline="") as f:
        for row in csv.DictReader(f):
            acc = row.get("accession", "").strip()
            if acc and acc in target_acc_to_digest:
                acc_to_rows[acc].append(row)

    common = sorted(target_acc_to_digest.keys() & acc_to_rows.keys())
    print(f"Accessions with alias table entries: {len(common)}")

    # Re-open as on_disk for writing aliases
    store = RefgetStore.on_disk(args.target)
    store.set_quiet(True)

    seq_aliases = {"refseq": [], "insdc": [], "ucsc": []}
    coll_aliases = {"refseq": [], "insdc": []}
    n_matched = 0
    n_unmatched = 0
    t_start = time.time()

    for i, accession in enumerate(common, 1):
        coll_digest = target_acc_to_digest[accession]
        alias_rows = acc_to_rows[accession]

        print(f"[{i}/{len(common)}] {accession} ({len(alias_rows)} seqs)...", end=" ", flush=True)

        # Collection-level aliases
        first_row = alias_rows[0]
        genbank_acc = first_row.get("genbank_assembly_accn", "").strip()
        refseq_acc = first_row.get("refseq_assembly_accn", "").strip()
        if refseq_acc:
            coll_aliases["refseq"].append((refseq_acc, coll_digest))
        if genbank_acc:
            coll_aliases["insdc"].append((genbank_acc, coll_digest))

        # Sequence-level aliases via name matching in level2
        level2 = store.get_collection_level2(coll_digest)
        names = level2.get("names", [])
        lengths = level2.get("lengths", [])
        sequences = level2.get("sequences", [])
        name_to_info = {n: (s, int(l)) for n, l, s in zip(names, lengths, sequences)}

        matched_this = 0
        for row in alias_rows:
            seq_name = row.get("sequence_name", "").strip()
            seq_length_str = row.get("sequence_length", "").strip()
            refseq_accn = row.get("refseq_accn", "").strip()
            genbank_accn = row.get("genbank_accn", "").strip()
            ucsc_name = row.get("ucsc_name", "").strip()
            seq_length = int(seq_length_str) if seq_length_str else None

            seq_digest = None
            for candidate in [seq_name, refseq_accn, genbank_accn, ucsc_name]:
                if candidate and candidate in name_to_info:
                    sd, sl = name_to_info[candidate]
                    if seq_length is None or sl == seq_length:
                        seq_digest = sd
                        break

            if seq_digest is None:
                n_unmatched += 1
                continue

            matched_this += 1
            if refseq_accn:
                seq_aliases["refseq"].append((refseq_accn, seq_digest))
            if genbank_accn:
                seq_aliases["insdc"].append((genbank_accn, seq_digest))
            if ucsc_name:
                seq_aliases["ucsc"].append((ucsc_name, seq_digest))

        n_matched += matched_this
        print(f"{matched_this}/{len(alias_rows)} matched")

    elapsed = time.time() - t_start
    n_seq = sum(len(v) for v in seq_aliases.values())
    n_coll = sum(len(v) for v in coll_aliases.values())
    print(f"\nMatching done in {elapsed:.1f}s")
    print(f"  Matched: {n_matched}, unmatched: {n_unmatched}")
    print(f"  Seq aliases: {n_seq}, coll aliases: {n_coll}")

    if args.dry_run:
        print("\n[DRY RUN] Skipping registration.")
        return

    print("\nRegistering aliases...")
    with tempfile.TemporaryDirectory() as tmpdir:
        for ns, pairs in seq_aliases.items():
            if not pairs:
                continue
            tsv = os.path.join(tmpdir, f"seq_{ns}.tsv")
            with open(tsv, "w") as f:
                for alias, digest in pairs:
                    f.write(f"{alias}\t{digest}\n")
            n = store.load_sequence_aliases(ns, tsv)
            print(f"  sequences/{ns}: {n} aliases loaded")

        for ns, pairs in coll_aliases.items():
            if not pairs:
                continue
            tsv = os.path.join(tmpdir, f"coll_{ns}.tsv")
            with open(tsv, "w") as f:
                for alias, digest in pairs:
                    f.write(f"{alias}\t{digest}\n")
            n = store.load_collection_aliases(ns, tsv)
            print(f"  collections/{ns}: {n} aliases loaded")

    print(f"\nDone! Store stats: {store.stats()}")


if __name__ == "__main__":
    main()
