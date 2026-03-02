"""
Tests for RefgetStore seqcol features: level1/level2, compare, find_collections_by_attribute.

Only tests that verify Python-specific behavior beyond what Rust tests cover:
- Rust/Python parity for compare()
- Multi-collection attribute search
- Basic level1/level2 smoke test
"""

import json
import pytest
from pathlib import Path

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
