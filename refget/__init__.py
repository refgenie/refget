# Project configuration, particularly for logging.

import logging

from .const import *
from ._version import __version__
from .hash_functions import *
from .clients import SequencesClient, SequenceCollectionsClient, PangenomesClient


from .utilities import *

try:
    # Requires optional dependencies, so we catch the ImportError
    from .seqcol_router import create_refget_router, get_dbagent
except ImportError:
    create_seqcol_router = None
    pass

logging.basicConfig(level=logging.INFO)
