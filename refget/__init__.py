# Project configuration, particularly for logging.

import logging

from .const import *
from .clients import SequenceClient, SequenceCollectionClient, PangenomeClient
from .digest_functions import *
from .utilities import *
from ._version import __version__
from .models import SequenceCollection

from .refget_store import *

try:
    # Requires optional dependencies, so we catch the ImportError
    from .refget_router import create_refget_router, get_dbagent
except ImportError:
    print("Optional dependencies not installed. Refget router will not be available.")
    create_refget_router = None
    get_dbagent = None
    pass

logging.basicConfig(level=logging.INFO)
