"""
Integration test fixtures for refget client testing.

Uses FastAPI TestClient with ephemeral Docker PostgreSQL.

Run with: ./scripts/test-integration.sh
"""

import os
import socket
import threading
import time
from pathlib import Path

import pytest

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
    from refget.router import get_dbagent
    from seqcolapi.main import app

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
def test_server(request):
    """
    Provide a seqcol server URL for integration tests.

    If --api-root option is provided, uses that external server.
    Otherwise, spins up a local test server with loaded test data.

    Usage: pytest tests/integration/ --api-root=https://seqcolapi.databio.org
    """
    external_url = request.config.getoption("--api-root")
    if external_url:
        # Use external server - no setup/teardown needed
        yield external_url.rstrip("/")
        return

    # Local server setup - needs loaded_dbagent
    loaded_dbagent = request.getfixturevalue("loaded_dbagent")

    import uvicorn

    from refget.router import get_dbagent
    from seqcolapi.main import app

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


@pytest.fixture(scope="session")
def store_test_server(tmp_path_factory):
    """
    Provide a store-backed seqcol server URL for integration tests.

    Creates a temporary RefgetStore, loads all 6 test FASTA files,
    and runs a store-backed uvicorn server in a background thread.
    No database required.

    Note: We build the app manually (instead of create_store_app) so we can
    reuse the same store instance that loaded the FASTAs, preserving
    correct array ordering. Opening a new store from the same path
    would lose FASTA-order due to a gtars hash-map ordering issue.
    """
    import json

    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from refget.router import create_refget_router, setup_backend
    from refget.store import RefgetStore
    from seqcolapi.const import ALL_VERSIONS

    # Create store and load test FASTAs
    store_dir = tmp_path_factory.mktemp("store")
    store = RefgetStore.on_disk(str(store_dir))

    test_fasta_dir = Path(__file__).parent.parent.parent / "test_fasta"
    for fa_file in [
        "base.fa",
        "different_names.fa",
        "different_order.fa",
        "pair_swap.fa",
        "subset.fa",
        "swap_wo_coords.fa",
    ]:
        fa_path = test_fasta_dir / fa_file
        store.add_sequence_collection_from_fasta(str(fa_path))

    # Build the app directly using the same store instance
    store_app = FastAPI(
        title="Sequence Collections API (Store-backed test)",
        version=ALL_VERSIONS["refget_version"],
    )
    store_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_backend(store_app, store=store)
    router = create_refget_router(sequences=False, pangenomes=False)
    store_app.include_router(router)

    # Load seqcol schema for service-info
    schema_path = Path(__file__).parent.parent.parent / "refget" / "schemas" / "seqcol.json"
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception:
        schema = None

    @store_app.get("/service-info", summary="GA4GH service info", tags=["General endpoints"])
    async def store_service_info():
        backend = getattr(store_app.state, "backend", None)
        caps = backend.capabilities() if backend and hasattr(backend, "capabilities") else {}
        return {
            "id": "org.databio.seqcolapi.store",
            "name": "Sequence collections (store-backed)",
            "type": {
                "group": "org.ga4gh",
                "artifact": "refget-seqcol",
                "version": ALL_VERSIONS["seqcol_spec_version"],
            },
            "description": "Store-backed API providing metadata for collections of reference sequences",
            "organization": {"name": "Databio Lab", "url": "https://databio.org"},
            "contactUrl": "https://github.com/refgenie/refget/issues",
            "version": ALL_VERSIONS,
            "seqcol": {
                "schema": schema,
                "refget_store": {"enabled": True, **caps},
            },
        }

    port = find_free_port()
    server_url = f"http://localhost:{port}"

    config = uvicorn.Config(store_app, host="127.0.0.1", port=port, log_level="error", ws="none")
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
        raise RuntimeError(f"Store test server failed to start on port {port}")

    yield server_url

    server.should_exit = True


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
