# %% [markdown]
# # Remote RefgetStore Demo
#
# This script demonstrates loading a RefgetStore from a remote URL (S3)
# and fetching sequences on-demand with local caching.
#
# **Run directly:** `python examples/remote_store.py`

# %%
import os
import tempfile
from pathlib import Path

from refget.store import RefgetStore

# Remote store URL (2023 Human Pangenome Reference - 47 haplotype-resolved assemblies)
REMOTE_URL = "https://refgenie.s3.us-east-1.amazonaws.com/pangenome_refget_store"

# Persistent cache directory
CACHE_DIR = Path.home() / ".refget" / "pangenome_cache"

# Example collection from the pangenome (HG03540.pri.mat.f1_v2)
EXAMPLE_COLLECTION = "0aHV7I-94paL9Z1H4LNlqsW3WxJhlou5"
EXAMPLE_SEQ_NAME = "JAGYVX010000006.1 unmasked:primary_assembly HG03540.pri.mat.f1_v2:JAGYVX010000006.1:1:96320881:1"

# %% [markdown]
# ## 1. Load Remote Store
#
# The store metadata (~1.5 MB) is fetched; sequences are loaded on-demand.

# %%
store = RefgetStore.load_remote(cache_path=str(CACHE_DIR), remote_url=REMOTE_URL)

print(f"Loaded {len(store)} sequences from {REMOTE_URL}")

# %% [markdown]
# ## 2. Store Statistics

# %%
stats = store.stats()
for key, value in stats.items():
    print(f"{key}: {value}")

# %% [markdown]
# ## 3. List Sequences

# %%
records = store.sequence_records()
for i, rec in enumerate(records[:5]):
    m = rec.metadata
    print(f"{i+1}. {m.name[:60]}...")
    print(f"   sha512t24u: {m.sha512t24u}, length: {m.length:,} bp")

# %% [markdown]
# ## 4. Fetch Sequence by ID
#
# Downloads sequence data on first access, then caches locally.

# %%
seq_digest = "du4GiRD_OcmdmCn_RmImyb71YZ4XoCdk"
record = store.get_sequence_by_id(seq_digest)
if record:
    print(f"Name: {record.metadata.name}")
    print(f"Length: {record.metadata.length:,} bp")
    print(f"MD5: {record.metadata.md5}")

# %% [markdown]
# ## 5. Get Substrings

# %%
sub_seq = store.get_substring(seq_digest, 0, 100)
print(f"[0:100]: {sub_seq}")

sub_seq2 = store.get_substring(seq_digest, 1000, 1100)
print(f"[1000:1100]: {sub_seq2}")

# %% [markdown]
# ## 6. Export Sequences to FASTA by Digest

# %%
output_fasta = os.path.join(tempfile.gettempdir(), "demo_export.fa")
digests_to_export = [
    "du4GiRD_OcmdmCn_RmImyb71YZ4XoCdk",
    "cPD3x19YSSfB_TzCKAnp1tzjOKlQVu7l",
    "d8BGSj_irEbXexaV7pStsWf9mFEZFL-8",
]
store.export_fasta_by_digests(digests_to_export, output_fasta, 80)

with open(output_fasta) as f:
    for i, line in enumerate(f):
        if i >= 6:
            print("...")
            break
        print(line.rstrip()[:70])

# %% [markdown]
# ## 7. Collection-Based Lookup
#
# Look up sequences by collection digest + sequence name.

# %%
record = store.get_sequence_by_collection_and_name(EXAMPLE_COLLECTION, EXAMPLE_SEQ_NAME)
if record:
    print(f"Collection: {EXAMPLE_COLLECTION}")
    print(f"Sequence: {EXAMPLE_SEQ_NAME[:50]}...")
    print(f"Length: {record.metadata.length:,} bp")
    print(f"Digest: {record.metadata.sha512t24u}")

# %% [markdown]
# ## 8. Batch Retrieval from BED File

# %%
temp_dir = tempfile.mkdtemp(prefix="refget_demo_")
bed_path = os.path.join(temp_dir, "regions.bed")

bed_content = f"""{EXAMPLE_SEQ_NAME}\t0\t100
{EXAMPLE_SEQ_NAME}\t1000\t1100
{EXAMPLE_SEQ_NAME}\t50000\t50050
"""
with open(bed_path, "w") as f:
    f.write(bed_content)

sequences = store.substrings_from_regions(EXAMPLE_COLLECTION, bed_path)
for seq in sequences:
    print(f"{seq.start:,}-{seq.end:,}: {seq.sequence[:40]}...")

# %% [markdown]
# ## 9. Export BED Regions to FASTA

# %%
output_regions = os.path.join(temp_dir, "regions.fa")
store.export_fasta_from_regions(EXAMPLE_COLLECTION, bed_path, output_regions)

with open(output_regions) as f:
    for line in f:
        print(line.rstrip()[:65])
