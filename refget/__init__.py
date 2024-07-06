# Project configuration, particularly for logging.

import logging

from .const import *
from ._version import __version__
from .hash_functions import *
from .refget import RefGetClient
from .refget import parse_fasta

# from .seqcol import *
from .utilities import *
from .seqcol_client import *

try:
    # Requires optional dependencies, so we catch the ImportError
    from .seqcol_router import seqcol_router
except ImportError:
    seqcol_router = None
    pass

logging.basicConfig(level=logging.INFO)
