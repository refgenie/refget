"""
Tests for SeqColBackend protocol and RefgetStoreBackend implementation.

Verifies that:
- RefgetStoreBackend wraps RefgetStore correctly
- All SeqColBackend protocol methods work
- Error handling (ValueError, KeyError) works properly
"""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    from refget.backend import RefgetStoreBackend, SeqColBackend
    from refget.store import RefgetStore

    _RUST_BINDINGS_AVAILABLE = True
except ImportError:
    _RUST_BINDINGS_AVAILABLE = False

from refget.router import create_refget_router

TEST_FASTA_DIR = Path("test_fasta")
BASE_FASTA = TEST_FASTA_DIR / "base.fa"
DIFFERENT_NAMES_FASTA = TEST_FASTA_DIR / "different_names.fa"

with open(TEST_FASTA_DIR / "test_fasta_digests.json") as fp:
    TEST_DIGESTS = json.load(fp)

BASE_DIGEST = TEST_DIGESTS["base.fa"]["top_level_digest"]
BASE_LEVEL1 = TEST_DIGESTS["base.fa"]["level1"]
BASE_LEVEL2 = TEST_DIGESTS["base.fa"]["level2"]
DIFFERENT_NAMES_DIGEST = TEST_DIGESTS["different_names.fa"]["top_level_digest"]


@pytest.fixture
def backend():
    """Create a RefgetStoreBackend with base.fa and different_names.fa loaded."""
    store = RefgetStore.in_memory()
    store.add_sequence_collection_from_fasta(str(BASE_FASTA))
    store.add_sequence_collection_from_fasta(str(DIFFERENT_NAMES_FASTA))
    return RefgetStoreBackend(store.into_readonly())


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestRefgetStoreBackend:
    """Tests for RefgetStoreBackend."""

    def test_satisfies_protocol(self, backend):
        """RefgetStoreBackend satisfies the SeqColBackend protocol."""
        assert isinstance(backend, SeqColBackend)

    def test_get_collection_level2(self, backend):
        """get_collection returns level2 by default."""
        result = backend.get_collection(BASE_DIGEST)
        assert "names" in result
        assert "lengths" in result
        assert "sequences" in result
        assert isinstance(result["names"], list)

    def test_get_collection_level1(self, backend):
        """get_collection with level=1 returns digest strings."""
        result = backend.get_collection(BASE_DIGEST, level=1)
        assert "names" in result
        assert isinstance(result["names"], str)

    def test_get_collection_not_found(self, backend):
        """get_collection raises ValueError for missing digest."""
        with pytest.raises(ValueError, match="not found"):
            backend.get_collection("nonexistent_digest")

    def test_get_collection_attribute(self, backend):
        """get_collection_attribute returns a single attribute array matching level2."""
        names = backend.get_collection_attribute(BASE_DIGEST, "names")
        assert isinstance(names, list)
        # Should match what get_collection returns
        level2 = backend.get_collection(BASE_DIGEST, level=2)
        assert names == level2["names"]

    def test_get_collection_attribute_not_found(self, backend):
        """get_collection_attribute raises ValueError for missing attribute."""
        with pytest.raises(ValueError, match="not found"):
            backend.get_collection_attribute(BASE_DIGEST, "nonexistent_attr")

    def test_get_collection_itemwise(self, backend):
        """get_collection_itemwise returns transposed list of dicts."""
        items = backend.get_collection_itemwise(BASE_DIGEST)
        assert isinstance(items, list)
        assert len(items) > 0
        for item in items:
            assert "names" in item
            assert "lengths" in item

    def test_get_collection_itemwise_with_limit(self, backend):
        """get_collection_itemwise respects limit parameter."""
        items = backend.get_collection_itemwise(BASE_DIGEST, limit=1)
        assert len(items) == 1

    def test_get_attribute(self, backend):
        """get_attribute returns attribute by its own digest."""
        names_digest = BASE_LEVEL1["names"]
        result = backend.get_attribute("names", names_digest)
        assert isinstance(result, list)

    def test_get_attribute_not_found(self, backend):
        """get_attribute raises KeyError for missing attribute."""
        with pytest.raises(KeyError):
            backend.get_attribute("names", "nonexistent_digest")

    def test_compare_digests(self, backend):
        """compare_digests returns comparison dict."""
        result = backend.compare_digests(BASE_DIGEST, DIFFERENT_NAMES_DIGEST)
        assert "attributes" in result
        assert "array_elements" in result

    def test_compare_digests_not_found(self, backend):
        """compare_digests raises ValueError for missing digest."""
        with pytest.raises(ValueError):
            backend.compare_digests("nonexistent", DIFFERENT_NAMES_DIGEST)

    def test_compare_digest_with_level2(self, backend):
        """compare_digest_with_level2 compares stored vs POSTed collection."""
        level2_b = backend.get_collection(DIFFERENT_NAMES_DIGEST, level=2)
        result = backend.compare_digest_with_level2(BASE_DIGEST, level2_b)
        assert "attributes" in result
        assert "array_elements" in result

    def test_list_collections(self, backend):
        """list_collections returns paginated results."""
        result = backend.list_collections()
        assert "results" in result
        assert "pagination" in result
        assert result["pagination"]["total"] >= 2

    def test_list_collections_pagination(self, backend):
        """list_collections respects page_size."""
        result = backend.list_collections(page=0, page_size=1)
        assert len(result["results"]) <= 1

    def test_collection_count(self, backend):
        """collection_count returns total number of collections."""
        count = backend.collection_count()
        assert count >= 2

    def test_capabilities(self, backend):
        """capabilities returns expected keys for RefgetStoreBackend."""
        caps = backend.capabilities()
        assert caps["backend_type"] == "refget_store"
        assert "n_collections" in caps
        assert "n_sequences" in caps
        assert "has_sequence_data" in caps
        assert isinstance(caps["collection_alias_namespaces"], list)
        assert isinstance(caps["sequence_alias_namespaces"], list)
        assert caps["n_collections"] >= 2


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestStoreBackend501:
    """Verify DB-only endpoints return 501 when only RefgetStoreBackend is configured."""

    @pytest.fixture
    def store_client(self):
        """Create a TestClient with RefgetStoreBackend but no dbagent."""
        app = FastAPI()
        router = create_refget_router(sequences=False, collections=True, pangenomes=False)
        app.include_router(router, prefix="/seqcol")

        store = RefgetStore.in_memory()
        store.add_sequence_collection_from_fasta(str(BASE_FASTA))
        backend = RefgetStoreBackend(store.into_readonly())
        app.state.backend = backend
        # Deliberately do NOT set app.state.dbagent
        return TestClient(app)

    def test_list_attributes_returns_501(self, store_client):
        """GET /list/attributes/names returns 501 without dbagent."""
        response = store_client.get("/seqcol/list/attributes/names")
        assert response.status_code == 501
        assert "database backend" in response.json()["detail"].lower()

    def test_similarities_post_returns_501(self, store_client):
        """POST /similarities/{digest} returns 501 without dbagent."""
        response = store_client.post(
            f"/seqcol/similarities/{BASE_DIGEST}",
            params={"species": "human"},
        )
        assert response.status_code == 501

    def test_similarities_json_post_returns_501(self, store_client):
        """POST /similarities/ returns 501 without dbagent."""
        response = store_client.post(
            "/seqcol/similarities/",
            json={"names": ["chr1"], "lengths": [100], "sequences": ["abc"]},
        )
        assert response.status_code == 501

    def test_backend_endpoints_still_work(self, store_client):
        """Backend-powered endpoints work fine without dbagent."""
        # GET /collection/{digest} uses get_backend, should work
        response = store_client.get(f"/seqcol/collection/{BASE_DIGEST}")
        assert response.status_code == 200
        data = response.json()
        assert "names" in data
        assert "lengths" in data

    def test_list_collections_still_works(self, store_client):
        """GET /list/collection uses get_backend, should work."""
        response = store_client.get("/seqcol/list/collection")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "pagination" in data
