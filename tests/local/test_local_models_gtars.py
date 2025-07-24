import pytest
import logging

_LOGGER = logging.getLogger(__name__)
from pathlib import Path
from refget import fasta_to_seqcol_dict
from refget.models import SequenceCollection as pythonSequenceCollection

try:
    from gtars.refget import (  # Adjust this import path to where your PyO3 module is
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
        # assert bridged_seq_col.sequences.value == python_seq_col.sequences.value
        # assert bridged_seq_col.sequences == python_seq_col.sequences
        assert bridged_seq_col.lengths == python_seq_col.lengths
