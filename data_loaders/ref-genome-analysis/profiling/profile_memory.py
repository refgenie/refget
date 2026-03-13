"""Profile RefgetStore memory usage on Rivanna."""
import os
import sys
import time
import resource
import csv

def rss_mb():
    """Current RSS in MB from /proc/self/status (more accurate than ru_maxrss)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024  # KB to MB
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

BRICK_ROOT = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta"
STORE_PATH = f"{BRICK_ROOT}/refget_store"
INVENTORY_CSV = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta/refgenomes_inventory.csv"

# Open the store
t0 = time.time()
store = RefgetStore.on_disk(STORE_PATH)
t1 = time.time()
print_mem(f"after open_local ({t1-t0:.1f}s)")
print(f"Store stats: {store.stats()}")

# Read inventory
rows = []
with open(INVENTORY_CSV) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Use offset to skip to unprocessed files
OFFSET = int(sys.argv[1]) if len(sys.argv) > 1 else 0
TARGET_NEW = int(sys.argv[2]) if len(sys.argv) > 2 else 5

if OFFSET:
    rows = rows[OFFSET:]
    print(f"Skipped to offset {OFFSET}, {len(rows)} remaining")

print(f"Total rows to process: {len(rows)}, targeting {TARGET_NEW} new files")
print_mem("before processing loop")

n_new = 0
n_skipped = 0

for i, row in enumerate(rows):
    fasta_path = row["path"]
    filename = row.get("filename", "")

    t0 = time.time()
    try:
        meta, was_new = store.add_sequence_collection_from_fasta(fasta_path, threads=4)
        elapsed = time.time() - t0

        if was_new:
            n_new += 1
            print(f"\n[{OFFSET+i+1}] NEW: {filename} -> {meta.digest} ({meta.n_sequences} seqs, {elapsed:.1f}s)")
            print_mem(f"after NEW #{n_new}")
            print(f"Store stats: {store.stats()}")
            if n_new >= TARGET_NEW:
                break
        else:
            n_skipped += 1
            if n_skipped % 50 == 0:
                print_mem(f"skipping... ({n_skipped} skipped, row {OFFSET+i+1})")
    except Exception as e:
        print(f"[{OFFSET+i+1}] FAILED {filename}: {e}")

print(f"\nDone: {n_new} new, {n_skipped} skipped")
print_mem("final")
