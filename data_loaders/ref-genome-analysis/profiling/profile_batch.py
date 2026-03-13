"""Profile RefgetStore on several normal genomes for timing comparison."""
import time
import resource

def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

from gtars.refget import RefgetStore

BRICK_ROOT = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta"
STORE_PATH = f"{BRICK_ROOT}/refget_store"
GENOMES = [
    # (path, old_pipeline_time, old_total_time, n_seqs)
    ("/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/vertebrates/fasta/GCA_964263255.1.fa.gz", 203.1, 213.2, 15265),
    ("/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/vertebrates/fasta/GCA_964263955.1.fa.gz", 32.6, 42.7, 11150),
    ("/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/vertebrates/fasta/GCA_964266715.1.fa.gz", 7.2, 17.0, 1581),
]

store = RefgetStore.on_disk(STORE_PATH)
print(f"Store opened. Stats: {store.stats()}\n")

for fasta, old_pipe, old_total, old_nseqs in GENOMES:
    name = fasta.split("/")[-1]
    t0 = time.time()
    meta, was_new = store.add_sequence_collection_from_fasta(fasta)
    elapsed = time.time() - t0
    status = "NEW" if was_new else "SKIP"
    print(f"{status} {name}: {meta.n_sequences} seqs, {elapsed:.1f}s (old: {old_pipe:.1f}s pipe / {old_total:.1f}s total), Peak={peak_mb():.0f} MB")
