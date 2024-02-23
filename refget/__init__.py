# Project configuration, particularly for logging.

import logging

from ._version import __version__
from .const import *
from .hash_functions import *
from .refget import RefGetClient
from .refget import parse_fasta
from .seqcol import *
from .utilities import *
from .seqcol_client import *

try:
    # Requires optional dependencies, so we catch the ImportError
    from .seqcol_router import seqcol_router
except ImportError:
    seqcol_router = None
    pass
