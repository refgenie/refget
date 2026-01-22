# Project configuration, particularly for logging.

import logging

from .const import *
from .digest_functions import *
from .exceptions import InvalidSeqColError
from ._version import __version__

# utilities imports jsonschema (~60ms) - made lazy

# Heavy imports moved to lazy loading via __getattr__:
# - clients (requests ~51ms)
# - models (sqlmodel ~245ms)
# - refget functions (agents -> sqlmodel)


def __getattr__(name):
    """Lazy import for heavy modules to speed up CLI startup."""
    if name in ("SequenceClient", "SequenceCollectionClient", "PangenomeClient", "FastaDrsClient"):
        from .clients import SequenceClient, SequenceCollectionClient, PangenomeClient, FastaDrsClient
        globals().update({
            "SequenceClient": SequenceClient,
            "SequenceCollectionClient": SequenceCollectionClient,
            "PangenomeClient": PangenomeClient,
            "FastaDrsClient": FastaDrsClient,
        })
        return globals()[name]

    if name == "SequenceCollection":
        from .models import SequenceCollection
        globals()["SequenceCollection"] = SequenceCollection
        return SequenceCollection

    # Re-export from gtars.refget for convenience
    if name in ("RefgetStore", "digest_fasta"):
        from gtars.refget import RefgetStore, digest_fasta
        globals().update({
            "RefgetStore": RefgetStore,
            "digest_fasta": digest_fasta,
        })
        return globals()[name]

    if name in ("add_fasta", "add_fasta_pep", "add_access_method"):
        from .refget import add_fasta, add_fasta_pep, add_access_method
        globals().update({
            "add_fasta": add_fasta,
            "add_fasta_pep": add_fasta_pep,
            "add_access_method": add_access_method,
        })
        return globals()[name]

    if name in ("create_refget_router", "get_dbagent", "fasta_drs_router"):
        try:
            from .refget_router import create_refget_router, get_dbagent, fasta_drs_router
            globals().update({
                "create_refget_router": create_refget_router,
                "get_dbagent": get_dbagent,
                "fasta_drs_router": fasta_drs_router,
            })
            return globals()[name]
        except ImportError:
            return None

    # Utilities functions (imports jsonschema ~60ms)
    utilities_exports = (
        "validate_seqcol", "validate_seqcol_bool", "compare_seqcols",
        "canonical_str", "seqcol_digest", "build_sorted_name_length_pairs",
        "build_name_length_pairs", "seqcol_dict_to_level1_dict",
        "level1_dict_to_seqcol_digest", "chrom_sizes_to_snlp_digest",
        "seqcol_to_snlp_digest", "calc_jaccard_similarities", "print_csc",
        "build_pangenome_model",
    )
    if name in utilities_exports:
        from . import utilities
        return getattr(utilities, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
