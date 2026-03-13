from pathlib import Path

import pytest

from refget import GTARS_INSTALLED
from refget.digests import ga4gh_digest, py_md5_digest, py_sha512t24u_digest

if GTARS_INSTALLED:
    from gtars.refget import (
        digest_fasta,
    )
    from gtars.refget import (
        md5_digest as gtars_md5_digest,
    )
    from gtars.refget import (
        sha512t24u_digest as gtars_sha512t24u_digest,
    )


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
        res_path = digest_fasta(p)
        res_str = digest_fasta("test_fasta/base.fa")

        for i in range(len(res_path.sequences)):
            assert (
                res_path.sequences[i].metadata.sha512t24u
                == res_str.sequences[i].metadata.sha512t24u
            )
