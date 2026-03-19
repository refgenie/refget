"""
Load FHR metadata JSON files into an existing RefgetStore.

Resolves accessions to collection digests via the store's 'insdc' alias
namespace. Strips vitalStats before loading, since those describe the source
assembly, not the specific sequence collection.

Usage:
    python load_fhr_metadata.py --store-path /path/to/store --fhr-dir fhr_metadata/
    python load_fhr_metadata.py --store-path /path/to/store --fhr file.fhr.json --digest abc123
"""

import argparse
import glob
import json
import os
import sys
import tempfile

from gtars.refget import RefgetStore


def strip_vital_stats(fhr_path):
    """Write a temp FHR file with vitalStats removed. Returns temp path."""
    with open(fhr_path) as f:
        fhr_data = json.load(f)
    provenance = {k: v for k, v in fhr_data.items() if k != "vitalStats"}
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".fhr.json", delete=False)
    json.dump(provenance, tmp, indent=2)
    tmp.close()
    return tmp.name


def load_fhr_dir(store, fhr_dir, namespaces=("insdc", "refseq")):
    """Load all .fhr.json files, resolving accession -> digest via alias namespaces."""
    fhr_files = sorted(glob.glob(os.path.join(fhr_dir, "*.fhr.json")))
    if not fhr_files:
        print(f"No .fhr.json files found in {fhr_dir}", file=sys.stderr)
        return

    print(f"Loading {len(fhr_files)} FHR files, resolving via {namespaces} aliases...", file=sys.stderr)

    n_loaded = 0
    n_skipped = 0
    for fhr_path in fhr_files:
        basename = os.path.basename(fhr_path)
        accession = basename.replace(".fhr.json", "")

        meta = None
        for ns in namespaces:
            meta = store.get_collection_metadata_by_alias(ns, accession)
            if meta is not None:
                break

        if meta is None:
            n_skipped += 1
            continue

        tmp_path = strip_vital_stats(fhr_path)
        try:
            store.load_fhr_metadata(meta.digest, tmp_path)
        finally:
            os.unlink(tmp_path)
        n_loaded += 1

        if n_loaded % 100 == 0:
            print(f"  ... {n_loaded} loaded", file=sys.stderr)

    print(f"\nLoaded {n_loaded}, skipped {n_skipped} (no alias match)", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Load FHR metadata into RefgetStore")
    parser.add_argument("--store-path", required=True, help="Path to RefgetStore")
    parser.add_argument("--fhr-dir", help="Directory of .fhr.json files")
    parser.add_argument("--fhr", help="Single .fhr.json file")
    parser.add_argument("--digest", help="Collection digest (required with --fhr)")
    args = parser.parse_args()

    store = RefgetStore.on_disk(args.store_path)

    if args.fhr_dir:
        load_fhr_dir(store, args.fhr_dir)
    elif args.fhr and args.digest:
        tmp_path = strip_vital_stats(args.fhr)
        try:
            store.load_fhr_metadata(args.digest, tmp_path)
        finally:
            os.unlink(tmp_path)
        print(f"Loaded {args.fhr} -> {args.digest}", file=sys.stderr)
    else:
        print("Provide --fhr-dir or --fhr + --digest", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
