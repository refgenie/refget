# %% [markdown]
# # Exploring the Reference Genome Jungle
#
# This tutorial connects to the reference genome jungle, a public RefgetStore
# holding human and mouse reference assemblies gathered from many providers
# (NCBI, Ensembl, UCSC, GENCODE, iGenomes, ENA, DDBJ, the Broad Institute,
# refgenie, and the 1000 Genomes Project). The same genome build often appears
# several times, once per provider, each with its own chromosome names, masking,
# and choice of alt contigs. That is the jungle. This tutorial shows how a
# RefgetStore lets you find your way through it: browse the store by alias,
# look up a genome by accession, compare two assemblies, translate chromosome
# names between providers, and export sequences to FASTA.
#
# For background on what the jungle store holds and how it relates to the other
# public stores, see [The reference genome jungle](../genome-collections-explained.md).
# This tutorial assumes you can already [install the refget package](../README.md#install)
# and know the basics of [RefgetStore](refgetstore.py) and [aliases](aliases.py).
#
# <div class="admonition success">
#   <p class="admonition-title">Learning objectives</p>
#   <ul>
#     <li>Open the jungle store from its public URL</li>
#     <li>Browse genomes through alias namespaces</li>
#     <li>Look up a genome by NCBI accession</li>
#     <li>Compare two assemblies</li>
#     <li>Translate chromosome names between providers</li>
#     <li>Export sequences from the store as FASTA</li>
#   </ul>
# </div>

# %% [markdown]
# ## 1. Opening the store
#
# The jungle store is published as static files on S3. Opening it remotely
# fetches only the store manifest, the collection index, and the alias tables;
# sequences are downloaded on demand into a local cache directory.

# %%
import os
import tempfile
from refget.store import RefgetStore

# %%
JUNGLE_URL = "https://refgenie.s3.us-east-1.amazonaws.com/refget-store/jungle/"

# A temporary local cache; reuse a permanent directory in real work so the
# store's index files and any downloaded sequences survive between sessions.
temp_dir = tempfile.mkdtemp(prefix="jungle_tutorial_")
cache_path = os.path.join(temp_dir, "cache")

store = RefgetStore.open_remote(cache_path=cache_path, remote_url=JUNGLE_URL)

info = store.stats()
print(f"Collections in the jungle: {info['n_collections']}")

# %% [markdown] output
# ```
# Collections in the jungle: 79
# ```

# %% [markdown]
# If you have a local copy of the store, open it directly instead:
#
# ```python
# store = RefgetStore.open_local("/path/to/jungle")
# ```

# %% [markdown]
# ## 2. Browsing the jungle by alias
#
# Every collection is identified by its content digest, but the store also
# carries human-readable aliases grouped into namespaces. Listing the
# namespaces tells you which kinds of identifiers you can look up.

# %%
namespaces = sorted(store.list_collection_alias_namespaces())
print(f"Collection alias namespaces: {namespaces}")

# %% [markdown] output
# ```
# Collection alias namespaces: ['accession', 'genome_assembly', 'insdc', 'name', 'refseq']
# ```

# %% [markdown]
# The `genome_assembly` namespace holds the short build names most people use.

# %%
for alias in sorted(store.list_collection_aliases("genome_assembly")):
    print(f"  {alias}")

# %% [markdown] output
# ```
#   hg18
#   hg19
#   hg38
#   mm10
#   mm37
#   mm38
#   mm39
#   mm9
# ```

# %% [markdown]
# The `accession` namespace holds NCBI assembly accessions, both RefSeq
# (`GCF_`) and GenBank (`GCA_`). The `name` namespace holds a descriptive name
# for every collection that records its build and provider, so it is the best
# way to see everything the store has.

# %%
accessions = sorted(store.list_collection_aliases("accession"))
print(f"Accession aliases: {len(accessions)}")
for alias in accessions[:5]:
    print(f"  {alias}")

names = sorted(store.list_collection_aliases("name"))
print(f"\nDescriptive names: {len(names)}")
for alias in names[:8]:
    print(f"  {alias}")

# %% [markdown] output
# ```
# Accession aliases: 16
#   GCA_000001405.14
#   GCA_000001405.15
#   GCA_000001635.8
#   GCA_000001635.9
#   GCF_000001405.25
#
# Descriptive names: 104
#   GRCh37-igenomes-ensembl
#   GRCh37-primary-assembly-46-gencode
#   GRCh37-primary-assembly-47-gencode
#   GRCh37.p13-fasta-full-analysis
#   GRCh37.p13-fasta-genomic
#   GRCh37.p13-fasta-no-alt-analysis
#   GRCh38-ena-15
#   GRCh38-ena-29
# ```

# %% [markdown]
# ## 3. Looking up a genome by accession
#
# Let's look up GRCh38.p14, the current human reference, by its RefSeq
# accession. Resolving an alias returns the full collection, so `len()` gives
# its sequence count.

# %%
hg38 = store.get_collection_by_alias("accession", "GCF_000001405.40")
print(f"Digest: {hg38.digest}")
print(f"Sequences: {len(hg38)}")

# %% [markdown] output
# ```
# Downloading collection metadata u1HyLgIlq8M_XvEwy0oGqAvKGHJMGtxH...
# Digest: u1HyLgIlq8M_XvEwy0oGqAvKGHJMGtxH
# Sequences: 705
# ```

# %% [markdown]
# A reverse lookup shows every alias that points at this collection. The same
# assembly is known by its RefSeq accession, its GenBank accession, and a
# descriptive name.

# %%
for namespace, alias in sorted(store.get_aliases_for_collection(hg38.digest)):
    print(f"  {namespace}:{alias}")

# %% [markdown] output
# ```
#   accession:GCF_000001405.40
#   insdc:GCA_000001405.29
#   name:GRCh38.p14-fasta-genomic
#   refseq:GCF_000001405.40
# ```

# %% [markdown]
# ## 4. Comparing two assemblies
#
# `compare()` runs the seqcol comparison between two collections. It reports
# which attributes both collections define and, for each attribute, how many
# array elements they share. Comparing GRCh38.p14 with GRCh37.p13 shows two
# builds that define the same attributes but share only a small fraction of
# their sequences.

# %%
hg19 = store.get_collection_by_alias("accession", "GCF_000001405.25")
comparison = store.compare(hg38.digest, hg19.digest)

print(f"GRCh38.p14: {len(hg38)} sequences, GRCh37.p13: {len(hg19)} sequences")
print(f"Attributes in both: {comparison['attributes']['a_and_b']}")
print("Elements shared by both, per attribute:")
for attribute, count in sorted(comparison["array_elements"]["a_and_b_count"].items()):
    print(f"  {attribute}: {count}")

# %% [markdown] output
# ```
# Downloading collection metadata XJWKh8nsSqBFfcU0DIHMZohYyCWF-vcA...
# GRCh38.p14: 705 sequences, GRCh37.p13: 297 sequences
# Attributes in both: ['lengths', 'name_length_pairs', 'names', 'sequences', 'sorted_name_length_pairs', 'sorted_sequences']
# Elements shared by both, per attribute:
#   lengths: 74
#   name_length_pairs: 65
#   names: 65
#   sequences: 65
#   sorted_name_length_pairs: 65
#   sorted_sequences: 65
# ```

# %% [markdown]
# ## 5. Translating chromosome names between providers
#
# The jungle holds GRCh38 from several providers. Ensembl names chromosomes
# `1`, `2`, `MT`; UCSC-style FASTAs name them `chr1`, `chr2`, `chrM`. Because
# the store identifies sequences by content, it can tell you which names refer
# to the same sequence. `match_sequence_names()` joins two collections on
# sequence digest and returns every name each side uses for that content.

# %%
ensembl = store.get_collection_by_alias("name", "hg38-primary-113-ensembl")
ucsc = store.get_collection_by_alias("name", "hg38-primary-refgenie")

result = store.match_sequence_names(ensembl.digest, ucsc.digest)
print(f"Ensembl sequences: {len(ensembl)}, UCSC-style sequences: {len(ucsc)}")
print(f"Shared sequences: {len(result['matches'])}")
print(f"Only in Ensembl: {len(result['a_only'])}, only in UCSC-style: {len(result['b_only'])}")
print("\nFirst matches (Ensembl name -> UCSC name):")
for row in result["matches"][:5]:
    print(f"  {row['names_a']} -> {row['names_b']}  ({row['length']:,} bp)")

# %% [markdown] output
# ```
# Downloading collection metadata oLfPx0NOBKKXMIngGeQ4YewtU4Ge_wKz...
# Downloading collection metadata Ba88PY52_qeifhJrgUXyin6UITdXNsg3...
# Ensembl sequences: 194, UCSC-style sequences: 25
# Shared sequences: 25
# Only in Ensembl: 169, only in UCSC-style: 0
#
# First matches (Ensembl name -> UCSC name):
#   ['1'] -> ['chr1']  (248,956,422 bp)
#   ['10'] -> ['chr10']  (133,797,422 bp)
#   ['11'] -> ['chr11']  (135,086,622 bp)
#   ['12'] -> ['chr12']  (133,275,309 bp)
#   ['13'] -> ['chr13']  (114,364,328 bp)
# ```

# %% [markdown]
# Every one of the 25 primary chromosomes is present in both files under a
# different name, while the 169 sequences found only on the Ensembl side are
# its unplaced and unlocalized scaffolds. Matches follow the order of the first
# collection's FASTA, and a name list with more than one entry means the same
# sequence appears under several names in that file. The same operation is
# available from the command line as `refget store match`.

# %% [markdown]
# ## 6. Exporting sequences as FASTA
#
# `export_fasta()` writes a collection, or a named subset of it, to a FASTA
# file. On a remote store it fetches whatever it needs itself -- no separate
# download step first. A whole human genome is over 3 Gbp, so here we export
# just the mitochondrial genome.

# %%
output_path = os.path.join(temp_dir, "hg38_chrM.fa")
store.export_fasta(ucsc.digest, output_path, ["chrM"])

# export_fasta() already fetched chrM into the cache; get_sequence_by_name()
# here is just to read its length for the printout below, not a requirement.
chrM = store.get_sequence_by_name(ucsc.digest, "chrM")
print(f"Exported {chrM.metadata.name} ({chrM.metadata.length:,} bp) to: {output_path}")
print(f"File size: {os.path.getsize(output_path):,} bytes")
print("\nFirst 3 lines:")
with open(output_path) as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        print(line.rstrip())

# %% [markdown] output
# ```
# Downloading sequence k3grVkjY-hoWcCUojHw6VU6GE3MZ8Sct...
# Exported chrM (16,569 bp) to: /tmp/jungle_tutorial_79aqbeoh/hg38_chrM.fa
# File size: 16,783 bytes
#
# First 3 lines:
# >chrM
# GATCACAGGTCTATCACCCTATTAACCACTCACGGGAGCTCTCCATGCATTTGGTATTTTCGTCTGGGGGGTATGCACGC
# GATAGCATTGCGAGACGCTGGAGCCGGAGCACCCTATGTCGCAGTATCTGTCTTTGATTCCTGCCTCATCCTATTATTTA
# ```

# %% [markdown]
# Pass `None` instead of a name list to export the whole collection -- on a
# remote store that fetches every sequence, so make sure that is what you
# want before running it on a multi-gigabase genome. The optional last
# argument sets the FASTA line width.

# %% [markdown]
# <div class="admonition success">
#   <p class="admonition-title">Summary</p>
#   <ul>
#     <li>The jungle store gathers <strong>human and mouse reference assemblies from many providers</strong> into one content-addressed store served from S3.</li>
#     <li><strong><code>open_remote()</code></strong> connects to it with a local cache; only the sequences you touch are downloaded.</li>
#     <li><strong>Alias namespaces</strong> (<code>accession</code>, <code>genome_assembly</code>, <code>name</code>, and others) let you find genomes by familiar identifiers instead of digests.</li>
#     <li><strong><code>compare()</code></strong> reports what two assemblies share, and <strong><code>match_sequence_names()</code></strong> translates chromosome names between providers by sequence content.</li>
#     <li><strong><code>export_fasta()</code></strong> writes a collection or a named subset to FASTA.</li>
#   </ul>
# </div>

# %% [markdown]
# ## What's next?
#
# - [The reference genome jungle](../genome-collections-explained.md) -- What the jungle store holds and how it relates to the other public stores
# - [RefgetStore tutorial](refgetstore.py) -- General store operations: creating stores, retrieving sequences, extracting regions
# - [Working with aliases](aliases.py) -- Managing your own aliases: adding, resolving, bulk loading, and removing aliases
# - [FHR metadata headers](fhr-metadata.py) -- Attaching assembly metadata (species, version, masking) to collections
