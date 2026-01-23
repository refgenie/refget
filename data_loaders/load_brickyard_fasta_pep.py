"""
Load FASTA files from the brickyard PEP project into the refget database.

This script uses agents directly instead of the removed wrapper functions.
For cloud storage uploads, use the CLI: refget admin ingest

Usage:
    python data_loaders/load_brickyard_fasta_pep.py
"""
import os
import json

import pephubclient
from refget.agents import RefgetDBAgent

phc = pephubclient.PEPHubClient()
p = phc.load_project("donaldcampbelljr/human_mouse_fasta_brickyard:default")
fa_root = ""  # PEP has absolute paths in the fasta column

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

with open("frontend/src/assets/brickyard_fasta.json", "w") as f:
    f.write(json.dumps(results, indent=2))

print("\nDone. Results saved to frontend/src/assets/brickyard_fasta.json")
