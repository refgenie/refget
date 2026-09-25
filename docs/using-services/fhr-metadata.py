# %% [markdown]
# # FHR Metadata Headers
#
# This guide shows how to attach
# [FAIR Headers Reference genome (FHR)](https://github.com/FAIR-bioHeaders/FHR-Specification)
# metadata to sequence collections in RefgetStore. FHR provides a standard way to
# describe genome assemblies with structured metadata -- species, version, authors,
# taxonomy, and more -- following the FAIR principles.
#
# **Prerequisites:** You have an on-disk or in-memory RefgetStore with at least one
# loaded sequence collection, and you are familiar with [RefgetStore basics](refgetstore.py).

# %% [markdown]
# ## Setup
#
# Create a temporary FASTA file and load it into a RefgetStore.

# %%
import json
import os
import tempfile

from refget.store import RefgetStore
from gtars.refget import FhrMetadata

temp_dir = tempfile.mkdtemp(prefix="fhr_howto_")

# Create a demo FASTA file
fasta_path = os.path.join(temp_dir, "genome.fa")
with open(fasta_path, "w") as f:
    f.write(">chr1\nATGCATGCATGCAGTCGTAGCNNNATGCATGC\n>chr2\nGGGGAAAATTTTCCCC\n")

# Create an on-disk store and load the genome
store_path = os.path.join(temp_dir, "my_store")
store = RefgetStore.on_disk(store_path)
store.set_quiet(True)
meta, _ = store.add_sequence_collection_from_fasta(fasta_path)
collection_digest = meta.digest

print(f"Collection digest: {collection_digest}")





# %% [markdown] output
# ```
# Collection digest: NikmJ6xnuvO741NgL-zszh5_p4DsD3nV
# ```

# %% [markdown]
# ## Create FHR metadata programmatically
#
# Construct an `FhrMetadata` object by passing keyword arguments. Multi-word field
# names use **camelCase** (matching the FHR JSON schema), while Python getter
# properties use snake_case. Not all fields have dedicated getters; use `to_dict()`
# to access any field. Properties with getters include: `genome`, `version`,
# `masking`, `genome_synonym`, `voucher_specimen`, `documentation`, `identifier`,
# `scholarly_article`, and `funding`.

# %%
fhr = FhrMetadata(
    schema="https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
    schemaVersion=1.0,
    genome="Homo sapiens",
    version="GRCh38.p14",
    taxon={
        "name": "Homo sapiens",
        "uri": "https://identifiers.org/taxonomy:9606",
    },
    masking="soft-masked",
    genomeSynonym=["hg38"],
    dateCreated="2024-06-15",
    license="CC0-1.0",
)

print(repr(fhr))
print(f"genome:         {fhr.genome}")
print(f"version:        {fhr.version}")
print(f"masking:        {fhr.masking}")
print(f"genome_synonym: {fhr.genome_synonym}")





# %% [markdown] output
# ```
# FhrMetadata(genome='Homo sapiens', version='GRCh38.p14')
# genome:         Homo sapiens
# version:        GRCh38.p14
# masking:        soft-masked
# genome_synonym: ['hg38']
# ```

# %% [markdown]
# ## Attach metadata to a collection
#
# Use `set_fhr_metadata` to associate the metadata with a specific sequence
# collection. On an on-disk store, this writes a sidecar JSON file
# (`<digest>.fhr.json`) into the `collections/` directory.

# %%
store.set_fhr_metadata(collection_digest, fhr)
print(f"Metadata attached to {collection_digest}")

# Verify the sidecar file was written
sidecar_path = os.path.join(store_path, "collections", f"{collection_digest}.fhr.json")
print(f"Sidecar exists: {os.path.exists(sidecar_path)}")





# %% [markdown] output
# ```
# Metadata attached to NikmJ6xnuvO741NgL-zszh5_p4DsD3nV
# Sidecar exists: True
# ```

# %% [markdown]
# ## Retrieve metadata
#
# Retrieve the `FhrMetadata` object for a collection, then inspect it as a
# Python dictionary with `to_dict()`.

# %%
retrieved = store.get_fhr_metadata(collection_digest)
print(repr(retrieved))
print(f"genome:  {retrieved.genome}")
print(f"version: {retrieved.version}")

# Get all fields as a dictionary
d = retrieved.to_dict()
print(f"\nFull metadata dict:")
for key, value in d.items():
    print(f"  {key}: {value}")





# %% [markdown] output
# ```
# FhrMetadata(genome='Homo sapiens', version='GRCh38.p14')
# genome:  Homo sapiens
# version: GRCh38.p14
#
# Full metadata dict:
#   schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json
#   schemaVersion: 1.0
#   genome: Homo sapiens
#   taxon: {'name': 'Homo sapiens', 'uri': 'https://identifiers.org/taxonomy:9606'}
#   version: GRCh38.p14
#   dateCreated: 2024-06-15
#   masking: soft-masked
#   genomeSynonym: ['hg38']
#   license: CC0-1.0
# ```

# %% [markdown]
# ## Load metadata from a JSON file
#
# If you already have FHR metadata as a JSON file, you can load it in two ways:
#
# - `FhrMetadata.from_json(path)` -- parse a JSON file into a Python object
# - `store.load_fhr_metadata(digest, path)` -- parse and attach in one step

# %%
# Write an example FHR JSON file
fhr_json_path = os.path.join(temp_dir, "grch38.fhr.json")
fhr_data = {
    "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
    "schemaVersion": 1.0,
    "genome": "Homo sapiens",
    "version": "GRCh38.p14",
    "taxon": {
        "name": "Homo sapiens",
        "uri": "https://identifiers.org/taxonomy:9606",
    },
    "masking": "soft-masked",
    "genomeSynonym": ["hg38"],
    "metadataAuthor": [
        {"name": "Jane Doe", "uri": "https://orcid.org/0000-0001-2345-6789"}
    ],
}
with open(fhr_json_path, "w") as f:
    json.dump(fhr_data, f, indent=2)

print(f"Wrote FHR JSON to: {fhr_json_path}")

# Option 1: Parse JSON into a Python object
fhr_from_file = FhrMetadata.from_json(fhr_json_path)
print(f"\nParsed from file: {repr(fhr_from_file)}")

# Option 2: Load and attach directly to a collection
store.load_fhr_metadata(collection_digest, fhr_json_path)
print(f"Loaded and attached to {collection_digest}")





# %% [markdown] output
# ```
# Wrote FHR JSON to: /tmp/fhr_howto_csbxoccr/grch38.fhr.json
#
# Parsed from file: FhrMetadata(genome='Homo sapiens', version='GRCh38.p14')
# Loaded and attached to NikmJ6xnuvO741NgL-zszh5_p4DsD3nV
# ```

# %% [markdown]
# ## Export metadata to JSON
#
# Write an `FhrMetadata` object to a JSON file with `to_json()`.

# %%
export_path = os.path.join(temp_dir, "exported.fhr.json")
retrieved = store.get_fhr_metadata(collection_digest)
retrieved.to_json(export_path)

# Verify the exported file
with open(export_path) as f:
    exported = json.load(f)
print(json.dumps(exported, indent=2))





# %% [markdown] output
# ```
# {
#   "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
#   "schemaVersion": "1.0",
#   "genome": "Homo sapiens",
#   "taxon": {
#     "name": "Homo sapiens",
#     "uri": "https://identifiers.org/taxonomy:9606"
#   },
#   "version": "GRCh38.p14",
#   "metadataAuthor": [
#     {
#       "name": "Jane Doe",
#       "uri": "https://orcid.org/0000-0001-2345-6789"
#     }
#   ],
#   "masking": "soft-masked",
#   "genomeSynonym": [
#     "hg38"
#   ]
# }
# ```

# %% [markdown]
# ## List and remove metadata
#
# Use `list_fhr_metadata()` to find which collections have FHR metadata, and
# `remove_fhr_metadata()` to detach it.

# %%
# List collections with FHR metadata
digests_with_fhr = store.list_fhr_metadata()
print(f"Collections with FHR metadata: {digests_with_fhr}")

# Remove FHR metadata from a collection
removed = store.remove_fhr_metadata(collection_digest)
print(f"\nRemoved: {removed}")

# Confirm removal
print(f"After removal: {store.get_fhr_metadata(collection_digest)}")
print(f"Collections with FHR metadata: {store.list_fhr_metadata()}")





# %% [markdown] output
# ```
# Collections with FHR metadata: ['NikmJ6xnuvO741NgL-zszh5_p4DsD3nV']
#
# Removed: True
# After removal: None
# Collections with FHR metadata: []
# ```

# %%
# Cleanup
import shutil
shutil.rmtree(temp_dir)
