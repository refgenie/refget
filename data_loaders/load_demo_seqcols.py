import os
import json

from refget.agents import RefgetDBAgent

# Before running this script, you'll need to set up env vars like so:
# source deployment/local_demo/local_demo.env


fa_root = "test_fasta"
DEMO_FASTA = json.load(open("test_fasta/test_fasta_digests.json"))
dbc = RefgetDBAgent()  # Parameters are read from the environment
print(f"SQL Engine: {dbc.engine}")

# Load some fasta files into the database

demo_results = {}
for name, demo_file in DEMO_FASTA.items():
    f = os.path.join(fa_root, demo_file["name"])
    print("Fasta file to be loaded: {}".format(f))
    demo_results[f] = dbc.seqcol.add_from_fasta_file_with_name(
        f, human_readable_name=name, update=True
    )
    print(demo_results[f])

# demo_results = {}
#
# for name, demo_file in DEMO_FASTA.items():
#     f = os.path.join(fa_root, demo_file["name"])
#     print("Fasta file to be loaded: {}".format(f))
#     name = name + "_ADDITIONAL_NICKNAME"
#     demo_results[f] = dbc.seqcol.add_from_fasta_file_with_name(
#         f, human_readable_name=name, update=True
#     )
#     print(demo_results[f])

# You can explore these results like this:
# with Session(dbc.engine) as session:
#     session.add(demo_results["test_fasta/base.fa"])
#     print("Digest is: ", demo_results["test_fasta/base.fa"].digest)
