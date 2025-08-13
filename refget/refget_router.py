"""
This module contains the FastAPI router for the sequence collection API.
It is designed to be attached to a FastAPI app instance, and provides
endpoints for retrieving and comparing sequence collections.

To use, first import it, then attach it to the app,
then create a dbagent object to connect to the database,
and attach it to the app state like this:

from refget import create_refget_router
from refget.agents import RefgetDBAgent

refget_router = create_refget_router(sequences=False, collections=True, pangenomes=False)
app.include_router(refget_router, prefix="/seqcol")
app.state.dbagent = RefgetDBAgent()
"""

import logging

from fastapi import APIRouter, Response, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from .models import Similarities, PaginationResult

from .examples import *

from henge import NotFoundException

_LOGGER = logging.getLogger(__name__)

# Import the global variable from the router
_SAMPLE_DIGESTS = {}


# dbagent is a RefgetDBAgent, which handles connection to the POSTGRES database
async def get_dbagent(request: Request):
    return request.app.state.dbagent


def create_refget_router(
    sequences: bool = False, collections: bool = True, pangenomes: bool = False
):
    """
    Create a FastAPI router for the sequence collection API.
    This router provides endpoints for retrieving and comparing sequence collections.
    You can choose which endpoints to include by setting the sequences, collections,
    or pangenomes flags.

    Args:
        sequences (bool): Include sequence endpoints
        collections (bool): Include sequence collection endpoints
        pangenomes (bool): Include pangenome endpoints

    Returns:
        (APIRouter): A FastAPI router with the specified endpoints

    Examples:
        ```
        app.include_router(create_refget_router(sequences=False, pangenomes=False))
        ```
    """

    refget_router = APIRouter()
    if sequences:
        _LOGGER.info("Adding sequence endpoints...")
        refget_router.include_router(seq_router)
    if collections:
        _LOGGER.info("Adding collection endpoints...")
        refget_router.include_router(seqcol_router)
    if pangenomes:
        _LOGGER.info("Adding pangenome endpoints...")
        refget_router.include_router(pangenome_router)
    return refget_router


seq_router = APIRouter()


@seq_router.get(
    "/sequence/{sequence_digest}",
    summary="Retrieve raw sequence via original refget protocol",
    include_in_schema=True,
    tags=["Retrieving data"],
)
async def sequence(
    dbagent=Depends(get_dbagent),
    sequence_digest: str = example_sequence,
    start: int = None,
    end: int = None,
):
    return Response(content=dbagent.seq.get(sequence_digest, start, end), media_type="text/plain")


@seq_router.get(
    "/sequence/{sequence_digest}/metadata",
    summary="Retrieve metadata for a sequence",
    tags=["Retrieving data"],
)
async def seq_metadata(dbagent=Depends(get_dbagent), sequence_digest: str = example_sequence):
    return NotImplementedError("Metadata retrieval not yet implemented.")
    return JSONResponse(dbagent.seq.get_metadata(sequence_digest))


seqcol_router = APIRouter()


@seqcol_router.get(
    "/collection/{collection_digest}",
    summary="Retrieve a sequence collection",
    tags=["Retrieving data"],
)
async def collection(
    dbagent=Depends(get_dbagent),
    collection_digest: str = example_collection_digest,
    level: int | None = None,
    collated: bool = True,
    attribute: str = None,
):
    if level == None:
        level = 2
    if level > 2:
        raise HTTPException(
            status_code=400,
            detail="Error: level > 2 disabled. Use a refget sequences server to retrieve sequences.",
        )
    try:
        if not collated:
            return JSONResponse(
                dbagent.seqcol.get(
                    collection_digest, return_format="itemwise", itemwise_limit=10000
                )
            )
        if attribute:
            return JSONResponse(dbagent.seqcol.get(collection_digest, attribute=attribute))
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
    dbagent=Depends(get_dbagent),
    attribute: str = "names",
    attribute_digest: str = example_attribute_digest,
):
    try:
        return JSONResponse(dbagent.attribute.get(attribute, attribute_digest))
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail="Error: attribute not found. Check the attribute and try again.",
        )
    except AttributeError as e:
        raise HTTPException(
            status_code=404,
            detail="Digest not found. Check the digest and try again.",
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
    _LOGGER.info("Comparing two digests...")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": collection_digest2}
    try:
        result.update(dbagent.compare_digests(collection_digest1, collection_digest2))
    except NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return JSONResponse(result)


@seqcol_router.post(
    "/similarities/{collection_digest}",
    summary="Calculate Jaccard similarities between a single sequence collection in the database and all other collections in the database (by species)",
    tags=["Comparing sequence collections"],
    response_model=Similarities,
)
async def calc_similarities(
    collection_digest: str,
    species: str = "human",
    page_size: int = 50,
    page: int = 0,
    dbagent=Depends(get_dbagent),
) -> Similarities:
    _LOGGER.info("Calculating Jaccard similarities...")
    try:
        seqcolA = dbagent.seqcol.get(digest=collection_digest)

        # Validate species parameter
        if species.lower() not in _SAMPLE_DIGESTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid species '{species}'. Choose from: {list(_SAMPLE_DIGESTS.keys())}",
            )

        # Get pre-loaded digests for the species
        target_digests = _SAMPLE_DIGESTS[species.lower()]

        if not target_digests:
            _LOGGER.warning(
                f"No pre-loaded digests found for {species}, returning {page_size} comparisons"
            )
            target_digests = None
        else:
            _LOGGER.info(f"Using {len(target_digests)} pre-loaded digests for {species}")

        # Use the modified get_many_level2_offset function with target_digests filter
        results = dbagent.seqcol.get_many_level2_offset(
            limit=page_size, offset=page * page_size, target_digests=target_digests
        )

        similarities = []
        for key in results.results.keys():
            human_readable_names = results.results[key]["human_readable_names"]
            jaccard_sims = dbagent.calc_similarities_seqcol_dicts(seqcolA, results.results[key])
            similarities.append(
                {
                    "digest": key,
                    "human_readable_names": human_readable_names,
                    "similarities": jaccard_sims,
                }
            )

        result = Similarities(
            similarities=similarities, pagination=results.pagination, reference_digest=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        _LOGGER.debug(f"Error in calc_similarities_from_json: {e}")
        raise HTTPException(status_code=500, detail="Error calculating similarities")

    return result


@seqcol_router.post(
    "/similarities/",
    summary="Calculate Jaccard similarities between input sequence collection and all collections in database",
    tags=["Comparing sequence collections"],
    response_model=Similarities,
)
async def calc_similarities_from_json(
    seqcolA: dict,
    species: str = "human",
    page_size: int = 50,
    page: int = 0,
    dbagent=Depends(get_dbagent),
) -> Similarities:
    """
    Calculate Jaccard similarities between input sequence collection and all collections in DB.
    Takes a JSON sequence collection directly instead of a digest.
    Take output from: refget digest-fasta "yourfasta.fa" -l 2 > myoutput.json

    Args:
        seqcolA: Input sequence collection dictionary
        species: Species to filter by ("human" or "mouse"), defaults to "human"
        page_size: Number of results per page
        page: Page number
        dbagent: Database agent dependency
    """
    _LOGGER.info(
        f"Calculating Jaccard similarities from input sequence collection for {species}..."
    )

    try:
        # Validate species parameter
        if species.lower() not in _SAMPLE_DIGESTS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid species '{species}'. Choose from: {list(_SAMPLE_DIGESTS.keys())}",
            )

        # Get pre-loaded digests for the species
        target_digests = _SAMPLE_DIGESTS[species.lower()]

        if not target_digests:
            _LOGGER.warning(f"No pre-loaded digests found for {species}")
            return Similarities(
                similarities=[],
                pagination=PaginationResult(page=page, page_size=page_size, total=0),
                reference_digest=None,
            )

        _LOGGER.info(f"Using {len(target_digests)} pre-loaded digests for {species}")

        # Use the modified get_many_level2_offset function with target_digests filter
        results = dbagent.seqcol.get_many_level2_offset(
            limit=page_size, offset=page * page_size, target_digests=target_digests
        )

        similarities = []
        for key in results.results.keys():
            human_readable_names = results.results[key]["human_readable_names"]
            jaccard_sims = dbagent.calc_similarities_seqcol_dicts(seqcolA, results.results[key])
            similarities.append(
                {
                    "digest": key,
                    "human_readable_names": human_readable_names,
                    "similarities": jaccard_sims,
                }
            )

        result = Similarities(
            similarities=similarities, pagination=results.pagination, reference_digest=None
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        _LOGGER.debug(f"Error in calc_similarities_from_json: {e}")
        raise HTTPException(status_code=500, detail="Error calculating similarities")

    return result


@seqcol_router.post(
    "/comparison/{collection_digest1}",
    summary="Compare a local sequence collection to one on the server",
    tags=["Comparing sequence collections"],
)
async def compare_1_digest(
    dbagent=Depends(get_dbagent),
    collection_digest1: str = example_digest_hg38,
    seqcolB: dict = example_hg38_sc,
):
    _LOGGER.info("Comparing one digests and one POSTed seqcol...")
    _LOGGER.info(f"digest1: {collection_digest1}")
    _LOGGER.info(f"seqcolB: {seqcolB}")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": "POSTed seqcol"}
    try:
        result.update(dbagent.compare_1_digest(collection_digest1, seqcolB))
    except NotFoundException as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return JSONResponse(result)


@seqcol_router.get(
    "/list/collections",
    summary="List sequence collections on the server",
    tags=["Discovering data"],
)
async def list_collections_by_offset(
    dbagent=Depends(get_dbagent), page_size: int = 100, page: int = 0
):

    res = dbagent.seqcol.list_by_offset(limit=page_size, offset=page * page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


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
    res = dbagent.attribute.search(
        attribute, attribute_digest, limit=page_size, offset=page * page_size
    )
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


@seqcol_router.get(
    "/list/attributes/{attribute}",
    summary="List values of attributes held on the server",
    tags=["Discovering data"],
)
async def list_attributes(
    dbagent=Depends(get_dbagent), attribute: str = "names", page_size: int = 100, page: int = 0
):
    try:
        res = dbagent.attribute.list(attribute, limit=page_size, offset=page * page_size)
        res["results"] = [x.digest for x in res["results"]]
        return JSONResponse(res)
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail="Error: attribute not found. Check the attribute and try again.",
        )


pangenome_router = APIRouter()


@pangenome_router.get(
    "/list/pangenomes",
    summary="List pangenomes on the server, paged by offset",
    tags=["Discovering data"],
    include_in_schema=True,
)
async def list_cpangenomes_by_offset(
    dbagent=Depends(get_dbagent), page_size: int = 100, page: int = 0
):
    res = dbagent.pangenome.list_by_offset(limit=page_size, offset=page * page_size)
    res["results"] = [x.digest for x in res["results"]]
    return JSONResponse(res)


@pangenome_router.get(
    "/pangenome/{pangenome_digest}",
    summary="Retrieve a pangenome",
    tags=["Retrieving data"],
    include_in_schema=True,
)
async def pangenome(
    dbagent=Depends(get_dbagent),
    pangenome_digest: str = example_pangenome_digest,
    level: int | None = None,
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
