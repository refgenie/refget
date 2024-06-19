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




from sqlmodel import create_engine, SQLModel, Field, Session
import refget, os
from tests.conftest import DEMO_FILES
from refget.models import *
from refget.agents import *


fa_root="demo_fasta"
f = os.path.join(fa_root, DEMO_FILES[0])
print("Fasta file to be loaded: {}".format(f))
postgres_url = "postgresql://postgres:postgres@localhost/postgres"
dbc = RefgetDBAgent(postgres_url)

sc1 = dbc.seqcol.get("RvFXEYkqNYw4_r8l67-tzNfj2k2PYlv2")
rows = dbc.truncate()
x = dbc.seqcol.add_from_fasta_file(f)
f2 = os.path.join(fa_root, DEMO_FILES[2])
x2 = dbc.seqcol.add_from_fasta_file(f2)


y = x
y.names_digest=123
y = SequenceCollection(**x.model_dump())

from sqlmodel import insert

with Session(dbc.engine) as session:
    session.add(y)
    session.commit()

with Session(dbc.engine) as session:
    stmt = insert(SequenceCollection).values(y.model_dump())
    dbc.engine.exec(stmt.on_conflict_do_nothing())

from sqlalchemy.dialects.postgresql import insert


with Session(dbc.engine) as session:
    stmt = insert(SequenceCollection).values(y.model_dump()).on_conflict_do_nothing()
    session.exec(stmt)




refget.fasta_file_to_seqcol(f)
f = os.path.join(fa_root, DEMO_FILES[1])
csc = refget.build_seqcol_model(fasta_file_to_seqcol(f))

fromdb = dbc.seqcol.get(csc.digest)
fromdb

csc.digest

object =csc
object.to_dict()
stmt = insert(SequenceCollection).values(object).on_conflict_do_nothing()
session.exec(stmt)



with Session(dbc.engine) as session:
    session.add(csc)
    session.refresh(csc)
    session.commit()

with Session(dbc.engine) as session:
    session.add(csc)
    try:
        session.commit()
    except IntegrityError as e:
        try: 
            with Session(dbc.engine) as session:
                session.add(csc.sequences)
                session.commit()
        except:
            pass
        try: 
            with Session(dbc.engine) as session:
                session.add(csc.names)
                session.commit()
        except:
            pass
        try:
            with Session(dbc.engine) as session:
                session.add(csc.lengths)
                session.commit()
        except:
            pass
        

csc
csc0 = refget.build_seqcol_model(fasta_file_to_seqcol(os.path.join(fa_root, DEMO_FILES[0])))

f = os.path.join(fa_root, DEMO_FILES[3])
csc3 = refget.build_seqcol_model(fasta_file_to_seqcol(f))
csc.lengths
from sqlalchemy.orm.session import make_transient
# with Session(dbc.engine) as session:

csc4 = refget.build_seqcol_model(fasta_file_to_seqcol(os.path.join(fa_root, DEMO_FILES[4])))
with Session(dbc.engine) as session:
    with session.no_autoflush:
        csc_simplified = SequenceCollection(digest=csc4.digest)
        names = session.get(NamesAttr, csc4.names.digest)
        if not names:
            names = NamesAttr(**csc4.names.model_dump())
            session.add(names)
        sequences = session.get(SequencesAttr, csc4.sequences.digest)
        if not sequences:
            sequences = SequencesAttr(**csc4.sequences.model_dump())
            session.add(sequences)
        lengths = session.get(LengthsAttr, csc4.lengths.digest)
        if not lengths:
            lengths = LengthsAttr(**csc4.lengths.model_dump())
            session.add(lengths)
        names.collection.append(csc_simplified)
        sequences.collection.append(csc_simplified)
        lengths.collection.append(csc_simplified)
        session.commit()


# What was the problem? That even just *creating* the object rom the other one...
# so I was saying: names = csc4.names, and that was *connected* to csc4.lengths, 
# so it was trying to insert that one on the csc.


session = Session(dbc.engine)



csc_simplified = SequenceCollection(digest=csc4.digest, 
                                    names=csc4.names,lengths=lengths, sequences=sequences)

lengths.collection.append(csc_simplified)
lengths.collection
lengths.collection.append(csc_simplified)
session.commit()

# stmt = select(SequencesAttr).where(SequencesAttr.digest == csc4.sequences.digest)
# results = session.exec(stmt)
# sequences = results.one_or_none()
# stmt = select(NamesAttr).where(NamesAttr.digest == csc4.names.digest)
# results = session.exec(stmt)
# names = results.one_or_none()
# stmt = select(LengthsAttr).where(LengthsAttr.digest == csc4.lengths.digest)
# results = session.exec(stmt)
# lengths = results.one_or_none()





print(f"names: {names}\n", f"lengths: {lengths}\n", f"sequences: {sequences}")

with session.no_autoflush:
    csc_simplified = SequenceCollection(digest=csc4.digest, 
                                        names=csc4.names,
                                        lengths=lengths,
                                        sequences=sequences)
    # lengths.collection.append(csc_simplified)
    # session.add(lengths)
    # sequences.collection.append(csc_simplified)
    # session.add(sequences)
    session.commit()

session.add(csc_simplified)
session.commit()


if sequences:
    sequences.collection.append(csc_simplified)
    session.refresh(csc_simplified)
if names:
    names.collection.append(csc_simplified)
else:
    session.add(names)
if lengths:
    lengths.collection.append(csc_simplified)

session.add(sequences)
session.add(lengths)
# session.add(csc_linked)
session.commit()




csc_linked = SequenceCollection(
    digest=csc4.digest,
    sequences=sequences or csc3.sequences,
    names=names or csc3.names,
    lengths=lengths or csc3.lengths
)





with Session(dbc.engine) as session:
    stmt = select(SequenceCollection).where(SequenceCollection.digest == "123")
    results = session.exec(stmt)
    exists = results.one_or_none()



demo_results = {}
for demo_file in DEMO_FILES:
    f = os.path.join(fa_root, demo_file)
    print("Fasta file to be loaded: {}".format(f))
    demo_results[f] = dbc.seqcol.add_from_fasta_file(f)

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

cna = CollectionNamesAttr (
    digest = seqcol_obj3["names"],
    value = ["blah", "blah2"]
)

ca = CollectionsAttr (
    digest = "compute_me", 
    value = [l1.digest, sc2.digest]
)

pg1 = Pangenome(digest="pangenome_digest", 
                names = cna, collections=ca)



What I need:
- [ ] RefgetDBAgent, replaces SeqColHenge and Henge objects
- [ ] functions for computing digests and 
creating these pydantic object representations nicer

