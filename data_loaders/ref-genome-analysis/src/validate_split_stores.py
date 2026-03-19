#!/usr/bin/env python3
"""
Validate the VGP and ref genome stores produced by 90_split_store.py.

Checks that the split stores are complete, internally consistent, and
that every collection from the source store ended up in exactly one
output store.

Usage:
    source env/on-cluster.env
    python src/validate_split_stores.py                  # validate both
    python src/validate_split_stores.py --store vgp      # VGP only
    python src/validate_split_stores.py --store ref      # ref only
    python src/validate_split_stores.py --thorough       # deep checks (slow)
"""

import argparse
import csv
import json
import os
import sys
import tempfile
import time

BRICK_ROOT = os.environ["BRICK_ROOT"]
STAGING = os.environ.get("STAGING", os.path.join(BRICK_ROOT, "refget_staging"))
SOURCE_PATH = os.environ.get("STORE_PATH", os.path.join(BRICK_ROOT, "refget_store"))
VGP_PATH = os.path.join(BRICK_ROOT, "refget-store/vgp")
REF_PATH = os.path.join(BRICK_ROOT, "refget-store/jungle")
DIGEST_MAP = os.path.join(STAGING, "digest_map.csv")

VGP_GROUPS = {"vertebrates"}

results = []


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


def load_digest_map(path):
    """Return (group->set_of_digests, all_rows)."""
    groups = {}
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append(row)
            digest = row.get("digest", "").strip()
            group = row.get("group", "unknown").strip()
            if digest:
                groups.setdefault(group, set()).add(digest)
    return groups, rows


def get_all_collection_digests(store):
    """Paginate through list_collections to get all digests."""
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


# ── Test 1: Store opens and basic stats ────────────────────────────────


def test_store_opens(store_path, label):
    """Verify store opens and has non-zero collections/sequences."""
    from refget.store import RefgetStore

    print(f"\n── {label}: Store opens and stats ──")

    try:
        store = RefgetStore.open_local(store_path)
        check(f"{label}_opens", True, f"path={store_path}")
    except Exception as e:
        check(f"{label}_opens", False, f"error={e}")
        return None

    try:
        stats = store.stats()
        check(f"{label}_stats", True, f"stats={stats}")
    except Exception as e:
        check(f"{label}_stats", False, f"error={e}")

    digests = get_all_collection_digests(store)
    check(f"{label}_has_collections", len(digests) > 0, f"n={len(digests)}")

    try:
        seqs = store.list_sequences()
        n_seqs = len(seqs)
        check(f"{label}_has_sequences", n_seqs > 0, f"n={n_seqs}")
    except Exception as e:
        check(f"{label}_has_sequences", False, f"error={e}")

    return store


# ── Test 2: Collection counts match digest map ────────────────────────


def test_collection_counts(store, label, expected_digests):
    """Verify the store has exactly the expected collections."""
    print(f"\n── {label}: Collection count vs digest map ──")

    store_digests = get_all_collection_digests(store)

    check(
        f"{label}_count_match",
        len(store_digests) == len(expected_digests),
        f"store={len(store_digests)}, expected={len(expected_digests)}",
    )

    missing = expected_digests - store_digests
    extra = store_digests - expected_digests

    check(
        f"{label}_no_missing",
        len(missing) == 0,
        f"missing={len(missing)}" + (f", sample={list(missing)[:3]}" if missing else ""),
    )
    check(
        f"{label}_no_extra",
        len(extra) == 0,
        f"extra={len(extra)}" + (f", sample={list(extra)[:3]}" if extra else ""),
    )

    return store_digests


# ── Test 3: Level2 integrity for all collections ──────────────────────


def test_level2_integrity(store, label, digests, limit=None):
    """Verify level2 arrays are aligned and valid for every collection."""
    print(f"\n── {label}: Level2 data integrity ──")

    to_check = sorted(digests)
    if limit:
        to_check = to_check[:limit]

    ok_count = 0
    fail_count = 0
    fail_details = []

    for digest in to_check:
        try:
            level2 = store.get_collection_level2(digest)
            names = level2.get("names", [])
            lengths = level2.get("lengths", [])
            sequences = level2.get("sequences", [])

            arrays_aligned = len(names) == len(lengths) == len(sequences) and len(names) > 0
            lengths_positive = all(l > 0 for l in lengths) if lengths else False
            seqs_nonempty = all(s and len(s) > 0 for s in sequences) if sequences else False

            if arrays_aligned and lengths_positive and seqs_nonempty:
                ok_count += 1
            else:
                fail_count += 1
                fail_details.append(
                    f"{digest[:16]}: names={len(names)} lengths={len(lengths)} "
                    f"seqs={len(sequences)} aligned={arrays_aligned} "
                    f"lengths_ok={lengths_positive} seqs_ok={seqs_nonempty}"
                )
        except Exception as e:
            fail_count += 1
            fail_details.append(f"{digest[:16]}: ERROR {e}")

    total = ok_count + fail_count
    check(
        f"{label}_level2_all_valid",
        fail_count == 0,
        f"ok={ok_count}/{total}" + (f", failures=[{'; '.join(fail_details[:5])}]" if fail_details else ""),
    )


# ── Test 4: Aliases were imported ─────────────────────────────────────


def test_aliases(store, label, digests):
    """Check that alias namespaces exist and at least some collections have aliases."""
    print(f"\n── {label}: Alias integrity ──")

    # Check namespaces exist
    try:
        coll_ns = store.list_collection_alias_namespaces()
        check(f"{label}_collection_alias_namespaces", len(coll_ns) > 0, f"namespaces={coll_ns}")
    except Exception as e:
        check(f"{label}_collection_alias_namespaces", False, f"error={e}")
        coll_ns = []

    try:
        seq_ns = store.list_sequence_alias_namespaces()
        check(f"{label}_sequence_alias_namespaces", len(seq_ns) > 0, f"namespaces={seq_ns}")
    except Exception as e:
        check(f"{label}_sequence_alias_namespaces", False, f"error={e}")
        seq_ns = []

    # Sample: check that some collections have aliases
    sample = sorted(digests)[:20]
    with_aliases = 0
    for digest in sample:
        try:
            aliases = store.get_aliases_for_collection(digest)
            if aliases and len(aliases) > 0:
                with_aliases += 1
        except Exception:
            pass

    check(
        f"{label}_collections_have_aliases",
        with_aliases > 0,
        f"with_aliases={with_aliases}/{len(sample)} (sampled)",
    )

    # For each namespace, count total aliases
    for ns in coll_ns:
        try:
            aliases = store.list_collection_aliases(ns)
            check(f"{label}_coll_alias_count_{ns}", len(aliases) > 0, f"n={len(aliases)}")
        except Exception as e:
            check(f"{label}_coll_alias_count_{ns}", False, f"error={e}")

    # Forward lookup: pick an alias and verify it resolves
    for ns in coll_ns[:1]:  # test first namespace
        try:
            aliases = store.list_collection_aliases(ns)
            if aliases:
                alias = aliases[0]
                resolved = store.get_collection_by_alias(ns, alias)
                check(
                    f"{label}_coll_alias_forward_lookup_{ns}",
                    resolved is not None,
                    f"alias={alias}, resolved={resolved.digest[:16] if resolved else None}",
                )
        except Exception as e:
            check(f"{label}_coll_alias_forward_lookup_{ns}", False, f"error={e}")

    # Sequence alias count proportionality check
    for ns in seq_ns:
        try:
            aliases = store.list_sequence_aliases(ns)
            n_aliases = len(aliases) if aliases else 0
            check(f"{label}_seq_alias_count_{ns}", n_aliases > 0, f"n={n_aliases}")
        except Exception as e:
            check(f"{label}_seq_alias_count_{ns}", False, f"error={e}")


# ── Test 5: FHR metadata was imported ─────────────────────────────────


def test_fhr_metadata(store, label, digests):
    """Check that FHR metadata exists for collections."""
    print(f"\n── {label}: FHR metadata ──")

    try:
        fhr_digests = store.list_fhr_metadata()
        n_fhr = len(fhr_digests)
        check(f"{label}_fhr_exists", n_fhr > 0, f"n_with_fhr={n_fhr}")
    except Exception as e:
        check(f"{label}_fhr_exists", False, f"error={e}")
        return

    # Verify FHR digests are in this store
    fhr_set = set(fhr_digests)
    orphan_fhr = fhr_set - digests
    check(
        f"{label}_fhr_no_orphans",
        len(orphan_fhr) == 0,
        f"orphaned_fhr={len(orphan_fhr)}" + (f", sample={list(orphan_fhr)[:3]}" if orphan_fhr else ""),
    )

    # Sample: read a few FHR records
    sample = list(fhr_set & digests)[:5]
    readable = 0
    for digest in sample:
        try:
            fhr = store.get_fhr_metadata(digest)
            if fhr is not None:
                readable += 1
        except Exception:
            pass

    check(
        f"{label}_fhr_readable",
        readable == len(sample),
        f"readable={readable}/{len(sample)}",
    )


# ── Test 6: Sequence retrieval works ──────────────────────────────────


def test_sequence_retrieval(store, label, digests):
    """Verify sequences can be retrieved for sampled collections."""
    print(f"\n── {label}: Sequence retrieval ──")

    sample = sorted(digests)[:5]
    ok_count = 0
    fail_details = []

    for coll_digest in sample:
        try:
            level2 = store.get_collection_level2(coll_digest)
            seq_digests = level2.get("sequences", [])
            lengths = level2.get("lengths", [])
            if not seq_digests:
                fail_details.append(f"{coll_digest[:16]}: no sequences")
                continue

            # Test first sequence in collection
            seq = store.get_sequence(seq_digests[0])
            if seq is not None:
                ok_count += 1
            else:
                fail_details.append(f"{coll_digest[:16]}: get_sequence returned None")
        except Exception as e:
            fail_details.append(f"{coll_digest[:16]}: {e}")

    check(
        f"{label}_sequence_retrieval",
        ok_count == len(sample),
        f"ok={ok_count}/{len(sample)}" + (f", failures=[{'; '.join(fail_details[:3])}]" if fail_details else ""),
    )


# ── Test 7: No overlap between VGP and ref stores ────────────────────


def test_no_overlap(vgp_store, ref_store):
    """Verify no collection appears in both stores."""
    print("\n── Cross-store: No overlap ──")

    vgp_digests = get_all_collection_digests(vgp_store)
    ref_digests = get_all_collection_digests(ref_store)

    overlap = vgp_digests & ref_digests
    check(
        "no_collection_overlap",
        len(overlap) == 0,
        f"overlap={len(overlap)}" + (f", sample={list(overlap)[:3]}" if overlap else ""),
    )


# ── Test 8: Full coverage — VGP + ref = source ───────────────────────


def test_full_coverage(vgp_store, ref_store, source_store):
    """Verify VGP + ref stores together contain all source collections."""
    print("\n── Cross-store: Full coverage ──")

    vgp_digests = get_all_collection_digests(vgp_store)
    ref_digests = get_all_collection_digests(ref_store)
    source_digests = get_all_collection_digests(source_store)

    combined = vgp_digests | ref_digests
    missing = source_digests - combined
    extra = combined - source_digests

    check(
        "combined_equals_source",
        len(missing) == 0 and len(extra) == 0,
        f"source={len(source_digests)}, vgp={len(vgp_digests)}, ref={len(ref_digests)}, "
        f"combined={len(combined)}, missing={len(missing)}, extra={len(extra)}",
    )


# ── Test 9: Roundtrip FASTA export ───────────────────────────────────


def test_roundtrip_fasta(store, label, digests, limit=3):
    """Export a few collections to FASTA and verify digest matches."""
    print(f"\n── {label}: Roundtrip FASTA export ──")

    try:
        from gtars.refget import digest_fasta
    except ImportError:
        check(f"{label}_roundtrip", False, "gtars.refget.digest_fasta not available")
        return

    sample = sorted(digests)[:limit]
    ok_count = 0
    fail_details = []

    for digest in sample:
        fd, tmp_path = tempfile.mkstemp(suffix=".fa")
        os.close(fd)
        try:
            store.export_fasta(digest, tmp_path, None, 80)
            exported_sc = digest_fasta(tmp_path)
            match = exported_sc.digest == digest
            if match:
                ok_count += 1
            else:
                fail_details.append(
                    f"{digest[:16]}: exported={exported_sc.digest[:16]} != original"
                )
        except Exception as e:
            fail_details.append(f"{digest[:16]}: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    check(
        f"{label}_roundtrip_fasta",
        ok_count == len(sample),
        f"ok={ok_count}/{len(sample)}" + (f", failures=[{'; '.join(fail_details)}]" if fail_details else ""),
    )


# ── Main ──────────────────────────────────────────────────────────────


def validate_store(store_path, label, expected_digests, thorough=False):
    """Run all single-store validations."""
    from refget.store import RefgetStore

    store = test_store_opens(store_path, label)
    if store is None:
        return None

    store_digests = test_collection_counts(store, label, expected_digests)

    # Level2: check all in thorough mode, sample otherwise
    limit = None if thorough else 20
    test_level2_integrity(store, label, store_digests, limit=limit)

    test_aliases(store, label, store_digests)
    test_fhr_metadata(store, label, store_digests)
    test_sequence_retrieval(store, label, store_digests)

    if thorough:
        test_roundtrip_fasta(store, label, store_digests, limit=5)

    return store


def main():
    parser = argparse.ArgumentParser(description="Validate split RefgetStores")
    parser.add_argument(
        "--store",
        choices=["vgp", "ref", "both"],
        default="both",
        help="Which store to validate (default: both)",
    )
    parser.add_argument(
        "--thorough",
        action="store_true",
        help="Run deep checks: all level2, roundtrip FASTA (slow)",
    )
    parser.add_argument("--vgp-path", default=VGP_PATH)
    parser.add_argument("--ref-path", default=REF_PATH)
    parser.add_argument("--source-path", default=SOURCE_PATH)
    parser.add_argument("--digest-map", default=DIGEST_MAP)
    args = parser.parse_args()

    print(f"Validating split stores")
    print(f"  Source:     {args.source_path}")
    print(f"  VGP:        {args.vgp_path}")
    print(f"  Ref:        {args.ref_path}")
    print(f"  Digest map: {args.digest_map}")
    print(f"  Thorough:   {args.thorough}")
    print("=" * 60)

    t_start = time.time()

    # Load digest map to compute expected sets
    group_digests, dm_rows = load_digest_map(args.digest_map)
    vgp_expected = set()
    ref_expected = set()
    for group, digests in group_digests.items():
        if group in VGP_GROUPS:
            vgp_expected |= digests
        else:
            ref_expected |= digests

    print(f"\nDigest map: {len(dm_rows)} rows, "
          f"VGP expected={len(vgp_expected)}, ref expected={len(ref_expected)}")

    vgp_store = None
    ref_store = None

    if args.store in ("vgp", "both"):
        vgp_store = validate_store(args.vgp_path, "vgp", vgp_expected, args.thorough)

    if args.store in ("ref", "both"):
        ref_store = validate_store(args.ref_path, "ref", ref_expected, args.thorough)

    # Cross-store checks (only if both stores validated)
    if vgp_store and ref_store:
        test_no_overlap(vgp_store, ref_store)

        # Full coverage against source
        from refget.store import RefgetStore
        if RefgetStore.store_exists(args.source_path):
            source_store = RefgetStore.open_local(args.source_path)
            test_full_coverage(vgp_store, ref_store, source_store)
        else:
            check("full_coverage", False, f"source store not found: {args.source_path}")

    # Summary
    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print(f"Time:   {elapsed:.1f}s")

    if failed > 0:
        print("\nFailed checks:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['name']}: {r['detail']}")

    # Write JSON report
    report_path = os.path.join(STAGING, "split_validation_report.json")
    os.makedirs(STAGING, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({"results": results, "passed": passed, "failed": failed}, f, indent=2)
    print(f"\nJSON report: {report_path}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
