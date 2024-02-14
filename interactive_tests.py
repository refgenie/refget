import seqcol
from seqcol import SeqColHenge


scc = SeqColHenge(database={}, schemas=["seqcol/schemas/SeqColArraySet.yaml"])
scc

fa_file = "demo_fasta/demo0.fa"
fa_object = seqcol.parse_fasta(fa_file)

skip_seq = False
aslist = []
names = []
lengths = []
lengthsi = []
sequences = []
for k in fa_object.keys():
    seq = str(fa_object[k])
    names.append(k)
    lengths.append(str(len(seq)))
    lengthsi.append(len(seq))
    sequences.append(seq)

array_set = {"names": names, "lengths": lengths, "sequences": sequences}

collection_checksum = scc.insert(array_set, "SeqColArraySet")
collection_checksum

scc.retrieve(collection_checksum)
scc.retrieve(collection_checksum, reclimit=1)

# scc.retrieve("5c4b07f08319d3d0815f5ee25c45916a01f9d1519f0112e8")

scc.retrieve(collection_checksum, reclimit=1)
scc.retrieve(collection_checksum, reclimit=2)
scc.retrieve(collection_checksum)
scc.supports_inherent_attrs

# Now a test of inherent attributes
import seqcol

scci = seqcol.SeqColHenge(database={}, schemas=["seqcol/schemas/SeqColArraySetInherent.yaml"])
scci
scci.schemas


fa_file = "demo_fasta/demo0.fa"
fa_object = seqcol.parse_fasta(fa_file)

array_set_i = {"names": names, "lengths": lengthsi, "sequences": sequences, "author": "urkel"}
array_set_i2 = {"names": names, "lengths": lengthsi, "sequences": sequences, "author": "nathan"}


di = scci.insert(array_set_i, "SeqColArraySet")
di = scci.insert(array_set_i2, "SeqColArraySet")
di
# scc.retrieve(di)
scci.retrieve(di)
fasta_path = "demo_fasta"
fasta1 = "demo2.fa"
fasta2 = "demo3.fa"
fasta5 = "demo5.fa.gz"
fasta6 = "demo6.fa"

import os

d = scci.load_fasta_from_filepath(os.path.join(fasta_path, fasta1))
d2 = scci.load_fasta_from_filepath(os.path.join(fasta_path, fasta2))
d2 = scci.load_fasta_from_filepath(os.path.join(fasta_path, fasta2))
d5 = scci.load_fasta_from_filepath(os.path.join(fasta_path, fasta5))
d6 = scci.load_fasta_from_filepath(os.path.join(fasta_path, fasta6))
scci.retrieve(d["digest"])

scci.retrieve(d5["digest"])

fa_object = seqcol.parse_fasta(os.path.join(fasta_path, fasta1))
SCAS = seqcol.fasta_to_csc(fa_object)
digest = scci.insert(SCAS, "SeqColArraySet", reclimit=1)


d["digest"]
d2["digest"]

scci.compare_digests(d["digest"], d2["digest"])
scci.compare(d["SCAS"], d2["SCAS"])


json.dumps(scci.compare(d5["SCAS"], d6["SCAS"]))
print(
    json.dumps(
        scci.compare(d5["SCAS"], d6["SCAS"]),
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    )
)

build_sorted_name_length_pairs(array_set_i)

# reorder

array_set_reordered = {}
for k, v in array_set.items():
    print(k, v)
    array_set_reordered[k] = list(reversed(v))

array_set
array_set_reordered

build_sorted_name_length_pairs(array_set)
build_sorted_name_length_pairs(array_set_reordered)


import henge


from henge import md5

names = []
lengths = []
seq_digests = []
for k in fa_object.keys():
    seq = str(fa_object[k])
    names.append(k)
    lengths.append(str(len(seq)))
    seq_digests.append(scc.checksum_function(seq))


array_set = {"names": names, "lengths": lengths, "sequences": seq_digests}
array_set
collection_checksum = scc.insert(array_set, "SeqColArraySet", reclimit=1)

scc.database = {}
scc.retrieve("d229d5c16b3a1b3788f01aa439f01e682ba84bc9935ad08a", reclimit=1)
scc.retrieve("d229d5c16b3a1b3788f01aa439f01e682ba84bc9935ad08a", reclimit=2)
scc.database[collection_checksum]
scc.checksum_function


scc.database["d229d5c16b3a1b3788f01aa439f01e682ba84bc9935ad08a"]

scc.database["a99fe2e92875099c84f73b20ef8e7dd2f2d12f063383bed0"]
scc.database["ca82b053295b6f49923d0b2cedb83de49c6be59688c3dfd9"]


import os

os.getcwd()


## standalone functions

import seqcol

fa_file = "demo_fasta/demo0.fa"
fa_object = seqcol.parse_fasta(fa_file)

# get a canonical seqcol object
csc = seqcol.fasta_to_csc(fa_object)
csc
import json

print(json.dumps(csc, indent=2))


seqcol.seqcol_digest(csc)
