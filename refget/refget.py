import henge
import json
import os
import pyfaidx
import logging
import requests
import yaml

from yacman import load_yaml
from copy import copy


_LOGGER = logging.getLogger(__name__)
henge.ITEM_TYPE = "_item_type"
SCHEMA_FILEPATH = os.path.join(
        os.path.dirname(__file__),
        "schemas")

sequence_schema = """description: "Schema for a single raw sequence"
henge_class: sequence
type: object
properties:
  sequence:
    type: string
    description: "Actual sequence content"
required:
  - sequence
"""



class RefGetClient(henge.Henge):
    def __init__(self, api_url_base=None, database={}, schemas=None, henges=None, checksum_function=henge.md5, suppress_connect=True):
        """
        A user interface to insert and retrieve decomposable recursive unique
        identifiers (DRUIDs).

        :param dict database: Dict-like lookup database with sequences and hashes.
        :param dict schemas: One or more jsonschema schemas describing the
            data types stored by this Henge
        :param function(str) -> str checksum_function: Default function to handle the digest of the
            serialized items stored in this henge.
        """      
        self.api_url_base = api_url_base
        self.local_cache = database
        self.info = None
        if not suppress_connect:
            self.info = self.get_service_info()


        # These are the item types that this henge can understand.
        if not schemas:
            schemas = [sequence_schema]
        print(schemas)
        super(RefGetClient, self).__init__(database, schemas, henges=henges,
                                          checksum_function=checksum_function)

    def refget_remote(self, digest, start=None, end=None):
        if not self.api_url_base:
            print("No remote URL connected")
            return

        url = "{base}{digest}?accept=text/plain".format(
            base=self.api_url_base,
            digest=digest)


        if start is not None and end is not None:
            full_retrieved = False
            url = "{base}&start={start}&end={end}".format(base=url, start=start, end=end)
        else:
            full_retrieved = True

        r = requests.get(url)
        result = r.content.decode('utf-8')

        if full_retrieved:
            self.load_seq(result)
                
        return result

    def refget(self, digest, start=None, end=None):
        full_data = None
        try:
            full_data = self.retrieve(digest)
            if start is not None and end is not None:
                result = full_data['sequence'][start:end]
            else:
                result = full_data['sequence']
            
            return result
        except henge.NotFoundException:
            return self.refget_remote(digest, start, end)

    def load_seq(self, seq):
        checksum = self.insert({'sequence': seq}, "sequence")
        _LOGGER.debug("Loaded {}".format(checksum))
        return checksum

    @property
    def service_info(self):
        if not self.info:
            self.info = self.get_service_info()
        return self.info
    
    def meta(self, digest):
        url = "{base}{digest}/metadata".format(
            base=self.api_url_base,
            digest=digest)
        
        r = requests.get(url)
        return json.loads(r.content.decode('utf-8'))
    
    def get_service_info(self):
        url = "{base}service-info".format(
            base=self.api_url_base)
        
        r = requests.get(url)
        return json.loads(r.content.decode('utf-8'))     


    def load_fasta(self, fa_file, lengths_only=False):
        """
        Calculates checksums and loads each sequence in a fasta file into the
        database.
        """
        fa_object = parse_fasta(fa_file)
        asdlist = []
        for k in fa_object.keys():
            seq = str(fa_object[k])
            seq_digest = self.load_seq(seq)
            asdlist.append({'name': k,
                          'length': len(seq), 
                          'sequence_digest': seq_digest})

        _LOGGER.debug(asdlist)
        return asdlist

    def load_sequence_dict(self, seqset):
        """
        Convert a 'seqset', which is a dict with names as sequence names and
        values as sequences, into the 'asdlist' required for henge insert.
        """
        seqset_new = copy(seqset)
        for k, v in seqset.items():
            if isinstance(v, str):
                seq = v
                v = {'sequence': seq}
            if 'length' not in v.keys():
                if 'sequence' not in v.keys():
                    _LOGGER.warning(
                        "Each sequence must have either length or a sequence.")
                else:
                    v['length'] = len(v['sequence'])
            if 'sequence' in v.keys():
                v['sequence_digest'] = self.load_seq(seq)
                del v['sequence']
            if 'name' not in v.keys():
                v['name'] = k
            if 'toplogy' not in v.keys():
                v['toplogy'] = 'linear'

            seqset_new[k] = v

        collection_checksum = self.insert(list(seqset_new.values()), 'ASDList')
        return collection_checksum, seqset_new



# Static functions below (these don't require a database)

def parse_fasta(fa_file):
    _LOGGER.debug("Hashing {}".format(fa_file))
    try:
        fa_object = pyfaidx.Fasta(fa_file)
    except pyfaidx.UnsupportedCompressionFormat:
        # pyfaidx can handle bgzip but not gzip; so we just hack it here and
        # unzip the file for checksumming, then rezip it for the rest of the
        # asset build.
        # TODO: streamline this to avoid repeated compress/decompress
        os.system("gunzip {}".format(fa_file))
        fa_file_unzipped = fa_file.replace(".gz", "")
        fa_object = pyfaidx.Fasta(fa_file_unzipped)
        os.system("gzip {}".format(fa_file_unzipped))
    return fa_object