import base64
import binascii
import hashlib
import json
import logging
import os
import pyfaidx

from jsonschema import Draft7Validator
from typing import Optional, Callable
from yacman import load_yaml

from .const import SeqCol
from .exceptions import *

_LOGGER = logging.getLogger(__name__)


def trunc512_digest(seq, offset=24) -> str:
    """Deprecated GA4GH digest function"""
    digest = hashlib.sha512(seq.encode()).digest()
    hex_digest = binascii.hexlify(digest[:offset])
    return hex_digest.decode()


def sha512t24u_digest(seq: str, offset: int = 24) -> str:
    """GA4GH digest function"""
    digest = hashlib.sha512(seq.encode()).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")


def canonical_str(item: dict) -> str:
    """Convert a dict into a canonical string representation"""
    return json.dumps(
        item, separators=(",", ":"), ensure_ascii=False, allow_nan=False, sort_keys=True
    )


def print_csc(csc: dict) -> str:
    """Convenience function to pretty-print a canonical sequence collection"""
    return print(json.dumps(csc, indent=2))


def validate_seqcol_bool(seqcol_obj: SeqCol, schema=None) -> bool:
    """
    Validate a seqcol object against the seqcol schema. Returns True if valid, False if not.

    To enumerate the errors, use validate_seqcol instead.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "seqcol.yaml")
    schema = load_yaml(schema_path)
    validator = Draft7Validator(schema)
    return validator.is_valid(seqcol_obj)


def validate_seqcol(seqcol_obj: SeqCol, schema=None) -> Optional[dict]:
    """Validate a seqcol object against the seqcol schema.
    Returns True if valid, raises InvalidSeqColError if not, which enumerates the errors.
    Retrieve individual errors with exception.errors
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "seqcol.yaml")
    schema = load_yaml(schema_path)
    validator = Draft7Validator(schema)
    if not validator.is_valid(seqcol_obj):
        errors = sorted(validator.iter_errors(seqcol_obj), key=lambda e: e.path)
        raise InvalidSeqColError("Validation failed", errors)
    return True


def format_itemwise(csc: SeqCol) -> list:
    """
    Format a SeqCol object into a list of dicts, one per sequence.
    """
    list_of_dicts = []
    # TODO: handle all properties, not just these 3
    # TODO: handle non-collated attributes, somehow
    for i in range(len(csc["lengths"])):
        list_of_dicts.append(
            {
                "name": csc["names"][i],
                "length": csc["lengths"][i],
                "sequence": csc["sequences"][i],
            }
        )
    return {"sequences": list_of_dicts}


def parse_fasta(fa_file) -> pyfaidx.Fasta:
    """
    Read in a gzipped or not gzipped FASTA file
    """
    try:
        return pyfaidx.Fasta(fa_file)
    except pyfaidx.UnsupportedCompressionFormat:
        # pyfaidx can handle bgzip but not gzip; so we just hack it here and
        # gunzip the file into a temporary one and read it in not to interfere
        # with the original one.
        from gzip import open as gzopen
        from tempfile import NamedTemporaryFile

        with gzopen(fa_file, "rt") as f_in, NamedTemporaryFile(mode="w+t", suffix=".fa") as f_out:
            f_out.writelines(f_in.read())
            f_out.seek(0)
            return pyfaidx.Fasta(f_out.name)


def chrom_sizes_to_digest(chrom_sizes_file_path: str) -> str:
    """Given a chrom.sizes file, return a digest"""
    seqcol_obj = chrom_sizes_to_seqcol(chrom_sizes_file_path)
    return seqcol_digest(seqcol_obj)


def chrom_sizes_to_seqcol(
    chrom_sizes_file_path: str,
    digest_function: Callable[[str], str] = sha512t24u_digest,
) -> dict:
    """Given a chrom.sizes file, return a canonical seqcol object"""
    with open(chrom_sizes_file_path, "r") as f:
        lines = f.readlines()
    CSC = {"lengths": [], "names": [], "sequences": [], "sorted_name_length_pairs": []}
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        seq_name, seq_length, ga4gh_digest, md5_digest = line.split("\t")
        snlp = {"length": seq_length, "name": seq_name}  # sorted_name_length_pairs
        snlp_digest = digest_function(canonical_str(snlp))
        CSC["lengths"].append(int(seq_length))
        CSC["names"].append(seq_name)
        CSC["sequences"].append(ga4gh_digest)
        CSC["sorted_name_length_pairs"].append(snlp_digest)
    CSC["sorted_name_length_pairs"].sort()
    return CSC


def fasta_file_to_digest(fa_file_path: str) -> str:
    """Given a fasta, return a digest"""
    seqcol_obj = fasta_file_to_seqcol(fa_file_path)
    return seqcol_digest(seqcol_obj)


def fasta_file_to_seqcol(fa_file_path: str) -> dict:
    """Given a fasta, return a canonical seqcol object"""
    fa_obj = parse_fasta(fa_file_path)
    return fasta_obj_to_seqcol(fa_obj)


def fasta_obj_to_seqcol(
    fa_object: pyfaidx.Fasta,
    verbose: bool = True,
    digest_function: Callable[[str], str] = sha512t24u_digest,
) -> dict:
    """
    Given a fasta object, return a CSC (Canonical Sequence Collection object)
    """
    # CSC = SeqColArraySet
    # Or equivalently, a "Level 1 SeqCol"

    CSC = {"lengths": [], "names": [], "sequences": [], "sorted_name_length_pairs": []}
    seqs = fa_object.keys()
    nseqs = len(seqs)
    print(f"Found {nseqs} chromosomes")
    i = 1
    for k in fa_object.keys():
        if verbose:
            print(f"Processing ({i} of {nseqs}) {k}...")
        seq = str(fa_object[k])
        seq_length = len(seq)
        seq_name = fa_object[k].name
        seq_digest = "SQ." + digest_function(seq.upper())
        snlp = {"length": seq_length, "name": seq_name}  # sorted_name_length_pairs
        snlp_digest = digest_function(canonical_str(snlp))
        CSC["lengths"].append(seq_length)
        CSC["names"].append(seq_name)
        CSC["sorted_name_length_pairs"].append(snlp_digest)
        CSC["sequences"].append(seq_digest)
        i += 1
    CSC["sorted_name_length_pairs"].sort()
    return CSC


def build_sorted_name_length_pairs(obj: dict, digest_function):
    """Builds the sorted_name_length_pairs attribute, which corresponds to the coordinate system"""
    sorted_name_length_pairs = []
    for i in range(len(obj["names"])):
        sorted_name_length_pairs.append({"length": obj["lengths"][i], "name": obj["names"][i]})
    nl_digests = []  # name-length digests
    for i in range(len(sorted_name_length_pairs)):
        nl_digests.append(digest_function(canonical_str(sorted_name_length_pairs[i])))

    nl_digests.sort()
    return nl_digests


def compare_seqcols(A: SeqCol, B: SeqCol):
    """
    Workhorse comparison function

    @param A Sequence collection A
    @param B Sequence collection B
    @return dict Following formal seqcol specification comparison function return value
    """
    validate_seqcol(A)  # First ensure these are the right structure
    validate_seqcol(B)

    all_keys = list(A.keys()) + list(set(B.keys()) - set(list(A.keys())))
    result = {}

    # Compute lengths of each array; only do this for array attributes
    a_lengths = {}
    b_lengths = {}
    for k in A.keys():
        a_lengths[k] = len(A[k])
    for k in B.keys():
        b_lengths[k] = len(B[k])

    return_obj = {
        "attributes": {"a_only": [], "b_only": [], "a_and_b": []},
        "array_elements": {
            "a": a_lengths,
            "b": b_lengths,
            "a_and_b": {},
            "a_and_b_same_order": {},
        },
    }

    for k in all_keys:
        _LOGGER.info(k)
        if k not in A:
            result[k] = {"flag": -1}
            return_obj["attributes"]["b_only"].append(k)
            # return_obj["array_elements"]["total"][k] = {"a": None, "b": len(B[k])}
        elif k not in B:
            return_obj["attributes"]["a_only"].append(k)
            # return_obj["array_elements"]["total"][k] = {"a": len(A[k]), "b": None}
        else:
            return_obj["attributes"]["a_and_b"].append(k)
            res = _compare_elements(A[k], B[k])
            # return_obj["array_elements"]["total"][k] = {"a": len(A[k]), "b": len(B[k])}
            return_obj["array_elements"]["a_and_b"][k] = res["a_and_b"]
            return_obj["array_elements"]["a_and_b_same_order"][k] = res["a_and_b_same_order"]
    return return_obj


def _compare_elements(A: list, B: list):
    """
    Compare elements between two arrays. Helper function for individual elements used by workhorse compare_seqcols function
    """

    A_filtered = list(filter(lambda x: x in B, A))
    B_filtered = list(filter(lambda x: x in A, B))
    A_count = len(A_filtered)
    B_count = len(B_filtered)
    overlap = min(len(A_filtered), len(B_filtered))  # counts duplicates

    if A_count + B_count < 1:
        # order match requires at least 2 matching elements
        order = None
    elif not (A_count == B_count == overlap):
        # duplicated matches means order match is undefined
        order = None
    else:
        order = A_filtered == B_filtered
    return {"a_and_b": overlap, "a_and_b_same_order": order}


def seqcol_digest(seqcol_obj: SeqCol, schema: dict = None) -> str:
    """
    Given a canonical sequence collection, compute its digest.

    :param dict seqcol_obj: Dictionary representation of a canonical sequence collection object
    :param dict schema: Schema defining the inherent attributes to digest
    :return str: The sequence collection digest
    """

    validate_seqcol(seqcol_obj)
    # Step 1a: Remove any non-inherent attributes,
    # so that only the inherent attributes contribute to the digest.
    seqcol_obj2 = {}
    if schema:
        for k in schema["inherent"]:
            # Step 2: Apply RFC-8785 to canonicalize the value
            # associated with each attribute individually.
            seqcol_obj2[k] = canonical_str(seqcol_obj[k])
    else:  # no schema provided, so assume all attributes are inherent
        for k in seqcol_obj:
            seqcol_obj2[k] = canonical_str(seqcol_obj[k])
    # Step 3: Digest each canonicalized attribute value
    # using the GA4GH digest algorithm.

    seqcol_obj3 = {}
    for attribute in seqcol_obj2:
        seqcol_obj3[attribute] = sha512t24u_digest(seqcol_obj2[attribute])
    # print(json.dumps(seqcol_obj3, indent=2))  # visualize the result

    # Step 4: Apply RFC-8785 again to canonicalize the JSON
    # of new seqcol object representation.

    seqcol_obj4 = canonical_str(seqcol_obj3)

    # Step 5: Digest the final canonical representation again.
    seqcol_digest = sha512t24u_digest(seqcol_obj4)
    return seqcol_digest


def explain_flag(flag):
    """Explains a compare flag"""
    print(f"Flag: {flag}\nBinary: {bin(flag)}\n")
    for e in range(0, 13):
        if flag & 2**e:
            print(FLAGS[2**e])
