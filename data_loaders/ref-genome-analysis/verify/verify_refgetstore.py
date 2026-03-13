#!/usr/bin/env python3
"""
Verification script for the brickyard RefgetStore.

Runs automated checks against the store at STORE_PATH and produces a
structured pass/fail report. Designed to work with a partial store
(not all files loaded yet) and without aliases (alias registration
has not been done yet).

Usage:
    python verify_refgetstore.py
    python verify_refgetstore.py --store-path /alt/path --limit 5

Expected results (update after first successful run):
- collections: ~XXX unique (out of ~1,147 input FASTAs processed so far)
- sequences: ~XXX unique
- roundtrip digest match: PASS for at least one collection
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time

BRICK_ROOT = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta"
STORE_PATH = f"{BRICK_ROOT}/refget_store"
INVENTORY_CSV = f"{BRICK_ROOT}/refgenomes_inventory.csv"
DIGEST_MAP_CSV = f"{BRICK_ROOT}/refget_staging/digest_map.csv"

results = []


def check(name, passed, detail=""):
    """Record and print a check result."""
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"[{status}] {name}" + (f" -- {detail}" if detail else ""))


def parse_args():
    parser = argparse.ArgumentParser(description="Verify brickyard RefgetStore")
    parser.add_argument("--store-path", default=STORE_PATH, help="RefgetStore path")
    parser.add_argument("--inventory", default=INVENTORY_CSV, help="Inventory CSV path")
    parser.add_argument("--digest-map", default=DIGEST_MAP_CSV, help="Digest map CSV path")
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of collections to test for round-trip export (default: 3)",
    )
    parser.add_argument(
        "--skip-roundtrip",
        action="store_true",
        help="Skip round-trip FASTA export checks (slow for large genomes)",
    )
    return parser.parse_args()


# ── Check 1: Store opens and stats are valid ───────────────────────────


def check_store_opens(store_path):
    """Open the store and verify basic stats."""
    try:
        from refget.store import RefgetStore

        store = RefgetStore.open_local(store_path)
        check("store_opens", True, f"path={store_path}")
    except Exception as e:
        check("store_opens", False, f"path={store_path}, error={e}")
        return None

    # Count collections and sequences
    try:
        collections = list(store.list_collections()["results"])
        n_collections = len(collections)
    except Exception as e:
        check("list_collections", False, f"error={e}")
        n_collections = 0

    try:
        sequences = list(store.list_sequences())
        n_sequences = len(sequences)
    except Exception as e:
        check("list_sequences", False, f"error={e}")
        n_sequences = 0

    check("collections_nonzero", n_collections > 0, f"collections={n_collections}")
    check("sequences_nonzero", n_sequences > 0, f"sequences={n_sequences}")

    # Stats object
    try:
        stats = store.stats()
        check("stats_callable", True, f"stats={stats}")
    except Exception as e:
        check("stats_callable", False, f"error={e}")

    return store


# ── Check 2: Digest map coverage ──────────────────────────────────────


def check_digest_map(store, digest_map_path):
    """Verify that digests in the digest map are present in the store."""
    if not os.path.exists(digest_map_path):
        check("digest_map_exists", False, f"not found: {digest_map_path}")
        return

    check("digest_map_exists", True, f"path={digest_map_path}")

    # Read digest map
    rows = []
    with open(digest_map_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total = len(rows)
    with_digest = [r for r in rows if r.get("digest")]
    with_error = [r for r in rows if r.get("error")]

    check(
        "digest_map_stats",
        len(with_digest) > 0,
        f"total_rows={total}, with_digest={len(with_digest)}, with_error={len(with_error)}",
    )

    # Get store collection digests for comparison
    store_digests = {meta.digest for meta in store.list_collections()["results"]}

    # Check how many digest_map digests are in the store
    matched = 0
    missing = []
    for row in with_digest:
        d = row["digest"]
        if d in store_digests:
            matched += 1
        else:
            missing.append(d[:16] + "...")

    check(
        "digest_map_coverage",
        matched == len(with_digest),
        f"in_store={matched}/{len(with_digest)}"
        + (f", missing_sample={missing[:5]}" if missing else ""),
    )


# ── Check 3: Collection level2 data integrity ─────────────────────────


def check_level2_integrity(store, n_to_check=3):
    """Verify level2 data for a sample of collections."""
    collections = list(store.list_collections()["results"])
    if not collections:
        check("level2_integrity", False, "no collections to check")
        return

    sample = collections[:n_to_check]
    all_ok = True
    details = []

    for meta in sample:
        digest = meta.digest
        try:
            level2 = store.get_collection_level2(digest)
            names = level2.get("names", [])
            lengths = level2.get("lengths", [])
            sequences = level2.get("sequences", [])

            arrays_ok = (
                len(names) == len(lengths) == len(sequences) and len(names) > 0
            )
            lengths_ok = all(l > 0 for l in lengths) if lengths else False

            if not arrays_ok or not lengths_ok:
                all_ok = False
                details.append(
                    f"{digest[:16]}: names={len(names)} lengths={len(lengths)} "
                    f"sequences={len(sequences)} lengths_positive={lengths_ok}"
                )
            else:
                details.append(
                    f"{digest[:16]}: {len(names)} seqs, OK"
                )
        except Exception as e:
            all_ok = False
            details.append(f"{digest[:16]}: ERROR {e}")

    check(
        "level2_arrays_valid",
        all_ok,
        f"checked={len(sample)}, results=[{'; '.join(details)}]",
    )


# ── Check 4: Round-trip FASTA export and digest comparison ─────────────


def check_roundtrip_export(store, store_path, digest_map_path, inventory_path, limit=3):
    """Export FASTAs from the store and compare digests to originals."""
    try:
        from gtars.refget import digest_fasta
    except ImportError:
        check("roundtrip_export", False, "gtars.refget.digest_fasta not available")
        return

    # Build a mapping from digest -> original path using digest_map + inventory
    digest_to_original = {}

    if os.path.exists(digest_map_path) and os.path.exists(inventory_path):
        # Read inventory to get path -> accession mapping (for reference)
        inv_lookup = {}
        with open(inventory_path, newline="") as f:
            for row in csv.DictReader(f):
                inv_lookup[row["path"]] = row

        # Read digest_map to get digest -> path mapping
        with open(digest_map_path, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("digest") and row.get("path"):
                    # Only keep the first mapping per digest (avoid duplicates)
                    if row["digest"] not in digest_to_original:
                        digest_to_original[row["digest"]] = row["path"]

    if not digest_to_original:
        check("roundtrip_export", False, "no digest-to-path mappings found")
        return

    # Pick a sample of collections that have original files
    collections = list(store.list_collections()["results"])
    test_pairs = []
    for meta in collections:
        if meta.digest in digest_to_original:
            original_path = digest_to_original[meta.digest]
            if os.path.exists(original_path):
                test_pairs.append((meta.digest, original_path))
                if len(test_pairs) >= limit:
                    break

    if not test_pairs:
        check("roundtrip_export", False, "no original FASTA files accessible for comparison")
        return

    all_match = True
    details = []

    for digest, original_path in test_pairs:
        fd, tmp_path = tempfile.mkstemp(suffix=".fa")
        os.close(fd)
        try:
            store.export_fasta(digest, tmp_path, None, 80)

            exported_sc = digest_fasta(tmp_path)
            original_sc = digest_fasta(original_path)

            match = exported_sc.digest == original_sc.digest
            if not match:
                all_match = False
            basename = os.path.basename(original_path)
            details.append(
                f"{basename}: {'MATCH' if match else 'MISMATCH'} "
                f"(exported={exported_sc.digest[:16]}... "
                f"original={original_sc.digest[:16]}...)"
            )
        except Exception as e:
            all_match = False
            basename = os.path.basename(original_path)
            details.append(f"{basename}: ERROR {e}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    check(
        "roundtrip_digest_match",
        all_match,
        f"tested={len(test_pairs)}, results=[{'; '.join(details)}]",
    )


# ── Check 5: CLI stats command works ──────────────────────────────────


def check_cli_stats(store_path):
    """Verify the CLI stats command runs against the store."""
    try:
        result = subprocess.run(
            ["refget", "store", "stats", "--path", store_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            check("cli_stats_runs", True, f"stdout={result.stdout.strip()[:200]}")
        else:
            check(
                "cli_stats_runs",
                False,
                f"returncode={result.returncode}, stderr={result.stderr.strip()[:200]}",
            )
    except FileNotFoundError:
        check("cli_stats_runs", False, "refget CLI not found in PATH")
    except subprocess.TimeoutExpired:
        check("cli_stats_runs", False, "timed out after 60s")
    except Exception as e:
        check("cli_stats_runs", False, f"error={e}")


# ── Check 6: Inventory cross-reference ────────────────────────────────


def check_inventory_crossref(store, inventory_path, digest_map_path):
    """Cross-check inventory against digest_map to verify completeness."""
    if not os.path.exists(inventory_path):
        check("inventory_exists", False, f"not found: {inventory_path}")
        return
    if not os.path.exists(digest_map_path):
        check("inventory_crossref", False, f"digest_map not found: {digest_map_path}")
        return

    # Count inventory rows
    with open(inventory_path, newline="") as f:
        inv_rows = list(csv.DictReader(f))

    # Count digest_map rows
    with open(digest_map_path, newline="") as f:
        dm_rows = list(csv.DictReader(f))

    inv_paths = {r["path"] for r in inv_rows}
    dm_paths = {r["path"] for r in dm_rows}

    # How many inventory files have been processed?
    processed = inv_paths & dm_paths
    unprocessed = inv_paths - dm_paths

    check(
        "inventory_processing_coverage",
        True,  # Always pass -- partial is expected
        f"inventory={len(inv_rows)}, digest_map={len(dm_rows)}, "
        f"processed={len(processed)}, unprocessed={len(unprocessed)}",
    )

    # Check error rate in digest_map
    errors = [r for r in dm_rows if r.get("error")]
    check(
        "digest_map_error_rate",
        len(errors) == 0,
        f"errors={len(errors)}/{len(dm_rows)}"
        + (f", samples={[r['filename'] + ': ' + r['error'] for r in errors[:3]]}" if errors else ""),
    )


# ── Summary and report ────────────────────────────────────────────────


def print_summary(store_path):
    """Print summary and write JSON report."""
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")

    if failed > 0:
        print("\nFailed checks:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['name']}: {r['detail']}")

    # Write JSON report next to the store
    report_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(report_dir, "verification_report.json")
    with open(report_path, "w") as f:
        json.dump(
            {"results": results, "passed": passed, "failed": failed},
            f,
            indent=2,
        )
    print(f"\nJSON report: {report_path}")

    return failed


def main():
    args = parse_args()
    store_path = args.store_path

    print(f"Verifying RefgetStore at: {store_path}")
    print(f"Inventory CSV: {args.inventory}")
    print(f"Digest map CSV: {args.digest_map}")
    print("=" * 60)

    t_start = time.time()

    # Check 1: Store opens and stats
    print("\n── Check 1: Store opens and stats ──")
    store = check_store_opens(store_path)
    if store is None:
        print("\nStore failed to open. Cannot continue.")
        print_summary(store_path)
        sys.exit(1)

    # Check 2: Digest map coverage
    print("\n── Check 2: Digest map coverage ──")
    check_digest_map(store, args.digest_map)

    # Check 3: Level2 data integrity
    print("\n── Check 3: Collection level2 data integrity ──")
    check_level2_integrity(store, n_to_check=min(args.limit, 5))

    # Check 4: Round-trip FASTA export
    if args.skip_roundtrip:
        print("\n── Check 4: Round-trip export (SKIPPED) ──")
        check("roundtrip_digest_match", True, "skipped via --skip-roundtrip")
    else:
        print("\n── Check 4: Round-trip FASTA export ──")
        check_roundtrip_export(
            store, store_path, args.digest_map, args.inventory, limit=args.limit
        )

    # Check 5: CLI stats command
    print("\n── Check 5: CLI stats command ──")
    check_cli_stats(store_path)

    # Check 6: Inventory cross-reference
    print("\n── Check 6: Inventory cross-reference ──")
    check_inventory_crossref(store, args.inventory, args.digest_map)

    elapsed = time.time() - t_start
    print(f"\nVerification completed in {elapsed:.1f}s")

    failed = print_summary(store_path)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
