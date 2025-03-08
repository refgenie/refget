import refget


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


seqcols = dbc.seqcol.list()
dbc.attribute.list("lengths")

sc1 = dbc.seqcol.get("RvFXEYkqNYw4_r8l67-tzNfj2k2PYlv2")
rows = dbc.truncate()
x = dbc.seqcol.add_from_fasta_file(f)
f2 = os.path.join(fa_root, DEMO_FILES[2])
x2 = dbc.seqcol.add_from_fasta_file(f2)


refget.fasta_to_seqcol(f)
f = os.path.join(fa_root, DEMO_FILES[1])
csc = refget.SequenceCollection.from_dict(fasta_to_seqcol(f))

fromdb = dbc.seqcol.get(csc.digest)

csc
csc0 = refget.SequenceCollection.from_dict(fasta_to_seqcol(os.path.join(fa_root, DEMO_FILES[0])))

f = os.path.join(fa_root, DEMO_FILES[3])
csc3 = refget.SequenceCollection.from_dict(fasta_to_seqcol(f))
csc.lengths
sc4 = refget.SequenceCollection.from_dict(fasta_to_seqcol(os.path.join(fa_root, DEMO_FILES[4])))

# What was the problem? That even just *creating* the object rom the other one...
# so I was saying: names = csc4.names, and that was *connected* to csc4.lengths,
# so it was trying to insert that one on the csc.

print(f"names: {names}\n", f"lengths: {lengths}\n", f"sequences: {sequences}")

import json

print(
    json.dumps(
        demo_results,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    )
)

# What I need:
# - [ ] RefgetDBAgent, replaces SeqColHenge and Henge objects
# - [ ] functions for computing digests and
# creating these pydantic object representations nicer

# - [ ] wire up endpoints to this new object
# - [ ] use peppy to grab a pep, process fastq.gz files?


from refget import fasta_to_seqcol

fasta_to_seqcol("demo_fasta/demo0.fa")
fasta_to_seqcol("/home/nsheff/sandbox/HG002.alt.pat.f1_v2.unmasked.fa.gz")


import gtars

import gc_count
from refget import sha512t24u_digest
from refget import sha512t24u_digest_bytes


gc_count.checksum_from_str("test").sha512
gc_count.sha512t24u_digest("test")
sha512t24u_digest_bytes("test")


var = "VB84F57JQBHY8SDPXJQ06P1STTEV8ZUPLX5T76OYSH88DM8IV9A9KSYJ0DBLQM665UZZC5033LW26RR1AQFKQ84BGHZLFZKRRBWN877GB1IP15KVJ9LX6Z1K0087WJGFB0HYKYQQZ0R24A77M6PY1ZY9E3TAAO7SI2UEI3MORCQUUXFB59L54M01NF8IWYA4579DL47VJ9DVAPUVJHX9FIK4BUN71UMOOIML9UKLIGDP9N80JJMIEJQKM85M8BEWQF8KS8DN77VVWBMO76VR2K8EHTBF403IWYAF3J2Z9WEDMQKAA0IJKGCHLYK7Y3WSODLDNWCRUU3UGSVPE7CJFZI6O9RMLARB1Y66CZ125L8ERKFU0UY53SNO5DNGGC0D5DOGH8MCZQYRJXELOQNA7KOHLVPBMRNQYVP1A49I3H2Y6DE8FG0WAXIZ6RKFNEBU4ES3X18E79KRJO2DKCXAYYMRPM4WMX8WIC9EP4K6Q07T7UM7G4S4TG31FS9WOUX9BIVFL0642307KV2SFG9YNH5IZB9IJ4TUMM1D25NBBECUMMM28JGZQ2765SZOYRL3BVIZBU1G8NN8Z7N2WEK08FV22LA5YE7GB6GTCEH4ISA2WBTBUEJH65V3MX8EVEU2FDLZKI02O27N3GQT556ZI2YY44GZDWV1Z21RWOWM411X4FFJ2BZ7LQAG5I9J3U4BIF7F3ESKOOIHG388V0PG95ZF5AW1IGD2T6VM9TPJN3HRNWGMHAU3M6O1C6HJBMHB6P26CZJEBZ1K75L35KV9S9UU4NYUJH0KADJNXFI9WVRI7AG89OOVWXQ2GSBT4QUYJW1UZDJ53JQ8M1FVS8J3KTVCSXUW97M8WCNNKQOFB7LHC4YHUZSRKA103L6DPBQG3MTAKPZ9VW5PTQ9QXFX5TMJHU5YOTJAFZ80ISSPX5ZUPABZ1SUZWHRR951CBZ3TYYO88BFNLGR1HKSCZZWG471PPW561NLGINKKBBD9P"

import random
import timeit
import string

strs = []
for i in range(1000):
    strs.append("".join(random.choices(string.ascii_uppercase + string.digits, k=1000)))


# Define the functions to benchmark
def benchmark_sha512t24u_digest():
    for var in strs:
        sha512t24u_digest(var)


def benchmark_gc_count_checksum():
    for var in strs:
        gc_count.checksum_from_str(var).sha512


def benchmark_gc_sha512_only():
    for var in strs:
        gc_count.sha512t24u_digest(var)


# Benchmark the functions
time_sha512t24u_digest = timeit.timeit(benchmark_sha512t24u_digest, number=1000)
time_gc_count_checksum = timeit.timeit(benchmark_gc_count_checksum, number=1000)
time_gc_512_only = timeit.timeit(benchmark_gc_sha512_only, number=1000)

print(f"sha512t24u_digest: {time_sha512t24u_digest} seconds")
print(f"gc_count.checksum_from_str().sha512: {time_gc_count_checksum} seconds")
print(f"gc_count.sha512t24u_digest: {time_gc_512_only} seconds")


# Reading the data from a client
import refget

seq_client = refget.SequencesClient(urls=["https://www.ebi.ac.uk/ena/cram"])
seq_client.get_sequence("6681ac2f62509cfc220d78751b8dc524", start=0, end=10)
seq_client.get_metadata("6681ac2f62509cfc220d78751b8dc524")
seq_client.service_info()
seq_client


col_client = refget.SequenceCollectionsClient(urls=["http://127.0.0.1:8100"])
col_client.list_collections()
col_client.get_collection("UNGAdNDmBbQbHihecPPFxwTydTcdFKxL")
col_client.service_info()
col_client


seq_client = refget.SequencesClient(urls=["http://127.0.0.1:8100"])
seq_client.get_sequence("iYtREV555dUFKg2_agSJW6suquUyPpMw")
seq_client.get_sequence("iYtREV555dUFKg2_agSJW6suquUyPpMw", start=0, end=4)

seq_client.get_metadata("6681ac2f62509cfc220d78751b8dc524")
seq_client.service_info()
seq_client

col_client.list_collections()

demo_results["test_fasta/base.fa"].sequences
DEMO_FILES


col_client.compare(
    demo_results["test_fasta/base.fa"].digest, demo_results["test_fasta/different_names.fa"].digest
)
