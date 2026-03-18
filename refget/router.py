"""
This module contains the FastAPI router for the refget sequence collection API.
It is designed to be attached to a FastAPI app instance, and provides
endpoints for retrieving and comparing sequence collections.

This router does not supply the /service-info endpoint, which should be created
by the main app.

To use, import the router and setup_backend, then wire them up:

from refget.router import create_refget_router, setup_backend

router = create_refget_router(sequences=False, collections=True, pangenomes=False)
app.include_router(router, prefix="/seqcol")
setup_backend(app, store=my_store)       # RefgetStore backend (no database)
# OR: setup_backend(app, engine=engine)  # PostgreSQL via RefgetDBAgent
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from .backend import SeqColBackend
from .examples import *
from .models import PaginatedDigestList, PaginationResult, Similarities

_LOGGER = logging.getLogger(__name__)

# Import the global variable from the router
_SAMPLE_DIGESTS: dict[str, list[str]] = {}

# Router configuration exposed for service-info endpoints
_ROUTER_CONFIG: dict = {}


def setup_backend(app, store=None, engine=None):
    """Configure the seqcol backend on a FastAPI app.

    Pass a RefgetStore to serve from the store (no database needed).
    The store is used directly (not converted to readonly) so it can lazy-load collections.
    Pass a SQLAlchemy engine to serve from PostgreSQL via RefgetDBAgent.
    """
    if store is not None:
        from .backend import RefgetStoreBackend

        app.state.backend = RefgetStoreBackend(store)
    elif engine is not None:
        from .agents import RefgetDBAgent

        dbagent = RefgetDBAgent(engine=engine)
        app.state.dbagent = dbagent
        app.state.backend = dbagent
    else:
        raise ValueError("setup_backend requires either store or engine")


async def get_backend(request: Request) -> SeqColBackend:
    """Get the SeqColBackend from the app state."""
    return request.app.state.backend


async def get_dbagent(request: Request):
    """Get the RefgetDBAgent for DB-only endpoints. Returns None if not configured."""
    dbagent = getattr(request.app.state, "dbagent", None)
    if dbagent is None:
        raise HTTPException(status_code=501, detail="This endpoint requires database backend")
    return dbagent


def create_refget_router(
    sequences: bool = False,
    collections: bool = True,
    pangenomes: bool = False,
    fasta_drs: bool = False,
    compliance: bool = True,
    refget_store_url: str = None,
) -> APIRouter:
    """
    Create a FastAPI router for the sequence collection API.
    This router provides endpoints for retrieving and comparing sequence collections.
    You can choose which endpoints to include by setting the sequences, collections,
    pangenomes, or fasta_drs flags.

    Args:
        sequences (bool): Include sequence endpoints
        collections (bool): Include sequence collection endpoints
        pangenomes (bool): Include pangenome endpoints
        fasta_drs (bool): Include FASTA DRS endpoints
        refget_store_url (str): URL of backing RefgetStore (e.g., s3://bucket/store/)

    Returns:
        (APIRouter): A FastAPI router with the specified endpoints

    Examples:
        ```
        app.include_router(create_refget_router(fasta_drs=True), prefix="/seqcol")
        ```
    """
    # Store config for service-info discovery
    _ROUTER_CONFIG["fasta_drs"] = fasta_drs
    _ROUTER_CONFIG["refget_store_url"] = refget_store_url

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
    if fasta_drs:
        _LOGGER.info("Adding FASTA DRS endpoints...")
        refget_router.include_router(fasta_drs_router, prefix="/fasta")
    if compliance:
        _LOGGER.info("Adding compliance endpoints...")
        refget_router.include_router(compliance_router)
    return refget_router


seq_router = APIRouter()


@seq_router.get(
    "/sequence/{sequence_digest}",
    summary="Retrieve raw sequence via original refget protocol",
    include_in_schema=True,
    tags=["Retrieving data"],
)
async def sequence(
    sequence_digest: str = example_sequence,
    start: int | None = Query(None, description="Start position (0-based, inclusive)"),
    end: int | None = Query(None, description="End position (0-based, exclusive)"),
    dbagent=Depends(get_dbagent),
):
    return Response(content=dbagent.seq.get(sequence_digest, start, end), media_type="text/plain")


@seq_router.get(
    "/sequence/{sequence_digest}/metadata",
    summary="Retrieve metadata for a sequence",
    tags=["Retrieving data"],
)
async def seq_metadata(sequence_digest: str = example_sequence, dbagent=Depends(get_dbagent)):
    raise HTTPException(status_code=501, detail="Metadata retrieval not yet implemented.")


seqcol_router = APIRouter()


@seqcol_router.get(
    "/collection/{collection_digest}",
    summary="Retrieve a sequence collection",
    tags=["Retrieving data"],
)
async def collection(
    collection_digest: str = example_collection_digest,
    level: int | None = Query(None, description="Recursion depth (1 or 2)", ge=1, le=2),
    collated: bool = Query(True, description="Return collated format (arrays) vs itemwise"),
    attribute: str | None = Query(
        None, description="Return only this attribute (e.g., 'names', 'lengths')"
    ),
    backend=Depends(get_backend),
):
    if level is None:
        level = 2
    if level > 2:
        raise HTTPException(
            status_code=400,
            detail="Error: level > 2 disabled. Use a refget sequences server to retrieve sequences.",
        )
    try:
        if not collated:
            return backend.get_collection_itemwise(collection_digest, limit=10000)
        if attribute:
            return backend.get_collection_attribute(collection_digest, attribute)
        return backend.get_collection(collection_digest, level=level)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@seqcol_router.get(
    "/attribute/collection/{attribute_name}/{attribute_digest}",
    summary="Retrieve a single attribute of a sequence collection",
    tags=["Retrieving data"],
)
async def attribute(
    attribute_name: str = "names",
    attribute_digest: str = example_attribute_digest,
    backend=Depends(get_backend),
):
    try:
        return backend.get_attribute(attribute_name, attribute_digest)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Error: attribute not found. Check the attribute and try again.",
        )
    except AttributeError:
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
    collection_digest1: str = example_digest_hg38,
    collection_digest2: str = example_digest_hg38_primary,
    backend=Depends(get_backend),
):
    _LOGGER.info("Comparing two digests...")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": collection_digest2}
    try:
        result.update(backend.compare_digests(collection_digest1, collection_digest2))
    except ValueError as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return result


@seqcol_router.post(
    "/similarities/{collection_digest}",
    summary="Calculate Jaccard similarities between a sequence collection and all others",
    tags=["Comparing sequence collections"],
    response_model=Similarities,
)
async def calc_similarities(
    collection_digest: str,
    species: str = Query("human", description="Species/group to filter by"),
    page_size: int = Query(50, description="Number of results per page"),
    page: int = Query(0, description="Page number (0-indexed)"),
    backend=Depends(get_backend),
) -> Similarities:
    _LOGGER.info("Calculating Jaccard similarities...")
    try:
        seqcolA = backend.get_collection(collection_digest, level=2)
    except (ValueError, KeyError):
        raise HTTPException(status_code=404, detail="Collection not found")

    return await _compute_similarities(seqcolA, species, page_size, page, backend)


@seqcol_router.post(
    "/similarities/",
    summary="Calculate Jaccard similarities between input sequence collection and all collections",
    tags=["Comparing sequence collections"],
    response_model=Similarities,
)
async def calc_similarities_from_json(
    seqcolA: dict,
    species: str = Query("human", description="Species/group to filter by"),
    page_size: int = Query(50, description="Number of results per page"),
    page: int = Query(0, description="Page number (0-indexed)"),
    backend=Depends(get_backend),
) -> Similarities:
    return await _compute_similarities(seqcolA, species, page_size, page, backend)


async def _compute_similarities(
    seqcolA: dict,
    species: str,
    page_size: int,
    page: int,
    backend: SeqColBackend,
) -> Similarities:
    """Shared implementation for both similarity endpoints."""
    try:
        # Get target digests for species if configured
        target_digests = _SAMPLE_DIGESTS.get(species.lower()) if _SAMPLE_DIGESTS else None

        if not _SAMPLE_DIGESTS:
            raise HTTPException(
                status_code=501,
                detail="Similarities not configured. No scom_config.json found.",
            )
        if not target_digests:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid species '{species}'. Choose from: {list(_SAMPLE_DIGESTS.keys())}",
            )

        result = backend.compute_similarities(
            seqcolA, page=page, page_size=page_size, target_digests=target_digests
        )
        return Similarities(**result)
    except Exception as e:
        _LOGGER.debug(f"Error computing similarities: {e}")
        raise HTTPException(status_code=500, detail="Error calculating similarities")


@seqcol_router.post(
    "/comparison/{collection_digest1}",
    summary="Compare a local sequence collection to one on the server",
    tags=["Comparing sequence collections"],
)
async def compare_1_digest(
    collection_digest1: str = example_digest_hg38,
    seqcolB: dict = example_hg38_sc,
    backend=Depends(get_backend),
):
    _LOGGER.info("Comparing one digests and one POSTed seqcol...")
    _LOGGER.info(f"digest1: {collection_digest1}")
    _LOGGER.info(f"seqcolB: {seqcolB}")
    result = {}
    result["digests"] = {"a": collection_digest1, "b": "POSTed seqcol"}
    try:
        result.update(backend.compare_digest_with_level2(collection_digest1, seqcolB))
    except ValueError as e:
        _LOGGER.debug(e)
        raise HTTPException(
            status_code=404,
            detail="Error: collection not found. Check the digest and try again.",
        )
    return result


@seqcol_router.get(
    "/list/collection",
    summary="List sequence collections on the server",
    tags=["Discovering data"],
    response_model=PaginatedDigestList,
)
async def list_collections_by_offset(
    page_size: int = Query(100, description="Number of results per page"),
    page: int = Query(0, description="Page number (0-indexed)"),
    names: str | None = Query(None, description="Filter by names attribute digest"),
    lengths: str | None = Query(None, description="Filter by lengths attribute digest"),
    sequences: str | None = Query(None, description="Filter by sequences attribute digest"),
    name_length_pairs: str | None = Query(None, description="Filter by name_length_pairs digest"),
    sorted_sequences: str | None = Query(None, description="Filter by sorted_sequences digest"),
    backend=Depends(get_backend),
):
    # Build filters from explicit parameters
    filters = {
        k: v
        for k, v in {
            "names": names,
            "lengths": lengths,
            "sequences": sequences,
            "name_length_pairs": name_length_pairs,
            "sorted_sequences": sorted_sequences,
        }.items()
        if v is not None
    }

    try:
        res = backend.list_collections(page=page, page_size=page_size, filters=filters or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Normalize results to digest strings (DB backend returns model objects)
    res["results"] = [x.digest if hasattr(x, "digest") else x for x in res["results"]]
    return res


@seqcol_router.get(
    "/list/attributes/{attribute}",
    summary="List values of attributes held on the server",
    tags=["Discovering data"],
    response_model=PaginatedDigestList,
)
async def list_attributes(
    backend=Depends(get_backend),
    attribute: str = "names",
    page_size: int = Query(100, description="Number of results per page"),
    page: int = Query(0, description="Page number (0-indexed)"),
):
    try:
        return backend.list_attributes(attribute, page=page, page_size=page_size)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Error: attribute not found. Check the attribute and try again.",
        )


pangenome_router = APIRouter()


@pangenome_router.get(
    "/list/pangenome",
    summary="List pangenomes on the server, paged by offset",
    tags=["Discovering data"],
    include_in_schema=True,
    response_model=PaginatedDigestList,
)
async def list_cpangenomes_by_offset(
    dbagent=Depends(get_dbagent),
    page_size: int = Query(100, description="Number of results per page"),
    page: int = Query(0, description="Page number (0-indexed)"),
):
    res = dbagent.pangenome.list_by_offset(limit=page_size, offset=page * page_size)
    res["results"] = [x.digest for x in res["results"]]
    return res


@pangenome_router.get(
    "/pangenome/{pangenome_digest}",
    summary="Retrieve a pangenome",
    tags=["Retrieving data"],
    include_in_schema=True,
)
async def pangenome(
    dbagent=Depends(get_dbagent),
    pangenome_digest: str = example_pangenome_digest,
    level: int | None = Query(None, description="Recursion depth (1-4)", ge=1, le=4),
    collated: bool = Query(True, description="Return collated format (arrays) vs itemwise"),
):
    if level is None:
        level = 2
    try:
        if not collated:
            return dbagent.pangenome.get(pangenome_digest, return_format="itemwise")
        if level == 1:
            return dbagent.pangenome.get(pangenome_digest, return_format="level1")
        if level == 2:
            return dbagent.pangenome.get(pangenome_digest, return_format="level2")
        if level == 3:
            return dbagent.pangenome.get(pangenome_digest, return_format="level3")
        if level == 4:
            return dbagent.pangenome.get(pangenome_digest, return_format="level4")
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


fasta_drs_router = APIRouter()


@fasta_drs_router.get(
    "/objects/{object_id}",
    summary="Get DRS object by ID",
    tags=["FASTA DRS"],
)
async def get_drs_object(
    object_id: str,
    dbagent=Depends(get_dbagent),
):
    """GA4GH DRS endpoint to retrieve object metadata"""
    try:
        drs_obj = dbagent.fasta_drs.get(object_id)
        return drs_obj.to_response(base_uri="drs://seqcolapi.databio.org")
    except ValueError:
        raise HTTPException(status_code=404, detail="Object not found")


@fasta_drs_router.get(
    "/objects/{object_id}/access/{access_id}",
    summary="Get access URL for DRS object",
    tags=["FASTA DRS"],
    include_in_schema=False,  # Hidden: only needed when using access_id instead of access_url
)
async def get_drs_access_url(
    object_id: str,
    access_id: str,
    dbagent=Depends(get_dbagent),
):
    """
    GA4GH DRS endpoint to get access URL.

    This endpoint is used when access methods specify an access_id instead of
    a direct access_url. It allows for dynamic URL generation (e.g., signed URLs)
    or additional authorization checks.

    Note: If access methods provide access_url directly, clients should use
    those URLs and don't need to call this endpoint.
    """
    try:
        drs_obj = dbagent.fasta_drs.get(object_id)
        for method in drs_obj.access_methods:
            # Handle both dict and object access
            method_access_id = (
                method.get("access_id") if isinstance(method, dict) else method.access_id
            )
            method_access_url = (
                method.get("access_url") if isinstance(method, dict) else method.access_url
            )

            if method_access_id == access_id:
                return method_access_url
        raise HTTPException(status_code=404, detail="Access ID not found")
    except ValueError:
        raise HTTPException(status_code=404, detail="Object not found")


@fasta_drs_router.get(
    "/service-info",
    summary="FASTA DRS service info",
    tags=["FASTA DRS"],
)
async def drs_service_info():
    """GA4GH DRS service-info endpoint"""
    return {
        "id": "org.databio.seqcolapi.drs",
        "name": "SeqCol API DRS Service",
        "type": {"group": "org.ga4gh", "artifact": "drs", "version": "1.5.0"},
        "description": "DRS service for FASTA files indexed by refget sequence collection digests",
        "organization": {"name": "databio", "url": "https://databio.org"},
        "version": "1.0.0",
    }


@fasta_drs_router.get(
    "/objects/{object_id}/index",
    summary="Get FAI index for FASTA file",
    tags=["FASTA DRS"],
)
async def get_fasta_index(
    object_id: str,
    dbagent=Depends(get_dbagent),
):
    """
    Get the FAI index data for a FASTA file.

    Returns index data that can be combined with seqcol names/lengths
    to reconstruct a complete .fai file.
    """
    try:
        drs_obj = dbagent.fasta_drs.get(object_id)
        return {
            "line_bases": drs_obj.line_bases,
            "extra_line_bytes": drs_obj.extra_line_bytes,
            "offsets": drs_obj.offsets,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Object not found")


compliance_router = APIRouter()


@compliance_router.get(
    "/compliance/run",
    summary="Run compliance checks against a seqcol server",
    tags=["Compliance"],
)
def run_compliance_endpoint(
    request: Request,
    target_url: str | None = Query(
        None, description="Target server URL to test (defaults to self)"
    ),
):
    """
    Run GA4GH SeqCol compliance structure tests against a server.

    Only runs structure tests (service-info, list, pagination, collection structure).
    Content tests that require specific test data are not included.

    If no target_url is provided, tests run against this server.
    """
    from .compliance import run_compliance

    if target_url is None:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host", request.url.netloc)
        target_url = f"{scheme}://{host}"

    return run_compliance(target_url)


@compliance_router.get(
    "/compliance/stream",
    summary="Stream compliance checks via Server-Sent Events",
    tags=["Compliance"],
)
def stream_compliance_endpoint(
    request: Request,
    target_url: str | None = Query(
        None, description="Target server URL to test (defaults to self)"
    ),
):
    """
    Stream compliance check results in real-time via Server-Sent Events.

    Each event contains a JSON object with type "start", "result", or "done".
    """
    from .compliance import run_compliance_stream

    if target_url is None:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host", request.url.netloc)
        target_url = f"{scheme}://{host}"

    def event_stream():
        for data in run_compliance_stream(target_url):
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
