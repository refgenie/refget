#!/usr/bin/env python3
"""
Split the combined refget store into two stores: VGP vertebrates and reference genomes.

Reads digest_map.csv (produced by 02_build/build_digest_map.py) which has a 'group'
column for every FASTA. Collections with group='vertebrates' go to the VGP store,
everything else goes to the ref store.

Usage:
    python src/90_split_store.py --dry-run
    python src/90_split_store.py
"""

import argparse
import csv
import os
import sys
import time

from refget.store import RefgetStore

BRICK_ROOT = os.environ["BRICK_ROOT"]
DEFAULT_SOURCE = os.environ.get("STORE_PATH", os.path.join(BRICK_ROOT, "refget_store"))
STAGING = os.environ.get("STAGING", os.path.join(BRICK_ROOT, "refget_staging"))
DEFAULT_DIGEST_MAP = os.path.join(STAGING, "digest_map.csv")
DEFAULT_VGP_OUTPUT = os.environ.get("VGP_STORE_PATH", os.path.join(BRICK_ROOT, "refget-store", "vgp"))
DEFAULT_REF_OUTPUT = os.environ.get("REF_STORE_PATH", os.path.join(BRICK_ROOT, "refget-store", "jungle"))

VGP_GROUPS = {"vertebrates"}


def _paginate(store):
    """Yield pages of collection results from a store."""
    page = 0
    while True:
        result = store.list_collections(page, 1000)
        yield result["results"]
        if len(result["results"]) < 1000:
            break
        page += 1


def load_digest_map(digest_map_path: str) -> dict[str, set[str]]:
    """Read digest_map.csv and return group -> set of digests."""
    groups: dict[str, set[str]] = {}
    with open(digest_map_path) as f:
        for row in csv.DictReader(f):
            digest = row.get("digest", "").strip()
            group = row.get("group", "unknown").strip()
            if digest:
                groups.setdefault(group, set()).add(digest)
    return groups


def split_store(
    source_path: str,
    digest_map_path: str,
    vgp_output: str,
    ref_output: str,
    dry_run: bool = False,
):
    # Load group -> digest mapping
    group_digests = load_digest_map(digest_map_path)

    vgp_digests = set()
    ref_digests = set()
    for group, digests in group_digests.items():
        label = "VGP" if group in VGP_GROUPS else "ref"
        print(f"  {group}: {len(digests)} collections ({label})")
        if group in VGP_GROUPS:
            vgp_digests |= digests
        else:
            ref_digests |= digests

    # Open source store and load all collections (metadata only)
    print(f"\nOpening source store: {source_path}")
    source = RefgetStore.on_disk(source_path)
    source.load_all_collections()

    # Get all store digests
    all_store_digests = set()
    page = 0
    while True:
        result = source.list_collections(page, 1000)
        for c in result["results"]:
            all_store_digests.add(c.digest)
        if len(result["results"]) < 1000:
            break
        page += 1

    vgp_in_store = vgp_digests & all_store_digests
    ref_in_store = ref_digests & all_store_digests
    unaccounted = all_store_digests - vgp_digests - ref_digests

    print(f"\nTotal in store:  {len(all_store_digests)}")
    print(f"VGP to import:   {len(vgp_in_store)}")
    print(f"Ref to import:   {len(ref_in_store)}")
    if unaccounted:
        print(f"Unaccounted:     {len(unaccounted)} (in store but not in digest_map)")

    if vgp_digests - all_store_digests:
        print(f"Warning: {len(vgp_digests - all_store_digests)} VGP digests not in store", file=sys.stderr)
    if ref_digests - all_store_digests:
        print(f"Warning: {len(ref_digests - all_store_digests)} ref digests not in store", file=sys.stderr)

    if dry_run:
        print("\n--dry-run: stopping here.")
        return

    # Import VGP collections
    print(f"\nCreating VGP store: {vgp_output}")
    vgp_store = RefgetStore.on_disk(vgp_output)
    existing_vgp = {c.digest for p in _paginate(vgp_store) for c in p}
    to_import_vgp = sorted(vgp_in_store - existing_vgp)
    print(f"VGP: {len(vgp_in_store)} total, {len(existing_vgp)} already imported, {len(to_import_vgp)} remaining")
    t0 = time.time()
    for i, digest in enumerate(to_import_vgp, 1):
        print(f"  [{i}/{len(to_import_vgp)}] {digest}")
        vgp_store.import_collection(source, digest)
    print(f"VGP import done in {time.time() - t0:.1f}s")

    # Import ref collections
    print(f"\nCreating ref store: {ref_output}")
    ref_store = RefgetStore.on_disk(ref_output)
    existing_ref = {c.digest for p in _paginate(ref_store) for c in p}
    to_import_ref = sorted(ref_in_store - existing_ref)
    print(f"Ref: {len(ref_in_store)} total, {len(existing_ref)} already imported, {len(to_import_ref)} remaining")
    t0 = time.time()
    for i, digest in enumerate(to_import_ref, 1):
        print(f"  [{i}/{len(to_import_ref)}] {digest}")
        ref_store.import_collection(source, digest)
    print(f"Ref import done in {time.time() - t0:.1f}s")

    print("\nDone!")
    print(f"  VGP store: {vgp_output}")
    print(f"  Ref store: {ref_output}")


def main():
    parser = argparse.ArgumentParser(
        description="Split combined refget store into VGP and ref genome stores."
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--digest-map", default=DEFAULT_DIGEST_MAP)
    parser.add_argument("--vgp-output", default=DEFAULT_VGP_OUTPUT)
    parser.add_argument("--ref-output", default=DEFAULT_REF_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    split_store(
        source_path=args.source,
        digest_map_path=args.digest_map,
        vgp_output=args.vgp_output,
        ref_output=args.ref_output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
