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


# HUMANS_SAMPLE_LIST = [
#     "base.fa",
#     "different_names.fa",
#     "different_order.fa",
#     "pair_swap.fa",
#     "subset.fa",
#     "swap_wo_coords.fa",
# ]

HUMANS_SAMPLE_LIST = [
    "GRCh38.p14-fasta-no-alt-analysis",
    "GRCh38.p14-fasta-full-analysis",
    "GRCh38.p14-fasta-genomic",
    "GRCh38.p14-fasta-full-analysis-plus-hs38d1",
    "GRCh38.p14-fasta-no-alt-plus-hs38d1",
    "GRCh37.p13-fasta-no-alt-analysis",
    "GRCh37.p13-fasta-full-analysis",
    "GRCh37.p13-fasta-genomic",
    "hg38-initial-ucsc",
    "hg38-p14-ucsc",
    "hg38-p14-masked-ucsc",
    "hg38-p14-analysisSet-ucsc",
    "hg19-initial-ucsc",
    "hg19-masked-ucsc",
    "hg19-p13-full-analysis-ucsc",
    "hg19-p13-no-alt-analysis-ucsc",
    "hg19-p13-plusMT-ucsc",
    "hg19-p13-plusMT-masked-ucsc",
    "hg38-primary-113-ensembl",
    "hg38-toplevel-113-ensembl",
    "hg38-alt-113-ensembl",
    "hg38-alt-rm-113-ensembl",
    "hg38-toplevel-rm-113-ensembl",
    "hg38-primary-rm-113-ensembl",
    "hg38-alt-sm-113-ensembl",
    "hg38-toplevel-sm-113-ensembl",
    "hg38-primary-sm-113-ensembl",
    "GRCh38-p14-47-gencode",
    "GRCh38-primary-assembly-47-gencode",
    "GRCh37-primary-assembly-47-gencode",
    "GRCh38-p14-46-gencode",
    "GRCh38-primary-assembly-46-gencode",
    "GRCh37-primary-assembly-46-gencode",
    "hg18-ucsc",
    "GRCh38-full-decoy-hla-ddbj",
    "homo-sapiens-assembly38-ddbj",
    "hg38-ddbj",
    "GRCh38-ena-29",
    "GRCh38-ena-15",
    "hg38-igenomes-ucsc",
    "hg19-igenomes-ucsc",
    "hg18-igenomes-ucsc",
    "hg38-refgenie",
    "hg38-primary-refgenie",
    "hg18-refgenie",
    "hg19-refgenie",
    "hg38-broad",
    "hg38-noALT-noHLA-noDecoy-broad",
    "b37-broad",
    "GRCh37-igenomes-ensembl",
    "GRCh38-igenomes-ncbi",
    "GRCh38-igenomes-build37-2-ncbi",
    "GRCh38-igenomes-build37-1-ncbi",
    "GRCh38-igenomes-build36-3-ncbi",
    "GRCh38-igenomes-decoy-ncbi",
    "hs37-1kg",
    "hs37d5",
    "hs38",
    "hs38DH",
    "hs37d5.fa",
]

MOUSE_SAMPLES_LIST = [
    "GRCm39-fasta-full-analysis",
    "GRCm39-fasta-genomic",
    "GRCm38.p6-fasta-genomic",
    "GRCm38.p6-fasta-genomic-GCA",
    "GRCm39-fasta-genomic-GCA",
    "GRCm39-fasta-full-analysis-ucsc-ids",
    "mm10-ucsc-initial-soft-masked",
    "mm10-ucsc-initial-hard-masked",
    "mm10-ucsc-p6-soft-masked",
    "mm10-ucsc-p6-hard-masked",
    "mm39-ucsc-initial-soft-masked",
    "mm39-ucsc-initial-hard-masked",
    "mm9-ucsc-initial",
    "GRCm39-primary-113-ensembl",
    "GRCm39-primary-rm-113-ensembl",
    "GRCm39-toplevel-113-ensembl",
    "GRCm39-toplevel-rm-113-ensembl",
    "GRCm39-primary-sm-113-ensembl",
    "GRCm39-toplevel-sm-113-ensembl",
    "GRCm39-toplevel-65-ensembl",
    "GRCm39-toplevel-rm-65-ensembl",
    "GRCm39-primary-M36-gencode",
    "GRCm39-all-M36-gencode",
    "GRCm39-all-M1-gencode",
    "mm10-refgenie-ncbi",
    "mm10-refgenie-ucsc",
    "GRCm38-igenomes-ensembl",
    "NCBIM37-igenomes-ensembl",
    "mm37-build37.1-igenomes-ncbi",
    "mm37-build37.2-igenomes-ncbi",
    "mm38-igenomes-ncbi",
    "mm9-igenomes-ucsc",
    "mm10-igenomes-ucsc",
    "GRCm39-ena-09",
    "GRCm39-ena-03",
    "GRCm39-ena-02",
]
