import peppy
import argparse
import refget
import os

from sqlmodel import create_engine, SQLModel, Field, Session
from refget.models import *
from refget.agents import *

# A simple argparser to get the PEP and the fa_root
parser = argparse.ArgumentParser(description="Load a pangenome reference into the database")
parser.add_argument("pep", help="Path to the PEP file")
parser.add_argument("fa_root", help="Path to the root of the pangenome fasta files")
args = parser.parse_args()

prj = peppy.Project(args.pep)
fa_root = args.fa_root

# prj = peppy.Project("../seqcolapi/analysis/data/hprc.csv")
# fa_root = "/ext/qumulo/brickyard/datasets_downloaded/pangenome_fasta"

dbc = RefgetDBAgent()
print(f"SQL Engine: {dbc.engine}")
print("Using PEP file: ", args.pep)
print("Using fa_root: ", fa_root)

# pangenome_obj = {}
# for s in prj.samples:
#     file_path = os.path.join(fa_root, s.fasta)
#     print(f"Fasta to be loaded: Name: {s.sample_name} File path: {file_path}")
#     pangenome_obj[s.sample_name] = dbc.seqcol.add_from_fasta_file(file_path)


dbc.pangenome.add_from_fasta_pep(prj, fa_root)

# with Session(dbc.engine) as session:
#     with session.no_autoflush:
#         session.add(p)
#         session.commit()


#  Try retrieving the data like this:
# dbc.seqcol.list()
# sc = dbc.seqcol.get("8aA37TYgiVohRqfRhXEeklIAXf2Rs8jw")
# dbc.seqcol.get("8aA37TYgiVohRqfRhXEeklIAXf2Rs8jw", return_format="level2")

# pangenome_digest = "LWzar7AHabrhP8Byw64OV14QrUDfX8Yu"
# pangenome_digest = "YHuz_Us0SSJC0_UK2VIVXYX7SbpipD-b" # Demo

# dbc.pangenome.get(pangenome_digest, return_format="level1")
# dbc.pangenome.get(pangenome_digest, return_format="level2")
# dbc.pangenome.get(pangenome_digest, return_format="level3")
# dbc.pangenome.get(pangenome_digest, return_format="level4")


# from refget.utilities import build_pangenome_model
# p = build_pangenome_model(demo_results)

# res = dbc.pangenome.add(p)

# res

# dbc.pangenome.get()




