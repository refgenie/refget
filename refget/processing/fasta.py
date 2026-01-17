"""FASTA processing functions using gtars."""
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from gtars.refget import digest_fasta

from .digest import sha512t24u_digest


def fasta_to_seqcol_dict(fasta_file_path: str | Path) -> dict:
    """
    Convert a FASTA file into a Sequence Collection dict.

    Args:
        fasta_file_path: Path to the FASTA file

    Returns:
        dict: A canonical sequence collection dictionary
    """
    from ..utilities import canonical_str  # Pure Python, stays in utilities

    fasta_seq_digests = digest_fasta(fasta_file_path)
    seqcol_dict = {
        "lengths": [],
        "names": [],
        "sequences": [],
        "sorted_name_length_pairs": [],
        "sorted_sequences": [],
    }
    for s in fasta_seq_digests.sequences:
        seq_name = s.metadata.name
        seq_length = s.metadata.length
        seq_digest = "SQ." + s.metadata.sha512t24u
        nlp = {"length": seq_length, "name": seq_name}
        snlp_digest = sha512t24u_digest(canonical_str(nlp))
        seqcol_dict["lengths"].append(seq_length)
        seqcol_dict["names"].append(seq_name)
        seqcol_dict["sorted_name_length_pairs"].append(snlp_digest)
        seqcol_dict["sequences"].append(seq_digest)
        seqcol_dict["sorted_sequences"].append(seq_digest)
    seqcol_dict["sorted_name_length_pairs"].sort()
    return seqcol_dict


def fasta_to_digest(
    fasta_file_path: str | Path, inherent_attrs: Optional[list] = None
) -> str:
    """
    Given a FASTA file path, return its seqcol digest.

    Args:
        fasta_file_path: Path to the FASTA file
        inherent_attrs: Attributes to include in the digest

    Returns:
        str: The top-level digest for this sequence collection
    """
    from ..utilities import seqcol_digest  # Pure Python, stays in utilities
    from ..const import DEFAULT_INHERENT_ATTRS

    if inherent_attrs is None:
        inherent_attrs = DEFAULT_INHERENT_ATTRS
    seqcol_obj = fasta_to_seqcol_dict(fasta_file_path)
    return seqcol_digest(seqcol_obj, inherent_attrs)


def create_fasta_drs_object(fasta_file: str, digest: str = None):
    """
    Create a FastaDrsObject from a FASTA file.

    Args:
        fasta_file: Path to a FASTA file
        digest: The refget digest of the sequence collection (optional).
                If not included, it will be computed.

    Returns:
        FastaDrsObject: The FastaDrsObject object
    """
    from ..models import FastaDrsObject, Checksum

    file_size = os.path.getsize(fasta_file)

    # Compute file checksums (SHA-256, MD5)
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    with open(fasta_file, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
            md5.update(block)
    sha256_checksum_val = sha256.hexdigest()
    md5_checksum_val = md5.hexdigest()

    # Use digest_fasta to get both seqcol digest and FAI data in a single pass
    seqcol = digest_fasta(fasta_file)

    offsets = []
    line_bases = None
    extra_line_bytes = None

    for seq_record in seqcol.sequences:
        fai = seq_record.metadata.fai
        if fai:  # None for gzipped files
            offsets.append(fai.offset)
            # Use values from first sequence (assumes consistent wrapping)
            if line_bases is None:
                line_bases = fai.line_bases
                extra_line_bytes = fai.line_bytes - fai.line_bases

    now = datetime.now(timezone.utc)

    # Use provided digest or the one computed by digest_fasta
    if digest is None:
        digest = seqcol.digest

    return FastaDrsObject(
        id=digest,
        name=os.path.basename(fasta_file),
        self_uri=None,  # Will be populated by to_response() when serving via API
        size=file_size,
        created_time=now,
        updated_time=now,
        version="1.0",
        mime_type="application/fasta",
        checksums=[
            Checksum(type="sha-256", checksum=sha256_checksum_val),
            Checksum(type="refget.seqcol", checksum=digest),
            Checksum(type="md5", checksum=md5_checksum_val),
        ],
        access_methods=[],
        description=f"DRS object for {os.path.basename(fasta_file)}",
        aliases=[os.path.basename(fasta_file).split(".")[0]],
        line_bases=line_bases,
        extra_line_bytes=extra_line_bytes,
        offsets=offsets if offsets else None,
    )


__all__ = ["fasta_to_seqcol_dict", "fasta_to_digest", "create_fasta_drs_object"]
