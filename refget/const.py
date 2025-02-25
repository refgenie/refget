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
SeqCol = dict


GTARS_INSTALLED = False
try:
    from gtars.digests import digest_fasta, sha512t24u_digest

    GTARS_INSTALLED = True
except ImportError:

    def digest_fasta(*args, **kwargs):
        raise ImportError("gtars is required for this function.")

    GTARS_INSTALLED = False
    _LOGGER.error("gtars not installed.")
