from sqlmodel import create_engine, SQLModel, Field, Session
import refget, os
from tests.conftest import DEMO_FILES
from refget.models import *
from refget.agents import *

# Before running this script, you'll need to set up env vars like so:
# source deployment/local_demo/local_demo.env 


dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")

fa_root="test_fasta"

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
