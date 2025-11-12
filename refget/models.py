import logging
import os
import hashlib

from copy import copy
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Column, Relationship
from sqlmodel import JSON
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel


from .digest_functions import sha512t24u_digest
from .const import DEFAULT_INHERENT_ATTRS
from .utilities import (
    canonical_str,
    build_name_length_pairs,
    seqcol_dict_to_level1_dict,
    fasta_to_seqcol_dict,
    level1_dict_to_seqcol_digest,
    fasta_to_digest,
)


_LOGGER = logging.getLogger(__name__)

class AccessURL(SQLModel):
    """
    A fully resolvable URL that can be used to fetch the actual object bytes.
    Optionally includes headers (e.g., authorization tokens) required for access.
    """
    url: str
    headers: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))


class AccessMethod(SQLModel):
    """
    Describes a method for accessing object bytes, including the protocol type
    (e.g., https, s3, gs) and either a direct URL or an access_id for the /access endpoint.
    At least one of access_url or access_id must be provided.
    """
    type: Literal["s3", "gs", "ftp", "gsiftp", "globus", "htsget", "https", "file"]
    access_url: Optional[AccessURL] = None
    region: Optional[str] = None
    access_id: Optional[str] = None


class Checksum(SQLModel, table=False):
    """
    A checksum for data integrity verification. The type field indicates the hash algorithm
    (e.g., "sha-256", "md5") and the checksum field contains the hex-string encoded hash value.
    """
    type: str  # e.g., "md5", "sha-256"
    checksum: str  # The hex-string encoded checksum value


class DrsObject(SQLModel, table=False):
    """
    A data object representing a single blob of bytes with metadata, checksums, and access methods.
    DRS objects are self-contained and provide all information needed for clients to retrieve the data.
    Conforms to GA4GH Data Repository Service (DRS) specification v1.4.0.
    """
    id: str
    self_uri: str
    size: int
    created_time: datetime
    checksums: List[Checksum] = Field(default_factory=list, sa_column=Column(JSON))
    name: Optional[str] = None
    updated_time: Optional[datetime] = None
    version: Optional[str] = None
    mime_type: Optional[str] = None
    access_methods: List[AccessMethod] = Field(default_factory=list, sa_column=Column(JSON))
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class FastaDrsObject(DrsObject, table=True):
    """
    A DRS object specialized for FASTA sequence files. Stores file metadata including
    size, checksums (SHA-256, MD5, and refget sequence collection digest), and creation time.
    The refget digest serves as the object ID, enabling content-addressable retrieval.
    """
    id: str = Field(primary_key=True)
    self_uri: Optional[str] = None  # Override to make optional for storage

    def to_response(self, base_uri: str = None) -> "FastaDrsObject":
        """
        Return a copy of this object with self_uri populated for API response.

        Args:
            base_uri: Base URI for the DRS service (e.g., "drs://seqcolapi.databio.org")
                     If not provided, returns self unchanged.

        Returns:
            FastaDrsObject with self_uri populated
        """
        if base_uri is None:
            return self

        return self.model_copy(update={"self_uri": f"{base_uri}/{self.id}"})

    @classmethod
    def from_fasta_file(cls, fasta_file: str, digest: str = None) -> "FastaDrsObject":
        """
        Given a FASTA file, create a FastaDrsObject object,
        return a populated FastaDrsObject with computed size and checksum.

        Args:
            fasta_file (str): Path to a FASTA file
            digest (str): The refget digest of the sequence collection 
                (optional). If not included, it wil be computed

        Returns:
            (FastaDrsObject): The FastaDrsObject object
        """

        file_size = os.path.getsize(fasta_file)

        # Compute checksum (SHA-256)
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with open(fasta_file, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
                md5.update(block)
        sha256_checksum_val = sha256.hexdigest()
        md5_checksum_val = md5.hexdigest()

        now = datetime.now(timezone.utc)

        if digest is None:
            # If no digest is provided, compute it from the file
            digest = fasta_to_digest(fasta_file)

        return FastaDrsObject(
            id=digest,
            name=os.path.basename(fasta_file),
            self_uri=None,  # Will be populated by to_response() when serving via API
            size=file_size,
            created_time=now,
            updated_time=now,
            version="1.0",
            mime_type="application/fasta",  # You could use `mimetypes` to guess if needed
            checksums=[
                Checksum(type="sha-256", checksum=sha256_checksum_val),
                Checksum(type="refget.seqcol", checksum=digest),  # Refget digest
                Checksum(type="md5", checksum=md5_checksum_val),
            ],
            access_methods=[],  # Populate this if you host the file somewhere
            description=f"DRS object for {os.path.basename(fasta_file)}",
            aliases=[os.path.basename(fasta_file).split(".")[0]]
        )
        



try:
    from gtars.refget import (  # Adjust this import path to where your PyO3 module is
        SequenceCollection as gtarsSequenceCollection,
    )

    _RUST_BINDINGS_AVAILABLE = True
except ImportError as e:
    _LOGGER.info(
        f"Could not import gtars python bindings. `from_PySequenceCollection` will not be available."
    )
    _RUST_BINDINGS_AVAILABLE = False


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


class HumanReadableNames(SQLModel, table=True):
    """
    A SQLModel/pydantic model that represents a refget sequence collection.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    human_readable_name: str = Field(unique=True)
    digest: str = Field(foreign_key="sequencecollection.digest", nullable=False)
    collection: "SequenceCollection" = Relationship(back_populates="human_readable_names")


# For a transient attribute, like sorted_name_length_pairs, you just need the attr_digest value.
# For attributes where you want to store the values in a table, you would also have the
# Relationship attribute.
class SequenceCollection(SQLModel, table=True):
    """
    A SQLModel/pydantic model that represents a refget sequence collection.
    """

    digest: str = Field(primary_key=True)
    """ Top-level digest of the SequenceCollection. """

    # human_readable_name: Optional[str] = Field(default=None)
    human_readable_names: List["HumanReadableNames"] = Relationship(back_populates="collection")

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
        cls, seqcol_dict: dict, inherent_attrs: Optional[list] = DEFAULT_INHERENT_ATTRS
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

        human_readable_names_list = []
        if "human_readable_names" in seqcol_dict and seqcol_dict["human_readable_names"]:
            # Assuming 'human_readable_name' is a list of strings in the input dictionary
            if isinstance(seqcol_dict["human_readable_names"], list):
                for name_str in seqcol_dict["human_readable_names"]:
                    human_readable_names_list.append(
                        HumanReadableNames(human_readable_name=name_str, digest=seqcol_digest)
                    )
            # Handle the case where a single string is provided for backward compatibility
            elif isinstance(seqcol_dict["human_readable_names"], str):
                human_readable_names_list.append(
                    HumanReadableNames(
                        human_readable_name=seqcol_dict["human_readable_names"],
                        digest=seqcol_digest,
                    )
                )

        seqcol = SequenceCollection(
            digest=seqcol_digest,
            human_readable_names=human_readable_names_list,
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

    @classmethod
    def from_PySequenceCollection(
        cls, gtars_seq_col: gtarsSequenceCollection
    ) -> "SequenceCollection":
        """
        Given a PySequenceCollection object (from Rust bindings), create a SequenceCollection object.

        Args:
           gtars_seq_col (PySequenceCollection): PySequenceCollection object from Rust bindings.

        Returns:
            (SequenceCollection): The SequenceCollection object.
        """
        if not _RUST_BINDINGS_AVAILABLE:
            raise RuntimeError(
                "Rust sequence collection bindings are not available. Cannot use `from_PySequenceCollection`."
            )

        sequences_value = []
        names_value = []
        lengths_value = []

        temp_seqcol_dict = {"names": [], "lengths": [], "sequences": []}

        for record in gtars_seq_col.sequences:
            sequences_value.append("SQ." + record.metadata.sha512t24u)
            names_value.append(record.metadata.name)
            lengths_value.append(record.metadata.length)

            temp_seqcol_dict["names"].append(record.metadata.name)
            temp_seqcol_dict["lengths"].append(record.metadata.length)
            temp_seqcol_dict["sequences"].append(record.metadata.sha512t24u)

        sequences_attr = SequencesAttr(
            digest=gtars_seq_col.lvl1.sequences_digest, value=sequences_value
        )
        _LOGGER.debug(f"SequencesAttr: {sequences_attr}")

        names_attr = NamesAttr(digest=gtars_seq_col.lvl1.names_digest, value=names_value)
        _LOGGER.debug(f"NamesAttr: {names_attr}")

        lengths_attr = LengthsAttr(
            digest=gtars_seq_col.lvl1.lengths_digest,
            value=lengths_value,
        )
        _LOGGER.debug(f"LengthsAttr: {lengths_attr}")

        nlp = build_name_length_pairs(temp_seqcol_dict)
        nlp_attr = NameLengthPairsAttr(digest=sha512t24u_digest(canonical_str(nlp)), value=nlp)
        _LOGGER.debug(f"NameLengthPairsAttr: {nlp_attr}")

        sorted_sequences_value = copy(sequences_value)
        sorted_sequences_value.sort()
        sorted_sequences_digest = sha512t24u_digest(canonical_str(sorted_sequences_value))
        sorted_sequences_attr = SortedSequencesAttr(
            digest=sorted_sequences_digest, value=sorted_sequences_value
        )
        _LOGGER.debug(f"SortedSequencesAttr: {sorted_sequences_attr}")

        snlp_digests = []
        for pair in nlp:
            snlp_digests.append(sha512t24u_digest(canonical_str(pair)))
        snlp_digests.sort()
        sorted_name_length_pairs_digest = sha512t24u_digest(canonical_str(snlp_digests))
        _LOGGER.debug(f"Sorted Name Length Pairs Digest: {sorted_name_length_pairs_digest}")

        seqcol = SequenceCollection(
            digest=gtars_seq_col.digest,
            human_readable_names=[],
            sequences=sequences_attr,
            sorted_sequences=sorted_sequences_attr,
            names=names_attr,
            lengths=lengths_attr,
            name_length_pairs=nlp_attr,
            sorted_name_length_pairs_digest=sorted_name_length_pairs_digest,
        )

        _LOGGER.debug(f"Created SequenceCollection from PySequenceCollection: {seqcol}")
        return seqcol

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


class PaginationResult(BaseModel):
    page: int = 0
    page_size: int = 10
    total: int


class ResultsSequenceCollections(BaseModel):
    """
    Sequence collection results with pagination
    """

    pagination: PaginationResult
    results: Dict[str, dict]


class Similarities(BaseModel):
    """
    Model to contain results from similarities calculations
    """

    similarities: List[Dict[str, Any]]
    pagination: PaginationResult
    reference_digest: Optional[str] = None


# This is now a transient attribute, so we don't need to store it in the database.
# class SortedNameLengthPairsAttr(SQLModel, table=True):
#     digest: str = Field(primary_key=True)
#     value: list = Field(sa_column=Column(JSON), default_factory=list)
#     collection: List["SequenceCollection"] = Relationship(
#         back_populates="sorted_name_length_pairs"
#     )
