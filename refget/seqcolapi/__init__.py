"""Sequence Collections API service — the optional, server-side half of refget.

Everything in this subpackage requires the optional service dependencies
(``pip install 'refget[seqcolapi]'``). They are imported here at module level,
in ordinary Python style, because **the package boundary is the gate**: nothing
in ``refget/__init__.py`` — or on any other base-install code path — imports
``refget.seqcolapi``. Either you asked for the service and the whole subpackage
loads, or it is never loaded at all. There is no middle state, and no
function-local imports scattered through the service code to maintain.

Two applications ship here:

* :mod:`refget.seqcolapi.main` — the PostgreSQL-backed ``app`` that runs
  seqcolapi.databio.org, plus the ``store_app`` built from the environment.
* :func:`create_seqcol_app` — the store-backed factory, which returns a
  self-contained, mountable app served out of a
  :class:`~refget.store.RefgetStore`.

Import the package, not its submodules::

    from refget.seqcolapi import create_seqcol_app, prepare_store

:mod:`refget.seqcolapi.main` is deliberately *not* imported here: it builds a
FastAPI app at module scope and, absent ``REFGET_STORE_URL`` /
``REFGET_STORE_PATH``, connects to PostgreSQL on import. Ask for it by name
(``uvicorn refget.seqcolapi.main:app``) when you want that.
"""

try:  # The gate. Fail here, once, with something actionable.
    import fastapi  # noqa: F401
except ImportError as e:  # pragma: no cover - exercised in a bare venv
    raise ImportError(
        "refget.seqcolapi requires the optional sequence-collections service "
        "dependencies (fastapi, uvicorn, ...), which are not installed.\n"
        "Install them with:  pip install 'refget[seqcolapi]'"
    ) from e

from refget.const import ALL_VERSIONS

from .app import (
    DEFAULT_CACHE_DIR,
    create_seqcol_app,
    create_store_app,
    load_seqcol_schema,
    prepare_store,
    store_service_info,
)
from .const import STATIC_DIRNAME, STATIC_PATH

__all__ = [
    "ALL_VERSIONS",
    "DEFAULT_CACHE_DIR",
    "STATIC_DIRNAME",
    "STATIC_PATH",
    "create_seqcol_app",
    "create_store_app",
    "load_seqcol_schema",
    "prepare_store",
    "store_service_info",
]
