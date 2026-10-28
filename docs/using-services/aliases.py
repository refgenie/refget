# %% [markdown]
# # Working with Aliases
#
# Aliases let you refer to sequences and collections using identifiers from
# external registries — like INSDC accessions or Ensembl stable IDs — instead
# of refget digests. Each alias lives in a **namespace** that identifies the
# registry or authority that assigned it (e.g., "insdc", "ensembl", "genbank").
#
# **Aliases vs. sequence names:** Sequence *names* (like "chr1") come from FASTA
# headers and are scoped to a single collection — the same name appears in many
# different assemblies. Aliases, by contrast, are *globally unique* identifiers
# assigned by a registry. An INSDC accession like "NC_000001.11" refers to exactly
# one sequence worldwide. For a deeper discussion, see
# [Names, Aliases, and Identifiers](../names-and-aliases-explained.md).
#
# This guide covers how to add, resolve, browse, bulk-load, and remove aliases.
#
# **Prerequisites:** You should already know how to create a RefgetStore and
# load FASTA files. See the [RefgetStore tutorial](refgetstore.py) if you
# need a refresher.

# %% [markdown]
# ## Setup

# %%
import os
import tempfile

from refget.store import RefgetStore

# Create a temp directory and a small FASTA file
temp_dir = tempfile.mkdtemp(prefix="refget_aliases_")

fasta_path = os.path.join(temp_dir, "example.fa")
with open(fasta_path, "w") as f:
    f.write(">chr1\nATGCATGCATGCATGCATGCATGCATGCATGC\n")
    f.write(">chr2\nGGGGAAAATTTTCCCCGGGGAAAATTTTCCCC\n")
    f.write(">chrM\nACGTACGTACGTACGT\n")

# Create a store, load the genome, and suppress progress output
store = RefgetStore.in_memory()
store.set_quiet(True)
meta, _ = store.add_sequence_collection_from_fasta(fasta_path)

# Grab digests we'll use throughout
collection_digest = meta.digest
records = list(store.list_sequences())
digest_map = {r.name: r.sha512t24u for r in records}

print(f"Collection digest: {collection_digest}")
for name, digest in digest_map.items():
    print(f"  {name}: {digest}")

# %% [markdown] output
# ```
# Collection digest: eKo5bRz2lZYOOTh1JWjjxOfxY6XQPhh3
#   chr1: Blf3ILywY3YsZmFcjBssmHEPN0dDWP_V
#   chr2: LBh5K2bNKvmfsWSVKvPbjXFrmIOxxr_b
#   chrM: U1x5Qz66jmXmv_oJtfYmtUNkwq1wZ75u
# ```

# %% [markdown]
# ## Adding sequence aliases
#
# Use `add_sequence_alias()` to map a registry namespace and identifier to a
# sequence digest. A single sequence can have aliases in multiple registries.

# %%
# Add INSDC RefSeq accessions for each sequence
store.add_sequence_alias("insdc", "NC_000001.11", digest_map["chr1"])
store.add_sequence_alias("insdc", "NC_000002.12", digest_map["chr2"])
store.add_sequence_alias("insdc", "NC_012920.1", digest_map["chrM"])

# Add GenBank accessions for the same sequences
store.add_sequence_alias("genbank", "CM000663.2", digest_map["chr1"])
store.add_sequence_alias("genbank", "CM000664.2", digest_map["chr2"])
store.add_sequence_alias("genbank", "J01415.2", digest_map["chrM"])

print("Added 6 aliases across 2 registries")

# %% [markdown] output
# ```
# Added 6 aliases across 2 registries
# ```

# %% [markdown]
# ## Resolving aliases
#
# Use `get_sequence_by_alias()` to look up a sequence by its registry identifier.
# This returns a `SequenceRecord` (or `None` if the alias does not exist).

# %%
# Look up a sequence by its INSDC accession
record = store.get_sequence_by_alias("insdc", "NC_000001.11")
if record:
    print(f"Name: {record.metadata.name}")
    print(f"Length: {record.metadata.length} bp")
    print(f"Digest: {record.metadata.sha512t24u}")

# Look up by GenBank accession
record2 = store.get_sequence_by_alias("genbank", "J01415.2")
if record2:
    print(f"\nJ01415.2 -> {record2.metadata.name} ({record2.metadata.length} bp)")

# Non-existent alias returns None
missing = store.get_sequence_by_alias("insdc", "NC_999999.1")
print(f"\nNon-existent alias: {missing}")

# %% [markdown] output
# ```
# Name: chr1
# Length: 32 bp
# Digest: Blf3ILywY3YsZmFcjBssmHEPN0dDWP_V
#
# J01415.2 -> chrM (16 bp)
#
# Non-existent alias: None
# ```

# %% [markdown]
# ## Reverse lookup
#
# Given a sequence digest, use `get_aliases_for_sequence()` to find all
# registry identifiers that point to it.

# %%
aliases = store.get_aliases_for_sequence(digest_map["chr1"])
print(f"Aliases for chr1 ({digest_map['chr1']}):")
for namespace, alias in aliases:
    print(f"  {namespace}/{alias}")

# %% [markdown] output
# ```
# Aliases for chr1 (Blf3ILywY3YsZmFcjBssmHEPN0dDWP_V):
#   insdc/NC_000001.11
#   genbank/CM000663.2
# ```

# %% [markdown]
# ## Collection aliases
#
# Collection aliases work the same way as sequence aliases, but map to
# collection digests. Use these to give assemblies human-readable names
# like "GRCh38" or "GRCm39".

# %%
# Add collection aliases from different authorities
store.add_collection_alias("ncbi", "GRCh38", collection_digest)
store.add_collection_alias("ucsc", "hg38", collection_digest)

# Resolve a collection alias. get_collection_by_alias() returns a full
# SequenceCollection (not just metadata), so use len() for the sequence count.
coll_meta = store.get_collection_by_alias("ncbi", "GRCh38")
if coll_meta:
    print(f"GRCh38 digest: {coll_meta.digest}")
    print(f"GRCh38 sequences: {len(coll_meta)}")

# Reverse lookup for collections
coll_aliases = store.get_aliases_for_collection(collection_digest)
print(f"\nAll aliases for this collection:")
for namespace, alias in coll_aliases:
    print(f"  {namespace}/{alias}")

# %% [markdown] output
# ```
# GRCh38 digest: eKo5bRz2lZYOOTh1JWjjxOfxY6XQPhh3
# GRCh38 sequences: 3
#
# All aliases for this collection:
#   ncbi/GRCh38
#   ucsc/hg38
# ```

# %% [markdown]
# ## Loading aliases from TSV files
#
# For bulk loading, prepare a TSV file with `alias<TAB>digest` on each line.
# Lines starting with `#` are treated as comments. Use `load_sequence_aliases()`
# to import the file into a namespace.

# %%
# Create a TSV alias file with Ensembl identifiers
tsv_path = os.path.join(temp_dir, "ensembl_aliases.tsv")
with open(tsv_path, "w") as f:
    f.write("# Ensembl release 112 sequence identifiers\n")
    f.write(f"1\t{digest_map['chr1']}\n")
    f.write(f"2\t{digest_map['chr2']}\n")
    f.write(f"MT\t{digest_map['chrM']}\n")

# Load the TSV into the "ensembl" namespace
count = store.load_sequence_aliases("ensembl", tsv_path)
print(f"Loaded {count} aliases into 'ensembl' namespace")

# Verify one of the loaded aliases
record = store.get_sequence_by_alias("ensembl", "2")
if record:
    print(f"ensembl/2 -> {record.metadata.name} ({record.metadata.length} bp)")

# %% [markdown] output
# ```
# Loaded 3 aliases into 'ensembl' namespace
# ensembl/2 -> chr2 (32 bp)
# ```

# %% [markdown]
# ## Browsing namespaces and aliases
#
# Use `list_sequence_alias_namespaces()` and `list_sequence_aliases()` to
# explore what registries and aliases are registered in the store.
#
# Note: these listings come back in hash-map order, not insertion order, so
# the namespace and alias order below will vary between runs. The *contents*
# are stable; only the order is not.

# %%
# List all sequence alias namespaces
namespaces = store.list_sequence_alias_namespaces()
print(f"Sequence alias namespaces: {namespaces}")

# List aliases within a namespace
for ns in namespaces:
    aliases = store.list_sequence_aliases(ns)
    print(f"\n  {ns}/")
    for alias in aliases:
        print(f"    {alias}")

# Collection namespaces and aliases work the same way
coll_namespaces = store.list_collection_alias_namespaces()
print(f"\nCollection alias namespaces: {coll_namespaces}")

for ns in coll_namespaces:
    coll_aliases = store.list_collection_aliases(ns)
    print(f"\n  {ns}/")
    for alias in coll_aliases:
        print(f"    {alias}")

# %% [markdown] output
# ```
# Sequence alias namespaces: ['ensembl', 'insdc', 'genbank']
#
#   ensembl/
#     1
#     2
#     MT
#
#   insdc/
#     NC_000001.11
#     NC_012920.1
#     NC_000002.12
#
#   genbank/
#     CM000664.2
#     J01415.2
#     CM000663.2
#
# Collection alias namespaces: ['ncbi', 'ucsc']
#
#   ncbi/
#     GRCh38
#
#   ucsc/
#     hg38
# ```

# %% [markdown]
# ## Removing aliases
#
# Use `remove_sequence_alias()` or `remove_collection_alias()` to delete
# individual aliases. Both return `True` if the alias existed, `False` otherwise.

# %%
# Remove a sequence alias
removed = store.remove_sequence_alias("ensembl", "MT")
print(f"Removed ensembl/MT: {removed}")

# Confirm it's gone
missing = store.get_sequence_by_alias("ensembl", "MT")
print(f"ensembl/MT after removal: {missing}")

# Removing a non-existent alias returns False
not_found = store.remove_sequence_alias("ensembl", "99")
print(f"Removed ensembl/99 (non-existent): {not_found}")

# Remove a collection alias
removed_coll = store.remove_collection_alias("ncbi", "GRCh38")
print(f"\nRemoved ncbi/GRCh38: {removed_coll}")

# %% [markdown] output
# ```
# Removed ensembl/MT: True
# ensembl/MT after removal: None
# Removed ensembl/99 (non-existent): False
#
# Removed ncbi/GRCh38: True
# ```

# %% [markdown]
# ## Alias persistence
#
# When using an on-disk store, aliases are persisted automatically in
# `aliases/sequences/` and `aliases/collections/` subdirectories. Each
# namespace is stored as a separate TSV file (e.g., `aliases/sequences/ucsc.tsv`).
# Aliases are restored when the store is reopened with `RefgetStore.open_local()`.

# %%
# Create an on-disk store with aliases
store_path = os.path.join(temp_dir, "persistent_store")
disk_store = RefgetStore.on_disk(store_path)
disk_store.set_quiet(True)
disk_meta, _ = disk_store.add_sequence_collection_from_fasta(fasta_path)

# Add aliases
seq_digest = list(disk_store.list_sequences())[0].sha512t24u
disk_store.add_collection_alias("ncbi", "GRCh38", disk_meta.digest)
disk_store.add_sequence_alias("insdc", "NC_000001.11", seq_digest)

# Reopen the store and verify aliases survived
reopened = RefgetStore.open_local(store_path)
coll = reopened.get_collection_by_alias("ncbi", "GRCh38")
print(f"Persisted collection alias resolved: {coll is not None}")

seq = reopened.get_sequence_by_alias("insdc", "NC_000001.11")
print(f"Persisted sequence alias resolved: {seq is not None}")

# %% [markdown] output
# ```
# Loading collection metadata eKo5bRz2lZYOOTh1JWjjxOfxY6XQPhh3...
# Persisted collection alias resolved: True
# Persisted sequence alias resolved: True
# ```

# %%
# Cleanup
import shutil
shutil.rmtree(temp_dir)
