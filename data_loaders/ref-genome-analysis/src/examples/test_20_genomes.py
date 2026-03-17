"""
Quick test: load 20 genomes into a RefgetStore and attach FHR metadata.

Usage:
    python test_20_genomes.py [--inventory PATH] [--limit N]
"""

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import time

from gtars.refget import RefgetStore

BRICK_ROOT = os.environ["BRICK_ROOT"]
INVENTORY_CSV = os.environ.get("INVENTORY_CSV", f"{BRICK_ROOT}/refgenomes_inventory.csv")
STAGING = os.environ.get("STAGING", f"{BRICK_ROOT}/refget_staging")
FHR_DIR = f"{STAGING}/fhr_metadata"
STORE_PATH = os.environ.get("STORE_PATH", "/scratch/ns5bc/test_refget_store_20")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default=INVENTORY_CSV)
    parser.add_argument("--store-path", default=STORE_PATH)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    # Read inventory
    with open(args.inventory, newline="") as f:
        rows = list(csv.DictReader(f))
    rows = rows[:args.limit]

    print(f"Loading {len(rows)} genomes into {args.store_path}")
    os.makedirs(args.store_path, exist_ok=True)
    store = RefgetStore.on_disk(args.store_path)

    # Phase 1: Load FASTAs
    print("\n=== Phase 1: Load FASTAs ===")
    digest_map = {}  # filename -> digest
    t_start = time.time()

    for i, row in enumerate(rows, 1):
        fasta_path = row["path"]
        filename = row.get("filename", os.path.basename(fasta_path))
        t0 = time.time()
        print(f"[{i}/{len(rows)}] {filename}...", end=" ", flush=True)
        try:
            meta, was_new = store.add_sequence_collection_from_fasta(fasta_path)
            elapsed = time.time() - t0
            status = "NEW" if was_new else "exists"
            print(f"{meta.digest} ({meta.n_sequences} seqs, {status}, {elapsed:.1f}s)")
            digest_map[filename] = meta.digest
        except Exception as e:
            print(f"FAILED: {e}")

    t_fasta = time.time() - t_start
    print(f"\nPhase 1 done: {len(digest_map)} loaded in {t_fasta:.1f}s")

    # Phase 2: Load FHR metadata (provenance only, no vitalStats) for all collections
    # Map build names to GCA accessions for known species
    BUILD_TO_ACCESSION = {
        ("homo_sapiens", "hg19"): "GCA_000001405",
        ("homo_sapiens", "hg38"): "GCA_000001405",
        ("mus_musculus", "mm9"):  "GCA_000001635",
        ("mus_musculus", "mm10"): "GCA_000001635",
        ("mus_musculus", "mm39"): "GCA_000001635",
    }

    print("\n=== Phase 2: Load FHR metadata ===")
    fhr_loaded = 0

    # Build accession -> set of digests from inventory metadata
    accession_digests = {}  # accession -> set of digests
    for row in rows:
        filename = row.get("filename", "")
        if filename not in digest_map:
            continue
        digest = digest_map[filename]

        # Try explicit accession column first
        accession = row.get("accession", "").strip()

        # Try extracting from filename
        if not accession:
            m = re.search(r'(GCA_\d+(?:\.\d+)?)', filename)
            if m:
                accession = m.group(1)

        # Fall back to group+build mapping
        if not accession:
            group = row.get("group", "").strip()
            build = row.get("build", "").strip()
            accession = BUILD_TO_ACCESSION.get((group, build), "")

        if accession:
            accession_digests.setdefault(accession, set()).add(digest)

    print(f"  Found {len(accession_digests)} accessions across {sum(len(v) for v in accession_digests.values())} collections")

    def load_fhr_for_accession(store, accession, fhr_data, digests):
        """Strip vitalStats and attach provenance FHR to all matching collections."""
        provenance = {k: v for k, v in fhr_data.items() if k != "vitalStats"}
        loaded = 0
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fhr.json", delete=False) as tmp:
            json.dump(provenance, tmp, indent=2)
            tmp_path = tmp.name
        try:
            for digest in digests:
                store.load_fhr_metadata(digest, tmp_path)
                print(f"    {accession} -> {digest}")
                loaded += 1
        finally:
            os.unlink(tmp_path)
        return loaded

    for accession, digests in sorted(accession_digests.items()):
        # Check for pre-generated FHR file
        fhr_path = os.path.join(FHR_DIR, f"{accession}.fhr.json")
        if os.path.exists(fhr_path):
            with open(fhr_path) as f:
                fhr_data = json.load(f)
            print(f"  {accession}: loading from file ({len(digests)} collections)")
            fhr_loaded += load_fhr_for_accession(store, accession, fhr_data, digests)
            continue

        # Try NCBI API
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fhr"))
            from genomeark_to_fhr import fetch_ncbi_report, ncbi_to_fhr
            print(f"  {accession}: fetching from NCBI...", end=" ", flush=True)
            report = fetch_ncbi_report(accession)
            fhr_data = ncbi_to_fhr(report)
            # Save full FHR (with vitalStats) for reference
            os.makedirs(FHR_DIR, exist_ok=True)
            with open(fhr_path, "w") as f:
                json.dump(fhr_data, f, indent=2)
            print(f"OK ({len(digests)} collections)")
            fhr_loaded += load_fhr_for_accession(store, accession, fhr_data, digests)
        except Exception as e:
            print(f"  {accession}: SKIP ({e})")

    print(f"\nPhase 2 done: {fhr_loaded} FHR entries loaded")

    # Summary
    print("\n=== Summary ===")
    store_stats = store.stats()
    print(f"Store stats: {store_stats}")
    fhr_digests = store.list_fhr_metadata()
    print(f"FHR entries: {len(fhr_digests)}")

    # Verify FHR data is readable
    for digest in fhr_digests:
        fhr = store.get_fhr_metadata(digest)
        print(f"  {digest}: genome={fhr.genome}, version={fhr.version}")

    print(f"\nStore path: {args.store_path}")
    print("Done!")


if __name__ == "__main__":
    main()
