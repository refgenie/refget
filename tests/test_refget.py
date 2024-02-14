import pytest
import os
from refget import RefGetClient
import tempfile

DEMO_FILES = ["demo.fa", "demo2.fa", "demo3.fa", "demo4.fa", "demo5.fa"]


class TestEmptyConstructor:
    def test_no_schemas_required(self):
        assert isinstance(RefGetClient(), RefGetClient)


class TestInsert:
    @pytest.mark.parametrize("fasta_name", DEMO_FILES)
    def test_insert_works(self, fasta_name, fasta_path):
        rgc = RefGetClient()
        d = rgc.load_seq("TCGA")
        assert rgc.refget(d) == "TCGA"
