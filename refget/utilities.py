import json
import logging
import os

from jsonschema import Draft7Validator
from pathlib import Path
from typing import Optional
from yacman import load_yaml

from .const import SeqColDict
from .exceptions import *
from .digest_functions import sha512t24u_digest, fasta_to_seq_digests, DigestFunction

_LOGGER = logging.getLogger(__name__)


def canonical_str(item: dict) -> bytes:
    """Convert a dict into a canonical string representation"""
    return json.dumps(
        item, separators=(",", ":"), ensure_ascii=False, allow_nan=False, sort_keys=True
    ).encode()


def print_csc(csc: dict) -> str:
    """Convenience function to pretty-print a canonical sequence collection"""
    return print(json.dumps(csc, indent=2))


def validate_seqcol_bool(seqcol_obj: SeqColDict, schema=None) -> bool:
    """
    Validate a seqcol object against the seqcol schema. Returns True if valid, False if not.

    To enumerate the errors, use validate_seqcol instead.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "seqcol.yaml")
    schema = load_yaml(schema_path)
    validator = Draft7Validator(schema)
    return validator.is_valid(seqcol_obj)


def validate_seqcol(seqcol_obj: SeqColDict, schema=None) -> bool:
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


def chrom_sizes_to_snlp_digest(
    chrom_sizes_file_path: str,
    digest_function: DigestFunction = sha512t24u_digest,
) -> dict:
    """
    Given a chrom.sizes file, return a level 1 digest for the
    sorted_name_length_pairs attribute
    """
    with open(chrom_sizes_file_path, "r") as f:
        lines = f.readlines()
    seqcol_obj: dict[str, list] = {"lengths": [], "names": []}

    for line in lines:
        line = line.strip()
        if line == "":
            continue
        seq_name, seq_length, ga4gh_digest, _ = line.split("\t")
        seqcol_obj["lengths"].append(int(seq_length))
        seqcol_obj["names"].append(seq_name)

    return seqcol_to_snlp_digest(seqcol_obj)


def seqcol_to_snlp_digest(seqcol_obj: SeqColDict) -> str:
    """
    Generate a sorted_name_length_pair attribute digest for a sequence collection object
    """

    name_length_pairs = build_name_length_pairs(seqcol_obj)
    nlp_strings = [canonical_str(x).decode("utf-8") for x in name_length_pairs]
    nlp_strings.sort()
    snlp_digest = sha512t24u_digest(canonical_str(nlp_strings))
    return snlp_digest


def fasta_to_digest(
    fa_file_path: str | Path, inherent_attrs: Optional[list] = ["names", "sequences"]
) -> str:
    """
    Given a fasta file path, return a digest

    Args:
        fa_file_path (str | Path): Path to the fasta file
        inherent_attrs (Optional[list], optional): Attributes to include in the digest.

    Returns:
        (str): The top-level digest for this sequence collection
    """
    seqcol_obj = fasta_to_seqcol_dict(fa_file_path)
    return seqcol_digest(seqcol_obj, inherent_attrs)


def fasta_to_seqcol_dict(
    fasta_file_path: str,
    digest_function: DigestFunction = sha512t24u_digest,
) -> SeqColDict:
    """
    Convert a FASTA file into a Sequence Collection object.

    Args:
        fasta_file_path (str): Path to the FASTA file
        digest_function (DigestFunction, optional): Digest function to use. Defaults to sha512t24u_digest.

    Returns:
        (dict): A canonical sequence collection object
    """

    fasta_seq_digests = fasta_to_seq_digests(fasta_file_path)
    seqcol_dict = {
        "lengths": [],
        "names": [],
        "sequences": [],
        "sorted_name_length_pairs": [],
        "sorted_sequences": [],
    }
    for s in fasta_seq_digests:
        seq_name = s.id
        seq_length = s.length
        seq_digest = "SQ." + s.sha512t24u
        nlp = {"length": seq_length, "name": seq_name}  # for name_length_pairs
        # snlp_digest = digest_function(canonical_str(nlp)) # for sorted_name_length_pairs
        snlp_digest = canonical_str(nlp)  # for sorted_name_length_pairs
        seqcol_dict["lengths"].append(seq_length)
        seqcol_dict["names"].append(seq_name)
        # seqcol_dict["name_length_pairs"].append(nlp)
        seqcol_dict["sorted_name_length_pairs"].append(snlp_digest)
        seqcol_dict["sequences"].append(seq_digest)
        seqcol_dict["sorted_sequences"].append(seq_digest)
    seqcol_dict["sorted_name_length_pairs"].sort()
    # seqcol_dict_digest = seqcol_digest(seqcol_dict)
    # dsc = DigestedSequenceCollection(**seqcol_dict)
    # dsc.digest = seqcol_digest(seqcol_dict)
    return seqcol_dict


def build_sorted_name_length_pairs(obj: dict, digest_function: DigestFunction = sha512t24u_digest):
    """Builds the sorted_name_length_pairs attribute, which corresponds to the coordinate system"""
    sorted_name_length_pairs = []
    for i in range(len(obj["names"])):
        sorted_name_length_pairs.append({"length": obj["lengths"][i], "name": obj["names"][i]})
    snlp_digests = []  # name-length digests
    for i in range(len(sorted_name_length_pairs)):
        snlp_digests.append(digest_function(canonical_str(sorted_name_length_pairs[i])))

    snlp_digests.sort()
    return snlp_digests


def build_name_length_pairs(obj: dict, digest_function: DigestFunction = sha512t24u_digest):
    """Builds the name_length_pairs attribute, which corresponds to the coordinate system"""
    name_length_pairs = []
    for i in range(len(obj["names"])):
        name_length_pairs.append({"length": obj["lengths"][i], "name": obj["names"][i]})
    return name_length_pairs


def compare_seqcols(A: SeqColDict, B: SeqColDict) -> dict:
    """
    Workhorse comparison function

    @param A Sequence collection A
    @param B Sequence collection B
    @return dict Following formal seqcol specification comparison function return value
    """
    # validate_seqcol(A)  # First ensure these are the right structure
    # validate_seqcol(B)
    a_keys = list(A.keys())
    b_keys = list(B.keys())
    a_keys.sort()
    b_keys.sort()

    all_keys = a_keys + list(set(b_keys) - set(a_keys))
    all_keys.sort()
    result = {}

    # Compute lengths of each array; only do this for array attributes
    a_lengths = {}
    b_lengths = {}
    for k in a_keys:
        a_lengths[k] = len(A[k])
    for k in b_keys:
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
        _LOGGER.debug(k)
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


def _compare_elements(A: list, B: list) -> dict:
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


def seqcol_dict_to_level1_dict(
    seqcol_dict: SeqColDict, inherent_attrs: Optional[list] = ["names", "sequences"]
) -> dict:
    """
    Convert a sequence collection dictionary to a level 1 dictionary
    """
    # Step 1a: Remove any non-inherent attributes,
    # so that only the inherent attributes contribute to the digest.
    filt_canonical_strs = {}
    if inherent_attrs:
        for k in inherent_attrs:
            # Step 2: Apply RFC-8785 to canonicalize the value
            # associated with each attribute individually.
            filt_canonical_strs[k] = canonical_str(seqcol_dict[k])
    else:  # no schema provided, so assume all attributes are inherent
        for k in seqcol_dict:
            filt_canonical_strs[k] = canonical_str(seqcol_dict[k])

    # Step 3: Digest each canonicalized attribute value
    # using the GA4GH digest algorithm.
    level1_dict = {}
    for attribute in filt_canonical_strs:
        level1_dict[attribute] = sha512t24u_digest(filt_canonical_strs[attribute])

    return level1_dict


def level1_dict_to_seqcol_digest(level1_dict: dict):
    # Step 4: Apply RFC-8785 again to canonicalize the JSON
    # of new seqcol object representation.
    level1_can_str = canonical_str(level1_dict)

    # Step 5: Digest the final canonical representation again.
    seqcol_digest = sha512t24u_digest(level1_can_str)
    return seqcol_digest


def seqcol_digest(
    seqcol_dict: SeqColDict, inherent_attrs: Optional[list] = ["names", "sequences"]
) -> str:
    """
    Given a canonical sequence collection, compute its digest.

    :param dict seqcol_dict: Dictionary representation of a canonical sequence collection object
    :param dict schema: Schema defining the inherent attributes to digest
    :return str: The sequence collection digest
    """

    validate_seqcol(seqcol_dict)
    level1_dict = seqcol_dict_to_level1_dict(seqcol_dict, inherent_attrs)
    seqcol_digest = level1_dict_to_seqcol_digest(level1_dict)
    return seqcol_digest


def build_pangenome_model():
    raise NotImplementedError


# def build_pangenome_model(pangenome_obj: dict) -> Pangenome:
#     # First add in the FASTA files individually, and build a dictionary of the results
#     # pangenome_obj = {}
#     # for s in prj.samples:
#     #     file_path = os.path.join(s.fasta, fasta_root)
#     #     f = os.path.join(fa_root, demo_file)
#     #     print("Fasta file to be loaded: {}".format(f))
#     #     pangenome_obj[s.sample_name] = self.seqcol.add_from_fasta_file(f)

#     # Now create a CollectionNamesAttr object
#     d = sha512t24u_digest(canonical_str(list(pangenome_obj.keys())))
#     v = ",".join(list(pangenome_obj.keys()))
#     cna = CollectionNamesAttr(digest=d, value=v)

#     # Now create a Collection object
#     collections_digest = sha512t24u_digest(
#         canonical_str([x.digest for x in pangenome_obj.values()])
#     )
#     collections_digest

#     pg_to_digest = {
#         "names": cna.digest,
#         "collections": collections_digest,
#     }

#     pangenome_digest = sha512t24u_digest(canonical_str(pg_to_digest))
#     pangenome_digest

#     p = Pangenome(
#         digest=pangenome_digest,
#         names=cna,
#         collections=list(pangenome_obj.values()),
#         collections_digest=collections_digest,
#     )

#     return p
