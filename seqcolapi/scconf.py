import logging
import os
import psycopg2

from collections.abc import Mapping
from psycopg2 import OperationalError, sql
from psycopg2.errors import UniqueViolation

_LOGGER = logging.getLogger(__name__)

# Use like:
# pgdb = RDBDict(...)       # Open connection
# pgdb["key"] = "value"     # Insert item
# pgdb["key"]               # Retrieve item
# pgdb.close()              # Close connection

def getenv(varname):
    """ Simple wrapper to make the Exception more informative for missing env var"""
    try: 
        return os.environ[varname]
    except KeyError:
        raise Exception(f"Environment variable {varname} not set.")

import pipestat
class PipestatMapping(pipestat.PipestatManager):
    """ A wrapper class to allow using a PipestatManager as a dict-like object."""
    def __getitem__(self, key):
        # This little hack makes this work with `in`;
        # e.g.: for x in rdbdict, which is now disabled, instead of infinite.
        if isinstance(key, int):
            raise IndexError
        return self.retrieve(key)

    def __setitem__(self, key, value):
        return self.insert({key: value})

    def __len__(self):
        return self.count_records()
        
    def _next_page(self):
        self._buf["page_index"] += 1
        limit = self._buf["page_size"]
        offset = self._buf["page_index"] * limit
        self._buf["keys"] = self.get_records(limit, offset)
        return self._buf["keys"][0]

    def __iter__(self):
        _LOGGER.debug("Iterating...")
        self._buf = {  # buffered iterator
            "current_view_index": 0,
            "len":  len(self),
            "page_size": 100,
            "page_index": -1,
            "keys": self._next_page(),
        }
        return self

    def __next__(self):
        if self._buf["current_view_index"] > self._buf["len"]:
            raise StopIteration
        
        idx = self._buf["current_view_index"] - self._buf["page_index"] * self._buf["page_size"]
        if idx <= self._buf["page_size"]:
            self._buf["current_view_index"] += 1
            return self._buf["keys"][idx-1]
        else:  # current index is beyond current page, but not beyond total
            return self._next_page()


class RDBDict(Mapping):
    """
    A Relational DataBase Dict.

    Simple database connection manager object that allows us to use a
    PostgresQL database as a simple key-value store to back Python
    dict-style access to database items.
    """

    def __init__(
        self,
        db_name: str = None,
        db_user: str = None,
        db_password: str = None,
        db_host: str = None,
        db_port: str = None,
        db_table: str = None,
    ):
        self.connection = None
        self.db_name = db_name or getenv("POSTGRES_DB")
        self.db_user = db_user or getenv("POSTGRES_USER")
        self.db_host = db_host or os.environ.get("POSTGRES_HOST") or "localhost"
        self.db_port = db_port or os.environ.get("POSTGRES_PORT") or "5432"
        self.db_table = db_table or os.environ.get("POSTGRES_TABLE") or "seqcol"
        db_password = db_password or getenv("POSTGRES_PASSWORD")

        try:
            self.connection = self.create_connection(
                self.db_name, self.db_user, db_password, self.db_host, self.db_port
            )
            if not self.connection:
                raise Exception("Connection failed")
        except Exception as e:
            _LOGGER.info(f"{self}")
            raise e
        _LOGGER.info(self.connection)
        self.connection.autocommit = True

    def __repr__(self):
        return (
            "RDBD object\n"
            + "db_table: {}\n".format(self.db_table)
            + "db_name: {}\n".format(self.db_name)
            + "db_user: {}\n".format(self.db_user)
            + "db_host: {}\n".format(self.db_host)
            + "db_port: {}\n".format(self.db_port)
        )

    def init_table(self):
        # Wrap statements to prevent SQL injection attacks
        stmt = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {table}(
            key TEXT PRIMARY KEY, 
            value TEXT);
        """
        ).format(table=sql.Identifier(self.db_table))
        return self.execute_query(stmt, params=None)

    def insert(self, key, value):
        stmt = sql.SQL(
            """
            INSERT INTO {table}(key, value)
            VALUES (%(key)s, %(value)s);
        """
        ).format(table=sql.Identifier(self.db_table))
        params = {"key": key, "value": value}
        return self.execute_query(stmt, params)

    def update(self, key, value):
        stmt = sql.SQL(
            """
            UPDATE {table} SET value=%(value)s WHERE key=%(key)s
        """
        ).format(table=sql.Identifier(self.db_table))
        params = {"key": key, "value": value}
        return self.execute_query(stmt, params)

    def __getitem__(self, key):
        # This little hack makes this work with `in`;
        # e.g.: for x in rdbdict, which is now disabled, instead of infinite.
        if isinstance(key, int):
            raise IndexError
        stmt = sql.SQL(
            """
            SELECT value FROM {table} WHERE key=%(key)s
        """
        ).format(table=sql.Identifier(self.db_table))
        params = {"key": key}
        res = self.execute_read_query(stmt, params)
        if not res:
            _LOGGER.info("Not found: {}".format(key))
        return res

    def __setitem__(self, key, value):
        try:
            return self.insert(key, value)
        except UniqueViolation as e:
            _LOGGER.info("Updating existing value for {}".format(key))
            return self.update(key, value)

    def __delitem__(self, key):
        stmt = sql.SQL(
            """
            DELETE FROM {table} WHERE key=%(key)s
        """
        ).format(table=sql.Identifier(self.db_table))
        params = {"key": key}
        res = self.execute_query(stmt, params)
        return res

    def create_connection(self, db_name, db_user, db_password, db_host, db_port):
        connection = None
        try:
            connection = psycopg2.connect(
                database=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            _LOGGER.info("Connection to PostgreSQL DB successful")
        except OperationalError as e:
            _LOGGER.info("Error: {e}".format(e=str(e)))
        return connection

    def execute_read_query(self, query, params=None):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                _LOGGER.debug(f"Query: {query}")
                _LOGGER.debug(f"Result: {result}")
                return None
        except OperationalError as e:
            _LOGGER.info("Error: {e}".format(e=str(e)))
            raise Exception
            return None
        except TypeError as e:
            _LOGGER.info("TypeError: {e}, item: {q}".format(e=str(e), q=query))
            raise Exception
            return None

    def execute_multi_query(self, query, params=None):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except OperationalError as e:
            _LOGGER.info("Error: {e}".format(e=str(e)))
            raise Exception
            return None
        except TypeError as e:
            pri_LOGGER.infont("TypeError: {e}, item: {q}".format(e=str(e), q=query))
            raise Exception
            return None

    def execute_query(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            return cursor.execute(query, params)
            _LOGGER.info("Query executed successfully")
        except OperationalError as e:
            _LOGGER.info("Error: {e}".format(e=str(e)))

    def close(self):
        _LOGGER.info("Closing connection")
        return self.connection.close()

    def __del__(self):
        if self.connection:
            self.close()

    def __len__(self):
        stmt = sql.SQL(
            """
            SELECT COUNT(*) FROM {table}
        """
        ).format(table=sql.Identifier(self.db_table))
        print(stmt)
        res = self.execute_read_query(stmt)
        return res

    def get_paged_keys(self, limit=None, offset=None):
        stmt_str = "SELECT key FROM {table}"
        if limit:
            stmt_str += f" LIMIT {limit}"
        if offset != None:
            stmt_str += f" OFFSET {offset}"
        stmt = sql.SQL(stmt_str).format(
            table=sql.Identifier(self.db_table))
        res = self.execute_multi_query(stmt)
        return res   

    def _next_page(self):
        self._buf["page_index"] += 1
        limit = self._buf["page_size"]
        offset = self._buf["page_index"] * limit
        self._buf["keys"] = self.get_paged_keys(limit, offset)
        return self._buf["keys"][0]

    def __iter__(self):
        _LOGGER.debug("Iterating...")
        self._buf = {  # buffered iterator
            "current_view_index": 0,
            "len":  len(self),
            "page_size": 10,
            "page_index": 0,
            "keys": self.get_paged_keys(10, 0),
        }
        return self

    def __next__(self):
        if self._buf["current_view_index"] > self._buf["len"]:
            raise StopIteration
        
        idx = self._buf["current_view_index"] - self._buf["page_index"] * self._buf["page_size"]
        if idx <= self._buf["page_size"]:
            self._buf["current_view_index"] += 1
            return self._buf["keys"][idx-1]
        else:  # current index is beyond current page, but not beyond total
            return self._next_page()

    # Old, non-paged iterator:
    # def __iter__(self):
    #     self._current_idx = 0
    #     return self

    # def __next__(self):
    #     stmt = sql.SQL(
    #         """
    #         SELECT key,value FROM {table} LIMIT 1 OFFSET %(idx)s
    #     """
    #     ).format(table=sql.Identifier(self.db_table))
    #     res = self.execute_read_query(stmt, {"idx": self._current_idx})
    #     self._current_idx += 1
    #     if not res:
    #         _LOGGER.info("Not found: {}".format(self._current_idx))
    #         raise StopIteration
    #     return res



# We don't need the full SeqColHenge,
# which also has loading capability, and requires pyfaidx, which requires
# biopython, which requires numpy, which is huge and can't compile the in
# default fastapi container.
# So, I had written the below class which provides retrieve only.
# HOWEVER, switching from alpine to slim allows install of numpy;
# This inflates the container size from 262Mb to 350Mb; perhaps that's worth paying.
# So I can avoid duplicating this and just use the full SeqColHenge from seqcol
# class SeqColHenge(refget.RefGetClient):
#     def retrieve(self, druid, reclimit=None, raw=False):
#         try:
#             return super(SeqColHenge, self).retrieve(druid, reclimit, raw)
#         except henge.NotFoundException as e:
#             _LOGGER.debug(e)
#             try:
#                 return self.refget(druid)
#             except Exception as e:
#                 _LOGGER.debug(e)
#                 raise e
#                 return henge.NotFoundException("{} not found in database, or in refget.".format(druid))
