"""Test suite shared objects and setup"""

import json
import os
import pytest
import requests
import sys

import oyaml as yaml

from refget.const import _schema_path

REQ_SERVICE_MARK = "require_service"
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


def ly(n, data_path):
    """Load YAML"""
    with open(os.path.join(data_path, n), "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def schema_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")


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


@pytest.fixture
def schema_sequence(schema_path):
    return ly("sequence.yaml", schema_path)


@pytest.fixture
def schema_asd(schema_path):
    return ly("annotated_sequence_digest.yaml", schema_path)


@pytest.fixture
def schema_acd(schema_path):
    return ly("annotated_collection_digest.yaml", schema_path)


# Here add require_service marker, for testing clients


def pytest_addoption(parser):
    """
    Add an option to specify the API root
    """
    parser.addoption("--api_root", "-R", action="store", default="http://0.0.0.0:8100")
    parser.addoption("--no-snlp", action="store_true", default=False)


@pytest.fixture()
def api_root(pytestconfig):
    """
    Get the API root from the command line argument, --api_root
    """
    return pytestconfig.getoption("api_root")


def check_server_is_running(api_root):
    """
    Check if a server is responding at the given API root
    """
    try:
        print(f"Checking if service is running at {api_root}")
        res = requests.get(f"{api_root}/")
        assert res.status_code == 200, "Service is not running"
        print("Server is running.")
        return True
    except Exception as e:
        print("Server is not running.")
        print("Error: ", sys.exc_info()[0])
        return False


def pytest_configure(config):
    """
    Register custom markers for tests that depend on CLI arguments
    You can add these markers  `@pytest.mark.<marker>`
    """
    config.addinivalue_line(
        "markers", f"{REQ_SERVICE_MARK}: mark test as requiring the service to run"
    )
    config.addinivalue_line("markers", "snlp: mark test as requiring the SNLP service to run")


# Pytest evaluates `skipif` before CLI arguments, so to skip tests based on CLI args,
# we must modify them after collection but before execution.
# This hook adds a `skip` mark to tests that should be skipped based on CLI args.
def pytest_collection_modifyitems(config, items):
    """
    Skip tests with marks, based on values from the command line.
    """

    # Skip `@pytest.mark.require_service` if the server is not running
    api_root = config.getoption("api_root")
    skip_missing_service = pytest.mark.skip(reason="need API to run")
    if not check_server_is_running(api_root):
        print("Skipping tests that require a server to be running...")
        for item in items:
            if REQ_SERVICE_MARK in item.keywords:
                item.add_marker(skip_missing_service)

    # Skip SNLP tests if --no-snlp is set
    no_snlp = config.getoption("no_snlp")
    skip_snlp = pytest.mark.skip(reason="Skipped due to --no-snlp option")
    if no_snlp:
        for item in items:
            if "snlp" in item.keywords:
                item.add_marker(skip_snlp)
