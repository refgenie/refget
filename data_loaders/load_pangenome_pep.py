import json
import os
import pephubclient
import time  # Add this import

from refget.agents import RefgetDBAgent

phc = pephubclient.PEPHubClient()
p = phc.load_project("nsheff/pangenome_fasta")
fa_root = os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/2023_hprc_draft")

rga = RefgetDBAgent()
total_files = len(p.samples)
for i, s in enumerate(p.samples, 1):
    fa_path = os.path.join(fa_root, s.fasta)
    print(f"Loading {fa_path} ({i} of {total_files})")

    start_time = time.time()  # Record start time
    rga.seqcol.add_from_fasta_file(fa_path, update=True)
    elapsed_time = time.time() - start_time  # Calculate elapsed time

    print(f"Loaded in {elapsed_time:.2f} seconds")


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
