"""Compatibility shim for :mod:`refget.seqcolapi.main`.

``uvicorn seqcolapi.main:app`` and ``uvicorn seqcolapi.main:store_app`` resolve
through here. Attribute access is forwarded rather than star-imported because
``store_app`` only exists when ``REFGET_STORE_URL`` / ``REFGET_STORE_PATH`` is
set, and a plain ``from ... import store_app`` would turn a missing store into
an ImportError at the wrong moment.
"""

from refget.seqcolapi import main as _main

__doc__ = _main.__doc__ or __doc__


def __getattr__(name):
    try:
        return getattr(_main, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__():
    return sorted(set(globals()) | set(dir(_main)))
