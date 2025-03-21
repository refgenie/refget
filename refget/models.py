import logging

from copy import copy
from sqlmodel import Field, SQLModel, Column, Relationship
from sqlmodel import JSON
from typing import List, Optional


from .digest_functions import sha512t24u_digest
from .utilities import (
    canonical_str,
    build_name_length_pairs,
    seqcol_dict_to_level1_dict,
    fasta_to_seqcol_dict,
    level1_dict_to_seqcol_digest,
)

_LOGGER = logging.getLogger(__name__)


class Sequence(SQLModel, table=True):
    digest: str = Field(primary_key=True)
    sequence: str
    length: int


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

    @classmethod
    def from_dict(cls, pangenome_obj: dict, inherent_attrs: Optional[list] = None) -> "Pangenome":
        """
        Given a dict representation of a pangenome, create a Pangenome object.
        This is the primary way to create a Pangenome object.

        Args:
            pangenome_obj (dict): Dictionary representation of a canonical pangenome object

        Returns:
            (Pangenome): The Pangenome object
        """
        raise NotImplementedError("This method is not yet implemented.")

    def level1(self):
        """Converts object into dict of level 1 representation of the Pangenome."""
        return {"names": self.names_digest, "collections": self.collections_digest}

    def level2(self):
        """Converts object into dict of level 2 representation of the Pangenome."""
        return {
            "names": self.names.value.split(","),
            "collections": [x.digest for x in self.collections],
        }

    def level3(self):
        """Converts object into dict of level 3 representation of the Pangenome."""
        return {
            "names": self.names.value.split(","),
            "collections": [x.level1() for x in self.collections],
        }

    def level4(self):
        """Converts object into dict of level 4 representation of the Pangenome."""
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
    """
    A SQLModel/pydantic model that represents a refget sequence collection.
    """

    digest: str = Field(primary_key=True)
    """ Top-level digest of the SequenceCollection. """

    sequences_digest: str = Field(foreign_key="sequencesattr.digest")
    sequences: "SequencesAttr" = Relationship(back_populates="collection")
    """ Array of sequence digests."""

    sorted_sequences_digest: str = Field(foreign_key="sortedsequencesattr.digest")
    sorted_sequences: "SortedSequencesAttr" = Relationship(back_populates="collection")
    """ Array of sorted sequence digests."""

    names_digest: str = Field(foreign_key="namesattr.digest")
    names: "NamesAttr" = Relationship(back_populates="collection")
    """ Array of sequence names. """

    lengths_digest: str = Field(foreign_key="lengthsattr.digest")
    lengths: "LengthsAttr" = Relationship(back_populates="collection")
    """ Array of sequence lengths. """

    sorted_name_length_pairs_digest: str = Field()
    """ Digest of the sorted name-length pairs, representing a unique digest of sort-invariant coordinate system. """
    # sorted_name_length_pairs_digest: str = Field(foreign_key="sortednamelengthpairsattr.digest")
    # sorted_name_length_pairs: "SortedNameLengthPairsAttr" = Relationship(
    #     back_populates="collection"
    # )
    name_length_pairs_digest: str = Field(foreign_key="namelengthpairsattr.digest")
    name_length_pairs: "NameLengthPairsAttr" = Relationship(back_populates="collection")
    """ Array of name-length pairs, representing the coordinate system of the collection. """

    @classmethod
    def input_validate(cls, seqcol_obj: dict) -> bool:
        """
        Given a dict representation of a sequence collection, validate it against the input schema.

        Args:
            seqcol_obj (dict): Dictionary representation of a canonical sequence collection object

        Returns:
            (bool): True if the object is valid, False otherwise
        """
        schema_path = os.path.join(os.path.dirname(__file__), "schemas", "seqcol.yaml")
        schema = load_yaml(schema_path)
        validator = Draft7Validator(schema)

        if not validator.is_valid(seqcol_obj.level2()):
            errors = sorted(validator.iter_errors(seqcol_obj), key=lambda e: e.path)
            raise InvalidSeqColError("Validation failed", errors)
        return True

    @classmethod
    def from_fasta_file(cls, fasta_file: str) -> "SequenceCollection":
        """
        Given a FASTA file, create a SequenceCollection object.

        Args:
            fasta_file (str): Path to a FASTA file

        Returns:
            (SequenceCollection): The SequenceCollection object
        """
        seqcol = fasta_to_seqcol_dict(fasta_file)
        return cls.from_dict(seqcol)

    @classmethod
    def from_dict(
        cls, seqcol_dict: dict, inherent_attrs: Optional[list] = ["names", "sequences"]
    ) -> "SequenceCollection":
        """
        Given a dict representation of a sequence collection, create a SequenceCollection object.
        This is the primary way to create a SequenceCollection object.

        Args:
            seqcol_dict (dict): Dictionary representation of a canonical sequence collection object
            schema (dict): Schema defining the inherent attributes to digest

        Returns:
            (SequenceCollection): The SequenceCollection object
        """

        # validate_seqcol(seqcol_dict)
        level1_dict = seqcol_dict_to_level1_dict(seqcol_dict, inherent_attrs)
        seqcol_digest = level1_dict_to_seqcol_digest(level1_dict)

        # Now, build the actual pydantic models
        sequences_attr = SequencesAttr(
            digest=level1_dict["sequences"], value=seqcol_dict["sequences"]
        )

        names_attr = NamesAttr(digest=level1_dict["names"], value=seqcol_dict["names"])

        # Any non-inherent attributes will have been filtered from the l1 dict
        # So we need to compute the digests for them here
        lengths_attr = LengthsAttr(
            digest=sha512t24u_digest(canonical_str(seqcol_dict["lengths"])),
            value=seqcol_dict["lengths"],
        )

        nlp = build_name_length_pairs(seqcol_dict)
        nlp_attr = NameLengthPairsAttr(digest=sha512t24u_digest(canonical_str(nlp)), value=nlp)
        _LOGGER.debug(f"nlp: {nlp}")
        _LOGGER.debug(f"Name-length pairs: {nlp_attr}")

        snlp_digests = []  # sorted_name_length_pairs digests
        for i in range(len(nlp)):
            snlp_digests.append(sha512t24u_digest(canonical_str(nlp[i])))
        snlp_digests.sort()

        # you can build it like this, but instead I'm just building it from the nlp, to save compute
        # snlp = build_sorted_name_length_pairs(seqcol_dict)
        # v = ",".join(snlp)
        snlp_digest_level1 = sha512t24u_digest(canonical_str(snlp_digests))
        # This is now a transient attribute, so we don't need to store it in the database.
        # snlp_attr = SortedNameLengthPairsAttr(digest=snlp_digest_level1, value=snlp_digests)

        sorted_sequences_value = copy(seqcol_dict["sequences"])
        sorted_sequences_value.sort()
        sorted_sequences_digest = sha512t24u_digest(canonical_str(sorted_sequences_value))
        sorted_sequences_attr = SortedSequencesAttr(
            digest=sorted_sequences_digest, value=sorted_sequences_value
        )
        _LOGGER.debug(f"sorted_sequences_value: {sorted_sequences_value}")
        _LOGGER.debug(f"sorted_sequences_digest: {sorted_sequences_digest}")
        _LOGGER.debug(f"sorted_sequences_attr: {sorted_sequences_attr}")

        seqcol = SequenceCollection(
            digest=seqcol_digest,
            sequences=sequences_attr,
            sorted_sequences=sorted_sequences_attr,
            names=names_attr,
            lengths=lengths_attr,
            name_length_pairs=nlp_attr,
            sorted_name_length_pairs_digest=snlp_digest_level1,
        )

        _LOGGER.debug(f"seqcol: {seqcol}")

        return seqcol

    pangenomes: List[Pangenome] = Relationship(
        back_populates="collections", link_model=PangenomeCollectionLink
    )

    def level1(self):
        """
        Converts object into dict of level 2 representation of the SequenceCollection.
        """
        return {
            "lengths": self.lengths.digest,
            "names": self.names.digest,
            "sequences": self.sequences.digest,
            "sorted_sequences": self.sorted_sequences.digest,
            "name_length_pairs": self.name_length_pairs.digest,
            "sorted_name_length_pairs": self.sorted_name_length_pairs_digest,
        }

    def level2(self):
        """
        Converts object into dict of level 2 representation of the SequenceCollection.
        """
        return {
            "lengths": self.lengths.value,
            "names": self.names.value,
            "sequences": self.sequences.value,
            "sorted_sequences": self.sorted_sequences.value,
            "name_length_pairs": self.name_length_pairs.value,
            # "sorted_name_length_pairs": self.sorted_name_length_pairs.value,  # decided to remove transient attrs from level 2 repr
        }

    def itemwise(self, limit=None):
        """
        Converts object into a list of dictionaries, one for each sequence in the collection.
        """
        if limit and len(self.sequences.value) > limit:
            raise ValueError(f"Too many sequences to format itemwise: {len(self.sequences.value)}")
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
    collection: List["SequenceCollection"] = Relationship(back_populates="name_length_pairs")


# This is now a transient attribute, so we don't need to store it in the database.
# class SortedNameLengthPairsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: list = Field(sa_column=Column(JSON), default_factory=list)
#     collection: List["SequenceCollection"] = Relationship(
#         back_populates="sorted_name_length_pairs"
#     )
