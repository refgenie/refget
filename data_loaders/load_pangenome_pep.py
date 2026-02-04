"""
Load pangenome FASTA files into the refget database.

This script uses agents directly instead of the removed wrapper functions.
For cloud storage uploads, use the CLI: refget admin ingest

Usage:
    python data_loaders/load_pangenome_pep.py
"""

import json
import os
import pephubclient

from refget.agents import RefgetDBAgent

phc = pephubclient.PEPHubClient()
p = phc.load_project("nsheff/pangenome_fasta")
fa_root = os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/2023_hprc_draft")

# Initialize database agent
dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

# Add FASTAs to database using agent directly
print("Adding FASTAs to database...")
results = {}
total = len(p.samples)
for i, s in enumerate(p.samples, 1):
    fa_path = os.path.join(fa_root, s.fasta)
    name = getattr(s, "sample_name", None)
    print(f"[{i}/{total}] Adding {s.fasta}...")
    if name:
        seqcol = dbc.seqcol.add_from_fasta_file_with_name(fa_path, name, update=True)
    else:
        seqcol = dbc.seqcol.add_from_fasta_file(fa_path, update=True)
    results[s.fasta] = seqcol.digest
    print(f"         -> {seqcol.digest}")


# Write out the results to a file:
updated_dict = p.to_dict()
with open("frontend/assets/human_reference.json", "w") as f:
    f.write(json.dumps(updated_dict["samples"], indent=2))


## Say I want to add the digest now back into the PEP on PEPhub.
# What's the best way to do it?
# 1. Use pipestat?
# 2. Use pephubClient?

# Would it be better to instead do this?
# import peppy
# p = peppy.Project("nsheff/pangenome_fasta")
