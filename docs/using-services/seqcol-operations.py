# %% [markdown]
# # Seqcol Operations
#
# This guide covers the sequence collection (seqcol) features of RefgetStore:
# retrieving collections at different detail levels, comparing collections,
# looking up collections by attribute digest, and controlling ancillary digest
# computation.
#
# **Prerequisites:** You need the `refget` package installed with gtars support
# (`pip install refget[all]`). This guide assumes familiarity with creating a
# RefgetStore and loading FASTA files (see the [RefgetStore tutorial](refgetstore.py)).

# %% [markdown]
# ## Setup
#
# Create two FASTA files with overlapping and distinct sequences, then load them
# into a store.

# %%
import os
import json
import tempfile

from refget.store import RefgetStore, digest_fasta

temp_dir = tempfile.mkdtemp(prefix="seqcol_howto_")

# First genome: two chromosomes
fasta1_path = os.path.join(temp_dir, "genome_a.fa")
with open(fasta1_path, "w") as f:
    f.write(">chr1\nACGTACGTACGTACGT\n>chr2\nGGGGAAAATTTTCCCC\n")

# Second genome: shares chr1 sequence, has different chr3
fasta2_path = os.path.join(temp_dir, "genome_b.fa")
with open(fasta2_path, "w") as f:
    f.write(">chr1\nACGTACGTACGTACGT\n>chr3\nTTTTAAAACCCCGGGGNNNNACGT\n")

store = RefgetStore.in_memory()
store.set_quiet(True)
store.add_sequence_collection_from_fasta(fasta1_path)
store.add_sequence_collection_from_fasta(fasta2_path)

# Get the collection digests for later use
digest_a = digest_fasta(fasta1_path).digest
digest_b = digest_fasta(fasta2_path).digest

print(f"Collection A: {digest_a}")
print(f"Collection B: {digest_b}")
print(f"Store has {len(store)} sequences")





# %% [markdown] output
# ```
# Collection A: g-n-_M2U_wMQJAH0LqKM0LxopwLHFB5x
# Collection B: K-uGppCoHaQJTuh-yUu79kDWjWomOcPE
# Store has 3 sequences
# ```

# %% [markdown]
# ## Level 1 retrieval
#
# Level 1 returns the **attribute digests** for a collection -- one digest per
# attribute (names, lengths, sequences). This is the lightest representation and
# does not require loading sequence data.

# %%
lvl1 = store.get_collection_level1(digest_a)
print(json.dumps(lvl1, indent=2))





# %% [markdown] output
# ```
# {
#   "names": "XEsH8IMZ09CBX17iXEWRagH50VGfARLo",
#   "lengths": "SXn5hTjQiD4skTpQFXcuYanbRsslm5lu",
#   "sequences": "AlRtUvDP8tkadAMxTJ3ErccxJ1Ch79T1",
#   "name_length_pairs": "s8Bh4bruth2m-OAAJvMvHJtcg0IgFtbq",
#   "sorted_name_length_pairs": "weuiIikf4uTSGp0BoHaoP3iNjofokg2c",
#   "sorted_sequences": "EjQi8LUJO9s914OI7uxOdfo_FLKgwufV"
# }
# ```

# %% [markdown]
# ## Level 2 retrieval
#
# Level 2 returns the **full arrays** for each attribute -- the actual names,
# lengths, and sequence digests that make up the collection.

# %%
lvl2 = store.get_collection_level2(digest_a)
print(json.dumps(lvl2, indent=2))





# %% [markdown] output
# ```
# {
#   "names": [
#     "chr2",
#     "chr1"
#   ],
#   "lengths": [
#     16,
#     16
#   ],
#   "sequences": [
#     "SQ.8zS0M3VBpV7-TNdB7RjfpMbC8hrz6SbH",
#     "SQ.U1x5Qz66jmXmv_oJtfYmtUNkwq1wZ75u"
#   ]
# }
# ```

# %% [markdown]
# ## Comparing collections
#
# The `compare` method produces a detailed comparison of two collections
# following the seqcol specification. The result describes which attributes
# are shared, which array elements overlap, and whether shared elements
# appear in the same order.

# %%
result = store.compare(digest_a, digest_b)
print(json.dumps(result, indent=2))





# %% [markdown] output
# ```
# {
#   "digests": {
#     "a": "g-n-_M2U_wMQJAH0LqKM0LxopwLHFB5x",
#     "b": "K-uGppCoHaQJTuh-yUu79kDWjWomOcPE"
#   },
#   "attributes": {
#     "a_only": [],
#     "b_only": [],
#     "a_and_b": [
#       "lengths",
#       "name_length_pairs",
#       "names",
#       "sequences",
#       "sorted_name_length_pairs",
#       "sorted_sequences"
#     ]
#   },
#   "array_elements": {
#     "a_count": {
#       "name_length_pairs": 2,
#       "sorted_name_length_pairs": 2,
#       "lengths": 2,
#       "names": 2,
#       "sorted_sequences": 2,
#       "sequences": 2
#     },
#     "b_count": {
#       "name_length_pairs": 2,
#       "lengths": 2,
#       "sorted_name_length_pairs": 2,
#       "sorted_sequences": 2,
#       "sequences": 2,
#       "names": 2
#     },
#     "a_and_b_count": {
#       "lengths": 1,
#       "sorted_name_length_pairs": 1,
#       "names": 1,
#       "name_length_pairs": 1,
#       "sequences": 1,
#       "sorted_sequences": 1
#     },
#     "a_and_b_same_order": {
#       "sequences": null,
#       "lengths": null,
#       "sorted_name_length_pairs": null,
#       "name_length_pairs": null,
#       "names": null,
#       "sorted_sequences": null
#     }
#   }
# }
# ```

# %% [markdown]
# The comparison shows:
#
# - **`attributes.a_and_b`**: Both collections have all six attribute keys
#   (names, lengths, sequences, plus the three ancillary attributes), though
#   the values differ. Neither has attribute keys the other lacks.
# - **`array_elements.a_and_b_count`**: One name ("chr1") appears in both, and
#   one length (16) is shared. Collection B's chr3 has a different length (24 bp),
#   so only one of the two length values overlaps.
# - **`array_elements.a_and_b_same_order`**: All values are `null`, meaning order
#   cannot be determined -- this happens when fewer than two elements overlap
#   within an attribute.

# %% [markdown]
# ## Finding collections by attribute
#
# To find which collections share a particular attribute value, use
# `find_collections_by_attribute`. Pass the attribute name and its level 1 digest.

# %%
# Get the "names" digest from collection A
names_digest = store.get_collection_level1(digest_a)["names"]
print(f"Looking for collections with names digest: {names_digest}")

# Find all collections that share this exact set of names
matches = store.find_collections_by_attribute("names", names_digest)
print(f"Matching collections: {matches}")





# %% [markdown] output
# ```
# Looking for collections with names digest: XEsH8IMZ09CBX17iXEWRagH50VGfARLo
# Matching collections: ['g-n-_M2U_wMQJAH0LqKM0LxopwLHFB5x']
# ```

# %% [markdown]
# Only collection A matched because collection B has different chromosome names
# (chr1 + chr3 instead of chr1 + chr2).

# %%
# Try with the "lengths" digest -- collection A has [16, 16], collection B has [16, 24]
lengths_digest = store.get_collection_level1(digest_a)["lengths"]
matches = store.find_collections_by_attribute("lengths", lengths_digest)
print(f"Collections sharing lengths digest: {matches}")





# %% [markdown] output
# ```
# Collections sharing lengths digest: ['g-n-_M2U_wMQJAH0LqKM0LxopwLHFB5x']
# ```

# %% [markdown]
# ## Getting attribute arrays
#
# To retrieve the raw array behind an attribute digest, use `get_attribute`.
# This returns the actual names, lengths, or sequence digests.

# %%
names_digest = store.get_collection_level1(digest_a)["names"]
names_array = store.get_attribute("names", names_digest)
print(f"Names array: {names_array}")

lengths_digest = store.get_collection_level1(digest_a)["lengths"]
lengths_array = store.get_attribute("lengths", lengths_digest)
print(f"Lengths array: {lengths_array}")

sequences_digest = store.get_collection_level1(digest_a)["sequences"]
sequences_array = store.get_attribute("sequences", sequences_digest)
print(f"Sequences array: {sequences_array}")





# %% [markdown] output
# ```
# Names array: ['chr2', 'chr1']
# Lengths array: [16, 16]
# Sequences array: ['SQ.8zS0M3VBpV7-TNdB7RjfpMbC8hrz6SbH', 'SQ.U1x5Qz66jmXmv_oJtfYmtUNkwq1wZ75u']
# ```

# %% [markdown]
# If no collection contains a matching attribute, `get_attribute` returns `None`:

# %%
result = store.get_attribute("names", "nonexistent_digest_value_here")
print(f"Result for unknown digest: {result}")





# %% [markdown] output
# ```
# Result for unknown digest: None
# ```

# %% [markdown]
# ## Ancillary digests
#
# By default, RefgetStore computes **all six attributes**: the three core
# attributes (`names`, `lengths`, `sequences`) plus three ancillary ones
# (`name_length_pairs`, `sorted_name_length_pairs`, `sorted_sequences`).
#
# The ancillary digests are useful for identifying collections that share
# the same coordinate system regardless of sequence order. You can disable
# them if you only need the core attributes.

# %%
# Ancillary digests are enabled by default
print(f"Ancillary digests enabled: {store.has_ancillary_digests()}")

# Level 1 includes all 6 attributes by default
lvl1_basic = store.get_collection_level1(digest_a)
print(f"Attributes (full): {list(lvl1_basic.keys())}")





# %% [markdown] output
# ```
# Ancillary digests enabled: True
# Attributes (full): ['names', 'lengths', 'sequences', 'name_length_pairs', 'sorted_name_length_pairs', 'sorted_sequences']
# ```

# %% [markdown]
# Disable ancillary digests to see only the three core attributes. New
# collections loaded after disabling will have only core attributes.

# %%
store.disable_ancillary_digests()
print(f"Ancillary digests enabled: {store.has_ancillary_digests()}")

# Create a fresh store with ancillary digests disabled
store2 = RefgetStore.in_memory()
store2.set_quiet(True)
store2.disable_ancillary_digests()
store2.add_sequence_collection_from_fasta(fasta1_path)
store2.add_sequence_collection_from_fasta(fasta2_path)

# Level 1 now includes only core attributes
lvl1_core = store2.get_collection_level1(digest_a)
print(f"Attributes (core only): {list(lvl1_core.keys())}")
print(json.dumps(lvl1_core, indent=2))





# %% [markdown] output
# ```
# Ancillary digests enabled: False
# Attributes (core only): ['names', 'lengths', 'sequences']
# {
#   "names": "XEsH8IMZ09CBX17iXEWRagH50VGfARLo",
#   "lengths": "SXn5hTjQiD4skTpQFXcuYanbRsslm5lu",
#   "sequences": "AlRtUvDP8tkadAMxTJ3ErccxJ1Ch79T1"
# }
# ```

# %% [markdown]
# The `sorted_name_length_pairs` digest is the same whether collections differ
# only in sequence order -- making it a sort-invariant coordinate system
# identifier. Use `find_collections_by_attribute` with `sorted_name_length_pairs`
# to find collections that share the same coordinate system.

# %%
# Re-enable ancillary digests
store2.enable_ancillary_digests()
print(f"Ancillary digests enabled: {store2.has_ancillary_digests()}")





# %% [markdown] output
# ```
# Ancillary digests enabled: True
# ```

# %% [markdown]
# ## Summary
#
# You have now used the seqcol features of RefgetStore to:
#
# - Retrieve level 1 (attribute digests) and level 2 (full arrays) representations
# - Compare two collections and interpret the comparison result
# - Find collections by attribute digest and retrieve attribute arrays
# - Enable and disable ancillary digest computation
#
# For related how-to guides, see:
#
# - [Working with Aliases](aliases.py) -- Assign human-readable names to collections
# - [FHR Metadata Headers](fhr-metadata.py) -- Attach FAIR metadata to collections

# %% [markdown]
# ## Cleanup

# %%
import shutil
shutil.rmtree(temp_dir)
