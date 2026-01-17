# Project configuration, particularly for logging.

import logging

from .const import *
from .clients import SequenceClient, SequenceCollectionClient, PangenomeClient, FastaDrsClient
from .digest_functions import *
from .utilities import *
from ._version import __version__
from .models import SequenceCollection

# Processing submodule (requires gtars) - users import explicitly:
# from refget.processing import RefgetStore, StorageMode

# Public API for adding FASTA files
from .refget import (
    add_fasta,
    add_fasta_pep,
    add_access_method,
)

try:
    # Requires optional dependencies, so we catch the ImportError
    from .refget_router import create_refget_router, get_dbagent, fasta_drs_router
except ImportError as e:
    print(f"Optional dependencies not installed. Refget router will not be available. Error: {e}")
    create_refget_router = None
    get_dbagent = None
    fasta_drs_router = None
    pass

logging.basicConfig(level=logging.INFO)
