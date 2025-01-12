# Project configuration, particularly for logging.

import logging

from .const import *
from ._version import __version__
from .hash_functions import *
from .clients import RefGetClient

from .utilities import *

try:
    # Requires optional dependencies, so we catch the ImportError
    from .seqcol_router import seqcol_router, get_dbagent
except ImportError:
    seqcol_router = None
    pass

logging.basicConfig(level=logging.INFO)
