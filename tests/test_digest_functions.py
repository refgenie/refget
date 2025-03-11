import pytest

from refget import (
    gtars_sha512t24u_digest,
    ga4gh_digest,
    py_sha512t24u_digest,
    gtars_md5_digest,
    py_md5_digest,
    fasta_to_seq_digests,
)
from refget.const import GTARS_INSTALLED
from pathlib import Path


@pytest.mark.skipif(not GTARS_INSTALLED, reason="gtars is not installed")
class TestRustDigest:
    def test_digest(self):
        digest_raw = gtars_sha512t24u_digest("ACGT")
        digest_prefixed = f"ga4gh:SQ.{digest_raw}"
        assert ga4gh_digest("ACGT") == digest_prefixed

    def test_rust_py_digest_equivalent(self):
        assert gtars_sha512t24u_digest("ACGT") == py_sha512t24u_digest("ACGT")
        assert gtars_sha512t24u_digest("tcga") == py_sha512t24u_digest("tcga")
        assert gtars_md5_digest("ACGT") == py_md5_digest("ACGT")
        assert gtars_md5_digest("tcga") == py_md5_digest("tcga")

    def test_rust_input_types(self):
        # These functions should accept both str and bytes
        str_digest = gtars_sha512t24u_digest("ACGT")
        bytes_digest = gtars_sha512t24u_digest(b"ACGT")
        assert str_digest == bytes_digest

        str_digest = gtars_md5_digest("ACGT")
        bytes_digest = gtars_md5_digest(b"ACGT")
        assert str_digest == bytes_digest

    def test_fasta_digest(self):
        # Function should accept a string or a PosixPath
        p = Path("test_fasta/base.fa")
        res_path = fasta_to_seq_digests(p)
        res_str = fasta_to_seq_digests("test_fasta/base.fa")

        for i in range(len(res_path)):
            assert res_path[i].sha512t24u == res_str[i].sha512t24u
