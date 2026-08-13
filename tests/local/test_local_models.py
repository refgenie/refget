import json
import os
from pathlib import Path

import pytest

from refget import InvalidSeqColError
from refget.models import SequenceCollection
from refget.utils import compare_seqcols, validate_seqcol
from tests.conftest import API_TEST_DIR, DEMO_FILES, DIGEST_TESTS

try:
    from gtars.refget import (  # noqa: F401
        SequenceCollection as gtarsSequenceCollection,
    )
    from gtars.refget import (
        digest_fasta,
    )

    _RUST_BINDINGS_AVAILABLE = True

except ImportError:
    _RUST_BINDINGS_AVAILABLE = False

# Pairs of files to compare, with the "correct" compare response
COMPARE_TESTS = [
    (
        DEMO_FILES[0],
        DEMO_FILES[1],
        f"{API_TEST_DIR}/comparison/compare_base.fa_different_names.fa.json",
    ),
    (
        DEMO_FILES[0],
        DEMO_FILES[2],
        f"{API_TEST_DIR}/comparison/compare_base.fa_different_order.fa.json",
    ),
    (DEMO_FILES[0], DEMO_FILES[3], f"{API_TEST_DIR}/comparison/compare_base.fa_pair_swap.fa.json"),
    (DEMO_FILES[0], DEMO_FILES[4], f"{API_TEST_DIR}/comparison/compare_base.fa_subset.fa.json"),
    (
        DEMO_FILES[0],
        DEMO_FILES[5],
        f"{API_TEST_DIR}/comparison/compare_base.fa_swap_wo_coords.fa.json",
    ),
]


def check_comparison(fasta1, fasta2, expected_comparison):
    """
    Check that the comparison of two sequence collections is as expected.
    """
    print(f"Comparison: Fasta1: {fasta1} vs Fasta2: {fasta2}. Expected: {expected_comparison}")
    d = SequenceCollection.from_fasta_file(fasta1)
    d2 = SequenceCollection.from_fasta_file(fasta2)
    with open(expected_comparison) as fp:
        correct_compare_response = json.load(fp)
        # Remove the 'digests' from the comparison dict, which is used in the API but
        # not provided by the function itself.
        correct_compare_response.pop("digests", None)
        proposed_compare_response = compare_seqcols(d.level2(), d2.level2())
        assert proposed_compare_response == correct_compare_response


class TestSequenceCollectionModel:
    def test_from_dict(self):
        # This is the dict for the `base.fa` demo file
        dict = {
            "lengths": [8, 4, 4],
            "names": ["chrX", "chr1", "chr2"],
            "sequences": [
                "SQ.iYtREV555dUFKg2_agSJW6suquUyPpMw",
                "SQ.YBbVX0dLKG1ieEDCiMmkrTZFt_Z5Vdaj",
                "SQ.AcLxtBuKEPk_7PGE_H4dGElwZHCujwH6",
            ],
            "sorted_sequences": [
                "SQ.AcLxtBuKEPk_7PGE_H4dGElwZHCujwH6",
                "SQ.YBbVX0dLKG1ieEDCiMmkrTZFt_Z5Vdaj",
                "SQ.iYtREV555dUFKg2_agSJW6suquUyPpMw",
            ],
            "name_length_pairs": [
                {"length": 8, "name": "chrX"},
                {"length": 4, "name": "chr1"},
                {"length": 4, "name": "chr2"},
            ],
        }
        sc = SequenceCollection.from_dict(dict)
        print(sc)
        assert sc.digest == "XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk"

    def test_sequence_collection_with_human_name(self):
        seqcol_dict = {
            "names": ["seq1"],
            "sequences": ["ABC"],
            "lengths": [3],
            "human_readable_names": "Test Collection",
        }
        sc = SequenceCollection.from_dict(seqcol_dict)
        assert sc.human_readable_names[0].human_readable_name == "Test Collection"

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_from_fasta_file(self, fa_file, fa_digest_bundle, fa_root):
        """Ensures the top-level digest of a SequenceCollection matches."""
        d = SequenceCollection.from_fasta_file(os.path.join(fa_root, fa_file))
        assert d.digest == fa_digest_bundle["top_level_digest"]
        assert (
            d.sorted_name_length_pairs_digest
            == fa_digest_bundle["sorted_name_length_pairs_digest"]
        )

        # Check level1 digests match expected answer
        level1 = d.level1()
        assert level1["lengths"] == fa_digest_bundle["level1"]["lengths"]
        assert level1["names"] == fa_digest_bundle["level1"]["names"]
        assert level1["sequences"] == fa_digest_bundle["level1"]["sequences"]
        assert level1["sorted_sequences"] == fa_digest_bundle["level1"]["sorted_sequences"]
        assert level1["name_length_pairs"] == fa_digest_bundle["level1"]["name_length_pairs"]


class TestCompare:
    """
    Test the compare function, using demo fasta files, and pre-computed
    compare function results stored as answer files.
    """

    @pytest.mark.parametrize(["fasta1", "fasta2", "answer_file"], COMPARE_TESTS)
    def test_fasta_compare(self, fasta1, fasta2, answer_file, fa_root):
        check_comparison(os.path.join(fa_root, fasta1), os.path.join(fa_root, fasta2), answer_file)


seqcol_obj = {
    "lengths": [248956422, 133797422, 135086622],
    "names": ["chr1", "chr2", "chr3"],
    "sequences": [
        "2648ae1bacce4ec4b6cf337dcae37816",
        "907112d17fcb73bcab1ed1c72b97ce68",
        "1511375dc2dd1b633af8cf439ae90cec",
    ],
}

bad_seqcol = {"bogus": True}


class TestValidate:
    """
    Test validation
    """

    def test_validate(self):
        is_valid = validate_seqcol(seqcol_obj)
        assert is_valid

    def test_failure(self):
        with pytest.raises(Exception):
            validate_seqcol(bad_seqcol)


class TestCollatedAttributeValidation:
    """
    Test validation of collated attributes
    """

    def test_valid_collated_attributes(self):
        """Test that valid collated attributes pass validation"""
        valid_dict = {
            "names": ["chr1", "chr2", "chr3"],
            "sequences": ["SQ.abc123", "SQ.def456", "SQ.ghi789"],
            "lengths": [100, 200, 300],
        }
        # Should not raise an error
        sc = SequenceCollection.from_dict(valid_dict)
        assert sc is not None

    def test_mismatched_collated_attributes(self):
        """Test that mismatched collated attribute lengths raise an error"""
        invalid_dict = {
            "names": ["chr1", "chr2", "chr3"],
            "sequences": ["SQ.abc123", "SQ.def456"],  # Only 2 sequences
            "lengths": [100, 200, 300],
        }
        # Should raise InvalidSeqColError
        with pytest.raises(InvalidSeqColError) as exc_info:
            SequenceCollection.from_dict(invalid_dict)

        # Check error message contains helpful info
        assert "Collated attributes must have the same length" in str(exc_info.value)
        assert "names=3" in str(exc_info.value)
        assert "sequences=2" in str(exc_info.value)

    def test_single_collated_attribute_valid(self):
        """Test that a single collated attribute doesn't cause issues"""
        valid_dict = {
            "names": ["chr1", "chr2"],
            "sequences": ["SQ.abc123", "SQ.def456"],
            "lengths": [100, 200],
        }
        # Should not raise an error
        sc = SequenceCollection.from_dict(valid_dict)
        assert sc is not None


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestRustPySequenceCollection:
    def test_pysequencecollection(self):
        p = Path("test_fasta/base.fa")

        gtars_digested_seq_col = digest_fasta(p)
        python_seq_col = SequenceCollection.from_fasta_file(p)

        bridged_seq_col = SequenceCollection.from_PySequenceCollection(
            gtars_seq_col=gtars_digested_seq_col
        )
        assert bridged_seq_col.digest == python_seq_col.digest == gtars_digested_seq_col.digest, (
            "Top-level digest mismatch!"
        )

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
