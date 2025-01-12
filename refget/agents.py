import json
import os
import logging
import peppy
import requests

from sqlmodel import create_engine, select, Session, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy import URL
from sqlalchemy.dialects.postgresql import insert


from .models import *
from .utilities import (
    build_seqcol_model,
    fasta_file_to_seqcol,
    format_itemwise,
    compare_seqcols,
    build_pangenome_model,
)
from .const import _LOGGER
from .const import SCHEMA_FILEPATH

ATTR_TYPE_MAP = {
    "sequences": SequencesAttr,
    "names": NamesAttr,
    "lengths": LengthsAttr,
    "name_length_pairs": NameLengthPairsAttr,
    "sorted_sequences": SortedSequencesAttr,
}


def read_yaml_url(url):
    """
    Read a YAML file from a URL.

    :param url: The URL to read the YAML file from.
    :return: The loaded YAML file as a dictionary.
    """
    import yaml

    _LOGGER.info("Reading URL: {}".format(url))
    try:
        response = requests.get(url)
        response.raise_for_status()
        text = response.text
        return yaml.safe_load(text)
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Error reading URL: {e}")
        raise e


def load_json(source):
    """
    Load a JSON from a file or URL.

    :param source: The file path or URL to the JSON.
    :return: The loaded JSON as a dictionary.
    """
    if os.path.isfile(source):
        with open(source, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        try:
            response = requests.get(source)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error loading JSON from URL: {e}")
            raise e



class SeqColAgent(object):
    def __init__(self, engine, inherent_attrs=None):
        self.engine = engine
        self.inherent_attrs = inherent_attrs

    def get(self, digest: str, return_format: str = "level2", attribute: str = None, itemwise_limit: int = None) -> SequenceCollection:
        with Session(self.engine) as session:
            statement = select(SequenceCollection).where(SequenceCollection.digest == digest)
            results = session.exec(statement)
            seqcol = results.one_or_none()
            if not seqcol:
                raise ValueError(f"SequenceCollection with digest '{digest}' not found")
            if attribute:  
                return getattr(seqcol, attribute).value
            elif return_format == "level2":
                return seqcol.level2()
            elif return_format == "level1":
                return seqcol.level1()
            elif return_format == "itemwise":
                return seqcol.itemwise(itemwise_limit)
            else:
                return seqcol

    def add(self, seqcol: SequenceCollection) -> SequenceCollection:
        with Session(self.engine) as session:
            with session.no_autoflush:
                csc = session.get(SequenceCollection, seqcol.digest)
                if csc:  # already exists
                    return csc
                csc_simplified = SequenceCollection(
                    digest=seqcol.digest,
                    sorted_name_length_pairs_digest=seqcol.sorted_name_length_pairs_digest,
                )  # not linked to attributes

                # Check if attributes exist; only create them if they don't
                names = session.get(NamesAttr, seqcol.names.digest)
                if not names:
                    names = NamesAttr(**seqcol.names.model_dump())
                    session.add(names)

                sequences = session.get(SequencesAttr, seqcol.sequences.digest)
                if not sequences:
                    sequences = SequencesAttr(**seqcol.sequences.model_dump())
                    session.add(sequences)

                sorted_sequences = session.get(SortedSequencesAttr, seqcol.sorted_sequences.digest)
                if not sorted_sequences:
                    sorted_sequences = SortedSequencesAttr(**seqcol.sorted_sequences.model_dump())
                    session.add(sorted_sequences)

                lengths = session.get(LengthsAttr, seqcol.lengths.digest)
                if not lengths:
                    lengths = LengthsAttr(**seqcol.lengths.model_dump())
                    session.add(lengths)

                # This is a transient attribute
                # sorted_name_length_pairs = session.get(
                #     SortedNameLengthPairsAttr, seqcol.sorted_name_length_pairs.digest
                # )
                # if not sorted_name_length_pairs:
                #     sorted_name_length_pairs = SortedNameLengthPairsAttr(
                #         **seqcol.sorted_name_length_pairs.model_dump()
                #     )
                #     session.add(sorted_name_length_pairs)

                name_length_pairs = session.get(
                    NameLengthPairsAttr, seqcol.name_length_pairs.digest
                )
                if not name_length_pairs:
                    name_length_pairs = NameLengthPairsAttr(
                        **seqcol.name_length_pairs.model_dump()
                    )
                    session.add(name_length_pairs)

                # Link the attributes back to the sequence collection
                names.collection.append(csc_simplified)
                sequences.collection.append(csc_simplified)
                sorted_sequences.collection.append(csc_simplified)
                lengths.collection.append(csc_simplified)
                # sorted_name_length_pairs.collection.append(csc_simplified)
                name_length_pairs.collection.append(csc_simplified)
                session.commit()
                return csc_simplified

    def add_from_dict(self, seqcol_dict: dict):
        seqcol = build_seqcol_model(seqcol_dict, self.inherent_attrs)
        _LOGGER.info(f"SeqCol: {seqcol}")
        _LOGGER.info(f"SeqCol name_length_pairs: {seqcol.name_length_pairs.value}")
        return self.add(seqcol)

    def add_from_fasta_file(self, fasta_file_path: str):
        CSC = fasta_file_to_seqcol(fasta_file_path)
        return self.add_from_dict(CSC)

    def list_by_offset(self, limit=50, offset=0):
        with Session(self.engine) as session:
            list_stmt = select(SequenceCollection).offset(offset).limit(limit)
            cnt_stmt = select(func.count(SequenceCollection.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {"pagination": { "page": int(offset/limit), "page_size": limit, "total": count}, "results": seqcols}

    def list(self, page_size=100, cursor=None):
        with Session(self.engine) as session:
            if cursor:
                list_stmt = (
                    select(SequenceCollection)
                    .where(SequenceCollection.digest >= cursor)
                    .limit(page_size)
                    .order_by(SequenceCollection.digest)
                )
            else:
                list_stmt = (
                    select(SequenceCollection).limit(page_size).order_by(SequenceCollection.digest)
                )
            cnt_stmt = select(func.count(SequenceCollection.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {"count": count, "page_size": page_size, "cursor": cursor, "items": seqcols}


class PangenomeAgent(object):
    def __init__(self, parent):
        self.engine = parent.engine
        self.parent = parent

    def get(self, digest: str, return_format: str = "level2") -> Pangenome:
        with Session(self.engine) as session:
            statement = select(Pangenome).where(Pangenome.digest == digest)
            result = session.exec(statement)
            pangenome = result.one_or_none()
            if not pangenome:
                raise ValueError(f"Pangenome with digest '{digest}' not found")
            if return_format == "level2":
                return pangenome.level2()
            elif return_format == "level1":
                return pangenome.level1()
            elif return_format == "level3":
                return pangenome.level3()
            elif return_format == "level4":
                return pangenome.level4()
            elif return_format == "itemwise":
                l2 = pangenome.level2()
                list_of_dicts = []
                for i in range(len(l2["names"])):
                    list_of_dicts.append(
                        {
                            "name": l2["names"][i],
                            "collection": l2["collections"][i],
                        }
                    )
                return {"collections": list_of_dicts}
            else:
                return pangenome

    def add(self, pangenome: Pangenome) -> Pangenome:

        with Session(self.engine) as session:
            with session.no_autoflush:
                pg = session.get(Pangenome, pangenome.digest)
                if pg:
                    return pg
                pg_simplified = Pangenome(
                    digest=pangenome.digest, collections_digest=pangenome.collections_digest
                )
                names = session.get(CollectionNamesAttr, pangenome.names.digest)
                if not names:
                    names = CollectionNamesAttr(**pangenome.names.model_dump())
                    session.add(names)
                for s in pangenome.collections:
                    seqcol = session.get(SequenceCollection, s.digest)
                    if not seqcol:  # If sequence collection does not exist, create it
                        seqcol = SequenceCollection(**s.model_dump())
                        session.add(seqcol)
                    pg_simplified.collections.append(seqcol)
                names.pangenome.append(pg_simplified)
                session.commit()
                return pg_simplified

    def add_from_fasta_pep(self, pep: peppy.Project, fa_root):
        # First add in the FASTA files individually, and build a dictionary of the results
        pangenome_obj = {}
        for s in pep.samples:
            file_path = os.path.join(fa_root, s.fasta)
            print(f"Fasta to be loaded: Name: {s.sample_name} File path: {file_path}")
            pangenome_obj[s.sample_name] = self.parent.seqcol.add_from_fasta_file(file_path)

        p = build_pangenome_model(pangenome_obj)
        return self.add(p)

    def list_by_offset(self, limit=50, offset=0):
        with Session(self.engine) as session:
            list_stmt = select(Pangenome).offset(offset).limit(limit)
            cnt_stmt = select(func.count(Pangenome.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {"pagination": { "page": int(offset/limit), "page_size": limit, "total": count}, "results": seqcols}


class AttributeAgent(object):
    def __init__(self, engine):
        self.engine = engine

    def get(self, attribute_type: str, digest: str):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            statement = select(Attribute).where(Attribute.digest == digest)
            results = session.exec(statement)
            response = results.first()
            # response.value = response.value.split(",")
            if attribute_type == "lengths":
                response.value = [int(x) for x in response.value]

            return response.value

    def list(self, attribute_type, offset=0, limit=50):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            list_stmt = select(Attribute).offset(offset).limit(limit)
            cnt_stmt = select(func.count(Attribute.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {"pagination": { "page": offset*limit, "page_size": limit, "total": count}, "results": seqcols}

    def search(self, attribute_type, digest, offset=0, limit=50):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            list_stmt = (
                select(SequenceCollection)
                .where(getattr(SequenceCollection, f"{attribute_type}_digest") == digest)
                .offset(offset)
                .limit(limit)
            )
            cnt_stmt = select(func.count(SequenceCollection.digest)).where(
                getattr(SequenceCollection, f"{attribute_type}_digest") == digest
            )
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {"pagination": { "page": offset*limit, "page_size": limit, "total": count}, "results": seqcols}


class RefgetDBAgent(object):
    """
    Primary aggregator agent, interface to all other agents
    """

    def __init__(
        self, postgres_str: str = None, schema=f'{SCHEMA_FILEPATH}/seqcol.json', inherent_attrs=["names", "sequences"]
    ):  # = "sqlite:///foo.db"

        # Connect to database using the provided engine string, or env var defaults
        if not postgres_str:
            POSTGRES_HOST = os.getenv("POSTGRES_HOST")
            POSTGRES_DB = os.getenv("POSTGRES_DB")
            POSTGRES_USER = os.getenv("POSTGRES_USER")
            POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
            postgres_str_old = (
                f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
            )
            postgres_str = URL.create(
                "postgresql",
                username=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
            )

        try:
            self.engine = create_engine(postgres_str, echo=True)
            SQLModel.metadata.create_all(self.engine)
        except Exception as e:
            _LOGGER.error(f"Error: {e}")
            _LOGGER.error("Unable to connect to database")
            _LOGGER.error(
                "Please check that you have set the database credentials correctly in the environment variables"
            )
            _LOGGER.error(f"Database engine string: {postgres_str}")
            raise e

        # Read schema
        if schema:
            self.schema_dict = load_json(schema)
            _LOGGER.info(f"Schema: {self.schema_dict}")
            try:
                self.inherent_attrs = self.schema_dict["ga4gh"]["inherent"]
            except KeyError:
                self.inherent_attrs = inherent_attrs
                _LOGGER.warning(f"No 'inherent' attributes found in schema; using defaults: {inherent_attrs}")
        else:
            _LOGGER.warning("No schema provided; using defaults")
            self.schema_dict = None
            self.inherent_attrs = inherent_attrs

        self.__seqcol = SeqColAgent(self.engine, self.inherent_attrs)
        self.__pangenome = PangenomeAgent(self)
        self.__attribute = AttributeAgent(self.engine)

    def compare_digests(self, digestA, digestB):
        A = self.seqcol.get(digestA, return_format="level2")
        B = self.seqcol.get(digestB, return_format="level2")
        return compare_seqcols(A, B)

    def compare_1_digest(self, digestA, seqcolB):
        A = self.seqcol.get(digestA, return_format="level2")
        B = build_seqcol_model(seqcolB, self.inherent_attrs).level2()
        _LOGGER.info(f"Comparing...")
        _LOGGER.info(f"B: {B}")
        return compare_seqcols(A, B)

    @property
    def seqcol(self) -> SeqColAgent:
        return self.__seqcol

    @property
    def pangenome(self) -> PangenomeAgent:
        return self.__pangenome

    @property
    def attribute(self) -> AttributeAgent:
        return self.__attribute

    def __str__(self):
        return f"RefgetDBAgent. Connection to database: '{self.engine}'"

    def truncate(self):
        """Delete all records from the database"""

        with Session(self.engine) as session:
            statement = delete(SequenceCollection)
            result1 = session.exec(statement)
            statement = delete(Pangenome)
            result = session.exec(statement)
            statement = delete(NamesAttr)
            result = session.exec(statement)
            statement = delete(LengthsAttr)
            result = session.exec(statement)
            statement = delete(SequencesAttr)
            result = session.exec(statement)
            statement = delete(SortedNameLengthPairsAttr)
            result = session.exec(statement)
            statement = delete(NameLengthPairsAttr)
            result = session.exec(statement)
            statement = delete(SortedSequencesAttr)
            result = session.exec(statement)
            
            session.commit()
            return result1.rowcount
