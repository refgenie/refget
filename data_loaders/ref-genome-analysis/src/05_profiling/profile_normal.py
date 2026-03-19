"""Profile RefgetStore on a normal-sized genome (GCA_964264875.2, 585 seqs).
Compare timing with old code (17.7s pipeline time)."""
import time
import resource

def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

def print_mem(label):
    print(f"[MEM] {label}: Peak={peak_mb():.1f} MB", flush=True)

print_mem("startup")

from gtars.refget import RefgetStore
print_mem("after import")

import os
BRICK_ROOT = os.environ["BRICK_ROOT"]
STORE_PATH = os.environ.get("STORE_PATH", f"{BRICK_ROOT}/refget_store")
FASTA = f"{BRICK_ROOT}/vertebrates/fasta/GCA_964264875.2.fa.gz"

t0 = time.time()
store = RefgetStore.on_disk(STORE_PATH)
print_mem(f"after open_local ({time.time()-t0:.1f}s)")

print(f"\nProcessing: {FASTA}")
t0 = time.time()
meta, was_new = store.add_sequence_collection_from_fasta(FASTA)
elapsed = time.time() - t0

print(f"Result: {'NEW' if was_new else 'SKIPPED'}")
print(f"Digest: {meta.digest}")
print(f"Sequences: {meta.n_sequences}")
print(f"Time: {elapsed:.1f}s (old code: 17.7s pipeline / 27.4s total)")
print_mem("after processing")
