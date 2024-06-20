from sqlmodel import create_engine, select, Session, delete, func
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from .models import *
from .utilities import build_seqcol_model, fasta_file_to_seqcol, format_itemwise

ATTR_TYPE_MAP = {
    "sequences": SequencesAttr,
    "names": NamesAttr,
    "lengths": LengthsAttr
}
from sqlalchemy.dialects.postgresql import insert




class SeqColAgent(object):
    def __init__(self, engine):
        self.engine = engine 

    def get(self, digest: str, return_format:str = "full"):
        with Session(self.engine) as session:
            statement = select(SequenceCollection).where(SequenceCollection.digest == digest)
            results = session.exec(statement)
            seqcol = results.first()
            if not seqcol:
                raise ValueError(f"SequenceCollection with digest '{digest}' not found")
            if return_format == "level2":
                return {
                        "names": seqcol.names.value,
                        "lengths": seqcol.lengths.value,
                        "sequences": seqcol.sequences.value,
                }
            elif return_format == "level1":
                return {
                        "names": seqcol.names_digest,
                        "lengths": seqcol.lengths_digest,
                        "sequences": seqcol.sequences_digest
                }
            elif return_format == "itemwise":
                l2 = {
                        "names": seqcol.names.value,
                        "lengths": seqcol.lengths.value,
                        "sequences": seqcol.sequences.value,
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
                names.collection.append(csc_simplified)
                sequences.collection.append(csc_simplified)
                lengths.collection.append(csc_simplified)
                session.commit()


    def add_from_dict(self, seqcol_dict: dict):
        seqcol = build_seqcol_model(seqcol_dict)
        return self.add(seqcol)

    def add_from_fasta_file(self, fasta_file_path: str):
        CSC = fasta_file_to_seqcol(fasta_file_path)
        return self.add_from_dict(CSC)
    
    def list(self, offset=0, limit=50):
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
            return results.first()
    
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






class RefgetDBAgent(object):
    def __init__(self, postgres_str):
        self.engine = create_engine(postgres_str, echo=True)
        SQLModel.metadata.create_all(self.engine)  
        self.__seqcol = SeqColAgent(self.engine)
        self.__pangenome = PangenomeAgent(self.engine)
        self.__attribute = AttributeAgent(self.engine)
    

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
