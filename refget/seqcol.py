import henge
import logging
import yacman

from itertools import compress

from .const import *
from .utilities import *


_LOGGER = logging.getLogger(__name__)
henge.ITEM_TYPE = "_item_type"


class SeqColConf(yacman.YAMLConfigManager):
    """
    Simple configuration manager object for SeqColHenge.
    """

    def __init__(
        self,
        entries={},
        filepath=None,
        yamldata=None,
        writable=False,
        wait_max=60,
        skip_read_lock=False,
    ):
        filepath = yacman.select_config(
            config_filepath=filepath, config_env_vars=["SEQCOLAPI_CONFIG"], config_name="seqcol"
        )
        super(SeqColConf, self).__init__(entries, filepath, yamldata, writable)


class SeqColHenge(henge.Henge):
    """
    Extension of henge that accommodates collections of sequences.
    """

    def __init__(
        self,
        database={},
        schemas=None,
        henges=None,
        checksum_function=sha512t24u_digest,
    ):
        """
        A user interface to insert and retrieve decomposable recursive unique
        identifiers (DRUIDs).

        :param dict database: Dict-like lookup database with sequences
            and hashes
        :param dict schemas: One or more jsonschema schemas describing the
            data types stored by this Henge
        :param function(str) -> str checksum_function: Default function to
            handle the digest of the
            serialized items stored in this henge.
        """
        super(SeqColHenge, self).__init__(
            database=database,
            schemas=schemas or INTERNAL_SCHEMAS,
            henges=henges,
            checksum_function=checksum_function,
        )
        _LOGGER.info("Initializing SeqColHenge")

    def load_fasta(self, fa_file, skip_seq=False, topology_default="linear"):
        """
        Load a sequence collection into the database

        :param str fa_file: path to the FASTA file to parse and load
        :param bool skip_seq: whether to disregard the actual sequences,
            load just the names and lengths and topology
        :param bool skip_seq: whether to disregard the actual sequences,
            load just the names and lengths and topology
        :param str topology_default: the default topology assigned to
            every sequence
        """
        # TODO: any systematic way infer topology from a FASTA file?
        if topology_default not in KNOWN_TOPOS:
            raise ValueError(
                f"Invalid topology ({topology_default}). " f"Choose from: {','.join(KNOWN_TOPOS)}"
            )
        fa_object = parse_fasta(fa_file)
        aslist = []
        for k in fa_object.keys():
            seq = str(fa_object[k])
            aslist.append(
                {
                    NAME_KEY: k,
                    LEN_KEY: len(seq),
                    TOPO_KEY: topology_default,
                    SEQ_KEY: {"" if skip_seq else SEQ_KEY: seq},
                }
            )
        collection_checksum = self.insert(aslist, ASL_NAME)
        _LOGGER.debug(f"Loaded {ASL_NAME}: {aslist}")
        return collection_checksum, aslist

    def load_fasta2(self, fa_file, skip_seq=False, topology_default="linear"):
        """
        Load a sequence collection into the database

        :param str fa_file: path to the FASTA file to parse and load
        :param bool skip_seq: whether to disregard the actual sequences,
            load just the names and lengths and topology
        :param bool skip_seq: whether to disregard the actual sequences,
            load just the names and lengths and topology
        :param str topology_default: the default topology assigned to
            every sequence
        """
        # TODO: any systematic way infer topology from a FASTA file?
        _LOGGER.info("Loading fasta file...")
        fa_object = parse_fasta(fa_file)
        aslist = []
        for k in fa_object.keys():
            seq = str(fa_object[k])
            _LOGGER.info("Loading key: {k} / Length: {l}...".format(k=k, l=len(seq)))
            aslist.append(
                {
                    NAME_KEY: k,
                    LEN_KEY: len(seq),
                    TOPO_KEY: topology_default,
                    SEQ_KEY: "" if skip_seq else seq,
                }
            )
        _LOGGER.info("Inserting into database...")
        collection_checksum = self.insert(aslist, "RawSeqCol")
        _LOGGER.debug(f"Loaded {ASL_NAME}: {aslist}")
        return collection_checksum, aslist

    def compare_digests(self, digestA, digestB):
        A = self.retrieve(digestA, reclimit=1)
        B = self.retrieve(digestB, reclimit=1)
        # _LOGGER.info(A)
        # _LOGGER.info(B)
        return compare_seqcols(A, B)

    def retrieve(self, druid, reclimit=None, raw=False):
        try:
            return super(SeqColHenge, self).retrieve(druid, reclimit, raw)
        except henge.NotFoundException as e:
            _LOGGER.debug(e)
            raise e
            try:
                return self.refget(druid)
            except Exception as e:
                _LOGGER.debug(e)
                raise e
                return henge.NotFoundException(
                    "{} not found in database, or in refget.".format(druid)
                )

    def load_fasta_from_refgenie(self, rgc, refgenie_key):
        """
        @param rgc RefGenConf object
        @param refgenie_key key of genome to load
        """
        filepath = rgc.seek(refgenie_key, "fasta")
        return self.load_fasta_from_filepath(filepath)

    def load_fasta_from_filepath(self, filepath):
        """
        @param filepath Path to fasta file
        """
        fa_object = parse_fasta(filepath)
        SCAS = fasta_obj_to_seqcol(fa_object, digest_function=self.checksum_function)
        digest = self.insert(SCAS, "SeqColArraySet", reclimit=1)
        return {
            "fa_file": filepath,
            "fa_object": fa_object,
            "SCAS": SCAS,
            "digest": digest,
        }

    def load_from_chromsizes(self, chromsizes):
        """
        @param chromsizes Path to chromsizes file
        """
        SCAS = chrom_sizes_to_seqcol(chromsizes, digest_function=self.checksum_function)
        digest = self.insert(SCAS, "SeqColArraySet", reclimit=1)
        return {
            "chromsizes_file": chromsizes,
            "SCAS": SCAS,
            "digest": digest,
        }

    def load_multiple_fastas(self, fasta_dict):
        """
        Wrapper for load_fasta_from_filepath

        @param fasta_list
        """
        results = {}
        for name in fasta_dict.keys():
            path = fasta_dict[name]["fasta"]
            print(f"Processing fasta '{name}'' at path '{path}'...")
            results[name] = self.load_fasta_from_filepath(path)
        return results
