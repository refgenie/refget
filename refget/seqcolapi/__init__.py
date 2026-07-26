"""Sequence Collections API service — the optional, server-side half of refget.

Everything in this subpackage requires the optional web-service dependencies
(``pip install 'refget[seqcolapi]'``: fastapi and uvicorn). They are imported
here at module level, in ordinary Python style, because **the package boundary
is the gate**: nothing in ``refget/__init__.py`` — or on any other base-install
code path — imports ``refget.seqcolapi``. Either you asked for the service and
the whole subpackage loads, or it is never loaded at all. There is no middle
state, and no function-local imports scattered through the service code to
maintain.

Two applications ship here, and they do **not** cost the same:

* :func:`create_seqcol_app` — the store-backed factory, which returns a
  self-contained, mountable app served out of a
  :class:`~refget.store.RefgetStore`. Needs ``refget[seqcolapi]`` only. No
  database, no ORM: nothing it reaches imports sqlmodel. This is the only app
  factory exported here; it is the one to call from your own code.
* :mod:`refget.seqcolapi.main` — the PostgreSQL-backed ``app`` that runs
  seqcolapi.databio.org, plus the ``store_app`` built from the environment by
  :func:`refget.seqcolapi.main.create_seqcolapi_store_app` (``create_seqcol_app``
  plus seqcolapi's own service identity and SCOM block). ``app`` needs
  ``refget[seqcolapi,db]``, because it goes through :mod:`refget.agents` and
  :mod:`refget.models`.

Import the package, not its submodules::

    from refget.seqcolapi import create_seqcol_app, prepare_store

:mod:`refget.seqcolapi.main` is deliberately *not* imported here: it reads the
environment and builds an app at module scope. Ask for it by name
(``uvicorn refget.seqcolapi.main:store_app``, or ``:app`` for the PostgreSQL
one) when you want that.
"""

from refget._deps import require

# Fail once, here, with something actionable -- not with a bare
# ModuleNotFoundError from four imports deep.
#
# Only fastapi is required. The store-backed app in .app needs no database:
# refget.router takes its response models from refget.response_models, and
# setup_backend imports RefgetDBAgent lazily inside its engine branch. The
# database gate belongs to .main, which is the only module here that imports
# sqlmodel -- and .main is deliberately not imported by this package.
require("refget.seqcolapi (the sequence collections service)", "seqcolapi", "fastapi")

from refget.const import ALL_VERSIONS  # noqa: E402

from .app import (
    DEFAULT_CACHE_DIR,
    create_seqcol_app,
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
    "load_seqcol_schema",
    "prepare_store",
    "store_service_info",
]
