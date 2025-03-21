import json
import os
import pytest
import refget

from .conftest import DEMO_FILES

# Pairs of files to compare, with the "correct" compare response
COMPARE_TESTS = [
    (DEMO_FILES[0], DEMO_FILES[1], "test_api/comparison/compare_base.fa_different_names.fa.json"),
    (DEMO_FILES[0], DEMO_FILES[2], "test_api/comparison/compare_base.fa_different_order.fa.json"),
    (DEMO_FILES[0], DEMO_FILES[3], "test_api/comparison/compare_base.fa_pair_swap.fa.json"),
    (DEMO_FILES[0], DEMO_FILES[4], "test_api/comparison/compare_base.fa_subset.fa.json"),
    (DEMO_FILES[0], DEMO_FILES[5], "test_api/comparison/compare_base.fa_swap_wo_coords.fa.json"),
]

# load json with right answers
with open("test_fasta/test_fasta_digests.json") as fp:
    correct_answers = json.load(fp)

# make tuples of each correct answer to parameterize tests
DIGEST_TESTS = []
for fa_name, fa_digest_bundle in correct_answers.items():
    DIGEST_TESTS.append((fa_name, fa_digest_bundle))


def check_comparison(fasta1, fasta2, expected_comparison):
    """
    Check that the comparison of two sequence collections is as expected.
    """
    print(f"Comparison: Fasta1: {fasta1} vs Fasta2: {fasta2}. Expected: {expected_comparison}")
    d = refget.SequenceCollection.from_fasta_file(fasta1)
    d2 = refget.SequenceCollection.from_fasta_file(fasta2)
    with open(expected_comparison) as fp:
        correct_compare_response = json.load(fp)
        # Remove the 'digests' from the comparison dict, which is used in the API but
        # not provided by the function itself.
        correct_compare_response.pop("digests", None)
        proposed_compare_response = refget.compare_seqcols(d.level2(), d2.level2())
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
        sc = refget.SequenceCollection.from_dict(dict)
        print(sc)
        assert sc.digest == "XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk"

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_from_fasta_file(self, fa_file, fa_digest_bundle, fa_root):
        """Ensures the top-level digest of a SequenceCollection matches."""
        d = refget.SequenceCollection.from_fasta_file(os.path.join(fa_root, fa_file))
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

    @pytest.mark.parametrize(["seqcol_obj"], [[seqcol_obj]])
    def test_validate(self, seqcol_obj):
        is_valid = refget.validate_seqcol(seqcol_obj)
        assert is_valid

    @pytest.mark.parametrize(["seqcol_obj"], [[bad_seqcol]])
    def test_failure(self, seqcol_obj):
        with pytest.raises(Exception):
            refget.validate_seqcol(seqcol_obj)
