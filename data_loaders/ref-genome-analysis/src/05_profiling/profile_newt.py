"""Profile RefgetStore memory on the palmate newt genome (GCA_964261635.1).

This genome has a single 2 GB chromosome — the worst case for pipeline memory.
Run via sbatch after removing the genome from the store to force re-processing.
"""
import os
import sys
import time
import resource

def rss_mb():
    """Current RSS in MB from /proc/self/status."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

def peak_mb():
    """Peak RSS (high-water mark)."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

def print_mem(label):
    print(f"[MEM] {label}: RSS={rss_mb():.1f} MB, Peak={peak_mb():.1f} MB", flush=True)

print_mem("startup")

from gtars.refget import RefgetStore
print_mem("after import")

BRICK_ROOT = os.environ["BRICK_ROOT"]
STORE_PATH = os.environ.get("STORE_PATH", f"{BRICK_ROOT}/refget_store")
NEWT_FASTA = f"{BRICK_ROOT}/vertebrates/fasta/GCA_964261635.1.fa.gz"

# Open the store
t0 = time.time()
store = RefgetStore.on_disk(STORE_PATH)
t1 = time.time()
print_mem(f"after open_local ({t1-t0:.1f}s)")
print(f"Store stats: {store.stats()}")

# Process the newt genome
print(f"\nProcessing newt genome: {NEWT_FASTA}")
t0 = time.time()
meta, was_new = store.add_sequence_collection_from_fasta(NEWT_FASTA)
elapsed = time.time() - t0

status = "NEW" if was_new else "SKIPPED (already exists)"
print(f"\nResult: {status}")
print(f"Digest: {meta.digest}")
print(f"Sequences: {meta.n_sequences}")
print(f"Time: {elapsed:.1f}s")
print_mem("after processing")
print(f"Store stats: {store.stats()}")
