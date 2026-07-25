"""The seqcolapi service entry points: ``store_app`` and ``app``.

Two deployments live behind this one module name, and they cost different
things to install:

``store_app`` -- RefgetStore-backed, no database
    Built here, eagerly, when ``REFGET_STORE_URL`` or ``REFGET_STORE_PATH`` is
    set. Needs ``pip install 'refget[seqcolapi]'`` and nothing else: no
    sqlmodel, no sqlalchemy, no psycopg2 anywhere in the environment::

        REFGET_STORE_PATH=/path/to/store uvicorn seqcolapi.main:store_app

``app`` -- PostgreSQL-backed (this is seqcolapi.databio.org)
    Lives in :mod:`refget.seqcolapi.dbapp` and is resolved here through a
    module-level ``__getattr__``. Needs
    ``pip install 'refget[seqcolapi-db]'``::

        uvicorn seqcolapi.main:app

The indirection is the point. If ``app`` were built at module scope, importing
this module would import sqlmodel, :mod:`refget.agents` and
:mod:`refget.models`, and every store-only deployment would have to install the
ORM to serve a directory of FASTA digests. Touching the name ``app`` is the
gate; ``uvicorn seqcolapi.main:app`` does exactly that and nothing else does.
"""

import logging
import os

from refget.router import _SAMPLE_DIGESTS

from .app import create_seqcol_app
from .const import ALL_VERSIONS

global _LOGGER
_LOGGER = logging.getLogger(__name__)

# `app` is resolved by __getattr__ below, and `store_app` only exists when the
# environment names a store -- neither is a module-level binding here.
__all__ = ["app", "store_app", "create_store_app"]  # noqa: F822


def _load_scom_config(store_path: str, remote: bool):
    """Load SCOM target digests from a JSON config.

    Checks (in order):
    1. SCOM_CONFIG_URL environment variable (any HTTP URL)
    2. scom_config.json next to the store (convention)

    Format: {"human": ["digest1", "digest2", ...], "mouse": [...]}
    """
    import json
    import os
    import urllib.request

    # Try env var first
    config_url = os.environ.get("SCOM_CONFIG_URL")

    # Fall back to store convention
    if not config_url:
        if remote:
            config_url = store_path.rstrip("/") + "/scom_config.json"
        else:
            config_path = os.path.join(store_path, "scom_config.json")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                for species, digests in config.items():
                    _SAMPLE_DIGESTS[species] = digests
                    _LOGGER.info(f"SCOM: loaded {len(digests)} target digests for '{species}'")
                return
            else:
                _LOGGER.info(
                    "No SCOM_CONFIG_URL set and no scom_config.json found. SCOM disabled."
                )
                return

    try:
        with urllib.request.urlopen(config_url, timeout=10) as resp:
            config = json.loads(resp.read())
        for species, digests in config.items():
            _SAMPLE_DIGESTS[species] = digests
            _LOGGER.info(f"SCOM: loaded {len(digests)} target digests for '{species}'")
    except Exception as e:
        _LOGGER.info(f"Could not load SCOM config from {config_url} ({e}). SCOM disabled.")


for key, value in ALL_VERSIONS.items():
    _LOGGER.info(f"{key}: {value}")


def create_store_app(store_path: str, remote: bool = False, cache_dir: str = "/tmp/seqcol_cache"):
    """Create a seqcolapi FastAPI app backed by a RefgetStore (no database).

    Thin wrapper over :func:`refget.seqcolapi.create_seqcol_app`, which owns the
    shared store-backed wiring (readonly store, backend, router, freshness,
    GA4GH service-info). Everything seqcolapi adds on top is SCOM, which is not
    a refget concern, so it is injected through ``service_info_extra``.

    Args:
        store_path: Path to store on disk, or S3 URL for remote stores.
        remote: If True, open as a remote (S3) store.
        cache_dir: Local cache directory for remote stores.

    Returns:
        FastAPI app with store-backed seqcol endpoints.
    """
    # Load SCOM config: check SCOM_CONFIG_URL env var, then fall back to store convention
    _load_scom_config(store_path, remote)

    def _scom_block():
        # Evaluated per request, because _SAMPLE_DIGESTS can be repopulated.
        return {
            "scom": {
                "enabled": bool(_SAMPLE_DIGESTS),
                "species": list(_SAMPLE_DIGESTS.keys()),
            }
        }

    return create_seqcol_app(
        store_path=store_path,
        remote=remote,
        cache_dir=cache_dir,
        # Advertise the store path (REFGET_STORE_HTTP_URL overrides it inside
        # store_service_info), matching the pre-extraction service-info exactly.
        store_url=store_path,
        service_info_id="org.databio.seqcolapi.store",
        service_info_name="Sequence collections (store-backed)",
        service_info_extra=_scom_block,
    )


_STORE_URL_ENV = os.environ.get("REFGET_STORE_URL")
_STORE_PATH_ENV = os.environ.get("REFGET_STORE_PATH")

if _STORE_URL_ENV:
    store_app = create_store_app(_STORE_URL_ENV, remote=True)
elif _STORE_PATH_ENV:
    store_app = create_store_app(_STORE_PATH_ENV, remote=False)


def __getattr__(name):
    """Resolve ``app`` -- and only ``app`` -- by importing the database module.

    PEP 562. This runs on the first ``seqcolapi.main.app`` look-up, which for a
    ``uvicorn seqcolapi.main:app`` deployment is at startup, so the observable
    behaviour (build the app, connect to PostgreSQL) is unchanged. What changed
    is that a store-only deployment never triggers it and therefore never needs
    the `db` extra installed.
    """
    if name in ("app", "lifespan_loader", "refget_router", "service_info"):
        from . import dbapp

        return getattr(dbapp, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | {"app", "lifespan_loader", "refget_router", "service_info"})
