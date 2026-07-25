"""Tests for the shared store-backed seqcol app factory (refget.app).

Covers the three properties the factory exists to guarantee:

- it returns a *mountable* app whose backend is its own, so two mounts are two
  independent stores (the multi-store door the ADR asks us not to close),
- its GA4GH service-info carries ``seqcol.refget_store.url`` plus the seqcol
  JSON schema, and
- the compliance endpoints self-target the seqcol service, not the server root.
"""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    from refget.store import RefgetStore

    _RUST_BINDINGS_AVAILABLE = True
except ImportError:
    _RUST_BINDINGS_AVAILABLE = False

from refget.app import create_seqcol_app, store_service_info
from refget.router import create_refget_router, setup_backend

TEST_FASTA_DIR = Path("test_fasta")
BASE_FASTA = TEST_FASTA_DIR / "base.fa"

with open(TEST_FASTA_DIR / "test_fasta_digests.json") as fp:
    TEST_DIGESTS = json.load(fp)

BASE_DIGEST = TEST_DIGESTS["base.fa"]["top_level_digest"]

pytestmark = pytest.mark.skipif(not _RUST_BINDINGS_AVAILABLE, reason="gtars is not installed")


def _readonly_store():
    store = RefgetStore.in_memory()
    store.add_sequence_collection_from_fasta(str(BASE_FASTA))
    store.load_all_collections()
    return store.into_readonly()


def _app(**kwargs):
    kwargs.setdefault("store", _readonly_store())
    kwargs.setdefault("cors", False)
    return create_seqcol_app(**kwargs)


class TestServiceInfo:
    def test_advertises_store_url(self):
        client = TestClient(_app(store_url="https://example.com/store/"))
        info = client.get("/service-info").json()
        assert info["seqcol"]["refget_store"]["enabled"] is True
        assert info["seqcol"]["refget_store"]["url"] == "https://example.com/store/"

    def test_carries_seqcol_schema_and_versions(self):
        client = TestClient(_app(store_url="https://example.com/store/"))
        info = client.get("/service-info").json()
        assert isinstance(info["seqcol"]["schema"], dict)
        assert info["version"]["refget_version"]
        assert info["type"] == {
            "group": "org.ga4gh",
            "artifact": "refget-seqcol",
            "version": "1.0.0",
        }

    def test_identity_is_caller_supplied(self):
        client = TestClient(
            _app(
                store_url="https://example.com/store/",
                service_info_id="org.refgenie.seqcol",
                service_info_name="Refgenie Sequence Collections",
            )
        )
        info = client.get("/service-info").json()
        assert info["id"] == "org.refgenie.seqcol"
        assert info["name"] == "Refgenie Sequence Collections"

    def test_no_store_url_reports_disabled(self):
        client = TestClient(_app())
        assert client.get("/service-info").json()["seqcol"]["refget_store"] == {"enabled": False}

    def test_http_url_env_override(self, monkeypatch):
        monkeypatch.setenv("REFGET_STORE_HTTP_URL", "https://public.example.com/store/")
        client = TestClient(_app(store_url="/local/on/disk"))
        info = client.get("/service-info").json()
        assert info["seqcol"]["refget_store"]["url"] == "https://public.example.com/store/"

    def test_extra_seqcol_block_can_be_a_callable(self):
        client = TestClient(
            _app(
                store_url="https://example.com/store/",
                service_info_extra=lambda: {"scom": {"enabled": True, "species": ["human"]}},
            )
        )
        assert client.get("/service-info").json()["seqcol"]["scom"]["species"] == ["human"]

    def test_store_service_info_builder_is_json_serializable(self):
        body = store_service_info(
            service_info_id="org.test",
            service_info_name="Test",
            store_url="https://example.com/store/",
        )
        json.dumps(body)


class TestMountable:
    """The factory must return an app, not mutate one -- see ADR decision C."""

    def test_serves_collections_when_mounted_under_a_prefix(self):
        host = FastAPI()
        host.mount("/seqcol", _app(store_url="https://a/store/"))
        client = TestClient(host)
        assert client.get("/seqcol/list/collection").status_code == 200
        assert client.get(f"/seqcol/collection/{BASE_DIGEST}").status_code == 200

    def test_two_mounts_are_two_independent_stores(self):
        host = FastAPI()
        host.mount("/a", _app(store_url="https://a/store/", service_info_id="org.test.a"))
        host.mount("/b", _app(store_url="https://b/store/", service_info_id="org.test.b"))
        client = TestClient(host)

        a = client.get("/a/service-info").json()
        b = client.get("/b/service-info").json()
        assert a["id"] == "org.test.a"
        assert b["id"] == "org.test.b"
        assert a["seqcol"]["refget_store"]["url"] == "https://a/store/"
        assert b["seqcol"]["refget_store"]["url"] == "https://b/store/"

    def test_host_app_keeps_its_own_root_service_info(self):
        host = FastAPI()

        @host.get("/service-info")
        def root_service_info():
            return {"id": "org.test.host"}

        host.mount("/seqcol", _app(store_url="https://a/store/"))
        client = TestClient(host)
        assert client.get("/service-info").json() == {"id": "org.test.host"}
        assert client.get("/seqcol/service-info").json()["seqcol"]["refget_store"]["url"]

    def test_factory_does_not_touch_the_host_app_state(self):
        host = FastAPI()
        host.mount("/seqcol", _app(store_url="https://a/store/"))
        assert not hasattr(host.state, "backend")


class TestComplianceSelfTarget:
    def test_mounted_app_targets_the_mount_path(self):
        host = FastAPI()
        host.mount("/seqcol", _app(store_url="https://a/store/"))
        result = TestClient(host).get("/seqcol/compliance/run").json()
        assert result["server_url"] == "http://testserver/seqcol"

    def test_included_router_targets_the_declared_mount_prefix(self):
        app = FastAPI()
        setup_backend(app, store=_readonly_store())
        app.include_router(create_refget_router(mount_prefix="/seqcol"), prefix="/seqcol")
        result = TestClient(app).get("/seqcol/compliance/run").json()
        assert result["server_url"] == "http://testserver/seqcol"

    def test_root_mounted_router_still_targets_the_root(self):
        app = FastAPI()
        setup_backend(app, store=_readonly_store())
        app.include_router(create_refget_router())
        result = TestClient(app).get("/compliance/run").json()
        assert result["server_url"] == "http://testserver"

    def test_explicit_target_url_wins(self):
        host = FastAPI()
        host.mount("/seqcol", _app(store_url="https://a/store/"))
        result = (
            TestClient(host)
            .get("/seqcol/compliance/run", params={"target_url": "https://elsewhere.example.com"})
            .json()
        )
        assert result["server_url"] == "https://elsewhere.example.com"
