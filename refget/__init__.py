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
    from .seqcol_router import seqcol_router, get_dbagent
except ImportError:
    seqcol_router = None
    pass

GTARS_INSTALLED = False
try:
    from gtars.digests import digest_fasta, sha512t24u_digest
    GTARS_INSTALLED = True
except ImportError:
    GTARS_INSTALLED = False
    _LOGGER.error("gtars not installed.")


logging.basicConfig(level=logging.INFO)
