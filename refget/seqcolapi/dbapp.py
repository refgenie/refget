"""The PostgreSQL-backed seqcolapi application (``seqcolapi.databio.org``).

This is the database half of the service, and it is a separate module for the
same reason :mod:`refget.models` is: **the module boundary is the gate**.
sqlmodel, :mod:`refget.agents` and :mod:`refget.models` are imported here at
top level, in ordinary Python style, and nothing imports this module unless you
actually asked for the PostgreSQL app -- :mod:`refget.seqcolapi.main` reaches
it only through a module-level ``__getattr__`` on the name ``app``.

That is what lets ``uvicorn seqcolapi.main:store_app`` run on
``pip install 'refget[seqcolapi]'`` with no ORM in the environment at all,
while ``uvicorn seqcolapi.main:app`` still needs
``pip install 'refget[seqcolapi,db]'``.

Importing this module connects to PostgreSQL (via
``setup_backend(app, engine=RefgetDBAgent().engine)``) unless ``REFGET_STORE_URL``
or ``REFGET_STORE_PATH`` is set. Ask for the app by name; do not import this
module for its side effects.
"""

import logging
import os
from contextlib import asynccontextmanager

from refget._deps import require

# Fail once, here, with something actionable. This is the one module in the
# service subpackage that needs the database extra, so it carries its own gate
# rather than making every store-only deployment pay for one.
require(
    "refget.seqcolapi.dbapp (the PostgreSQL-backed seqcolapi app)",
    "db",
    "sqlmodel",
    "sqlalchemy",
)

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from sqlmodel import Session, select  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402

from refget.agents import RefgetDBAgent  # noqa: E402
from refget.const import HUMANS_SAMPLE_LIST, MOUSE_SAMPLES_LIST  # noqa: E402
from refget.models import HumanReadableNames  # noqa: E402
from refget.router import (  # noqa: E402
    _ROUTER_CONFIG,
    _SAMPLE_DIGESTS,
    create_refget_router,
    setup_backend,
)

from .const import ALL_VERSIONS, STATIC_DIRNAME, STATIC_PATH  # noqa: E402
from .examples import *  # noqa: E402,F401,F403

_LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_loader(app):
    """
    Lifespan event to pre-load sample names and their digests
    """
    _LOGGER.info("Starting lifespan: Loading sample data...")

    # Initialize backend via setup_backend
    setup_backend(app, engine=RefgetDBAgent().engine)

    species_samples = {"human": HUMANS_SAMPLE_LIST, "mouse": MOUSE_SAMPLES_LIST}

    for species, sample_names in species_samples.items():
        try:
            _LOGGER.info(f"Loading {len(sample_names)} sample names for {species}")

            with Session(app.state.dbagent.engine) as session:
                statement = select(HumanReadableNames).where(
                    HumanReadableNames.human_readable_name.in_(sample_names)
                )
                results = session.exec(statement).all()

                target_digests = [result.digest for result in results]

            _SAMPLE_DIGESTS[species] = target_digests
            _LOGGER.info(f"Pre-loaded {len(target_digests)} digests for {species}")

        except Exception as e:
            _LOGGER.error(f"Error loading sample data for {species}: {e}")
            _SAMPLE_DIGESTS[species] = []

    _LOGGER.info("Lifespan startup complete: Sample data loaded")

    yield  # Application runs here

    # Cleanup
    _LOGGER.info("Lifespan shutdown: Cleaning up sample data...")
    _SAMPLE_DIGESTS.clear()


app = FastAPI(
    title="Sequence Collections API",
    description="An API providing metadata such as names, lengths, and other values for collections of reference sequences",
    version=ALL_VERSIONS["refget_version"],
    lifespan=lifespan_loader,
)

origins = ["*"]

app.add_middleware(  # This is a public API, so we allow all origins
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
# RefgetStore URL (set to None if not using a backing store)
REFGET_STORE_URL = None  # e.g., "s3://my-bucket/store/"

# This is where the magic happens
# This will add the seqcol endpoints to the app
refget_router = create_refget_router(
    sequences=False,
    pangenomes=False,
    fasta_drs=True,
    refget_store_url=REFGET_STORE_URL,
)
app.include_router(refget_router)


# Catch-all error handler for any uncaught exceptions, return a 500 error with detailed information
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return await http_exception_handler(
        request, HTTPException(status_code=500, detail=str(exc))
    )  # Pass it to HTTP handler


# General Exception Handler (Covers All HTTPExceptions)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"http-{exc.status_code}",  # Generic error code
            "detail": exc.detail,  # FastAPI-style error message
            "status": exc.status_code,
            "path": str(request.url),  # URL of the request
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: Exception):
    raise HTTPException(status_code=404, detail=str(exc))


@app.get("favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("/static/favicon.ico")


@app.get("/", summary="Home page", tags=["General endpoints"], response_class=HTMLResponse)
async def index(request: Request):
    """
    Returns a landing page HTML with the server resources ready to download. No inputs required.
    """
    with open(f"{STATIC_PATH}/index.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)


@app.get("/service-info", summary="GA4GH service info", tags=["General endpoints"])
async def service_info():
    # Build seqcol capabilities object
    seqcol_info = {
        "schema": getattr(app.state.dbagent, "schema_dict", None)
        if hasattr(app.state, "dbagent")
        else None,
        "sorted_name_length_pairs": True,
        "fasta_drs": {"enabled": _ROUTER_CONFIG.get("fasta_drs", False)},
    }

    # Get backend capabilities
    backend = getattr(app.state, "backend", None)
    caps = backend.capabilities() if backend and hasattr(backend, "capabilities") else {}

    # Add refget_store info
    store_url = _ROUTER_CONFIG.get("refget_store_url")
    if store_url:
        seqcol_info["refget_store"] = {"enabled": True, "url": store_url, **caps}
    else:
        seqcol_info["refget_store"] = {"enabled": False}

    # Advertise alias + FHR availability independent of refget_store_url
    seqcol_info["aliases"] = {
        "enabled": bool(
            caps.get("collection_alias_namespaces") or caps.get("sequence_alias_namespaces")
        )
    }
    seqcol_info["fhr_metadata"] = {"enabled": bool(caps.get("fhr_metadata_collections"))}

    return {
        "id": "org.databio.seqcolapi",
        "name": "Sequence collections",
        "type": {
            "group": "org.ga4gh",
            "artifact": "refget-seqcol",
            "version": ALL_VERSIONS["seqcol_spec_version"],
        },
        "description": "An API providing metadata such as names, lengths, and other values for collections of reference sequences",
        "organization": {"name": "Databio Lab", "url": "https://databio.org"},
        "contactUrl": "https://github.com/refgenie/refget/issues",
        "documentationUrl": "https://seqcolapi.databio.org",
        "updatedAt": "2025-02-20T00:00:00Z",
        "environment": "dev",
        "version": ALL_VERSIONS,
        "seqcol": seqcol_info,
    }


# Mount statics after other routes for lower precedence
app.mount("/", StaticFiles(directory=STATIC_PATH), name=STATIC_DIRNAME)


# Bind the database backend at import time, exactly as before the split -- but
# not when the environment names a store, because then the caller wants
# `store_app` and this module was only reached by an incidental attribute look-up.
if not os.environ.get("REFGET_STORE_URL") and not os.environ.get("REFGET_STORE_PATH"):
    setup_backend(app, engine=RefgetDBAgent().engine)
