# This is simply a wrapper for gtars.refget 's RefgetStore for user convenience.
import logging
import sys
from .const import GTARS_INSTALLED

_LOGGER = logging.getLogger(__name__)

if GTARS_INSTALLED:
    from gtars.refget import (
        RefgetStore,
        StorageMode,
        RetrievedSequence,
    )
else:
    # gtars is not installed. We'll create a dummy class that raises an error.
    # This prevents the user's code from crashing immediately upon import.
    class RefgetStore:
        def __init__(self, *args, **kwargs):
            raise ImportError("gtars is required for this function.")

    # Also define dummy classes for the associated types
    class StorageMode:
        Raw = None
        Encoded = None

    class RetrievedSequence:
        pass

    _LOGGER.warning(
        "Warning: 'gtars' package not found. RefgetStore and associated functionality will not be available.\n"
    )
