import os

from refget._version import __version__ as refget_version
from gtars import __version__ as gtars_version
from platform import python_version

ALL_VERSIONS = {
    "refget_version": refget_version,
    "gtars_version": gtars_version,
    "python_version": python_version(),
    "seqcol_spec_version": "1.0.0",
}
STATIC_DIRNAME = "static"
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATIC_DIRNAME)
