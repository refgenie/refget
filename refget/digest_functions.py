import hashlib
import binascii
import base64

from typing import Callable, Union

from .const import GTARS_INSTALLED

if GTARS_INSTALLED:

    from gtars.digests import sha512t24u_digest as gtars_sha512t24u_digest
    from gtars.digests import md5_digest as gtars_md5_digest
    from gtars.digests import digest_fasta as fasta_to_seq_digests

    sha512t24u_digest = gtars_sha512t24u_digest
    md5_digest = gtars_md5_digest
else:

    # gtars package is not installed, so we will use the Python implementation,
    # which will be much slower.

    def gtars_sha512t24u_digest(seq):
        raise Exception("gtars is not installed")

    def fasta_to_seq_digests(*args, **kwargs):
        raise ImportError("gtars is required for this function.")

    sha512t24u_digest = py_sha512t24u_digest
    md5_digest = py_md5_digest


DigestFunction = Callable[[Union[str, bytes]], str]
""" A type alias for a digest function that takes a sequence and returns a digest. """


def trunc512_digest(seq, offset=24) -> str:
    """Deprecated GA4GH digest function"""
    digest = hashlib.sha512(seq.encode()).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode()


def ga4gh_digest(seq):
    """Adds the ga4gh:SQ. prefix to the digest, for sequences use"""
    digest = sha512t24u_digest(seq)
    return "ga4gh:SQ.{}".format(digest)


def py_sha512t24u_digest(seq: str | bytes, offset: int = 24) -> str:
    """GA4GH digest function in python"""
    if isinstance(seq, str):
        seq = seq.encode("utf-8")
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")


def py_md5_digest(seq) -> str:
    """MD5 digest function in Python"""
    return hashlib.md5(seq.encode()).hexdigest()
