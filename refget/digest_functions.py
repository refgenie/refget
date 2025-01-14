from typing import Union
import hashlib
import binascii
import base64


def trunc512_digest(seq, offset=24) -> str:
    """Deprecated GA4GH digest function"""
    digest = hashlib.sha512(seq.encode()).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode()


def sha512t24u_digest(seq: Union[str, bytes], offset: int = 24) -> str:
    """GA4GH digest function"""
    if isinstance(seq, str):
        seq = seq.encode("utf-8")
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")


def sha512t24u_digest_bytes(seq: Union[str, bytes], offset: int = 24) -> str:
    """GA4GH digest function"""
    if isinstance(seq, str):
        seq = seq.encode("utf-8")
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")
