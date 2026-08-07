"""Plain-pydantic HTTP response bodies for the sequence collections API.

These live here, and not in :mod:`refget.models`, purely so that they can be
imported without a database. ``refget.models`` is the *database* module: it
imports sqlmodel and sqlalchemy at module level and therefore requires
``pip install 'refget[db]'``. The types below are ordinary
``pydantic.BaseModel`` subclasses -- they describe what goes over the wire, not
what is stored -- so making :mod:`refget.router` depend on them costs nothing.

That is what lets the store-backed app (``refget.seqcolapi.create_seqcol_app``,
``uvicorn refget.seqcolapi.main:store_app``) run on ``refget[seqcolapi]``
alone, with no sqlmodel, sqlalchemy or psycopg2 anywhere in the environment.
Before this split, ``refget.router`` reached sqlalchemy transitively through
``refget.models`` and dragged the whole ORM into a deployment that never
touches PostgreSQL.

Keep this module free of sqlmodel/sqlalchemy imports. ``refget.models``
re-exports every name defined here, so existing
``from refget.models import Similarities`` code keeps working.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

__all__ = [
    "PaginationResult",
    "ResultsSequenceCollections",
    "Similarities",
    "PaginatedDigestList",
]


class PaginationResult(BaseModel):
    page: int = 0
    page_size: int = 10
    total: int


class ResultsSequenceCollections(BaseModel):
    """
    Sequence collection results with pagination
    """

    pagination: PaginationResult
    results: Dict[str, dict]


class Similarities(BaseModel):
    """
    Model to contain results from similarities calculations
    """

    similarities: List[Dict[str, Any]]
    pagination: PaginationResult
    reference_digest: Optional[str] = None


class PaginatedDigestList(BaseModel):
    """Paginated list of digests, used by list endpoints"""

    pagination: PaginationResult
    results: List[str]
