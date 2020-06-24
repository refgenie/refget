# Refget digests from published refget v1.0 protocol
# Retrieved July 2019
# http://samtools.github.io/hts-specs/refget.html

import base64
import hashlib
import binascii

def trunc512_digest(seq, offset=24):
    digest = hashlib.sha512(seq.encode()).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode()

def vmc_digest(seq, digest_size=24):
    # b64 encoding results in 4/3 size expansion of data and padded if
    # not multiple of 3, which doesn't make sense for this use
    assert digest_size % 3 == 0, "digest size must be multiple of 3"
    digest = hashlib.sha512(seq).digest()
    return _vmc_format(digest, digest_size)

def _vmc_format(digest, digest_size=24):
    tdigest_b64us = base64.urlsafe_b64encode(digest[:digest_size])
    return "VMC:GS_{}".format(tdigest_b64us)

def vmc_to_trunc512(vmc):
    base64_strip = vmc.replace("VMC:GS_","")
    digest = base64.urlsafe_b64decode(base64_strip)
    hex_digest = binascii.hexlify(digest)
    return hex_digest

def trunc512_to_vmc(trunc512):
    digest_length = len(trunc512)*2
    digest = binascii.unhexlify(trunc512)
    return _vmc_format(digest, digest_length)

def md5(seq):
    return hashlib.md5(seq.encode()).hexdigest()
