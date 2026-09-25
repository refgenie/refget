# %% [markdown]
# # Getting Started with refget
#
# This 5-minute tutorial shows you the essential refget workflow: install the
# package, compute a digest from a FASTA file, and inspect the result.
#
# <div class="admonition success">
#   <p class="admonition-title">Learning objectives</p>
#   <ul>
#     <li>Install the refget package</li>
#     <li>Compute a GA4GH digest for a FASTA file</li>
#     <li>Inspect individual sequence digests and metadata</li>
#   </ul>
# </div>
#
# **Prerequisites:** Python 3.9+

# %% [markdown]
# ## 1. Installation
#
# ```bash
# pip install refget
# ```
#
# This installs both the Python wrapper and the Rust-based gtars engine that
# handles fast digest computation.

# %% [markdown]
# ## 2. Compute a digest from a FASTA file
#
# The `digest_fasta` function reads a FASTA file and returns a
# `SequenceCollection` object containing the collection digest and metadata
# for every sequence. One function call, one digest.

# %%
import tempfile
import os

from refget import digest_fasta

# Create a small FASTA file to work with
temp_dir = tempfile.mkdtemp(prefix="refget_getting_started_")
fasta_path = os.path.join(temp_dir, "demo.fa")
with open(fasta_path, "w") as f:
    f.write(">chrX\nTTGGGGAA\n>chr1\nGGAA\n>chr2\nGCGC\n")

# Digest the FASTA file
collection = digest_fasta(fasta_path)
print("Collection digest:", collection.digest)


# %% [markdown] output
# ```
# Collection digest: XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk
# ```

# %% [markdown]
# ## 3. Inspect the sequence collection
#
# The returned `SequenceCollection` lets you iterate through each sequence
# and see its name, length, and GA4GH digest.

# %%
print(f"This collection has {len(collection)} sequences:\n")
for seq in collection:
    m = seq.metadata
    print(f"  {m.name:6s}  length={m.length}  sha512t24u={m.sha512t24u}")


# %% [markdown] output
# ```
# This collection has 3 sequences:
# 
#   chrX    length=8  sha512t24u=iYtREV555dUFKg2_agSJW6suquUyPpMw
#   chr1    length=4  sha512t24u=YBbVX0dLKG1ieEDCiMmkrTZFt_Z5Vdaj
#   chr2    length=4  sha512t24u=AcLxtBuKEPk_7PGE_H4dGElwZHCujwH6
# ```

# %% [markdown]
# ## 4. Compute a single sequence digest
#
# You can also compute a digest for a raw sequence string with
# `digest_sequence`. The digest is deterministic and content-based, so
# the same sequence always produces the same digest regardless of where
# it appears.

# %%
from refget import digest_sequence

record = digest_sequence(b"GCGC")
print("digest_sequence(b'GCGC'):", record.metadata.sha512t24u)
print()
print("This matches chr2 from our FASTA file above!")


# %% [markdown] output
# ```
# digest_sequence(b'GCGC'): AcLxtBuKEPk_7PGE_H4dGElwZHCujwH6
# 
# This matches chr2 from our FASTA file above!
# ```

# %% [markdown]
# ## 5. Use the CLI
#
# The same operation is available from the command line:
#
# ```bash
# refget fasta digest demo.fa
# ```

# %%
import subprocess

result = subprocess.run(
    ["refget", "fasta", "digest", fasta_path],
    capture_output=True,
    text=True,
)
print(result.stdout.strip())


# %% [markdown] output
# ```
# {
#   "digest": "XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk",
#   "file": "demo.fa"
# }
# ```

# %% [markdown]
# ## Summary and next steps
#
# <div class="admonition success">
#   <p class="admonition-title">Summary</p>
#   <ul>
#     <li><code>digest_fasta(path)</code> computes a GA4GH collection digest from a FASTA file</li>
#     <li>Each sequence gets a deterministic, content-based SHA-512/24u digest</li>
#     <li>The same operations are available via the <code>refget</code> CLI</li>
#   </ul>
# </div>
#
# ### What's next?
#
# - [What are refget digests?](../digests-explained.md) -- Understanding the algorithm behind digests
# - [RefgetStore tutorial](refgetstore.py) -- Storing and retrieving sequences locally
# - [Seqcol Operations](seqcol-operations.py) -- Comparing sequence collections
# - [CLI reference](../reference/cli.md) -- Full command-line documentation

# %%
# Cleanup
import shutil
shutil.rmtree(temp_dir)
