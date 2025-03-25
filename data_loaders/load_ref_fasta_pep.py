import pephubclient
from refget.agents import RefgetDBAgent
import os
import time  # Add this import
import json

phc = pephubclient.PEPHubClient()
p = phc.load_project("nsheff/human_fasta_ref")
fa_root = os.path.expandvars("$BRICKYARD/datasets_downloaded/pangenome_fasta/reference_fasta")


rga = RefgetDBAgent()
results = rga.seqcol.add_from_fasta_pep(p, fa_root)

with open("frontend/src/assets/ref_fasta.json", "w") as f:
    f.write(json.dumps(results, indent=2))



# total_files = len(p.samples)
# results = {}
# for i, s in enumerate(p.samples, 1):
#     fa_path = os.path.join(fa_root, s.fasta)
#     print(f"Loading {fa_path} ({i} of {total_files})")

#     start_time = time.time()  # Record start time
#     results[s.fasta] = rga.seqcol.add_from_fasta_file(fa_path)
#     elapsed_time = time.time() - start_time  # Calculate elapsed time

#     print(f"Loaded in {elapsed_time:.2f} seconds")

# print(results)
