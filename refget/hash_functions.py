# Refget digests from published refget v1.0 protocol
# Retrieved July 2019
# http://samtools.github.io/hts-specs/refget.html

import base64
import hashlib
import binascii
from typing import Union

def trunc512_digest(seq, offset=24):
    digest = hashlib.sha512(seq.encode("utf-8")).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode("utf-8")


def ga4gh_digest(seq, digest_size=24):
    # b64 encoding results in 4/3 size expansion of data and padded if
    # not multiple of 3, which doesn't make sense for this use
    assert digest_size % 3 == 0, "digest size must be multiple of 3"
    digest = hashlib.sha512(seq.encode("utf-8")).digest()
    return _ga4gh_format(digest, digest_size)


def _ga4gh_format(digest, digest_size=24):
    tdigest_b64us = base64.urlsafe_b64encode(digest[:digest_size])
    return "ga4gh:SQ.{}".format(tdigest_b64us.decode("utf-8"))


def ga4gh_to_trunc512(vmc):
    base64_strip = vmc.replace("ga4gh:SQ.", "")
    digest = base64.urlsafe_b64decode(base64_strip)
    hex_digest = binascii.hexlify(digest)
    return hex_digest.decode("utf-8")


def trunc512_to_ga4gh(trunc512):
    digest_length = len(trunc512) * 2
    digest = binascii.unhexlify(trunc512)
    return _ga4gh_format(digest, digest_length)



# def trunc512_digest(seq, offset=24) -> str:
#     """Deprecated GA4GH digest function"""
#     digest = hashlib.sha512(seq.encode()).digest()
#     hex_digest = binascii.hexlify(digest[:offset])
#     return hex_digest.decode()



# def sha512t24u_digest_bytes(seq: Union[str, bytes], offset: int = 24) -> str:
#     """GA4GH digest function"""
#     if isinstance(seq, str):
#         seq = seq.encode("utf-8")
#     digest = hashlib.sha512(seq).digest()
#     tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
#     return tdigest_b64us.decode("ascii")

def py_sha512t24u_digest(seq: Union[str, bytes], offset: int = 24) -> str:
    """GA4GH digest function in python"""
    if isinstance(seq, str):
        seq = seq.encode("utf-8")
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")

def md5(seq):
    return hashlib.md5(seq.encode()).hexdigest()

from .const import GTARS_INSTALLED

if GTARS_INSTALLED:
    from gtars.digests import sha512t24u_digest as gtars_sha512t24u_digest
    sha512t24u_digest = gtars_sha512t24u_digest
else:
    def gtars_sha512t24u_digest(seq):
        raise Exception("gtars is not installed")
    
    sha512t24u_digest = py_sha512t24u_digest
