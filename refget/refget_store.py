# This is simply a wrapper for gtars.refget 's GlobalRefgetStore for user convenience.
import sys
from .const import GTARS_INSTALLED

if GTARS_INSTALLED:
    from gtars.refget import (
        GlobalRefgetStore,
        StorageMode,
        RetrievedSequence,
    )

    # We can now create aliases for the classes to expose them directly under `refget`.
    GlobalRefgetStore = GlobalRefgetStore
    StorageMode = StorageMode
    RetrievedSequence = RetrievedSequence

else:
    # gtars is not installed. We'll create a dummy class that raises an error.
    # This prevents the user's code from crashing immediately upon import.
    class GlobalRefgetStore:
        def __init__(self, *args, **kwargs):
            raise ImportError("gtars is required for this function.")

    # Also define dummy classes for the associated types
    class StorageMode:
        Raw = None
        Encoded = None

    class RetrievedSequence:
        pass

    class SequenceCollection:
        pass

    # We can provide a more helpful message here
    sys.stderr.write(
        "Warning: 'gtars' package not found. GlobalRefgetStore and associated functionality will not be available.\n"
    )
    sys.stderr.flush()
