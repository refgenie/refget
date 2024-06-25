import os

from sqlmodel import create_engine, select, Session, delete, func
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from .models import *
from .utilities import build_seqcol_model, fasta_file_to_seqcol, format_itemwise, compare_seqcols

ATTR_TYPE_MAP = {
    "sequences": SequencesAttr,
    "names": NamesAttr,
    "lengths": LengthsAttr,
    "sorted_name_length_pairs": SortedNameLengthPairsAttr
}
from sqlalchemy.dialects.postgresql import insert

def read_url(url):
    import yaml
    print("Reading URL: {}".format(url))
    from urllib.request import urlopen
    from urllib.error import HTTPError
    try:
        response = urlopen(url)
    except HTTPError as e:
        raise e
    data = response.read()  # a `bytes` object
    text = data.decode("utf-8")
    return yaml.safe_load(text)



class SeqColAgent(object):
    def __init__(self, engine, inherent_attrs=None):
        self.engine = engine 
        self.inherent_attrs = inherent_attrs

    def get(self, digest: str, return_format:str = "full"):
        with Session(self.engine) as session:
            statement = select(SequenceCollection).where(SequenceCollection.digest == digest)
            results = session.exec(statement)
            seqcol = results.first()
            if not seqcol:
                raise ValueError(f"SequenceCollection with digest '{digest}' not found")
            if return_format == "level2":
                return {
                        "lengths": [int(x) for x in seqcol.lengths.value.split(",")],
                        "names": seqcol.names.value.split(","),
                        "sequences": seqcol.sequences.value.split(","),
                        "sorted_name_length_pairs": seqcol.sorted_name_length_pairs.value.split(","),
                }
            elif return_format == "level1":
                return {
                        "lengths": seqcol.lengths_digest,
                        "names": seqcol.names_digest,
                        "sequences": seqcol.sequences_digest,
                        "sorted_name_length_pairs": seqcol.sorted_name_length_pairs_digest,
                }
            elif return_format == "itemwise":
                l2 = {
                        "names": seqcol.names.value.split(","),
                        "lengths": [int(x) for x in seqcol.lengths.value.split(",")],
                        "sequences": seqcol.sequences.value.split(","),
                        "sorted_name_length_pairs": seqcol.sorted_name_length_pairs.value.split(","),
                }
                return format_itemwise(l2)
            else:
                return seqcol
            
    def add(self, seqcol: SequenceCollection):
        with Session(self.engine) as session:
            with session.no_autoflush:
                csc = session.get(SequenceCollection, seqcol.digest)
                if csc:
                    return csc
                csc_simplified = SequenceCollection(digest=seqcol.digest)
                names = session.get(NamesAttr, seqcol.names.digest)
                if not names:
                    names = NamesAttr(**seqcol.names.model_dump())
                    session.add(names)
                sequences = session.get(SequencesAttr, seqcol.sequences.digest)
                if not sequences:
                    sequences = SequencesAttr(**seqcol.sequences.model_dump())
                    session.add(sequences)
                lengths = session.get(LengthsAttr, seqcol.lengths.digest)
                if not lengths:
                    lengths = LengthsAttr(**seqcol.lengths.model_dump())
                    session.add(lengths)
                sorted_name_length_pairs = session.get(SortedNameLengthPairsAttr, seqcol.sorted_name_length_pairs.digest)
                if not sorted_name_length_pairs:
                    sorted_name_length_pairs = SortedNameLengthPairsAttr(**seqcol.sorted_name_length_pairs.model_dump())
                    session.add(sorted_name_length_pairs)
                names.collection.append(csc_simplified)
                sequences.collection.append(csc_simplified)
                lengths.collection.append(csc_simplified)
                sorted_name_length_pairs.collection.append(csc_simplified)
                session.commit()


    def add_from_dict(self, seqcol_dict: dict):
        seqcol = build_seqcol_model(seqcol_dict, self.inherent_attrs)
        print(seqcol)
        return self.add(seqcol)

    def add_from_fasta_file(self, fasta_file_path: str):
        CSC = fasta_file_to_seqcol(fasta_file_path)
        print("CSCSCC:::::::::::::::::::::::::::::::::::::::")
        print(CSC)
        return self.add_from_dict(CSC)
    
    def list_by_offset(self, limit=50, offset=0):
        with Session(self.engine) as session:
            list_stmt =  select(SequenceCollection).offset(offset).limit(limit)
            cnt_stmt = select(func.count(SequenceCollection.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {
                "count": count,
                "limit": limit,
                "offset": offset,
                "items": seqcols
            }
    
    def list(self, page_size=100, cursor=None):
        with Session(self.engine) as session:
            if cursor: 
                list_stmt =  select(SequenceCollection).where(SequenceCollection.digest >= cursor).limit(page_size).order_by(SequenceCollection.digest)
            else:
                list_stmt =  select(SequenceCollection).limit(page_size).order_by(SequenceCollection.digest)
            cnt_stmt = select(func.count(SequenceCollection.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {
                "count": count,
                "page_size": page_size,
                "cursor": cursor,
                "items": seqcols
            }

        
class PangenomeAgent(object):
    def __init__(self, engine):
        self.engine = engine 

    def get(self, digest: str):
        with Session(self.engine) as session:
            statement = select(Pangenome).where(Pangenome.digest == digest)
            results = session.exec(statement)
            return results.first()


class AttributeAgent(object):
    def __init__(self, engine):
        self.engine = engine
    
    def get(self, attribute_type: str, digest: str):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            statement = select(Attribute).where(Attribute.digest == digest)
            results = session.exec(statement)
            response = results.first()
            response.value = response.value.split(",")
            if attribute_type == "lengths":
                response.value = [int(x) for x in response.value]
            return response
    
    def list(self, attribute_type, offset=0, limit=50):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            list_stmt =  select(Attribute).offset(offset).limit(limit)
            cnt_stmt = select(func.count(Attribute.digest))
            cnt_res = session.exec(cnt_stmt)
            list_res = session.exec(list_stmt)
            count = cnt_res.one()
            seqcols = list_res.all()
            return {
                "count": count,
                "limit": limit,
                "offset": offset,
                "items": seqcols
            }

    def search(self, attribute_type, digest):
        Attribute = ATTR_TYPE_MAP[attribute_type]
        with Session(self.engine) as session:
            statement = select(SequenceCollection).where(getattr(SequenceCollection, f"{attribute_type}_digest") == digest)
            results = session.exec(statement)
            return results.all()



class RefgetDBAgent(object):
    """
    Primary aggregator agent, interface to all other agents
    """
    def __init__(self, postgres_str: str = None, inherent_attrs=["names", "lengths", "sequences"]): # = "sqlite:///foo.db"
        if not postgres_str:
            POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
            POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
            POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
            POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
            postgres_str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
        self.engine = create_engine(postgres_str, echo=True)
        SQLModel.metadata.create_all(self.engine)  
        self.inherent_attrs = inherent_attrs
        self.__seqcol = SeqColAgent(self.engine, self.inherent_attrs)
        self.__pangenome = PangenomeAgent(self.engine)
        self.__attribute = AttributeAgent(self.engine)

    

    def compare_digests(self, digestA, digestB):
        A = self.seqcol.get(digestA, return_format="level2")
        B = self.seqcol.get(digestB, return_format="level2")
        # _LOGGER.info(A)
        # _LOGGER.info(B)
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
            statement=delete(SequenceCollection)
            result1 = session.exec(statement)
            statement=delete(Pangenome)
            result = session.exec(statement)
            statement=delete(NamesAttr)
            result = session.exec(statement)
            statement=delete(LengthsAttr)
            result = session.exec(statement)
            statement=delete(SequencesAttr)
            result = session.exec(statement)
            session.commit()
            return result1.rowcount
