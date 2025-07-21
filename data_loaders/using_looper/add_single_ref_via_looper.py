import sys
from refget.agents import RefgetDBAgent

absolute_fasta_path = sys.argv[1]

rga = RefgetDBAgent()
results = rga.seqcol.add_from_fasta_file(fasta_file_path=absolute_fasta_path)