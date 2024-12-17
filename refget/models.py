

from typing import List
from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, String, Relationship, Integer
from sqlmodel import JSON


class PangenomeCollectionLink(SQLModel, table=True):
    pangenome_digest: str = Field(foreign_key="pangenome.digest", primary_key=True)
    collection_digest: str = Field(foreign_key="sequencecollection.digest", primary_key=True)


class Pangenome(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    names: "CollectionNamesAttr" = Relationship(back_populates="pangenome")
    names_digest: str = Field(foreign_key="collectionnamesattr.digest")
    collections: List["SequenceCollection"] = Relationship(
        back_populates="pangenomes", link_model=PangenomeCollectionLink
    )
    collections_digest: str

    def level1(self):
        return {"names": self.names_digest, "collections": self.collections_digest}

    def level2(self):
        return {
            "names": self.names.value.split(","),
            "collections": [x.digest for x in self.collections],
        }

    def level3(self):
        return {
            "names": self.names.value.split(","),
            "collections": [x.level1() for x in self.collections],
        }

    def level4(self):
        return {
            "names": self.names.value.split(","),
            "collections": [x.level2() for x in self.collections],
        }


class CollectionNamesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: str
    pangenome: List["Pangenome"] = Relationship(back_populates="names")
    # value: List[str] = Field(sa_column=Column(ARRAY(String)))


# For a transient attribute, like sorted_name_length_pairs, you just need the attr_digest value.
# For attributes where you want to store the values in a table, you would also have the 
# Relationship attribute.
class SequenceCollection(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    sequences_digest: str = Field(foreign_key="sequencesattr.digest")
    sequences: "SequencesAttr" = Relationship(back_populates="collection")
    sorted_sequences_digest: str = Field(foreign_key="sortedsequencesattr.digest")
    sorted_sequences: "SortedSequencesAttr" = Relationship(back_populates="collection")
    names_digest: str = Field(foreign_key="namesattr.digest")
    names: "NamesAttr" = Relationship(back_populates="collection")
    lengths_digest: str = Field(foreign_key="lengthsattr.digest")
    lengths: "LengthsAttr" = Relationship(back_populates="collection")
    sorted_name_length_pairs_digest: str = Field()
    # sorted_name_length_pairs_digest: str = Field(foreign_key="sortednamelengthpairsattr.digest")
    # sorted_name_length_pairs: "SortedNameLengthPairsAttr" = Relationship(
    #     back_populates="collection"
    # )
    name_length_pairs_digest: str = Field(foreign_key="namelengthpairsattr.digest")
    name_length_pairs: "NameLengthPairsAttr" = Relationship(
        back_populates="collection"
    )

    pangenomes: List[Pangenome] = Relationship(
        back_populates="collections", link_model=PangenomeCollectionLink
    )

    def level1(self):
        return {
            "lengths": self.lengths_digest,
            "names": self.names_digest,
            "sequences": self.sequences_digest,
            "sorted_sequences": self.sorted_sequences_digest,
            "name_length_pairs": self.name_length_pairs_digest,
            "sorted_name_length_pairs": self.sorted_name_length_pairs_digest,
        }

    def level2(self):
        return {
            "lengths": self.lengths.value,
            "names": self.names.value,
            "sequences": self.sequences.value,
            "sorted_sequences": self.sorted_sequences.value,
            "name_length_pairs": self.name_length_pairs.value,
            # "sorted_name_length_pairs": self.sorted_name_length_pairs.value,  # decided to remove transient attrs from level 2 repr
        }

    def itemwise(self, limit=None):
        if limit and len(self.sequences.value) > limit:
            raise ValueError(
                f"Too many sequences to format itemwise: {len(self.sequences.value)}"
            )
        list_of_dicts = []
        for i in range(len(self.lengths.value)):
            list_of_dicts.append(
                {
                    "name": self.names.value[i],
                    "length": self.lengths.value[i],
                    "sequence": self.sequences.value[i],
                }
            )
        return list_of_dicts


# Each of these classes will become a separate table in the database.

class SequencesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(back_populates="sequences")


class SortedSequencesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(back_populates="sorted_sequences")


class NamesAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(back_populates="names")


class LengthsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(back_populates="lengths")

class NameLengthPairsAttr(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    value: list = Field(sa_column=Column(JSON), default_factory=list)
    collection: List["SequenceCollection"] = Relationship(
        back_populates="name_length_pairs"
    )

# This is now a transient attribute, so we don't need to store it in the database.
# class SortedNameLengthPairsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: list = Field(sa_column=Column(JSON), default_factory=list)
#     collection: List["SequenceCollection"] = Relationship(
#         back_populates="sorted_name_length_pairs"
#     )
