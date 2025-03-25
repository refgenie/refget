# This script computes the refget digest for each fasta file in the pangenome
# and produces a json file with the digests.


from refget import fasta_to_digest
import json

total_files = len(p.samples)
results = {}
for i, s in enumerate(p.samples, 1):
    fa_path = os.path.join(fa_root, s.fasta)
    print(f"Computing digest for {fa_path} ({i} of {total_files})")
    start_time = time.time()  # Record start time
    digest = fasta_to_digest(fa_path)
    elapsed_time = time.time() - start_time  # Calculate elapsed time
    results[s.fasta] = digest
    print(f"Loaded in {elapsed_time:.2f} seconds")

for i, s in enumerate(p.samples, 1):
    print(f"{s.fasta}: {results[s.fasta]}")
    s.refget_digest = results[s.fasta]

updated_dict = p.to_dict()
with open("frontend/src/assets/hprc.json", "w") as f:
    f.write(json.dumps(updated_dict["samples"], indent=2))

