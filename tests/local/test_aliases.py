"""Tests for RefgetStore alias functionality."""

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
    """Return the sha512t24u digest of the first sequence in the store."""
    return store.list_sequences()[0].sha512t24u


@pytest.fixture
def col_digest(store):
    """Return the digest of the first collection in the store."""
    return store.list_collections()[0].digest


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestSequenceAliases:
    def test_add_and_retrieve(self, store, seq_digest):
        store.add_sequence_alias("chromosomes", "chr1", seq_digest)
        result = store.get_sequence_by_alias("chromosomes", "chr1")
        assert result is not None
        assert result.metadata.sha512t24u == seq_digest

    def test_list_namespaces(self, store, seq_digest):
        store.add_sequence_alias("ucsc", "chrX", seq_digest)
        namespaces = store.list_sequence_alias_namespaces()
        assert "ucsc" in namespaces

    def test_list_aliases_in_namespace(self, store, seq_digest):
        store.add_sequence_alias("ucsc", "chr1", seq_digest)
        store.add_sequence_alias("ucsc", "chr2", seq_digest)
        aliases = store.list_sequence_aliases("ucsc")
        assert "chr1" in aliases
        assert "chr2" in aliases

    def test_reverse_lookup(self, store, seq_digest):
        store.add_sequence_alias("ucsc", "chr1", seq_digest)
        result = store.get_aliases_for_sequence(seq_digest)
        assert ("ucsc", "chr1") in result

    def test_remove_alias(self, store, seq_digest):
        store.add_sequence_alias("ucsc", "chr1", seq_digest)
        removed = store.remove_sequence_alias("ucsc", "chr1")
        assert removed is True
        result = store.get_sequence_by_alias("ucsc", "chr1")
        assert result is None

    def test_remove_nonexistent_returns_false(self, store):
        removed = store.remove_sequence_alias("fake", "fake")
        assert removed is False

    def test_get_nonexistent_returns_none(self, store):
        result = store.get_sequence_by_alias("fake_ns", "fake_alias")
        assert result is None

    def test_multiple_namespaces_same_digest(self, store, seq_digest):
        store.add_sequence_alias("ucsc", "chr1", seq_digest)
        store.add_sequence_alias("ensembl", "1", seq_digest)
        aliases = store.get_aliases_for_sequence(seq_digest)
        namespaces = {ns for ns, _ in aliases}
        assert "ucsc" in namespaces
        assert "ensembl" in namespaces

    def test_load_from_tsv(self, store, seq_digest):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(f"chr1\t{seq_digest}\n")
            f.write(f"chr2\t{seq_digest}\n")
            tsv_path = f.name
        try:
            count = store.load_sequence_aliases("from_file", tsv_path)
            assert count == 2
            result = store.get_sequence_by_alias("from_file", "chr1")
            assert result is not None
        finally:
            os.unlink(tsv_path)


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestCollectionAliases:
    def test_add_and_retrieve(self, store, col_digest):
        store.add_collection_alias("genomes", "hg38", col_digest)
        result = store.get_collection_by_alias("genomes", "hg38")
        assert result is not None
        assert result.digest == col_digest

    def test_list_namespaces(self, store, col_digest):
        store.add_collection_alias("genomes", "hg38", col_digest)
        namespaces = store.list_collection_alias_namespaces()
        assert "genomes" in namespaces

    def test_list_aliases_in_namespace(self, store, col_digest):
        store.add_collection_alias("genomes", "hg38", col_digest)
        store.add_collection_alias("genomes", "GRCh38", col_digest)
        aliases = store.list_collection_aliases("genomes")
        assert "hg38" in aliases
        assert "GRCh38" in aliases

    def test_reverse_lookup(self, store, col_digest):
        store.add_collection_alias("genomes", "hg38", col_digest)
        result = store.get_aliases_for_collection(col_digest)
        assert ("genomes", "hg38") in result

    def test_remove_alias(self, store, col_digest):
        store.add_collection_alias("genomes", "hg38", col_digest)
        removed = store.remove_collection_alias("genomes", "hg38")
        assert removed is True
        result = store.get_collection_by_alias("genomes", "hg38")
        assert result is None

    def test_remove_nonexistent_returns_false(self, store):
        removed = store.remove_collection_alias("fake", "fake")
        assert removed is False

    def test_get_nonexistent_returns_none(self, store):
        result = store.get_collection_by_alias("fake_ns", "fake_alias")
        assert result is None

    def test_multiple_namespaces_same_digest(self, store, col_digest):
        store.add_collection_alias("ucsc", "hg38", col_digest)
        store.add_collection_alias("ncbi", "GRCh38", col_digest)
        aliases = store.get_aliases_for_collection(col_digest)
        namespaces = {ns for ns, _ in aliases}
        assert "ucsc" in namespaces
        assert "ncbi" in namespaces

    def test_load_from_tsv(self, store, col_digest):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(f"hg38\t{col_digest}\n")
            f.write(f"GRCh38\t{col_digest}\n")
            tsv_path = f.name
        try:
            count = store.load_collection_aliases("from_file", tsv_path)
            assert count == 2
            result = store.get_collection_by_alias("from_file", "hg38")
            assert result is not None
        finally:
            os.unlink(tsv_path)
