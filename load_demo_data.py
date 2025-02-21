from sqlmodel import create_engine, SQLModel, Field, Session
import refget, os
from tests.conftest import DEMO_FILES
from refget.models import *
from refget.agents import *

# Before running this script, you'll need to set up env vars like so:
# source deployment/local_demo/local_demo.env


fa_root = "test_fasta"
dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

# Load some fasta files into the database

demo_results = {}
for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    demo_results[f] = dbc.seqcol.add_from_fasta_file(f)
    print(demo_results[f])




# You can explore these results like this:
# with Session(dbc.engine) as session:
#     session.add(demo_results["test_fasta/base.fa"])
#     print("Digest is: ", demo_results["test_fasta/base.fa"].digest)



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

# Loading some sequences
demo_results = {}
for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    seqs = parse_fasta(f)
    for seq_name, seq in seqs.items():
        print("Sequence to be loaded: {}".format(seq_name))
        seq_obj = Sequence(digest=refget.digest_functions.sha512t24u_digest(seq), sequence=seq, length=len(seq))
        demo_results[seq_obj.digest] = dbc.seq.add(seq_obj)
    print(demo_results[seq_obj.digest])



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





col_client.compare(demo_results["test_fasta/base.fa"].digest, demo_results["test_fasta/different_names.fa"].digest)