"""
Integration test fixtures for refget client testing.

Uses FastAPI TestClient with ephemeral Docker PostgreSQL.
Prerequisites:
1. Start test database: ./tests/integration/scripts/test-db.sh start
2. Run tests: RUN_INTEGRATION_TESTS=true pytest tests/integration/
"""
import os
import pytest
from pathlib import Path

# Set environment variables BEFORE any app imports
# Must match test-db.sh settings
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["POSTGRES_USER"] = "testuser"
os.environ["POSTGRES_PASSWORD"] = "testpass"
os.environ["POSTGRES_DB"] = "refget_test"

from fastapi.testclient import TestClient

# Skip all integration tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to run.",
)

# Test database configuration - must match test-db.sh
TEST_DB_URL = "postgresql://testuser:testpass@localhost:5433/refget_test"

# Known digests from test_fasta/test_fasta_digests.json
KNOWN_DIGESTS = {
    "base.fa": "XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk",
    "different_names.fa": "QvT5tAQ0B8Vkxd-qFftlzEk2QyfPtgOv",
    "different_order.fa": "Tpdsg75D4GKCGEHtIiDSL9Zx-DSuX5V8",
}


@pytest.fixture(scope="session")
def test_fasta_path():
    """Path to test FASTA files"""
    return Path(__file__).parent.parent.parent / "test_fasta"


@pytest.fixture(scope="session")
def test_dbagent():
    """Create RefgetDBAgent connected to test PostgreSQL"""
    from refget.agents import RefgetDBAgent

    dbagent = RefgetDBAgent(postgres_str=TEST_DB_URL)
    yield dbagent
    if hasattr(dbagent, "engine"):
        dbagent.engine.dispose()


@pytest.fixture(scope="session")
def loaded_dbagent(test_dbagent, test_fasta_path):
    """DBAgent pre-loaded with test FASTA files"""
    # Load test FASTA files
    for fa_file in ["base.fa", "different_names.fa", "different_order.fa"]:
        fa_path = test_fasta_path / fa_file
        test_dbagent.seqcol.add_from_fasta_file(str(fa_path))
    return test_dbagent


@pytest.fixture(scope="session")
def client(loaded_dbagent):
    """Create TestClient with test database"""
    from seqcolapi.main import app
    from refget.refget_router import get_dbagent

    def override_get_dbagent():
        return loaded_dbagent

    app.dependency_overrides[get_dbagent] = override_get_dbagent
    app.state.dbagent = loaded_dbagent

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def base_digest():
    """Digest for base.fa"""
    return KNOWN_DIGESTS["base.fa"]


@pytest.fixture(scope="session")
def different_names_digest():
    """Digest for different_names.fa"""
    return KNOWN_DIGESTS["different_names.fa"]


@pytest.fixture(scope="session")
def different_order_digest():
    """Digest for different_order.fa"""
    return KNOWN_DIGESTS["different_order.fa"]
