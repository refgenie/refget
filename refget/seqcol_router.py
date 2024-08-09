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


# dbagent is a RefgetDBAgent

async def get_dbagent(request: Request):
    return request.app.state.dbagent


@seqcol_router.get(
    "/sequence/{sequence_digest}",
    summary="Retrieve raw sequence via original refget protocol",
    tags=["Retrieving data"],
)
async def refget(request: Request, sequence_digest: str = example_sequence):
    schenge = request.app.state.schenge
    raise HTTPException(
        status_code=400,
        detail="Error: this server does not support raw sequence retrieval. Use a refget server instead.",
    )
    # If you wanted to implement refget sequences, you would do it here
    return Response(content=schenge.refget(sequence_digest))


@seqcol_router.get(
    "/collection/{collection_digest}",
    summary="Retrieve a sequence collection",
    tags=["Retrieving data"],
)
async def collection(
    dbagent=Depends(get_dbagent),
    collection_digest: str = example_collection_digest,
    level: Union[int, None] = None,
    collated: bool = True,
):
    if level == None:
        level = 2
    if level > 2:
        raise HTTPException(
            status_code=400,
            detail="Error: recursion > 1 disabled. Use the /refget server to retrieve sequences.",
        )
    try:
        if not collated:
            return JSONResponse(dbagent.seqcol.get(collection_digest, return_format="itemwise"))
        if level == 1:
            return JSONResponse(dbagent.seqcol.get(collection_digest, return_format="level1"))
        if level == 2:
            return JSONResponse(dbagent.seqcol.get(collection_digest, return_format="level2"))
        return JSONResponse({"error": "Invalid level specified."})
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

@seqcol_router.get(
    "/attribute/collection/{attribute}/{attribute_digest}",
    summary="Retrieve a single attribute of a sequence collection",
    tags=["Retrieving data"],
)
async def attribute(
    dbagent=Depends(get_dbagent), attribute: str = "names", attribute_digest: str = example_digest
):
    return JSONResponse(dbagent.attribute.get(attribute, attribute_digest))




@seqcol_router.get(
    "/pangenome/{pangenome_digest}",
    summary="Retrieve a pangenome",
    tags=["Retrieving data"],
)
async def pangenome(
    dbagent=Depends(get_dbagent),
    pangenome_digest: str = example_pangenome_digest,
    level: Union[int, None] = None,
    collated: bool = True,
):
    if level == None:
        level = 2
    try:
        if not collated:
            return JSONResponse(dbagent.pangenome.get(pangenome_digest, return_format="itemwise"))
        if level == 1:
            return JSONResponse(dbagent.pangenome.get(pangenome_digest, return_format="level1"))
        if level == 2:
            return JSONResponse(dbagent.pangenome.get(pangenome_digest, return_format="level2"))
        if level == 3:
            return JSONResponse(dbagent.pangenome.get(pangenome_digest, return_format="level3"))
        if level == 4:
            return JSONResponse(dbagent.pangenome.get(pangenome_digest, return_format="level4"))
        if level > 4:
            raise HTTPException(
                status_code=400,
                detail="Error: recursion > 4 disabled. Use the /refget server to retrieve sequences.",
            )
        raise HTTPException(
            status_code=400,
            detail="Invalid level specified",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )



@seqcol_router.get(
    "/collection2/{collection_digest}",
    summary="Retrieve a sequence collection",
    tags=["Retrieving sequence collections"],
    include_in_schema=False,
)
async def collection2(
    schenge=Depends(get_schenge),
    collection_digest: str = example_digest,
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
        csc = schenge.retrieve(collection_digest, reclimit=level - 1)
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
    "/comparison/{collection_digest1}/{collection_digest2}",
    summary="Compare two sequence collections hosted on the server",
    tags=["Comparing sequence collections"],
)
async def compare_2_digests(
    dbagent=Depends(get_dbagent),
    collection_digest1: str = example_digest_hg38,
    collection_digest2: str = example_digest_hg38_primary,
):
    _LOGGER.info("Compare called")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": collection_digest2}
    try:
        result.update(dbagent.compare_digests(collection_digest1, collection_digest2))
    except henge.NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return JSONResponse(result)


@seqcol_router.get(
    "/comparison2/{collection_digest1}/{collection_digest2}",
    summary="Compare two sequence collections hosted on the server",
    tags=["Comparing sequence collections"],
    include_in_schema=False,
)
async def compare_2_digests2(
    schenge=Depends(get_schenge),
    collection_digest1: str = example_digest_hg38,
    collection_digest2: str = example_digest_hg38_primary,
):
    _LOGGER.info("Compare called")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": collection_digest2}
    try:
        result.update(schenge.compare_digests(collection_digest1, collection_digest2))
    except henge.NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return JSONResponse(result)


@seqcol_router.post(
    "/comparison/{collection_digest1}",
    summary="Compare a local sequence collection to one on the server",
    tags=["Comparing sequence collections"],
)
async def compare_1_digest(
    schenge=Depends(get_schenge),
    collection_digest1: str = example_digest_hg38,
    B: dict = example_hg38_sc,
):
    _LOGGER.info(f"digest1: {collection_digest1}")
    _LOGGER.info(f"B: {B}")
    A = schenge.retrieve(collection_digest1, reclimit=1)
    return JSONResponse(schenge.compat_all(A, B))



@seqcol_router.get(
    "/list/collections",
    summary="List sequence collections on the server",
    tags=["Discovering data"],
)
async def list_collections_by_offset(
    dbagent=Depends(get_dbagent), page_size: int = 100, page: int = 0
):
    res = dbagent.seqcol.list_by_offset(limit=page_size, offset=page*page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


# @seqcol_router.get(
#     "/list-by-cursor",
#     summary="List sequence collections on the server, paged by cursor",
#     tags=["Discovering data"],
# )
# async def list_collections_by_token(
#     dbagent=Depends(get_dbagent), page_size: int = 100, cursor: str = None
# ):
#     res = dbagent.seqcol.list(page_size=page_size, cursor=cursor)
#     res["results"] = [x.digest for x in res["results"]]
#     return JSONResponse(res)





@seqcol_router.get(
    "/list/collections/{attribute}/{attribute_digest}",
    summary="Filtered list of sequence collections that contain a given attribute",
    tags=["Discovering data"],
)
async def attribute_search(
    dbagent=Depends(get_dbagent),
    attribute: str = "names",
    attribute_digest: str = example_attribute_digest,
    page_size: int = 100,
    page: int = 0,
):
    # attr = dbagent.attribute.get(attribute, digest)
    res = dbagent.attribute.search(attribute, attribute_digest, limit=page_size, offset=page*page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


@seqcol_router.get(
    "/list/attributes/{attribute}",
    summary="List attributes on the server",
    tags=["Discovering data"],
)
async def list_attributes(
    dbagent=Depends(get_dbagent), attribute: str = "names", page_size: int = 100, page: int = 0
):
    res = dbagent.attribute.list(attribute, limit=page_size, offset=page*page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


@seqcol_router.get(
    "/list/pangenomes",
    summary="List pangenomes on the server, paged by offset",
    tags=["Discovering data"],
)
async def list_cpangenomes_by_offset(
    dbagent=Depends(get_dbagent), page_size: int = 100, page: int = 0
):
    res = dbagent.pangenome.list_by_offset(limit=page_size, offset=page*page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)



