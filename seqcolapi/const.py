import os

from refget._version import __version__ as refget_pkg_version
from platform import python_version

from ._version import __version__ as seqcolapi_version

ALL_VERSIONS = {
    "seqcolapi_version": seqcolapi_version,
    "refget_pkg_version": refget_pkg_version,
    "python_version": python_version(),
    "seqcol_spec_version": "1.0.0",
}
STATIC_DIRNAME = "static"
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATIC_DIRNAME)
