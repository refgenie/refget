import os
import refget
import json

from refget.models import Sequence
from refget.agents import RefgetDBAgent

DEMO_FASTA = json.load(open("test_fasta/test_fasta_digests.json"))
fa_root = "test_fasta"
dbc = RefgetDBAgent()  # Parameters are read from the environment


# simple fasta file parser
def parse_fasta(fasta_file):
    with open(fasta_file, "r") as f:
        lines = f.readlines()
    seqs = {}
    seq = None
    for line in lines:
        if line.startswith(">"):
            if seq:
                seqs[seq_name] = seq
            seq_name = line.strip().replace(">", "")
            seq = ""
        else:
            seq += line.strip()
    seqs[seq_name] = seq
    return seqs


# Load some sequences
demo_results = {}
for demo_file in DEMO_FASTA:
    f = os.path.join(fa_root, demo_file["name"])
    print("Fasta file to be loaded: {}".format(f))
    seqs = parse_fasta(f)
    for seq_name, seq in seqs.items():
        print("Sequence to be loaded: {}".format(seq_name))
        seq_obj = Sequence(
            digest=refget.digest_functions.sha512t24u_digest(seq), sequence=seq, length=len(seq)
        )
        demo_results[seq_obj.digest] = dbc.seq.add(seq_obj)
    print(demo_results[seq_obj.digest])
