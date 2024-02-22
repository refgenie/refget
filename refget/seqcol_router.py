"""
This module contains the FastAPI router for the sequence collection API.
It is designed to be attached to a FastAPI app instance, and provides
endpoints for retrieving and comparing sequence collections.

To use, first import it, then attach it to the app,
then attach the schenge to the app state, like this:

from refget import seqcol_router
app.include_router(seqcol_router, prefix="/seqcol")
app.state.schenge = schenge
"""

import henge
import logging

from fastapi import APIRouter, Response, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Union

from .examples import *

_LOGGER = logging.getLogger(__name__)

seqcol_router = APIRouter()


async def get_schenge(request: Request):
    """Dependency to get the schenge from the app state"""
    return request.app.state.schenge


@seqcol_router.get("/test")
async def test(schenge=Depends(get_schenge)):
    return str(schenge)


@seqcol_router.get(
    "/sequence/{digest}",
    summary="Retrieve raw sequence via refget protocol",
    tags=["Refget endpoints"],
)
async def refget(request: Request, digest: str = example_sequence):
    schenge = request.app.state.schenge
    return Response(content=schenge.refget(digest))


@seqcol_router.get(
    "/collection/{digest}",
    summary="Retrieve a sequence collection",
    tags=["Retrieving sequence collections"],
)
async def collection(
    schenge=Depends(get_schenge),
    digest: str = example_digest,
    level: Union[int, None] = None,
    collated: bool = True,
):
    print("Retrieving collection")
    print(str(schenge))
    if level == None:
        level = 2
    if level > 2:
        raise HTTPException(
            status_code=400,
            detail="Error: recursion > 1 disabled. Use the /refget server to retrieve sequences.",
        )
    try:
        csc = schenge.retrieve(digest, reclimit=level - 1)
    except henge.NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    try:
        if not collated:
            if len(csc["lengths"]) > 10000:
                raise HTTPException(
                    status_code=413,
                    detail="This server won't decollate collections with > 10000 sequences",
                )
            else:
                return JSONResponse(content=format_itemwise(csc))
        else:
            return JSONResponse(content=csc)
    except:
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )


@seqcol_router.get(
    "/comparison/{digest1}/{digest2}",
    summary="Compare two sequence collections hosted on the server",
    tags=["Comparing sequence collections"],
)
async def compare_2_digests(
    schenge=Depends(get_schenge),
    digest1: str = example_digest_hg38,
    digest2: str = example_digest_hg38_primary,
):
    _LOGGER.info("Compare called")
    result = {}
    result["digests"] = {"a": digest1, "b": digest2}
    try:
        result.update(schenge.compare_digests(digest1, digest2))
    except henge.NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return JSONResponse(result)


@seqcol_router.post(
    "/comparison/{digest1}",
    summary="Compare a local sequence collection to one on the server",
    tags=["Comparing sequence collections"],
)
async def compare_1_digest(
    schenge=Depends(get_schenge), digest1: str = example_digest_hg38, B: dict = example_hg38_sc
):
    _LOGGER.info(f"digest1: {digest1}")
    _LOGGER.info(f"B: {B}")
    A = schenge.retrieve(digest1, reclimit=1)
    return JSONResponse(schenge.compat_all(A, B))


@seqcol_router.get(
    "/list-by-offset",
    summary="List sequence collections on the server",
    tags=["Listing sequence collections"],
)
async def list_collections_by_offset(
    schenge=Depends(get_schenge), limit: int = 100, offset: int = 0
):
    return JSONResponse(schenge.list_by_offset(limit=limit, offset=offset))


@seqcol_router.get(
    "/list",
    summary="List sequence collections on the server",
    tags=["Listing sequence collections"],
)
async def list_collections_by_token(
    schenge=Depends(get_schenge), page_size: int = 100, cursor: str = None
):
    return JSONResponse(schenge.list(page_size=page_size, cursor=cursor))
