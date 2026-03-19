"""Profile RefgetStore on 5 genomes: newt + 4 normal. Compare timing and memory."""
import time
import resource

def peak_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

def rss_mb():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except:
        pass
    return peak_mb()

from gtars.refget import RefgetStore

import os
BRICK_ROOT = os.environ["BRICK_ROOT"]
STORE_PATH = os.environ.get("STORE_PATH", f"{BRICK_ROOT}/refget_store")
GENOMES = [
    # (path, old_total_time, n_seqs, label)
    (f"{BRICK_ROOT}/vertebrates/fasta/GCA_964261635.1.fa.gz", 183.7, 448, "newt (2GB chr)"),
    (f"{BRICK_ROOT}/vertebrates/fasta/GCA_964263255.1.fa.gz", 213.2, 15265, "15K seqs"),
    (f"{BRICK_ROOT}/vertebrates/fasta/GCA_964263955.1.fa.gz", 42.7, 11150, "11K seqs"),
    (f"{BRICK_ROOT}/vertebrates/fasta/GCA_964264875.2.fa.gz", 27.4, 585, "585 seqs"),
    (f"{BRICK_ROOT}/vertebrates/fasta/GCA_964266715.1.fa.gz", 17.0, 1581, "1.6K seqs"),
]

store = RefgetStore.on_disk(STORE_PATH)
print(f"Store opened. Stats: {store.stats()}")
print(f"RSS after open: {rss_mb():.0f} MB\n")

print(f"{'Genome':<30} {'Seqs':>6} {'New(s)':>8} {'Old(s)':>8} {'Ratio':>7} {'Peak MB':>8}")
print("-" * 75)

for fasta, old_total, old_nseqs, label in GENOMES:
    name = fasta.split("/")[-1]
    t0 = time.time()
    meta, was_new = store.add_sequence_collection_from_fasta(fasta)
    elapsed = time.time() - t0
    ratio = elapsed / old_total
    status = "NEW" if was_new else "SKIP"
    print(f"{label:<30} {meta.n_sequences:>6} {elapsed:>7.1f}s {old_total:>7.1f}s {ratio:>6.2f}x {peak_mb():>7.0f}", flush=True)

print(f"\nFinal RSS: {rss_mb():.0f} MB, Peak: {peak_mb():.0f} MB")
print(f"Store stats: {store.stats()}")
