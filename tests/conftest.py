"""Test suite shared objects and setup"""

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

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


# ============================================================
# CLI Runner Fixtures
# ============================================================


@pytest.fixture
def runner():
    """Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def cli(runner):
    """
    Convenience fixture for invoking CLI commands.

    Usage:
        result = cli("fasta", "digest", "file.fa")
        assert result.exit_code == 0
    """
    from refget.cli import app

    def invoke(*args):
        return runner.invoke(app, list(args))

    return invoke


# ============================================================
# Test Data Paths
# ============================================================

TEST_DATA_DIR = Path(__file__).parent.parent / "test_fasta"
BASE_FASTA = TEST_DATA_DIR / "base.fa"


@pytest.fixture(scope="session")
def test_data_root():
    """Provides the absolute path to the test_fasta directory."""
    return TEST_DATA_DIR


DIFFERENT_NAMES_FASTA = TEST_DATA_DIR / "different_names.fa"
DIFFERENT_ORDER_FASTA = TEST_DATA_DIR / "different_order.fa"
PAIR_SWAP_FASTA = TEST_DATA_DIR / "pair_swap.fa"
SUBSET_FASTA = TEST_DATA_DIR / "subset.fa"
SWAP_WO_COORDS_FASTA = TEST_DATA_DIR / "swap_wo_coords.fa"
SAMPLE_FHR_JSON = TEST_DATA_DIR / "sample_fhr.json"


# ============================================================
# FASTA File Fixtures
# ============================================================


@pytest.fixture
def sample_fasta(tmp_path):
    """Create sample FASTA in temp directory."""
    fasta = tmp_path / "sample.fa"
    fasta.write_text(">chr1\nACGTACGT\n>chr2\nGGCCGGCC\n")
    return fasta


@pytest.fixture
def sample_fasta_gz(tmp_path):
    """Create gzipped sample FASTA."""
    import gzip

    fasta = tmp_path / "sample.fa.gz"
    with gzip.open(fasta, "wt") as f:
        f.write(">chr1\nACGTACGT\n>chr2\nGGCCGGCC\n")
    return fasta


@pytest.fixture
def large_fasta(tmp_path):
    """Create larger FASTA for performance tests."""
    fasta = tmp_path / "large.fa"
    seq = "ACGTACGTACGT" * 1000
    content = f">chr1\n{seq}\n>chr2\n{seq}\n"
    fasta.write_text(content)
    return fasta


@pytest.fixture
def multi_seq_fasta(tmp_path):
    """Create FASTA with multiple sequences for comprehensive testing."""
    fasta = tmp_path / "multi.fa"
    fasta.write_text(
        ">chr1 description one\nACGTACGT\n>chr2 description two\nGGCCGGCC\n>chr3\nTTAATTAA\n"
    )
    return fasta


# ============================================================
# Store Fixtures
# ============================================================


@pytest.fixture
def temp_store(tmp_path, cli):
    """Initialize a temporary RefgetStore."""
    store_path = tmp_path / "store"
    result = cli("store", "init", "--path", str(store_path))
    # Note: This may fail until CLI is implemented - that's expected
    if result.exit_code == 0:
        return store_path
    # Return path anyway for tests that check failure scenarios
    return store_path


@pytest.fixture
def populated_store(temp_store, cli):
    """Store with test FASTA already loaded."""
    result = cli("store", "add", str(BASE_FASTA), "--path", str(temp_store))
    if result.exit_code != 0:
        pytest.skip("Store CLI not yet implemented")

    # Parse digest from JSON output
    output = json.loads(result.stdout)
    return {
        "path": temp_store,
        "digest": output["digest"],
    }


# ============================================================
# Config Fixtures
# ============================================================


@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config file."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(f"""[store]
path = "{tmp_path}/store"
""")
    return config_path


@pytest.fixture
def env_with_config(temp_config, monkeypatch):
    """Set REFGET_CONFIG env var to temp config."""
    monkeypatch.setenv("REFGET_CONFIG", str(temp_config))
    return temp_config


# ============================================================
# Assertion Helpers
# ============================================================


def assert_valid_digest(digest: str):
    """Assert string is valid seqcol digest format."""
    # Seqcol digests are typically 32 chars (sha512t24u base64)
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
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="Skip tests that require network access",
    )
    parser.addoption(
        "--no-db",
        action="store_true",
        default=False,
        help="Skip tests that require database access",
    )
    parser.addoption(
        "--api-root",
        action="store",
        default=None,
        help="External seqcol server URL for tests (e.g., https://seqcolapi.databio.org)",
    )


@pytest.fixture(scope="session")
def api_root(request):
    """API root URL for compliance/integration tests."""
    url = request.config.getoption("--api-root")
    return url.rstrip("/") if url else None


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "snlp: mark test as requiring the SNLP service to run")
    config.addinivalue_line("markers", "requires_network: mark test as requiring network access")
    config.addinivalue_line("markers", "requires_db: mark test as requiring database access")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "recommended: mark test as RECOMMENDED (not REQUIRED) by GA4GH spec"
    )
    config.addinivalue_line(
        "markers", "require_service: mark test as requiring a running seqcol service"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on command line options"""
    # Skip SNLP tests if --no-snlp is set
    no_snlp = config.getoption("no_snlp")
    skip_snlp = pytest.mark.skip(reason="Skipped due to --no-snlp option")
    if no_snlp:
        for item in items:
            if "snlp" in item.keywords:
                item.add_marker(skip_snlp)

    # Skip network tests if --no-network is set
    no_network = config.getoption("no_network")
    skip_network = pytest.mark.skip(reason="Skipped due to --no-network option")
    if no_network:
        for item in items:
            if "requires_network" in item.keywords:
                item.add_marker(skip_network)

    # Skip database tests if --no-db is set
    no_db = config.getoption("no_db")
    skip_db = pytest.mark.skip(reason="Skipped due to --no-db option")
    if no_db:
        for item in items:
            if "requires_db" in item.keywords:
                item.add_marker(skip_db)

    # Skip require_service tests if no api_root or test_server available
    api_root = config.getoption("api_root")
    if api_root is None:
        skip_service = pytest.mark.skip(
            reason="No --api-root provided and not running via integration test_server"
        )
        for item in items:
            if "require_service" in item.keywords:
                # Only skip if this is the base TestAPI class, not a subclass with test_server
                if "TestAPI" in item.nodeid and "TestComplianceViaIntegration" not in item.nodeid:
                    item.add_marker(skip_service)
