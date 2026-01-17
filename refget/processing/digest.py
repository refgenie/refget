"""Digest functions using gtars (fast Rust implementation)."""
from gtars.refget import (
    sha512t24u_digest,
    md5_digest,
    digest_fasta,
)

__all__ = ["sha512t24u_digest", "md5_digest", "digest_fasta"]
