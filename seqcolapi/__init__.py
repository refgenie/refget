"""Compatibility shim: ``seqcolapi`` now lives in :mod:`refget.seqcolapi`.

The service code moved into the refget package so that it actually ships in the
wheel. This top-level package is kept only so that existing deployments -- whose
``Dockerfile`` does ``COPY seqcolapi/ /app/seqcolapi`` and then runs
``uvicorn seqcolapi.main:app`` or ``uvicorn seqcolapi.main:store_app`` -- keep
working unchanged.

New code should import from :mod:`refget.seqcolapi` instead.
"""

from refget.seqcolapi import *  # noqa: F401,F403
from refget.seqcolapi import __all__ as __all__  # noqa: PLC0414
