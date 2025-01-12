import pytest

from refget import gtars_sha512t24u_digest, ga4gh_digest, py_sha512t24u_digest
from refget.const import GTARS_INSTALLED

@pytest.mark.skipif(not GTARS_INSTALLED, reason="gtars is not installed")
class TestRustDigest:
    def test_digest(self):
        dig_raw = gtars_sha512t24u_digest("ACGT")
        dig_prefixed = f'ga4gh:SQ.{dig_raw}'
        assert ga4gh_digest("ACGT") == dig_prefixed

    def test_rust_py_digest_equivalent(self):
        assert gtars_sha512t24u_digest("ACGT") == py_sha512t24u_digest("ACGT")
        assert gtars_sha512t24u_digest("tcga") == py_sha512t24u_digest("tcga")

