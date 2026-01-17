"""Test suite shared objects and setup"""

import json
import os
import pytest

API_TEST_DIR = "tests/api"

DEMO_FILES = [
    "base.fa",
    "different_names.fa",
    "different_order.fa",
    "pair_swap.fa",
    "subset.fa",
    "swap_wo_coords.fa",
]

# JSON with correct answers for digest tests
TEST_FASTA_METADATA_FILE = "test_fasta/test_fasta_digests.json"

# load json with right answers
with open(TEST_FASTA_METADATA_FILE) as fp:
    TEST_FASTA_DIGESTS = json.load(fp)

# make tuples of each correct answer to parameterize tests
DIGEST_TESTS = []
for fa_name, fa_digest_bundle in TEST_FASTA_DIGESTS.items():
    DIGEST_TESTS.append((fa_name, fa_digest_bundle))


@pytest.fixture
def fa_root():
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir),
        "test_fasta",
    )


@pytest.fixture
def fasta_path():
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir), "test_fasta"
    )


def pytest_addoption(parser):
    """Add options for test configuration"""
    parser.addoption("--no-snlp", action="store_true", default=False)


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "snlp: mark test as requiring the SNLP service to run")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on command line options"""
    # Skip SNLP tests if --no-snlp is set
    no_snlp = config.getoption("no_snlp")
    skip_snlp = pytest.mark.skip(reason="Skipped due to --no-snlp option")
    if no_snlp:
        for item in items:
            if "snlp" in item.keywords:
                item.add_marker(skip_snlp)
