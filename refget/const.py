import os


def _schema_path(name):
    return os.path.join(SCHEMA_FILEPATH, name)


CONTENT_ALL_A_IN_B = 2**0
CONTENT_ALL_B_IN_A = 2**1
LENGTHS_ALL_A_IN_B = 2**2
LENGTHS_ALL_B_IN_A = 2**3
NAMES_ALL_A_IN_B = 2**4
NAMES_ALL_B_IN_A = 2**5
TOPO_ALL_A_IN_B = 2**6
TOPO_ALL_B_IN_A = 2**7
CONTENT_ANY_SHARED = 2**8
LENGTHS_ANY_SHARED = 2**9
NAMES_ANY_SHARED = 2**10
CONTENT_A_ORDER = 2**11
CONTENT_B_ORDER = 2**12

FLAGS = {
    CONTENT_ALL_A_IN_B: "CONTENT_ALL_A_IN_B",
    CONTENT_ALL_B_IN_A: "CONTENT_ALL_B_IN_A",
    LENGTHS_ALL_A_IN_B: "LENGTHS_ALL_A_IN_B",
    LENGTHS_ALL_B_IN_A: "LENGTHS_ALL_B_IN_A",
    NAMES_ALL_A_IN_B: "NAMES_ALL_A_IN_B",
    NAMES_ALL_B_IN_A: "NAMES_ALL_B_IN_A",
    TOPO_ALL_A_IN_B: "TOPO_ALL_A_IN_B",
    TOPO_ALL_B_IN_A: "TOPO_ALL_B_IN_A",
    CONTENT_ANY_SHARED: "CONTENT_ANY_SHARED",
    LENGTHS_ANY_SHARED: "LENGTHS_ANY_SHARED",
    NAMES_ANY_SHARED: "NAMES_ANY_SHARED",
    CONTENT_A_ORDER: "CONTENT_A_ORDER",
    CONTENT_B_ORDER: "CONTENT_B_ORDER",
}

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
