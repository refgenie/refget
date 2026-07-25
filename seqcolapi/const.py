import os

# ALL_VERSIONS moved into the distributed `refget` package (refget/const.py) so
# the shared store-backed app factory can build service-info without seqcolapi,
# which is not shipped in the refget wheel. Re-exported here for compatibility.
from refget.const import ALL_VERSIONS  # noqa: F401

STATIC_DIRNAME = "static"
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATIC_DIRNAME)
