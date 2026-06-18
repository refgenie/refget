#!/usr/bin/env python3
"""Compute seqcol coordinate system digests from BAM and VCF file headers.

Extracts sequence names and lengths from BAM @SQ headers or VCF ##contig
headers and computes two GA4GH Sequence Collections (seqcol) attribute digests:

  - name_length_pairs (NLP) digest: ordered coordinate system identity.
  - sorted_name_length_pairs (SNLP) digest: order-invariant coordinate system
    identity, useful for determining if two files share the same reference
    coordinate space regardless of contig ordering.

These are standard seqcol attribute-level digests computable from existing
file headers without access to the underlying sequences. They answer the
question "can these files be analyzed together?" without modifying any
file formats.

Usage:
    python seqcol_from_header.py input.bam
    python seqcol_from_header.py input.vcf.gz
    python seqcol_from_header.py input.cram

Multiple files can be provided to compare their coordinate systems:
    python seqcol_from_header.py file1.bam file2.vcf.gz

Requirements:
    pip install pysam refget
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pysam

from refget.digests import sha512t24u_digest
from refget.utils import (
    build_name_length_pairs,
    build_sorted_name_length_pairs,
    canonical_str,
)

# ---------------------------------------------------------------------------
# Extraction from file headers
# ---------------------------------------------------------------------------


def extract_from_bam(bam_path: str | Path) -> tuple[list[str], list[int]]:
    """Extract sequence names and lengths from a BAM/CRAM file header.

    Reads the @SQ lines from the BAM header. Each @SQ line provides a
    sequence name (SN) and length (LN).

    Args:
        bam_path: Path to a BAM or CRAM file (index not required for
            header-only access).

    Returns:
        Tuple of (names, lengths) lists.
    """
    save = pysam.set_verbosity(0)  # suppress index warnings for header-only access
    try:
        with pysam.AlignmentFile(str(bam_path), check_sq=False) as af:
            sq_lines = af.header.to_dict().get("SQ", [])
    finally:
        pysam.set_verbosity(save)

    names = [sq["SN"] for sq in sq_lines]
    lengths = [sq["LN"] for sq in sq_lines]
    return names, lengths


def extract_from_vcf(vcf_path: str | Path) -> tuple[list[str], list[int]]:
    """Extract sequence names and lengths from a VCF/BCF file header.

    Reads ##contig=<ID=...,length=...> lines from the VCF header.

    Args:
        vcf_path: Path to a VCF, VCF.GZ, or BCF file.

    Returns:
        Tuple of (names, lengths) lists.

    Raises:
        ValueError: If any contig header is missing a length field.
    """
    vcf = pysam.VariantFile(str(vcf_path))
    names = []
    lengths = []
    for contig in vcf.header.contigs.values():
        if contig.length is None:
            raise ValueError(
                f"VCF contig '{contig.name}' has no length defined in the header. "
                "All ##contig lines must include a length= field."
            )
        names.append(contig.name)
        lengths.append(contig.length)
    vcf.close()
    return names, lengths


def extract_names_lengths(file_path: str | Path) -> tuple[list[str], list[int]]:
    """Auto-detect file type and extract names/lengths from the header.

    Supports BAM, CRAM, VCF, VCF.GZ, and BCF files.

    Args:
        file_path: Path to the input file.

    Returns:
        Tuple of (names, lengths) lists.

    Raises:
        ValueError: If the file type cannot be determined.
    """
    path = Path(file_path)
    suffixes = "".join(path.suffixes).lower()

    if suffixes.endswith((".bam", ".cram", ".sam")):
        return extract_from_bam(path)
    elif suffixes.endswith((".vcf", ".vcf.gz", ".vcf.bgz", ".bcf")):
        return extract_from_vcf(path)
    else:
        raise ValueError(
            f"Unrecognized file extension '{suffixes}' for {path.name}. "
            "Supported: .bam, .cram, .sam, .vcf, .vcf.gz, .bcf"
        )


# ---------------------------------------------------------------------------
# Digest computation
# ---------------------------------------------------------------------------


def compute_nlp_digest(names: list[str], lengths: list[int]) -> str:
    """Compute the name_length_pairs (NLP) attribute-level digest.

    The NLP attribute's level 2 representation is an array of objects like
    ``[{"length": 248956422, "name": "chr1"}, ...]``. The level 1 digest
    is computed by canonicalizing this entire array (RFC-8785) and applying
    the GA4GH sha512t24u digest -- i.e., the standard seqcol attribute
    encoding.

    This captures the *ordered* coordinate system.

    Args:
        names: Sequence/contig names.
        lengths: Corresponding sequence lengths.

    Returns:
        The NLP digest string (sha512t24u, 32 characters).
    """
    obj = {"names": names, "lengths": lengths}
    nlp = build_name_length_pairs(obj)
    return sha512t24u_digest(canonical_str(nlp))


def compute_snlp_digest(names: list[str], lengths: list[int]) -> str:
    """Compute the sorted_name_length_pairs (SNLP) attribute-level digest.

    Same as NLP, but the array of individual pair digests is sorted
    lexicographically before the array-level digest. This makes the digest
    invariant to contig ordering.

    Args:
        names: Sequence/contig names.
        lengths: Corresponding sequence lengths.

    Returns:
        The SNLP digest string (sha512t24u, 32 characters).
    """
    obj = {"names": names, "lengths": lengths}
    # build_sorted_name_length_pairs already returns sorted individual digests
    snlp_digests = build_sorted_name_length_pairs(obj)
    return sha512t24u_digest(canonical_str(snlp_digests))


def compute_all_digests(names: list[str], lengths: list[int]) -> dict[str, str]:
    """Compute NLP and SNLP digests from names and lengths.

    Returns:
        Dictionary with keys: name_length_pairs, sorted_name_length_pairs,
        and num_sequences.
    """
    return {
        "name_length_pairs": compute_nlp_digest(names, lengths),
        "sorted_name_length_pairs": compute_snlp_digest(names, lengths),
        "num_sequences": len(names),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def format_output(file_path: str, digests: dict, output_format: str = "text") -> str:
    """Format digest results for display."""
    if output_format == "json":
        return json.dumps({"file": file_path, **digests}, indent=2)

    lines = [
        f"File: {file_path}",
        f"  Sequences:                    {digests['num_sequences']}",
        f"  name_length_pairs (NLP):      {digests['name_length_pairs']}",
        f"  sorted_name_length_pairs:     {digests['sorted_name_length_pairs']}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute seqcol coordinate system digests from BAM/VCF headers.",
        epilog=(
            "NLP (name_length_pairs) captures the ordered coordinate system. "
            "SNLP (sorted_name_length_pairs) is order-invariant. "
            "Two files with the same SNLP can be analyzed together."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="BAM, CRAM, VCF, VCF.GZ, or BCF file(s)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    args = parser.parse_args(argv)

    results = []
    errors = 0

    for file_path in args.files:
        try:
            names, lengths = extract_names_lengths(file_path)
        except (ValueError, OSError, Exception) as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            errors += 1
            continue

        if not names:
            print(
                f"Warning: {file_path} has no sequence/contig entries in header.", file=sys.stderr
            )
            errors += 1
            continue

        digests = compute_all_digests(names, lengths)
        results.append({"file": file_path, "digests": digests})

    if args.json:
        if len(results) == 1:
            print(json.dumps({"file": results[0]["file"], **results[0]["digests"]}, indent=2))
        else:
            out = [{"file": r["file"], **r["digests"]} for r in results]
            print(json.dumps(out, indent=2))
    else:
        for i, r in enumerate(results):
            if i > 0:
                print()
            print(format_output(r["file"], r["digests"]))

    if len(results) > 1:
        nlp_values = {r["digests"]["name_length_pairs"] for r in results}
        snlp_values = {r["digests"]["sorted_name_length_pairs"] for r in results}

        print()
        if len(nlp_values) == 1:
            print(
                "All files share the SAME coordinate system (identical names, lengths, and order)."
            )
        elif len(snlp_values) == 1:
            print(
                "Files have the same coordinate system but DIFFERENT contig ordering "
                "(sorted_name_length_pairs match, but name_length_pairs differ)."
            )
        else:
            print("Files have DIFFERENT coordinate systems.")

    return 1 if errors and not results else 0


if __name__ == "__main__":
    sys.exit(main())
