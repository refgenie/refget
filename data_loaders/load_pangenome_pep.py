import json
import os
import pephubclient

from refget import add_fasta_pep
from refget.agents import RefgetDBAgent

phc = pephubclient.PEPHubClient()
p = phc.load_project("nsheff/pangenome_fasta")
fa_root = os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/2023_hprc_draft")

# Cloud storage configuration from environment (JSON array)
storage = json.loads(os.environ.get("FASTA_STORAGE_LOCATIONS", "[]")) or None

# Initialize database agent
dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

# Add FASTAs to database (and optionally upload to cloud storage)
print("Adding FASTAs to database...")
results = add_fasta_pep(p, fa_root, dbagent=dbc, storage=storage)


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
