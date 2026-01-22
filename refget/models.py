import json
import logging
from copy import copy
from datetime import datetime, timezone
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel, Column, Relationship
from sqlmodel import JSON
from typing import List, Optional, Dict, Any, Literal, TYPE_CHECKING
from pydantic import BaseModel, field_validator, field_serializer


from .digest_functions import sha512t24u_digest

if TYPE_CHECKING:
    from gtars.refget import SequenceCollection as gtarsSequenceCollection


class PydanticJSON(TypeDecorator):
    """
    A JSON type that knows how to serialize Pydantic/SQLModel objects.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python objects to JSON-serializable form before storing."""
        if value is None:
            return None
        if isinstance(value, list):
            return [self._serialize_item(item) for item in value]
        return self._serialize_item(value)

    def _serialize_item(self, item):
        """Serialize a single item."""
        if hasattr(item, "model_dump"):
            return item.model_dump(exclude_none=True)
        return item


from .const import DEFAULT_INHERENT_ATTRS, DEFAULT_PASSTHRU_ATTRS, SEQCOL_SCHEMA_PATH
from .exceptions import InvalidSeqColError
from .utilities import (
    canonical_str,
    build_name_length_pairs,
    seqcol_dict_to_level1_dict,
    level1_dict_to_seqcol_digest,
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

    DRS 1.5.0 adds the 'cloud' field to explicitly specify the cloud provider.
    """

    type: Literal["s3", "gs", "ftp", "gsiftp", "globus", "htsget", "https", "file"]
    access_url: Optional[AccessURL] = None
    region: Optional[str] = None
    access_id: Optional[str] = None
    cloud: Optional[str] = None  # e.g., "aws", "gcp", "azure", "backblaze"


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
    checksums: List[Checksum] = Field(default_factory=list, sa_column=Column(PydanticJSON))
    name: Optional[str] = None
    updated_time: Optional[datetime] = None
    version: Optional[str] = None
    mime_type: Optional[str] = None
    access_methods: List[AccessMethod] = Field(
        default_factory=list, sa_column=Column(PydanticJSON)
    )
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator("checksums", mode="before")
    @classmethod
    def coerce_checksums(cls, v):
        """Coerce dicts to Checksum objects when loading from JSON."""
        if v is None:
            return []
        return [Checksum.model_validate(item) if isinstance(item, dict) else item for item in v]

    @field_serializer("checksums")
    def serialize_checksums(self, v):
        """Serialize Checksum objects (or dicts) to dicts for JSON output."""
        if v is None:
            return []
        return [
            item.model_dump() if hasattr(item, "model_dump") else item for item in v
        ]

    @field_validator("access_methods", mode="before")
    @classmethod
    def coerce_access_methods(cls, v):
        """Coerce dicts to AccessMethod objects when loading from JSON."""
        if v is None:
            return []
        return [
            AccessMethod.model_validate(item) if isinstance(item, dict) else item for item in v
        ]

    @field_serializer("access_methods")
    def serialize_access_methods(self, v):
        """Serialize AccessMethod objects (or dicts) to dicts for JSON output."""
        if v is None:
            return []
        return [
            item.model_dump() if hasattr(item, "model_dump") else item for item in v
        ]


class FastaDrsObject(DrsObject, table=True):
    """
    A DRS object specialized for FASTA sequence files. Stores file metadata including
    size, checksums (SHA-256, MD5, and refget sequence collection digest), and creation time.
    The refget digest serves as the object ID, enabling content-addressable retrieval.
    """

    id: str = Field(primary_key=True)
    self_uri: Optional[str] = None  # Override to make optional for storage

    # FAI index fields
    line_bases: Optional[int] = None  # Bases per line (e.g., 60)
    extra_line_bytes: Optional[int] = (
        None  # Extra bytes per line for newline (1 for \n, 2 for \r\n)
    )
    offsets: Optional[List[int]] = Field(
        default=None, sa_column=Column(JSON)
    )  # Byte offset per sequence

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
                (optional). If not included, it will be computed

        Returns:
            (FastaDrsObject): The FastaDrsObject object

        Raises:
            ImportError: If gtars is not installed (required for FASTA processing)
        """
        from .processing.fasta import create_fasta_drs_object

        return create_fasta_drs_object(fasta_file, digest)


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
    # Note: For transient attributes (per schema ga4gh.transient), we only store the digest, not the full value/relationship.
    # This must be manually kept in sync with schemas/seqcol.json - SQLModel classes cannot be dynamically generated from schema
    # because SQLAlchemy requires class definitions at import time for ORM mappings and database migrations.
    # sorted_name_length_pairs_digest: str = Field(foreign_key="sortednamelengthpairsattr.digest")
    # sorted_name_length_pairs: "SortedNameLengthPairsAttr" = Relationship(
    #     back_populates="collection"
    # )
    name_length_pairs_digest: str = Field(foreign_key="namelengthpairsattr.digest")
    name_length_pairs: "NameLengthPairsAttr" = Relationship(back_populates="collection")
    """ Array of name-length pairs, representing the coordinate system of the collection. """

    @classmethod
    def _validate_collated_attributes(cls, seqcol_dict: dict) -> None:
        """
        Validate that all collated attributes have the same length.

        Collated attributes are attributes whose values match 1-to-1 with the sequences
        in the collection and are represented in the same order.

        Args:
            seqcol_dict (dict): Dictionary representation of a sequence collection

        Raises:
            InvalidSeqColError: If collated attributes have mismatched lengths
        """
        # Load schema to identify collated attributes
        with open(SEQCOL_SCHEMA_PATH, "r") as f:
            schema = json.load(f)

        # Find all collated attributes from schema
        collated_attrs = []
        if "properties" in schema:
            for attr_name, attr_spec in schema["properties"].items():
                if isinstance(attr_spec, dict) and attr_spec.get("collated") is True:
                    collated_attrs.append(attr_name)

        # Check lengths of collated attributes that exist in the dict
        lengths = {}
        for attr in collated_attrs:
            if attr in seqcol_dict:
                if isinstance(seqcol_dict[attr], list):
                    lengths[attr] = len(seqcol_dict[attr])

        # Verify all collated attributes have the same length
        if lengths:
            expected_length = next(iter(lengths.values()))
            mismatched = {
                attr: length for attr, length in lengths.items() if length != expected_length
            }

            if mismatched:
                all_lengths = ", ".join(f"{attr}={length}" for attr, length in lengths.items())
                error_msg = f"Collated attributes must have the same length. Found mismatched lengths: {all_lengths}"
                raise InvalidSeqColError(error_msg, errors=[mismatched])

    @classmethod
    def from_fasta_file(cls, fasta_file: str) -> "SequenceCollection":
        """
        Given a FASTA file, create a SequenceCollection object.

        Args:
            fasta_file (str): Path to a FASTA file

        Returns:
            (SequenceCollection): The SequenceCollection object

        Raises:
            ImportError: If gtars is not installed (required for FASTA processing)
        """
        from .processing.fasta import fasta_to_seqcol_dict

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
            inherent_attrs (list, optional): List of inherent attributes to digest

        Returns:
            (SequenceCollection): The SequenceCollection object
        """

        # Validate collated attributes have matching lengths
        cls._validate_collated_attributes(seqcol_dict)

        # validate_seqcol(seqcol_dict)
        level1_dict = seqcol_dict_to_level1_dict(seqcol_dict)
        seqcol_digest = level1_dict_to_seqcol_digest(level1_dict, inherent_attrs)

        # Now, build the actual pydantic models
        sequences_attr = SequencesAttr(
            digest=level1_dict["sequences"], value=seqcol_dict["sequences"]
        )

        names_attr = NamesAttr(digest=level1_dict["names"], value=seqcol_dict["names"])

        lengths_attr = LengthsAttr(digest=level1_dict["lengths"], value=seqcol_dict["lengths"])

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
            # Handle single string input (convert to list)
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
        cls, gtars_seq_col: "gtarsSequenceCollection"
    ) -> "SequenceCollection":
        """
        Given a PySequenceCollection object (from Rust bindings), create a SequenceCollection object.

        Args:
           gtars_seq_col (PySequenceCollection): PySequenceCollection object from Rust bindings.

        Returns:
            (SequenceCollection): The SequenceCollection object.

        Raises:
            ImportError: If gtars is not installed (required for this conversion)
        """
        from .processing.bridge import seqcol_from_gtars

        return seqcol_from_gtars(gtars_seq_col)

    def level1(self):
        """
        Converts object into dict of level 1 representation of the SequenceCollection.

        Returns attribute digests for most attributes, but returns raw values for passthru attributes.
        Note: Passthru handling for dict-based construction happens in seqcol_dict_to_level1_dict().
        When passthru attributes are added to the database model, return .value instead of .digest here.
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
            # sorted_name_length_pairs is transient - only digest stored, not value
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
