import os
import logging

_LOGGER = logging.getLogger(__name__)


def _schema_path(name):
    return os.path.join(SCHEMA_FILEPATH, name)


KNOWN_TOPOS = ["linear", "circular"]
NAME_KEY = "name"
SEQ_KEY = "sequence"
TOPO_KEY = "topology"
LEN_KEY = "length"

# internal schemas paths determination
ASL_NAME = "AnnotatedSequenceList"
SCHEMA_NAMES = [ASL_NAME + ".yaml"]
SCHEMA_FILEPATH = os.path.join(os.path.dirname(__file__), "schemas")
INTERNAL_SCHEMAS = [_schema_path(s) for s in SCHEMA_NAMES]

# Alias dict to make typehinting clearer
SeqColDict = dict


GTARS_INSTALLED = False
try:
    GTARS_INSTALLED = True
except ImportError:
    GTARS_INSTALLED = False
    _LOGGER.error("gtars not installed. Some functions will be slower or unavailable.")
