import pytest
import os
from refget import RefGetClient
import tempfile

DEMO_FILES = ["demo.fa", "demo2.fa", "demo3.fa", "demo4.fa", "demo5.fa"]


class TestEmptyConstructor:
    def test_no_schemas_required(self):
        assert isinstance(RefGetClient(), RefGetClient)


class TestSequenceCollections:
    def test_get_collection(self):
        rgc = RefGetClient()
        seqcol = rgc.get_collection("fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32")
        assert isinstance(seqcol, dict)

    def test_list_collections(self):
        rgc = RefGetClient()
        l = rgc.list_collections()
        assert isinstance(l, dict)
        assert "results" in l
        assert len(l["results"]) > 0

    def test_list_attributes(self):
        rgc = RefGetClient()
        a = rgc.list_attributes("lengths")
        assert isinstance(a, dict)
        assert "results" in a
        assert len(a["results"]) > 0

    def test_compare(self):
        rgc = RefGetClient()
        c = rgc.compare("fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32", "fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32")
        assert isinstance(c, dict)
        assert "digests" in c


# _LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel("DEBUG")
# rgc = RefGetClient(seqcol_api_urls=["https://seqcolapi.databio.org", "https://localhost"])
# rgc = RefGetClient(seqcol_api_urls=["https://localhost", "https://seqcolapi.databio.org"])

# seqcol = rgc.get_collection("fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32")
# seqcol = rgc.get_collection("MFxJDHkVdTBlPvUFRbYWDZYxmycvHSRp")
# l = rgc.list_collections(page_size=5)
# a = rgc.list_attributes("lengths", page_size=3)

# l = rgc.list_collections(page=1, page_size=2, attribute="lengths", attribute_digest="cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RX")


# rgc.get_sequence(seqcol["sequences"][0])

# rgc.compare("fLf5M0BOIPIqcfbE6R8oYwxsy-PnoV32", "MFxJDHkVdTBlPvUFRbYWDZYxmycvHSRp")
