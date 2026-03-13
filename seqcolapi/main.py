import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlmodel import Session, select
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from refget.agents import RefgetDBAgent
from refget.const import HUMANS_SAMPLE_LIST, MOUSE_SAMPLES_LIST
from refget.models import HumanReadableNames
from refget.router import _ROUTER_CONFIG, _SAMPLE_DIGESTS, create_refget_router

from .const import ALL_VERSIONS, STATIC_DIRNAME, STATIC_PATH
from .examples import *

global _LOGGER
_LOGGER = logging.getLogger(__name__)

for key, value in ALL_VERSIONS.items():
    _LOGGER.info(f"{key}: {value}")


@asynccontextmanager
async def lifespan_loader(app):
    """
    Lifespan event to pre-load sample names and their digests
    """
    _LOGGER.info("Starting lifespan: Loading sample data...")

    # Initialize database agent and store in app state
    dbagent = RefgetDBAgent()
    app.state.dbagent = dbagent
    app.state.backend = dbagent  # RefgetDBAgent satisfies SeqColBackend

    species_samples = {"human": HUMANS_SAMPLE_LIST, "mouse": MOUSE_SAMPLES_LIST}

    for species, sample_names in species_samples.items():
        try:
            _LOGGER.info(f"Loading {len(sample_names)} sample names for {species}")

            with Session(dbagent.engine) as session:
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
        "schema": dbagent.schema_dict,
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


def create_global_dbagent():
    """
    Create a global database agent for use in the app.
    """
    global dbagent
    dbagent = RefgetDBAgent()  # Configured via env vars
    return dbagent


def create_store_app(store_path: str, remote: bool = False, cache_dir: str = "/tmp/seqcol_cache"):
    """Create a seqcolapi FastAPI app backed by a RefgetStore (no database).

    Args:
        store_path: Path to store on disk, or S3 URL for remote stores.
        remote: If True, open as a remote (S3) store.
        cache_dir: Local cache directory for remote stores.

    Returns:
        FastAPI app with store-backed seqcol endpoints.
    """
    from refget.backend import RefgetStoreBackend
    from refget.store import RefgetStore

    if remote:
        store = RefgetStore.open_remote(cache_dir, store_path)
    else:
        store = RefgetStore.on_disk(store_path)

    backend = RefgetStoreBackend(store.into_readonly())

    store_app = FastAPI(title="Sequence Collections API (Store-backed)")
    store_app.state.backend = backend
    router = create_refget_router(
        sequences=False, pangenomes=False, refget_store_url=store_path if remote else None
    )
    store_app.include_router(router)
    return store_app


if __name__ != "__main__":
    _dbagent = create_global_dbagent()
    app.state.dbagent = _dbagent
    app.state.backend = _dbagent  # RefgetDBAgent satisfies SeqColBackend
