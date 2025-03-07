import logging

from fastapi import FastAPI, Depends
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from refget import create_refget_router, get_dbagent
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from .const import ALL_VERSIONS, STATIC_PATH, STATIC_DIRNAME
from .examples import *

global _LOGGER
_LOGGER = logging.getLogger(__name__)

for key, value in ALL_VERSIONS.items():
    _LOGGER.info(f"{key}: {value}")

app = FastAPI(
    title="Sequence Collections API",
    description="An API providing metadata such as names, lengths, and other values for collections of reference sequences",
    version=ALL_VERSIONS["seqcolapi_version"],
)

origins = ["*"]

app.add_middleware(  # This is a public API, so we allow all origins
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is where the magic happens
refget_router = create_refget_router(sequences=False, pangenomes=False)
print(refget_router)
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
async def generic_exception_handler(request: Request, exc: Exception):
    raise HTTPException(status_code=404, detail=str(exc))


@app.get("favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(f"/static/favicon.ico")


@app.get("/", summary="Home page", tags=["General endpoints"], response_class=HTMLResponse)
async def index(request: Request):
    """
    Returns a landing page HTML with the server resources ready to download. No inputs required.
    """
    with open(f"{STATIC_PATH}/index.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)


@app.get("/service-info", summary="GA4GH service info", tags=["General endpoints"])
async def service_info(dbagent=Depends(get_dbagent)):
    ret = {
        "id": "org.databio.seqcolapi",
        "name": "Sequence collections",
        "type": {
            "group": "org.ga4gh",
            "artifact": "refget.seqcol",
            "version": ALL_VERSIONS["seqcol_spec_version"],
        },
        "description": "An API providing metadata such as names, lengths, and other values for collections of reference sequences",
        "organization": {"name": "Databio Lab", "url": "https://databio.org"},
        "contactUrl": "https://github.com/refgenie/refget/issues",
        "documentationUrl": "https://seqcolapi.databio.org",
        "updatedAt": "2025-02-20T00:00:00Z",
        "environment": "dev",
        "version": ALL_VERSIONS["seqcolapi_version"],
        "seqcol": {"schema": dbagent.schema_dict, "sorted_name_length_pairs": True},
    }
    return JSONResponse(content=ret)


# Mount statics after other routes for lower precedence
app.mount(f"/", StaticFiles(directory=STATIC_PATH), name=STATIC_DIRNAME)


def create_global_dbagent():
    """
    Create a global database agent for use in the app.
    """
    from refget.agents import RefgetDBAgent

    global dbagent
    dbagent = RefgetDBAgent()  # Configured via env vars
    return dbagent


if __name__ != "__main__":
    app.state.dbagent = create_global_dbagent()
