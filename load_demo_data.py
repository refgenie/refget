from sqlmodel import create_engine, SQLModel, Field, Session
import refget, os
from tests.conftest import DEMO_FILES
from refget.models import *
from refget.agents import *

dbc = RefgetDBAgent()

fa_root="test_fasta"

# Load some fasta files into the database

demo_results = {}
for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    demo_results[f] = dbc.seqcol.add_from_fasta_file(f)
    print(demo_results[f])





import json
from refget import SeqColClient

template = """
Filepath: {f}
Digest: {digest}
Object: {pretty_str}
"""

scc = SeqColClient("http://127.0.0.1:8100")
scc.get_collection(digest)

for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    digest = refget.fasta_file_to_digest(f, dbc.inherent_attrs)
    pretty_str = scc.get_collection(digest)
    print(template.format(f=f, digest=digest, pretty_str=pretty_str))




# demo_results = {}
# for demo_file in DEMO_FILES:
#     f = os.path.join(fa_root, demo_file)
#     print("Fasta file to be loaded: {}".format(f))
#     demo_results[f] = dbc.seqcol.add_from_fasta_file(f)

