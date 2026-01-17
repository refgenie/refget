"""Digest functions with Python fallbacks.

When gtars is available, uses fast Rust implementations.
When gtars is not available, falls back to pure Python implementations (slower).
"""
import hashlib
import base64

from typing import Callable, Union

from .const import GTARS_INSTALLED


def ga4gh_digest(seq):
    """Adds the ga4gh:SQ. prefix to the digest, for sequences use"""
    digest = sha512t24u_digest(seq)
    return "ga4gh:SQ.{}".format(digest)


def py_sha512t24u_digest(seq: str | bytes, offset: int = 24) -> str:
    """GA4GH digest function in pure Python (slower fallback)."""
    if isinstance(seq, str):
        seq = seq.encode("utf-8")
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")


def py_md5_digest(seq) -> str:
    """MD5 digest function in pure Python."""
    return hashlib.md5(seq.encode()).hexdigest()


# Default exports - use gtars if available, else Python fallback
if GTARS_INSTALLED:
    from .processing.digest import sha512t24u_digest, md5_digest
else:
    sha512t24u_digest = py_sha512t24u_digest
    md5_digest = py_md5_digest


DigestFunction = Callable[[Union[str, bytes]], str]
"""A type alias for a digest function that takes a sequence and returns a digest."""
