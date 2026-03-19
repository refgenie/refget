"""
refget - GA4GH reference sequence and sequence collection tools.

Import from submodules:
    from refget.store import RefgetStore, digest_fasta, StorageMode, compute_fai, digest_sequence, SequenceCollection
    from refget.digests import sha512t24u_digest, md5_digest, ga4gh_digest
    from refget.utils import compare_seqcols, validate_seqcol, seqcol_digest
    from refget.clients import SequenceCollectionClient, FastaDrsClient
    from refget.router import create_refget_router
    from refget.agents import RefgetDBAgent
"""

from ._version import __version__
from .backend import RefgetStoreBackend, SeqColBackend
from .clients import SequenceCollectionClient
from .const import GTARS_INSTALLED
from .exceptions import InvalidSeqColError
from .store import (
    RefgetStore,
    SequenceCollection,
    StorageMode,
    compute_fai,
    digest_fasta,
    digest_sequence,
)
from .utils import canonical_str

__all__ = [
    "__version__",
    "InvalidSeqColError",
    "GTARS_INSTALLED",
    "canonical_str",
    "RefgetStore",
    "StorageMode",
    "digest_fasta",
    "compute_fai",
    "digest_sequence",
    "SequenceCollection",
    "SeqColBackend",
    "RefgetStoreBackend",
    "SequenceCollectionClient",
]
