# import henge
import json
import logging
import os
import sys
import uvicorn
import yacman

from fastapi import Body, FastAPI, Response, Depends
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse, FileResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from typing import Union

from .const import *
from .scconf import RDBDict
from .examples import *

from refget import format_itemwise
from yacman import select_config, FutureYAMLConfigManager as YAMLConfigManager


class SeqColConf(YAMLConfigManager):
    pass


global _LOGGER

_LOGGER = logging.getLogger(__name__)

templates = Jinja2Templates(directory=TEMPLATES_PATH)

for key, value in ALL_VERSIONS.items():
    _LOGGER.info(f"{key}: {value}")


app = FastAPI(
    title="Sequence Collections API",
    description="An API providing metadata such as names, lengths, and other values for collections of reference sequences",
    version=seqcolapi_version,
)

from refget import create_refget_router, get_dbagent

# This is where the magic happens
app.include_router(create_refget_router(sequences=False, pangenomes=False))

origins = ["*"]

app.add_middleware(  # This is a public API, so we allow all origins
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Catch-all error handler for any uncaught exceptions, return a 500 error with detailed information
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return await http_exception_handler(request, HTTPException(status_code=500, detail=str(exc)))  # Pass it to HTTP handler

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


@app.get("/", summary="Home page", tags=["General endpoints"])
async def index(request: Request):
    """
    Returns a landing page HTML with the server resources ready to download. No inputs required.
    """
    templ_vars = {"request": request, "openapi_version": app.openapi()["openapi"]}
    _LOGGER.debug("merged vars: {}".format(dict(templ_vars, **ALL_VERSIONS)))
    return templates.TemplateResponse("index.html", dict(templ_vars, **ALL_VERSIONS))


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
        "contactUrl": "https://github.com/refgenie/seqcol/issues",
        "documentationUrl": "https://seqcolapi.databio.org",
        "updatedAt": "2021-03-01T00:00:00Z",
        "environment": "dev",
        "version": ALL_VERSIONS["seqcolapi_version"],
        "seqcol": {"schema": dbagent.schema_dict, "sorted_name_length_pairs": True},
    }
    return JSONResponse(content=ret)


# Mount statics after other routes for lower precedence
app.mount(f"/", StaticFiles(directory=STATIC_PATH), name=STATIC_DIRNAME)


# def create_globals(scconf: yacman.YAMLConfigManager):
#     """
#     Create global variables for the app to use.
#     """
#     print(scconf)
#     _LOGGER.info(f"Connecting to database... {scconf.exp['database']['host']}")
#     global schenge

#     pgdb = RDBDict(
#         db_name=scconf.exp["database"]["name"],
#         db_user=scconf.exp["database"]["user"],
#         db_password=scconf.exp["database"]["password"],
#         db_host=scconf.exp["database"]["host"],
#         db_port=scconf.exp["database"]["port"],
#         db_table=scconf.exp["database"]["table"],
#     )
#     _LOGGER.info(f"Using schema: {scconf['schemas']}")
#     schenge = SeqColHenge(
#         database=pgdb,
#         schemas=scconf["schemas"],
#     )
#     return schenge


def create_global_dbagent():
    from refget.agents import RefgetDBAgent

    global dbagent
    dbagent = RefgetDBAgent()  # Configured via env vars
    return dbagent


def main(injected_args=None):
    # Entry point for running from console_scripts, installed package
    parser = build_parser()
    # parser = logmuse.add_logging_options(parser)
    args = parser.parse_args()
    if injected_args:
        args.__dict__.update(injected_args)
    if not args.command:
        parser.print_help()
        print("No subcommand given")
        sys.exit(1)

    # _LOGGER = logmuse.logger_via_cli(args, make_root=True)
    _LOGGER.info(f"args: {args}")
    # if "config" in args and args.config is not None:
    #     scconf = SeqColConf.from_yaml_file(args.config)
    #     create_globals(scconf)
    #     app.state.schenge = schenge
    #     app.state.dbagent = dbagent
    #     port = args.port or scconf.exp["server"]["port"]
    #     _LOGGER.info(f"Running on port {port}")
    #     uvicorn.run(app, host=scconf.exp["server"]["host"], port=port)
    # else:
    create_global_dbagent()
    app.state.dbagent = dbagent


if __name__ != "__main__":
    create_global_dbagent()
    app.state.dbagent = dbagent
