"""
Integration test fixtures for refget client testing.

Uses FastAPI TestClient with ephemeral Docker PostgreSQL.

Run with: ./scripts/test-integration.sh
"""

import os
import pytest
import socket
import threading
import time
from pathlib import Path

# Set environment variables BEFORE any app imports
# Must match test-db.sh settings
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["POSTGRES_USER"] = "testuser"
os.environ["POSTGRES_PASSWORD"] = "testpass"
os.environ["POSTGRES_DB"] = "refget_test"

from fastapi.testclient import TestClient

# Test database configuration - must match test-db.sh
TEST_DB_URL = "postgresql://testuser:testpass@localhost:5433/refget_test"

# Known digests from test_fasta/test_fasta_digests.json
KNOWN_DIGESTS = {
    "base.fa": "XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk",
    "different_names.fa": "QvT5tAQ0B8Vkxd-qFftlzEk2QyfPtgOv",
    "different_order.fa": "Tpdsg75D4GKCGEHtIiDSL9Zx-DSuX5V8",
}


def find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


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
    # Load all test FASTA files needed for compliance tests
    for fa_file in [
        "base.fa",
        "different_names.fa",
        "different_order.fa",
        "pair_swap.fa",
        "subset.fa",
        "swap_wo_coords.fa",
    ]:
        fa_path = test_fasta_path / fa_file
        test_dbagent.seqcol.add_from_fasta_file(str(fa_path))
    return test_dbagent


@pytest.fixture(scope="session")
def client(loaded_dbagent):
    """Create TestClient with test database"""
    from seqcolapi.main import app
    from refget.router import get_dbagent

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


@pytest.fixture(scope="session")
def test_server(loaded_dbagent):
    """
    Run the seqcolapi server on a free port for CLI integration tests.

    Yields the base URL (e.g., "http://localhost:12345") for the server.
    """
    import uvicorn
    from seqcolapi.main import app
    from refget.router import get_dbagent

    def override_get_dbagent():
        return loaded_dbagent

    app.dependency_overrides[get_dbagent] = override_get_dbagent
    app.state.dbagent = loaded_dbagent

    port = find_free_port()
    server_url = f"http://localhost:{port}"

    # Run server in a background thread (ws="none" disables websockets to avoid deprecation warnings)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", ws="none")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to start
    max_wait = 5.0
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Test server failed to start on port {port}")

    yield server_url

    # Shutdown
    server.should_exit = True
    app.dependency_overrides.clear()


@pytest.fixture
def cli_runner():
    """CLI runner for integration tests."""
    from typer.testing import CliRunner
    from refget.cli.main import app

    runner = CliRunner()

    def run(*args, env=None):
        """Run CLI command with optional environment variables."""
        return runner.invoke(app, list(args), env=env)

    return run
