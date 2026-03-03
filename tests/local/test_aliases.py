"""Smoke tests for RefgetStore alias functionality via Python bindings."""

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


@pytest.fixture
def store():
    """Create an in-memory RefgetStore with base.fa loaded."""
    s = RefgetStore.in_memory()
    s.disable_encoding()
    s.add_sequence_collection_from_fasta(FASTA_PATH)
    return s


@pytest.fixture
def seq_digest(store):
    return store.list_sequences()[0].sha512t24u


@pytest.fixture
def col_digest(store):
    return store.list_collections()[0].digest


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_sequence_alias_round_trip(store, seq_digest):
    """Add, retrieve, and remove a sequence alias; verify None for missing aliases."""
    # Not found returns None
    assert store.get_sequence_by_alias("ucsc", "chr1") is None

    # Add and retrieve
    store.add_sequence_alias("ucsc", "chr1", seq_digest)
    result = store.get_sequence_by_alias("ucsc", "chr1")
    assert result is not None
    assert result.metadata.sha512t24u == seq_digest

    # Remove
    assert store.remove_sequence_alias("ucsc", "chr1") is True
    assert store.get_sequence_by_alias("ucsc", "chr1") is None
    assert store.remove_sequence_alias("ucsc", "chr1") is False


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_collection_alias_round_trip(store, col_digest):
    """Add, retrieve, and remove a collection alias; verify None for missing aliases."""
    assert store.get_collection_by_alias("genomes", "hg38") is None

    store.add_collection_alias("genomes", "hg38", col_digest)
    result = store.get_collection_by_alias("genomes", "hg38")
    assert result is not None
    assert result.digest == col_digest

    assert store.remove_collection_alias("genomes", "hg38") is True
    assert store.get_collection_by_alias("genomes", "hg38") is None
    assert store.remove_collection_alias("genomes", "hg38") is False


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_load_sequence_aliases_from_tsv(store, seq_digest):
    """Load aliases from TSV; verify count return and post-load lookup."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write(f"chr1\t{seq_digest}\n")
        f.write(f"chr2\t{seq_digest}\n")
        tsv_path = f.name
    try:
        count = store.load_sequence_aliases("from_file", tsv_path)
        assert count == 2
        assert store.get_sequence_by_alias("from_file", "chr1") is not None
    finally:
        os.unlink(tsv_path)


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
def test_load_collection_aliases_from_tsv(store, col_digest):
    """Load aliases from TSV; verify count return and post-load lookup."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write(f"hg38\t{col_digest}\n")
        f.write(f"GRCh38\t{col_digest}\n")
        tsv_path = f.name
    try:
        count = store.load_collection_aliases("from_file", tsv_path)
        assert count == 2
        assert store.get_collection_by_alias("from_file", "hg38") is not None
    finally:
        os.unlink(tsv_path)
