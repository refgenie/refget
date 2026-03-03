"""Smoke test for RefgetStore.remove_collection() Python binding."""

import os
import tempfile

import pytest

from refget.store import RefgetStore

try:
    from gtars.refget import RefgetStore as _check

    _RUST_BINDINGS_AVAILABLE = True
except ImportError:
    _RUST_BINDINGS_AVAILABLE = False

FASTA_PATH = "test_fasta/base.fa"


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_remove_collection_round_trip():
    """Add a collection, remove it with orphan cleanup, verify store is empty."""
    store = RefgetStore.in_memory()
    store.set_quiet(True)
    store.add_sequence_collection_from_fasta(FASTA_PATH)

    assert len(store.list_collections()) == 1
    assert len(store.list_sequences()) > 0

    digest = store.list_collections()[0].digest

    # Nonexistent returns False
    assert store.remove_collection("nonexistent") is False

    # Real removal with orphan cleanup
    assert store.remove_collection(digest, remove_orphan_sequences=True) is True
    assert len(store.list_collections()) == 0
    assert len(store.list_sequences()) == 0
