# I've been thinking about how to store the collections in a database.
# I would like to move away from using henge, and use SQLModel.
# To start, I won't bother with auto-generation of the pydantic
# objects, I will make the models I want and then later revisit if necessary.

# the one issue is this: Sequence collections are made up of lists/arrays. These
# do not naturally fit in the database. So, maybe the models should actually 
# look different.

from pydantic import  create_model
from typing import List 
from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, String, Relationship, Integer

# First, get a dict of attributes from the JSON Schema:
kwargs = {
	"names":(List, []),
	"sequences":(List, []),
	"lengths":(List, []),
}

# Now, create a pydantic/SQLModel model
SequenceCollection = create_model(
    'SequenceCollection', **kwargs,
    __base__=SQLModel
) 

# DigestedSequenceCollection = create_model(
# 	'DigestedSequenceCollection', digest=(str, ""), 
# 	__base__= SequenceCollection,
# 	__cls_kwargs__={"table": True})

# Equivalent to:
# class DigestedSequenceCollection(SQLModel, table=True):
#     """ A collection of sequences with their digest. """
#     digest: str = Field(primary_key=True)
#     sequences: List[str] = Field(sa_column=Column(ARRAY(String)))
#     names: List[str] = Field(sa_column=Column(ARRAY(String)))
#     lengths: List[int] = Field(sa_column=Column(ARRAY(Integer)))

# class DigestedPangenome(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     sequence_collections: List[DigestedSequenceCollection] = Field(sa_column=Column(ARRAY(DigestedSequenceCollection)))
#     # could add: __cls_kwargs__={"table": True},


class Pangenome(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    names: "CollectionNamesAttr" = Relationship(back_populates="pangenome")
    names_digest: str = Field(foreign_key="collectionnamesattr.digest")
    collections: "CollectionsAttr" = Relationship(back_populates="pangenome")
    collections_digest: str = Field(foreign_key="collectionsattr.digest")
    # could add: __cls_kwargs__={"table": True},

class CollectionsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    pangenome: Pangenome = Relationship(back_populates="collections")
    # value: List[str] = Field(sa_column=Column(ARRAY(String)))

class CollectionNamesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    pangenome: Pangenome = Relationship(back_populates="names")   
    value: str
    # value: List[str] = Field(sa_column=Column(ARRAY(String)))
class SequenceCollection(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    sequences_digest: str = Field(foreign_key="sequencesattr.digest")
    sequences: "SequencesAttr" = Relationship(back_populates="collection")
    names_digest: str = Field(foreign_key="namesattr.digest")
    names: "NamesAttr" = Relationship(back_populates="collection")
    lengths_digest: str = Field(foreign_key="lengthsattr.digest")
    lengths: "LengthsAttr" = Relationship(back_populates="collection")
    sorted_name_length_pairs_digest: str = Field(foreign_key="sortednamelengthpairsattr.digest")
    sorted_name_length_pairs: "SortedNameLengthPairsAttr" = Relationship(back_populates="collection")

class SequencesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    collection: List["SequenceCollection"] = Relationship(back_populates="sequences")

class NamesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    collection: List["SequenceCollection"] = Relationship(back_populates="names")   

class LengthsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    collection: List["SequenceCollection"] = Relationship(back_populates="lengths")   

class SortedNameLengthPairsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    collection: List["SequenceCollection"] = Relationship(back_populates="sorted_name_length_pairs")





# class SequencesAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: List[str] = Field(sa_column=Column(ARRAY(String)))
#     collection: List["SequenceCollection"] = Relationship(back_populates="sequences")

# class NamesAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: List[str] = Field(sa_column=Column(ARRAY(String)))
#     collection: List["SequenceCollection"] = Relationship(back_populates="names")   

# class LengthsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: List[int] = Field(sa_column=Column(ARRAY(String)))
#     collection: List["SequenceCollection"] = Relationship(back_populates="lengths")   














# class GenericAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: str = Field()
#     name: str = Field()
#     member_of: "L1SequenceCollection" = Relationship(back_populates="sequences_rel")

# class L1GenericCollection(SQLModel, table=True):
#     """ Representation of a collection of generic attributes. """
#     id: int = Field(primary_key=True)
#     generic_attrs_digest: List[str] = Field(foreign_key="genericattr.digest", sa_column=Column(ARRAY(str)))
#     attrs: List[GenericAttr] = Relationship(back_populates="member_of")
#     summarizes: "ComprehensiveSequenceCollection" = Relationship(back_populates="level1")



# class ComprehensiveSequenceCollection(SQLModel, table=True):
#     """
#     Top-level representation. Pointers to
#     """
#     digest: str = Field(primary_key=True)
#     level1_id: int = Field(foreign_key="l1sequencecollection.id")
#     level1: L1SequenceCollection = Relationship(back_populates="summarizes")
#     sequences: List[str] = Field(sa_column=Column(ARRAY(str)))
#     names: List[str] = Field(sa_column=Column(ARRAY(str)))
#     lengths: List[int] = Field(sa_column=Column(ARRAY(int)))
#     # could add: __cls_kwargs__={"table": True},


if False:


    from pydantic import  create_model
    from typing import List 
    from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, Float, Relationship



    class GenericAttr(SQLModel):
        digest: str = Field(primary_key=True)
        value: str = Field()
        name: str = Field()

    class SequencesAttr(GenericAttr, table=True):
        member_of: "L1SequenceCollection" = Relationship(back_populates="sequences_rel")
        pass

    class LengthsAttr(GenericAttr, table=True):
        member_of: "L1SequenceCollection" = Relationship(back_populates="lengths_rel")
        pass

    class NamesAttr(GenericAttr, table=True):    
        member_of: "L1SequenceCollection" = Relationship(back_populates="names_rel")
        pass

    class L1SequenceCollection(SQLModel, table=True):
        digest: int = Field(primary_key=True)
        sequences_digest: str = Field(foreign_key="sequencesattr.digest")
        sequences_rel: SequencesAttr = Relationship(back_populates="member_of")
        names_digest: str = Field(foreign_key="namesattr.digest")
        names_rel: NamesAttr = Relationship(back_populates="member_of")
        lengths_digest: str = Field(foreign_key="lengthsattr.digest")
        lengths_rel: LengthsAttr = Relationship(back_populates="member_of")
        

    sc1 = {"names": ["chr1", "chr2"], "sequences": ["ay89fw", "we4f9x"], "lengths": [1,2]}
    sc1 = {"names_digest": "123", "sequences_digest": "234", "lengths_digest": "52345"}


    x = L1SequenceCollection(**sc1)

