"""Shared test constants and helpers importable from any test subpackage."""

import json
from pathlib import Path

import pytest

TEST_DATA_DIR = Path(__file__).parent.parent / "test_fasta"
BASE_FASTA = TEST_DATA_DIR / "base.fa"
DIFFERENT_NAMES_FASTA = TEST_DATA_DIR / "different_names.fa"
DIFFERENT_ORDER_FASTA = TEST_DATA_DIR / "different_order.fa"
PAIR_SWAP_FASTA = TEST_DATA_DIR / "pair_swap.fa"
SUBSET_FASTA = TEST_DATA_DIR / "subset.fa"
SWAP_WO_COORDS_FASTA = TEST_DATA_DIR / "swap_wo_coords.fa"
SAMPLE_FHR_JSON = TEST_DATA_DIR / "sample_fhr.json"

TEST_FASTA_METADATA_FILE = TEST_DATA_DIR / "test_fasta_digests.json"
with open(TEST_FASTA_METADATA_FILE) as fp:
    TEST_FASTA_DIGESTS = json.load(fp)


def assert_valid_digest(digest: str):
    """Assert string is valid seqcol digest format."""
    assert len(digest) >= 32, f"Invalid digest format: {digest}"


def assert_json_output(result, required_keys: list = None):
    """Assert CLI output is valid JSON with optional required keys."""
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Output is not valid JSON: {result.stdout}")

    if required_keys:
        for key in required_keys:
            assert key in data, f"Missing key '{key}' in output: {data}"

    return data
