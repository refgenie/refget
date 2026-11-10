"""Tests for compare_seqcols / _compare_elements (match gtars' Rust compare_elements)."""

import glob
import json
import os
import time

import pytest

from refget.models import SequenceCollection
from refget.utils import _compare_elements, compare_seqcols
from tests.conftest import API_TEST_DIR

# Spec fixtures named compare_<a>.fa_<b>.fa.json, one per pair of demo FASTA files
FIXTURE_FILES = sorted(glob.glob(f"{API_TEST_DIR}/comparison/compare_*.fa_*.fa.json"))


def _fixture_pair(path):
    name = os.path.basename(path)[len("compare_") : -len(".json")]
    fasta_a, fasta_b = name.split(".fa_")
    return f"{fasta_a}.fa", fasta_b


@pytest.mark.parametrize("answer_file", FIXTURE_FILES, ids=os.path.basename)
def test_spec_fixtures(answer_file, fa_root):
    fasta_a, fasta_b = _fixture_pair(answer_file)
    a = SequenceCollection.from_fasta_file(os.path.join(fa_root, fasta_a)).level2()
    b = SequenceCollection.from_fasta_file(os.path.join(fa_root, fasta_b)).level2()
    with open(answer_file) as fp:
        expected = json.load(fp)
    expected.pop("digests", None)
    assert compare_seqcols(a, b) == expected


def test_fixtures_found():
    assert len(FIXTURE_FILES) >= 15


@pytest.mark.parametrize(
    "a, b, count, order",
    [
        ([], [], 0, None),
        (["a"], ["a"], 1, None),  # one shared element: order undefined
        (["a", "b", "c"], ["c", "x"], 1, None),
        (["a", "b"], ["a", "b"], 2, True),
        (["a", "b"], ["b", "a"], 2, False),
        (["a", "b", "c"], ["a", "x", "c"], 2, True),
        (["a", "b"], ["x", "y"], 0, None),
    ],
)
def test_basic(a, b, count, order):
    assert _compare_elements(a, b) == {"a_and_b": count, "a_and_b_same_order": order}


@pytest.mark.parametrize(
    "a, b, count, order",
    [
        # Unbalanced duplicates: filtered lengths differ, so order is undefined
        (["a", "a"], ["a"], 1, None),
        (["a", "a", "b"], ["a", "b"], 2, None),
        # Balanced duplicates: filtered arrays compared directly
        (["a", "a", "b"], ["a", "b", "b"], 3, False),
        (["a", "b", "a"], ["a", "b", "a"], 3, True),
        ([1, 1, 2], [1, 2, 2], 3, False),
    ],
)
def test_duplicates(a, b, count, order):
    assert _compare_elements(a, b) == {"a_and_b": count, "a_and_b_same_order": order}


def test_unhashable_elements():
    x = {"name": "chr1", "length": 10}
    y = {"name": "chr2", "length": 20}
    # Key order inside the dicts must not matter
    y_reordered = {"length": 20, "name": "chr2"}
    assert _compare_elements([x, y], [x, y_reordered]) == {
        "a_and_b": 2,
        "a_and_b_same_order": True,
    }
    assert _compare_elements([x, y], [y_reordered, x]) == {
        "a_and_b": 2,
        "a_and_b_same_order": False,
    }
    assert _compare_elements([x], [x]) == {"a_and_b": 1, "a_and_b_same_order": None}
    # A dict never matches its own JSON string
    assert _compare_elements([x, "a"], [json.dumps(x, sort_keys=True), "a"])["a_and_b"] == 1


def test_element_types_match_rust_canonical_json():
    # Bools are not numbers: true and 1 differ, false and 0 differ
    assert _compare_elements([True, False], [1, 0])["a_and_b"] == 0
    assert _compare_elements([True, 1], [1, True]) == {"a_and_b": 2, "a_and_b_same_order": False}
    # Ints and integral floats are the same number
    assert _compare_elements([1, 2, 3], [1.0, 2.0, 3.0]) == {
        "a_and_b": 3,
        "a_and_b_same_order": True,
    }
    assert _compare_elements([1.5], [1])["a_and_b"] == 0
    # A number never matches its string, and None matches only None
    assert _compare_elements([1, "1", None], ["1", None, 2])["a_and_b"] == 2
    # Dicts follow the same rules inside
    assert (
        _compare_elements([{"name": "a", "length": 10}], [{"length": 10.0, "name": "a"}])["a_and_b"]
        == 1
    )
    assert (
        _compare_elements([{"name": "a", "flag": True}], [{"name": "a", "flag": 1}])["a_and_b"] == 0
    )


def test_compare_seqcols_name_length_pairs():
    a = {
        "names": ["chr1", "chr2"],
        "lengths": [10, 20],
        "name_length_pairs": [{"name": "chr1", "length": 10}, {"name": "chr2", "length": 20}],
    }
    b = {
        "names": ["chr2", "chr1"],
        "lengths": [20, 10],
        "name_length_pairs": [{"length": 20, "name": "chr2"}, {"length": 10, "name": "chr1"}],
    }
    res = compare_seqcols(a, b)["array_elements"]
    assert res["a_and_b_count"] == {"lengths": 2, "name_length_pairs": 2, "names": 2}
    assert res["a_and_b_same_order"] == {
        "lengths": False,
        "name_length_pairs": False,
        "names": False,
    }


def test_performance_100k():
    n = 100_000
    a = [f"SQ.{i:032d}" for i in range(n)]
    b = list(reversed(a))
    pairs_a = [{"name": f"chr{i}", "length": i} for i in range(n)]
    pairs_b = list(reversed(pairs_a))
    start = time.perf_counter()
    assert _compare_elements(a, b) == {"a_and_b": n, "a_and_b_same_order": False}
    assert _compare_elements(pairs_a, pairs_b) == {"a_and_b": n, "a_and_b_same_order": False}
    # The old quadratic version took minutes here; the linear one takes well under a second
    assert time.perf_counter() - start < 5
