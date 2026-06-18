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
    return RefgetStoreBackend(store)


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

    def test_compute_similarities_surfaces_aliases(self, backend):
        """human_readable_names is populated from registered collection aliases.

        Regression test: the prior implementation scanned alias namespaces and
        assumed list_collection_aliases returned dicts/objects with .digest/.alias,
        which raised on every iteration and left human_readable_names empty. The
        reverse get_aliases_for_collection lookup must surface the alias name.
        """
        backend._store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)

        seqcol = backend.get_collection(BASE_DIGEST)
        result = backend.compute_similarities(seqcol)

        entry = next(s for s in result["similarities"] if s["digest"] == BASE_DIGEST)
        assert "hg38_base" in entry["human_readable_names"]

        # A collection with no aliases yields an empty list, not a skipped entry.
        other = next(s for s in result["similarities"] if s["digest"] == DIFFERENT_NAMES_DIGEST)
        assert other["human_readable_names"] == []


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestReadonlyStoreBackend:
    """RefgetStoreBackend served from a ReadonlyRefgetStore (the concurrent path).

    Builds a store, loads all collections, converts via into_readonly(), wraps
    the readonly store in RefgetStoreBackend, and exercises every backend method
    to prove they all work against ReadonlyRefgetStore.
    """

    @pytest.fixture
    def readonly_backend(self):
        store = RefgetStore.in_memory()
        store.add_sequence_collection_from_fasta(str(BASE_FASTA))
        store.add_sequence_collection_from_fasta(str(DIFFERENT_NAMES_FASTA))
        store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)
        # Load-then-convert: readonly store cannot lazy-load.
        store.load_all_collections()
        readonly = store.into_readonly()
        # Sanity: the readonly variant is a distinct type.
        from refget.store import ReadonlyRefgetStore

        assert isinstance(readonly, ReadonlyRefgetStore)
        return RefgetStoreBackend(readonly)

    def test_satisfies_protocol(self, readonly_backend):
        assert isinstance(readonly_backend, SeqColBackend)

    def test_get_collection(self, readonly_backend):
        result = readonly_backend.get_collection(BASE_DIGEST)
        assert "names" in result and "lengths" in result and "sequences" in result

    def test_get_collection_attribute(self, readonly_backend):
        names = readonly_backend.get_collection_attribute(BASE_DIGEST, "names")
        assert isinstance(names, list)

    def test_get_attribute(self, readonly_backend):
        result = readonly_backend.get_attribute("names", BASE_LEVEL1["names"])
        assert isinstance(result, list)

    def test_list_collections(self, readonly_backend):
        result = readonly_backend.list_collections()
        assert result["pagination"]["total"] >= 2

    def test_capabilities(self, readonly_backend):
        caps = readonly_backend.capabilities()
        assert caps["backend_type"] == "refget_store"
        assert caps["n_collections"] >= 2

    def test_compute_similarities(self, readonly_backend):
        seqcol = readonly_backend.get_collection(BASE_DIGEST)
        result = readonly_backend.compute_similarities(seqcol)
        entry = next(s for s in result["similarities"] if s["digest"] == BASE_DIGEST)
        assert "hg38_base" in entry["human_readable_names"]


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestServeReadonlyConversion:
    """The `store serve` CLI helper loads + converts to a readonly store, and
    --lazy preserves the mutable-store path."""

    def test_into_readonly_helper(self):
        from refget.cli.store import _into_readonly
        from refget.store import ReadonlyRefgetStore

        store = RefgetStore.in_memory()
        store.add_sequence_collection_from_fasta(str(BASE_FASTA))
        readonly = _into_readonly(store, load_sequences=False)
        assert isinstance(readonly, ReadonlyRefgetStore)
        backend = RefgetStoreBackend(readonly)
        assert backend.collection_count() >= 1

    def test_lazy_serves_from_mutable_store(self):
        # The --lazy path wraps the mutable RefgetStore directly (no conversion).
        store = RefgetStore.in_memory()
        store.add_sequence_collection_from_fasta(str(BASE_FASTA))
        backend = RefgetStoreBackend(store)
        assert backend._store is store
        assert isinstance(backend._store, RefgetStore)
        assert backend.collection_count() >= 1


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
        backend = RefgetStoreBackend(store)
        app.state.backend = backend
        # Deliberately do NOT set app.state.dbagent
        return TestClient(app)

    def test_list_attributes_works_without_dbagent(self, store_client):
        """GET /list/attributes/names works via backend without dbagent."""
        response = store_client.get("/seqcol/list/attributes/names")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "pagination" in data

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


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestBackendAliasAndFhr:
    """Backend-level alias resolution and FHR metadata."""

    def test_resolve_alias(self, backend):
        backend._store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)
        assert backend.resolve_alias("collection", "ucsc", "hg38_base") == BASE_DIGEST
        assert backend.resolve_alias("collection", "ucsc", "missing") is None

    def test_list_alias_namespaces_and_aliases(self, backend):
        backend._store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)
        assert "ucsc" in backend.list_alias_namespaces("collection")
        assert "hg38_base" in backend.list_aliases("collection", "ucsc")

    def test_aliases_for(self, backend):
        backend._store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)
        pairs = backend.aliases_for("collection", BASE_DIGEST)
        assert ("ucsc", "hg38_base") in pairs

    def test_get_and_list_fhr(self, backend):
        from refget.store import FhrMetadata

        assert backend.get_fhr(BASE_DIGEST) is None
        backend._store.set_fhr_metadata(BASE_DIGEST, FhrMetadata(genome="Test", version="v1"))
        fhr = backend.get_fhr(BASE_DIGEST)
        assert fhr is not None and fhr.get("genome") == "Test"
        assert BASE_DIGEST in backend.list_fhr()

    def test_capabilities_includes_fhr(self, backend):
        caps = backend.capabilities()
        assert "fhr_metadata_collections" in caps
        assert isinstance(caps["fhr_metadata_collections"], list)


@pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")
class TestAliasFhrEndpoints:
    """Router-level alias + FHR endpoints over a store-backed app."""

    @pytest.fixture
    def app_client(self):
        app = FastAPI()
        router = create_refget_router(sequences=False, collections=True, pangenomes=False)
        app.include_router(router, prefix="/seqcol")

        store = RefgetStore.in_memory()
        store.add_sequence_collection_from_fasta(str(BASE_FASTA))
        store.add_collection_alias("ucsc", "hg38_base", BASE_DIGEST)
        from refget.store import FhrMetadata

        store.set_fhr_metadata(BASE_DIGEST, FhrMetadata(genome="Test organism", version="v1.0"))
        app.state.backend = RefgetStoreBackend(store)
        return TestClient(app)

    def test_resolve_alias_endpoint(self, app_client):
        r = app_client.get("/seqcol/alias/collection/ucsc/hg38_base")
        assert r.status_code == 200
        assert r.json()["digest"] == BASE_DIGEST

    def test_resolve_alias_not_found(self, app_client):
        r = app_client.get("/seqcol/alias/collection/ucsc/nope")
        assert r.status_code == 404

    def test_resolve_alias_bad_kind(self, app_client):
        r = app_client.get("/seqcol/alias/bogus/ucsc/hg38_base")
        assert r.status_code == 400

    def test_list_alias_namespaces_endpoint(self, app_client):
        r = app_client.get("/seqcol/list/alias/collection")
        assert r.status_code == 200
        assert "ucsc" in r.json()["namespaces"]

    def test_list_aliases_endpoint(self, app_client):
        r = app_client.get("/seqcol/list/alias/collection/ucsc")
        assert r.status_code == 200
        assert "hg38_base" in r.json()["aliases"]

    def test_aliases_for_endpoint(self, app_client):
        r = app_client.get(f"/seqcol/aliases/collection/{BASE_DIGEST}")
        assert r.status_code == 200
        assert ["ucsc", "hg38_base"] in r.json()["aliases"]

    def test_fhr_endpoint(self, app_client):
        r = app_client.get(f"/seqcol/collection/{BASE_DIGEST}/fhr")
        assert r.status_code == 200
        assert r.json()["genome"] == "Test organism"

    def test_fhr_endpoint_not_found(self, app_client):
        r = app_client.get("/seqcol/collection/nonexistent/fhr")
        assert r.status_code == 404

    def test_list_fhr_endpoint(self, app_client):
        r = app_client.get("/seqcol/list/fhr")
        assert r.status_code == 200
        assert BASE_DIGEST in r.json()["collections"]

    def test_client_resolve_alias_and_fhr(self, app_client):
        """SequenceCollectionClient methods work against the mounted app."""
        from refget.clients import SequenceCollectionClient

        client = SequenceCollectionClient(urls=["http://testserver/seqcol"], raise_errors=False)

        # Patch the client's HTTP layer to use the TestClient.
        import refget.clients as clients_mod

        orig_get = clients_mod.requests.get

        def fake_get(url, params=None, **kwargs):
            path = url.replace("http://testserver", "")
            return app_client.get(path, params=params)

        clients_mod.requests.get = fake_get
        try:
            resolved = client.resolve_alias("ucsc", "hg38_base")
            assert resolved["digest"] == BASE_DIGEST
            fhr = client.get_fhr(BASE_DIGEST)
            assert fhr["genome"] == "Test organism"
        finally:
            clients_mod.requests.get = orig_get
