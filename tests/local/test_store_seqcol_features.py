"""
Tests for RefgetStore seqcol features: level1/level2, compare, find_collections_by_attribute.

Only tests that verify Python-specific behavior beyond what Rust tests cover:
- Rust/Python parity for compare()
- Multi-collection attribute search
- Basic level1/level2 smoke test
- Multi-collection disk roundtrip preserves per-collection ordering and names
"""

import json
import tempfile
from pathlib import Path

import pytest

try:
    from refget.store import RefgetStore

    _RUST_BINDINGS_AVAILABLE = True
except ImportError:
    _RUST_BINDINGS_AVAILABLE = False

TEST_FASTA_DIR = Path("test_fasta")
BASE_FASTA = TEST_FASTA_DIR / "base.fa"
DIFFERENT_NAMES_FASTA = TEST_FASTA_DIR / "different_names.fa"

with open(TEST_FASTA_DIR / "test_fasta_digests.json") as fp:
    TEST_DIGESTS = json.load(fp)

BASE_DIGEST = TEST_DIGESTS["base.fa"]["top_level_digest"]
BASE_LEVEL1 = TEST_DIGESTS["base.fa"]["level1"]
BASE_LEVEL2 = TEST_DIGESTS["base.fa"]["level2"]
DIFFERENT_NAMES_DIGEST = TEST_DIGESTS["different_names.fa"]["top_level_digest"]


@pytest.fixture
def store_with_base():
    """Create an in-memory store with base.fa loaded."""
    store = RefgetStore.in_memory()
    store.add_sequence_collection_from_fasta(str(BASE_FASTA))
    return store


@pytest.fixture
def store_with_two():
    """Create an in-memory store with base.fa and different_names.fa loaded."""
    store = RefgetStore.in_memory()
    store.add_sequence_collection_from_fasta(str(BASE_FASTA))
    store.add_sequence_collection_from_fasta(str(DIFFERENT_NAMES_FASTA))
    return store


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_level1_and_level2_smoke(store_with_base):
    """Level1 returns digests, level2 returns arrays, both have required keys."""
    lvl1 = store_with_base.get_collection_level1(BASE_DIGEST)
    lvl2 = store_with_base.get_collection_level2(BASE_DIGEST)

    for key in ("names", "lengths", "sequences"):
        assert key in lvl1
        assert key in lvl2
        # Level1 values are digest strings, level2 values are lists
        assert isinstance(lvl1[key], str)
        assert isinstance(lvl2[key], list)

    # Verify level2 matches expected values
    assert sorted(lvl2["names"]) == sorted(BASE_LEVEL2["names"])
    assert sorted(lvl2["lengths"]) == sorted(BASE_LEVEL2["lengths"])


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_compare_matches_python_implementation(store_with_two):
    """Verify store.compare() (Rust) agrees with compare_seqcols() (Python) on core attributes."""
    from refget.utils import compare_seqcols

    lvl2_a = store_with_two.get_collection_level2(BASE_DIGEST)
    lvl2_b = store_with_two.get_collection_level2(DIFFERENT_NAMES_DIGEST)

    python_result = compare_seqcols(lvl2_a, lvl2_b)
    rust_result = store_with_two.compare(BASE_DIGEST, DIFFERENT_NAMES_DIGEST)

    core_attrs = {"names", "lengths", "sequences"}
    assert core_attrs <= set(python_result["attributes"]["a_and_b"])
    assert core_attrs <= set(rust_result["attributes"]["a_and_b"])

    for attr in core_attrs:
        assert (
            rust_result["array_elements"]["a_and_b_count"][attr]
            == python_result["array_elements"]["a_and_b_count"][attr]
        )
        assert (
            rust_result["array_elements"]["a_and_b_same_order"][attr]
            == python_result["array_elements"]["a_and_b_same_order"][attr]
        )


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_shared_attribute_returns_multiple(store_with_two):
    """base.fa and different_names.fa share lengths; searching by lengths returns both."""
    lengths_digest = BASE_LEVEL1["lengths"]
    results = store_with_two.find_collections_by_attribute("lengths", lengths_digest)
    assert BASE_DIGEST in results
    assert DIFFERENT_NAMES_DIGEST in results


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_multi_collection_disk_roundtrip_preserves_ordering():
    """Multi-collection disk roundtrip preserves per-collection names and element ordering.

    Tests the complete PyO3 -> Rust -> disk -> Rust -> PyO3 roundtrip for three
    collections that share sequences under different names and different orderings.
    This covers the intersection of the two previously-fixed bugs:
      1. HashMap ordering (inner map now IndexMap)
      2. Global name leakage (get_collection() overrides meta.name from name_lookup)
    """
    # FASTA A: base ordering — chrX first, then chr1, then chr2
    fasta_a = ">chrX\nTTGGGGAA\n>chr1\nGGAA\n>chr2\nGCGC\n"
    # FASTA B: different order — chr1 first, same sequences as A
    fasta_b = ">chr1\nGGAA\n>chr2\nGCGC\n>chrX\nTTGGGGAA\n"
    # FASTA C: name swap — chr2 has GGAA, chr1 has GCGC (opposite of A/B)
    fasta_c = ">chrX\nTTGGGGAA\n>chr2\nGGAA\n>chr1\nGCGC\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        fasta_a_path = tmpdir / "a.fa"
        fasta_b_path = tmpdir / "b.fa"
        fasta_c_path = tmpdir / "c.fa"
        fasta_a_path.write_text(fasta_a)
        fasta_b_path.write_text(fasta_b)
        fasta_c_path.write_text(fasta_c)

        store_path = tmpdir / "store"

        # Build a disk-backed store and load three FASTAs
        store = RefgetStore.on_disk(str(store_path))
        meta_a, _ = store.add_sequence_collection_from_fasta(str(fasta_a_path))
        meta_b, _ = store.add_sequence_collection_from_fasta(str(fasta_b_path))
        meta_c, _ = store.add_sequence_collection_from_fasta(str(fasta_c_path))
        digest_a = meta_a.digest
        digest_b = meta_b.digest
        digest_c = meta_c.digest

        # Record level2 before write
        store.load_all_collections()
        pre_a = store.get_collection_level2(digest_a)
        pre_b = store.get_collection_level2(digest_b)
        pre_c = store.get_collection_level2(digest_c)

        # Verify pre-write ordering
        assert pre_a["names"] == ["chrX", "chr1", "chr2"], f"A names: {pre_a['names']}"
        assert pre_b["names"] == ["chr1", "chr2", "chrX"], f"B names: {pre_b['names']}"
        assert pre_c["names"] == ["chrX", "chr2", "chr1"], f"C names: {pre_c['names']}"

        store.write()
        del store

        # Reopen from disk and verify roundtrip
        reloaded = RefgetStore.open_local(str(store_path))
        reloaded.load_all_collections()

        post_a = reloaded.get_collection_level2(digest_a)
        post_b = reloaded.get_collection_level2(digest_b)
        post_c = reloaded.get_collection_level2(digest_c)

        assert post_a["names"] == pre_a["names"], f"A names after roundtrip: {post_a['names']}"
        assert post_b["names"] == pre_b["names"], f"B names after roundtrip: {post_b['names']}"
        assert post_c["names"] == pre_c["names"], f"C names after roundtrip: {post_c['names']}"

        assert post_a["lengths"] == pre_a["lengths"], "A lengths after roundtrip"
        assert post_b["lengths"] == pre_b["lengths"], "B lengths after roundtrip"
        assert post_c["lengths"] == pre_c["lengths"], "C lengths after roundtrip"

        assert post_a["sequences"] == pre_a["sequences"], "A sequences after roundtrip"
        assert post_b["sequences"] == pre_b["sequences"], "B sequences after roundtrip"
        assert post_c["sequences"] == pre_c["sequences"], "C sequences after roundtrip"

        # Cross-check: FASTA C chr2=GGAA and A chr1=GGAA should share the same sequence digest
        assert post_c["sequences"][1] == post_a["sequences"][1], (
            "C.chr2 and A.chr1 both have GGAA, should share sequence digest"
        )


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_remove_collection_round_trip():
    """Add a collection, remove it with orphan cleanup, verify store is empty."""
    store = RefgetStore.in_memory()
    store.set_quiet(True)
    store.add_sequence_collection_from_fasta(str(BASE_FASTA))

    assert len(store.list_collections()["results"]) == 1
    assert len(store.list_sequences()) > 0

    digest = store.list_collections()["results"][0].digest

    # Nonexistent returns False
    assert store.remove_collection("nonexistent") is False

    # Real removal with orphan cleanup
    assert store.remove_collection(digest, remove_orphan_sequences=True) is True
    assert len(store.list_collections()["results"]) == 0
    assert len(store.list_sequences()) == 0
