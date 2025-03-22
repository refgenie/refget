import os
import refget

from tests.conftest import DEMO_FILES
from refget import canonical_str, sha512t24u_digest

fa_root = "test_fasta"

sc0 = refget.SequenceCollection.from_fasta_file(os.path.join(fa_root, DEMO_FILES[0]))
sc1 = refget.SequenceCollection.from_fasta_file(os.path.join(fa_root, DEMO_FILES[1]))

refget.compare_seqcols(sc0.level2(), sc1.level2())


refget.build_sorted_name_length_pairs(sc0.level2())
nlp = refget.build_name_length_pairs(sc1.level2())

# option 1 (way we abandoned that tried to use intermediate strings)
snlp = [canonical_str(x).decode("utf-8") for x in nlp]
snlp.sort()
snlp
snlp_digest = sha512t24u_digest(canonical_str(snlp))

# option 2 (way we decided to do it)
snlp_digests = []  # name-length digests
for i in range(len(nlp)):
    snlp_digests.append(sha512t24u_digest(canonical_str(nlp[i])))
snlp_digests.sort()


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

# What was the problem? That even just *creating* the object from the other one...
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


refget.SequenceCollection.from_fasta_file("demo_fasta/demo0.fa")
refget.SequenceCollection.from_fasta_file(
    "/home/nsheff/sandbox/HG002.alt.pat.f1_v2.unmasked.fa.gz"
)

import gtars

import gc_count
from refget import sha512t24u_digest
from refget import sha512t24u_digest_bytes

sha512t24u_digest_bytes("test")


# --------------------------------------------------
# Benchmarking digest functions

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


# --------------------------------------------------
# Reading the data from a client
import refget

seq_client = refget.SequenceClient(urls=["https://www.ebi.ac.uk/ena/cram"])
seq_client.get_sequence("6681ac2f62509cfc220d78751b8dc524", start=0, end=10)
seq_client.get_metadata("6681ac2f62509cfc220d78751b8dc524")
seq_client.service_info()
seq_client


col_client = refget.SequenceCollectionClient(urls=["http://127.0.0.1:8100"])
col_client.list_collections()
col_client.get_collection("UNGAdNDmBbQbHihecPPFxwTydTcdFKxL")
col_client.service_info()
col_client


seq_client = refget.SequenceClient(urls=["http://127.0.0.1:8100"])
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


col_client = refget.SequenceCollectionClient(urls=["https://seqcolapi.databio.org"])
col_client.list_collections()
col_client.get_collection("XZlrcEGi6mlopZ2uD8ObHkQB1d0oDwKk", level=1)

