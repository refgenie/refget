"""
Processing submodule - requires gtars for FASTA processing, digest computation,
and local RefgetStore operations.

This submodule will raise ImportError immediately if gtars is not installed.
"""
from ..const import GTARS_INSTALLED

if not GTARS_INSTALLED:
    raise ImportError(
        "The refget.processing module requires gtars. "
        "Install with: pip install gtars"
    )

# Only reached if gtars is available
from .store import RefgetStore, StorageMode, RetrievedSequence
from .digest import sha512t24u_digest, md5_digest, digest_fasta
from .fasta import fasta_to_digest, fasta_to_seqcol_dict, create_fasta_drs_object
from .bridge import seqcol_from_gtars

__all__ = [
    # Store
    "RefgetStore",
    "StorageMode",
    "RetrievedSequence",
    # Digest
    "sha512t24u_digest",
    "md5_digest",
    "digest_fasta",
    # FASTA
    "fasta_to_digest",
    "fasta_to_seqcol_dict",
    "create_fasta_drs_object",
    # Bridge
    "seqcol_from_gtars",
]
