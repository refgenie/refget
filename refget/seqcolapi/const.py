import os

# ALL_VERSIONS lives in refget.const (the base package) so that service-info can
# be built without importing anything from this optional subpackage. Re-exported
# here because both seqcolapi apps and the top-level `seqcolapi` compatibility
# shim read it from this module.
from refget.const import ALL_VERSIONS  # noqa: F401

STATIC_DIRNAME = "static"
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), STATIC_DIRNAME)
