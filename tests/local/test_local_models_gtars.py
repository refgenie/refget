import pytest
import logging

_LOGGER = logging.getLogger(__name__)
from pathlib import Path

from refget.models import SequenceCollection as pythonSequenceCollection

from refget.refget_store import GlobalRefgetStore, StorageMode

try:
    from gtars.refget import (
        SequenceCollection as gtarsSequenceCollection,
        digest_fasta,
    )

    _RUST_BINDINGS_AVAILABLE = True

except ImportError as e:
    _LOGGER.warning(
        f"Could not import gtars python bindings. `from_PySequenceCollection` will not be available."
    )
    _RUST_BINDINGS_AVAILABLE = False


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestRustPySequenceCollection:
    def test_pysequencecollection(self):

        p = Path("test_fasta/base.fa")

        gtars_digested_seq_col = digest_fasta(p)
        python_seq_col = pythonSequenceCollection.from_fasta_file(p)

        bridged_seq_col = pythonSequenceCollection.from_PySequenceCollection(
            gtars_seq_col=gtars_digested_seq_col
        )
        assert (
            bridged_seq_col.digest == python_seq_col.digest == gtars_digested_seq_col.digest
        ), "Top-level digest mismatch!"

        assert bridged_seq_col.sequences.digest == python_seq_col.sequences.digest
        assert bridged_seq_col.sequences.value == python_seq_col.sequences.value
        assert bridged_seq_col.sequences == python_seq_col.sequences
        assert bridged_seq_col.lengths == python_seq_col.lengths
        assert bridged_seq_col.names == python_seq_col.names
        assert bridged_seq_col.sorted_sequences == python_seq_col.sorted_sequences
        assert bridged_seq_col.sorted_sequences_digest == python_seq_col.sorted_sequences_digest
        assert bridged_seq_col.name_length_pairs == python_seq_col.name_length_pairs
        assert (
            bridged_seq_col.sorted_name_length_pairs_digest
            == python_seq_col.sorted_name_length_pairs_digest
        )


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestRustRefgetStore:
    def test_store(self):
        # just make sure this is callable if gtars is installed.
        s = GlobalRefgetStore(mode=StorageMode.Raw)
        s.import_fasta("test_fasta/base.fa")
