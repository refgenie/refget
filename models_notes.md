
# Build Sequence Collections pydantic models

## Henge

How should I store the collections in a database? I started using Henge.
It was a general-purpose key-value store that could be used to store data of any arbitrary structure, using the principled digest mechanism for intermediate elements.
In the end, I decided to move away from using henge, and use SQLModel, because I could just make the code a little easier to reason about.
I guess henge just turned out too be too abstract.

So now the models use SQLModel/pyandtic objects.

## SQLModel

For now, I'm hard-coding the models. 
I think this makes the most sense at the moment.
In the future, if necessary, I could automatically generate the models, based on a schema, using something like this:

```python
from pydantic import create_model

# First, get a dict of attributes from the JSON Schema:
kwargs = {
    "names": (List, []),
    "sequences": (List, []),
    "lengths": (List, []),
}

# Now, create a pydantic/SQLModel model
SequenceCollection = create_model("SequenceCollection", **kwargs, __base__=SQLModel)
```


## Arrays

One issue is this that Sequence collections are made up of lists/arrays. 
These do not naturally fit in the database.
I think I started with using separate tables for the individual elements. 
But I found it was much easier to use the `Column(ARRAY(String)))`, which worked pretty well; this would set the column type to ARRAY.
But the problem with this is that I think it's specific to POSTGRES.
I want the models to be able to work with alternative back-ends easily.
So, I decided to just go with the JSON column.
This turned out to work really well and I think it's more universal.

So for example, the "NamesAttr" table has 2 columns, 'digest' and 'value'.
Digest is a string, and value is a JSON column, where I put the content of the array.


This is some old deprecated models I had been working on, under different modeling approaches; probably can delete these soon if I don't need to revisit it.

```python

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


# class PangenomeOld2(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     names: "CollectionNamesAttr" = Relationship(back_populates="pangenome")
#     names_digest: str = Field(foreign_key="collectionnamesattr.digest")
#     collections: "CollectionsAttr" = Relationship(back_populates="pangenome")
#     collections_digest: str = Field(foreign_key="collectionsattr.digest")
#     # could add: __cls_kwargs__={"table": True},

# class CollectionsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: str
#     pangenome: Pangenome = Relationship(back_populates="collections")
# value: List[str] = Field(sa_column=Column(ARRAY(String)))


# class CollectionsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: list["SequenceCollection"]
#     pangenome: Pangenome = Relationship(back_populates="collections")
#     # value: List[str] = Field(sa_column=Column(ARRAY(String)))

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

    from pydantic import create_model
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

    sc1 = {"names": ["chr1", "chr2"], "sequences": ["ay89fw", "we4f9x"], "lengths": [1, 2]}
    sc1 = {"names_digest": "123", "sequences_digest": "234", "lengths_digest": "52345"}

    x = L1SequenceCollection(**sc1)
```

