import pephubclient
from refget.agents import RefgetDBAgent
import os

phc = pephubclient.PEPHubClient()
p = phc.load_project("nsheff/pangenome_fasta")
fa_root = os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/2023_hprc_draft")

rga = RefgetDBAgent()
for s in p.samples:
    print(f"Loading {s.fasta}")
    fa_path = os.path.join(fa_root, s.fasta)
    rga.seqcol.add_from_fasta_file(fa_path)

## Say I want to add the digest now back into the PEP on PEPhub.
# What's the best way to do it?
# 1. Use pipestat?
# 2. Use pephubClient?

# Would it be better to instead do this?
# import peppy
# p = peppy.Project("nsheff/pangenome_fasta")

