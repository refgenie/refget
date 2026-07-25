"""Store-backed sequence-collections application factory.

This module owns the canonical wiring for serving the GA4GH sequence
collections API out of a :class:`~refget.store.RefgetStore`: opening and
loading the store, converting it to a thread-safe readonly snapshot, binding
the backend, mounting the refget router, optional freshness reloading, and a
complete GA4GH ``/service-info`` document.

**The factory returns a mountable app; it never mutates a caller's app.**

That is deliberate and load-bearing. :func:`refget.router.setup_backend` stores
the backend on ``app.state.backend`` and :func:`refget.router.get_backend`
reads it back off ``request.app.state`` -- an *app-global* binding, not a
router-scoped one. Including ``create_refget_router()`` twice at two prefixes
of the same app therefore does **not** give you two stores; both mounts resolve
through the same ``app.state.backend``. Returning a self-contained
sub-application instead means each store gets its own ``state.backend``, its
own service-info and its own freshness policy, so a host app can do::

    host.mount("/jungle", create_seqcol_app(store_path=url_a, remote=True))
    host.mount("/other", create_seqcol_app(store_path=url_b, remote=True))

Serving several stores from one process is not a requirement today, and
nothing here implements it. The point is only that the shape does not preclude
it.

Typical use::

    from refget.app import create_seqcol_app

    app.mount("/seqcol", create_seqcol_app(store_path=store_url, remote=True))
"""

import json
import logging
import os

from .const import ALL_VERSIONS, SEQCOL_SCHEMA_PATH, SEQCOL_SPEC_VERSION

_LOGGER = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = "/tmp/seqcol_cache"
DEFAULT_ORGANIZATION = {"name": "Databio Lab", "url": "https://databio.org"}
DEFAULT_CONTACT_URL = "https://github.com/refgenie/refget/issues"


def prepare_store(
    store_path: str,
    remote: bool = False,
    cache_dir: str = DEFAULT_CACHE_DIR,
):
    """Open a RefgetStore and return a fully-loaded ReadonlyRefgetStore.

    Loads every collection and then converts to a readonly snapshot, because
    concurrent HTTP reads must borrow the store immutably -- a mutable
    ``RefgetStore`` lazy-loads through a mutable borrow (see
    ``refget.backend.RefgetStoreBackend``).

    Note that ``into_readonly()`` **consumes** the receiver: the pyo3 binding
    does ``std::mem::replace(&mut self.inner, RefgetStore::in_memory())``, so
    the ``RefgetStore`` object handed in is left empty. Never pass a store that
    someone else still holds a reference to -- open a second one instead.

    Args:
        store_path: Path to a store on disk, or a URL for a remote store.
        remote: If True, open as a remote store.
        cache_dir: Local cache directory used for remote stores.

    Returns:
        A ReadonlyRefgetStore suitable for concurrent serving.
    """
    from .store import RefgetStore

    if remote:
        store = RefgetStore.open_remote(cache_dir, store_path)
    else:
        store = RefgetStore.on_disk(store_path)

    store.load_all_collections()
    return store.into_readonly()


def load_seqcol_schema() -> dict | None:
    """Load the canonical seqcol JSON schema shipped with the package.

    Resolved through ``refget.const.SEQCOL_SCHEMA_PATH`` rather than any
    repo-relative path, so it works from site-packages in a deployed image.
    """
    try:
        with open(SEQCOL_SCHEMA_PATH) as f:
            return json.load(f)
    except Exception as e:
        _LOGGER.warning(f"Could not load seqcol schema from {SEQCOL_SCHEMA_PATH}: {e}")
        return None


def store_service_info(
    *,
    service_info_id: str,
    service_info_name: str,
    store_url: str | None,
    capabilities: dict | None = None,
    description: str | None = None,
    organization: dict | None = None,
    contact_url: str | None = None,
    documentation_url: str | None = None,
    extra_seqcol: dict | None = None,
) -> dict:
    """Build the GA4GH service-info body for a store-backed seqcol service.

    Args:
        service_info_id: Reverse-domain service id, e.g. ``org.refgenie.seqcol``.
        service_info_name: Human-readable service name.
        store_url: The publicly reachable RefgetStore URL to advertise. The
            ``REFGET_STORE_HTTP_URL`` environment variable overrides it, for
            deployments whose internal store path is not publicly fetchable.
        capabilities: Backend capabilities dict (``backend.capabilities()``).
        extra_seqcol: Extra keys merged into the ``seqcol`` block (seqcolapi
            passes its ``scom`` block through here).

    Returns:
        A JSON-serializable service-info dict carrying ``seqcol.refget_store.url``.
    """
    caps = capabilities or {}
    advertised = os.environ.get("REFGET_STORE_HTTP_URL", store_url)

    seqcol: dict = {"schema": load_seqcol_schema()}
    if advertised:
        seqcol["refget_store"] = {"enabled": True, "url": advertised, **caps}
    else:
        seqcol["refget_store"] = {"enabled": False}
    seqcol["aliases"] = {
        "enabled": bool(
            caps.get("collection_alias_namespaces") or caps.get("sequence_alias_namespaces")
        )
    }
    seqcol["fhr_metadata"] = {"enabled": bool(caps.get("fhr_metadata_collections"))}
    if extra_seqcol:
        seqcol.update(extra_seqcol)

    info = {
        "id": service_info_id,
        "name": service_info_name,
        "type": {
            "group": "org.ga4gh",
            "artifact": "refget-seqcol",
            "version": SEQCOL_SPEC_VERSION,
        },
        "description": description
        or "Store-backed API providing metadata for collections of reference sequences",
        "organization": organization or DEFAULT_ORGANIZATION,
        "contactUrl": contact_url or DEFAULT_CONTACT_URL,
        "version": ALL_VERSIONS,
        "seqcol": seqcol,
    }
    if documentation_url:
        info["documentationUrl"] = documentation_url
    return info


def create_seqcol_app(
    store=None,
    *,
    store_path: str | None = None,
    remote: bool = False,
    cache_dir: str = DEFAULT_CACHE_DIR,
    store_url: str | None = None,
    service_info_id: str = "org.ga4gh.seqcol.store",
    service_info_name: str = "Sequence collections (store-backed)",
    description: str | None = None,
    organization: dict | None = None,
    contact_url: str | None = None,
    documentation_url: str | None = None,
    service_info_extra=None,
    sequences: bool = False,
    collections: bool = True,
    pangenomes: bool = False,
    fasta_drs: bool = False,
    compliance: bool = True,
    freshness: bool | None = None,
    freshness_interval: int = 300,
    cors: bool = True,
    defer_backend: bool = False,
    title: str = "Sequence Collections API (Store-backed)",
):
    """Create a self-contained, mountable seqcol app served from a RefgetStore.

    The returned app owns its own ``state.backend``, so mounting several of
    them at different prefixes yields several independent stores. Do not pass
    the returned app to ``setup_backend`` again.

    Args:
        store: An already-prepared ReadonlyRefgetStore. If omitted,
            ``store_path`` is opened via :func:`prepare_store`.
        store_path: Store path/URL to open when ``store`` is not given.
        remote: Open ``store_path`` as a remote store.
        cache_dir: Local cache directory for remote stores.
        store_url: Store URL to advertise in service-info. Defaults to
            ``store_path`` when the store is remote.
        service_info_id: Reverse-domain id for this service instance.
        service_info_name: Human-readable name for this service instance.
        service_info_extra: Extra ``seqcol`` keys for service-info. Either a
            dict or a zero-argument callable evaluated per request (seqcolapi
            uses the callable form because its SCOM digests load lazily).
        freshness: Attach ``StoreFreshnessMiddleware`` so the app picks up a
            republished store without a restart. Defaults to ``remote``.
        cors: Add a permissive CORS middleware. Set False when the host app
            already installs one.
        defer_backend: Build the routes now but do not open or bind a store.
            The caller must then call ``refget.router.setup_backend(seqcol_app,
            store=...)`` before the first request. Mounted sub-applications do
            not receive their own lifespan events, so a host app that wants to
            open the store on startup rather than at import time has to mount
            the routes early and bind the backend from *its* lifespan.

    Returns:
        A FastAPI application ready to serve standalone or to ``app.mount()``.
    """
    from fastapi import FastAPI

    from .router import create_refget_router, setup_backend

    if store is None and not defer_backend:
        if store_path is None:
            raise ValueError(
                "create_seqcol_app requires `store`, `store_path`, or defer_backend=True"
            )
        store = prepare_store(store_path, remote=remote, cache_dir=cache_dir)

    if store_url is None and remote:
        store_url = store_path

    app = FastAPI(title=title, version=ALL_VERSIONS["refget_version"])

    if cors:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if store is not None:
        setup_backend(app, store=store)
    app.include_router(
        create_refget_router(
            sequences=sequences,
            collections=collections,
            pangenomes=pangenomes,
            fasta_drs=fasta_drs,
            compliance=compliance,
            refget_store_url=store_url,
        )
    )

    if freshness is None:
        freshness = remote
    if freshness:
        if not store_path:
            raise ValueError("freshness requires `store_path` to poll for rgstore.json")
        from .middleware import StoreFreshnessMiddleware

        app.add_middleware(
            StoreFreshnessMiddleware,
            store_url=store_path,
            cache_dir=cache_dir,
            check_interval=freshness_interval,
        )

    @app.get("/service-info", summary="GA4GH service info", tags=["General endpoints"])
    async def service_info():
        backend = getattr(app.state, "backend", None)
        caps = backend.capabilities() if backend and hasattr(backend, "capabilities") else {}
        extra = service_info_extra() if callable(service_info_extra) else service_info_extra
        return store_service_info(
            service_info_id=service_info_id,
            service_info_name=service_info_name,
            store_url=store_url,
            capabilities=caps,
            description=description,
            organization=organization,
            contact_url=contact_url,
            documentation_url=documentation_url,
            extra_seqcol=extra,
        )

    return app


def create_store_app(
    store_path: str,
    remote: bool = False,
    cache_dir: str = DEFAULT_CACHE_DIR,
    **kwargs,
):
    """Create a standalone store-backed seqcol app (no database).

    Thin convenience wrapper around :func:`create_seqcol_app` for serving a
    single store at the root of its own process.

    Args:
        store_path: Path to store on disk, or S3/HTTP URL for remote stores.
        remote: If True, open as a remote store.
        cache_dir: Local cache directory for remote stores.

    Returns:
        FastAPI app with store-backed seqcol endpoints at the root.
    """
    return create_seqcol_app(store_path=store_path, remote=remote, cache_dir=cache_dir, **kwargs)
