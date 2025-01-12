import base64
import binascii
import hashlib
import json
import logging
import os

from jsonschema import Draft7Validator
from typing import Optional, Callable, Union
from yacman import load_yaml

from .const import SeqCol, GTARS_INSTALLED
from .exceptions import *
from .models import *

from .hash_functions import sha512t24u_digest
if False:
    from gtars.digests import digest_fasta, sha512t24u_digest

_LOGGER = logging.getLogger(__name__)


def canonical_str(item: dict) -> bytes:
    """Convert a dict into a canonical string representation"""
    return json.dumps(
        item, separators=(",", ":"), ensure_ascii=False, allow_nan=False, sort_keys=True
    ).encode()


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

    if type(seqcol_obj) == SequenceCollection:
        seqcol_obj = seqcol_obj.model_dump()  # can only validate dict

    if not validator.is_valid(seqcol_obj):
        errors = sorted(validator.iter_errors(seqcol_obj), key=lambda e: e.path)
        raise InvalidSeqColError("Validation failed", errors)
    return True


def format_itemwise(csc: SeqCol) -> list:
    """
    Format a SeqCol object into a list of dicts, one per sequence.

    Deprecated! Use SequenceCollection.itemwise()
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
    return list_of_dicts


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


def fasta_file_to_digest(fa_file_path: str, inherent_attrs: list = None) -> str:
    """Given a fasta, return a digest"""
    seqcol_obj = fasta_file_to_seqcol(fa_file_path)
    return seqcol_digest(seqcol_obj, inherent_attrs)


def fasta_file_to_seqcol(
    fasta_file_path: str,
    digest_function: Callable[[bytes], str] = sha512t24u_digest,
) -> dict:
    """
    Convert a FASTA file into a Sequence Collection digest.
    """
    if GTARS_INSTALLED:  # Use gtars if available
        fasta_seq_digests = digest_fasta(fasta_file_path)
        CSC = {"lengths": [], "names": [], "sequences": [], "sorted_name_length_pairs": [], "sorted_sequences": []}
        for s in fasta_seq_digests:
            seq_name = s.id
            seq_length = s.length
            seq_digest = "SQ." + s.sha512t24u
            nlp = {"length": seq_length, "name": seq_name}  # for name_length_pairs
            # snlp_digest = digest_function(canonical_str(nlp)) # for sorted_name_length_pairs
            snlp_digest = canonical_str(nlp) # for sorted_name_length_pairs
            CSC["lengths"].append(seq_length)
            CSC["names"].append(seq_name)
            # CSC["name_length_pairs"].append(nlp)
            CSC["sorted_name_length_pairs"].append(snlp_digest)
            CSC["sequences"].append(seq_digest)
            CSC["sorted_sequences"].append(seq_digest)
        CSC["sorted_name_length_pairs"].sort()
        # csc_digest = seqcol_digest(CSC)
        # dsc = DigestedSequenceCollection(**CSC)
        # dsc.digest = seqcol_digest(CSC)
        return CSC
    else:
        raise ImportError("Install gtars to compute digests from FASTA files.")


def build_sorted_name_length_pairs(
    obj: dict, digest_function: Callable[[str], str] = sha512t24u_digest
):
    """Builds the sorted_name_length_pairs attribute, which corresponds to the coordinate system"""
    sorted_name_length_pairs = []
    print(obj["names"])
    for i in range(len(obj["names"])):
        print(i)
        sorted_name_length_pairs.append({"length": obj["lengths"][i], "name": obj["names"][i]})
    nl_digests = []  # name-length digests
    for i in range(len(sorted_name_length_pairs)):
        nl_digests.append(digest_function(canonical_str(sorted_name_length_pairs[i])))

    nl_digests.sort()
    return nl_digests


def build_name_length_pairs(
    obj: dict, digest_function: Callable[[str], str] = sha512t24u_digest
):
    """Builds the name_length_pairs attribute, which corresponds to the coordinate system"""
    name_length_pairs = []
    for i in range(len(obj["names"])):
        name_length_pairs.append({"length": obj["lengths"][i], "name": obj["names"][i]})
    return name_length_pairs



def compare_seqcols(A: SeqCol, B: SeqCol) -> dict:
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


def seqcol_digest(seqcol_obj: SeqCol, inherent_attrs: list = None) -> str:
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
    if inherent_attrs:
        for k in inherent_attrs:
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


def build_seqcol_model(seqcol_obj: dict, inherent_attrs: list = None) -> SequenceCollection:
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
    if inherent_attrs:
        for k in inherent_attrs:
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

    # Now, build the actual pydantic models
    v = ",".join(seqcol_obj["sequences"])
    sequences_attr = SequencesAttr(digest=seqcol_obj3["sequences"], value=seqcol_obj["sequences"])

    v = ",".join(seqcol_obj["names"])
    names_attr = NamesAttr(digest=seqcol_obj3["names"], value=seqcol_obj["names"])

    v = ",".join([str(x) for x in seqcol_obj["lengths"]])
    lengths_attr = LengthsAttr(digest=sha512t24u_digest(canonical_str(seqcol_obj["lengths"])), value=seqcol_obj["lengths"])

    print(seqcol_obj2)
    nlp = build_name_length_pairs(seqcol_obj)
    nlp_attr = NameLengthPairsAttr(digest=sha512t24u_digest(canonical_str(nlp)), value=nlp)
    _LOGGER.info(f"nlp: {nlp}")
    _LOGGER.info(f"nlp canonical_str: {canonical_str(nlp)}")
    _LOGGER.info(f"Name-length pairs: {nlp_attr}")


    # snlp = build_sorted_name_length_pairs(seqcol_obj)
    # v = ",".join(snlp)
    # snlp_attr = SortedNameLengthPairsAttr(digest=sha512t24u_digest(canonical_str(snlp)), value=snlp)

    from copy import copy
    snlp = [canonical_str(x).decode("utf-8") for x in nlp]
    snlp.sort()
    _LOGGER.info(f"--- SNLP: {snlp}")
    snlp_digest = sha512t24u_digest(canonical_str(snlp))
    _LOGGER.info(f"--- SNLP: {snlp_digest}")
    # snlp_attr = SortedNameLengthPairsAttr(digest=snlp_digest, value=snlp)

    sorted_sequences_value = copy(seqcol_obj["sequences"])
    sorted_sequences_value.sort()
    sorted_sequences_digest = sha512t24u_digest(canonical_str(sorted_sequences_value))
    sorted_sequences_attr = SortedSequencesAttr(digest=sorted_sequences_digest, value=sorted_sequences_value)
    _LOGGER.info(f"sorted_sequences_value: {sorted_sequences_value}")
    _LOGGER.info(f"sorted_sequences_digest: {sorted_sequences_digest}")
    _LOGGER.info(f"sorted_sequences_attr: {sorted_sequences_attr}")

    seqcol = SequenceCollection(
        digest=seqcol_digest,
        sequences=sequences_attr,
        sorted_sequences=sorted_sequences_attr,
        names=names_attr,
        lengths=lengths_attr,
        name_length_pairs=nlp_attr,
        sorted_name_length_pairs_digest=snlp_digest,
    )


    _LOGGER.info(f"seqcol: {seqcol}")

    return seqcol


def build_pangenome_model(pangenome_obj: dict) -> Pangenome:

    # First add in the FASTA files individually, and build a dictionary of the results
    # pangenome_obj = {}
    # for s in prj.samples:
    #     file_path = os.path.join(s.fasta, fasta_root)
    #     f = os.path.join(fa_root, demo_file)
    #     print("Fasta file to be loaded: {}".format(f))
    #     pangenome_obj[s.sample_name] = self.seqcol.add_from_fasta_file(f)

    # Now create a CollectionNamesAttr object
    d = sha512t24u_digest(canonical_str(list(pangenome_obj.keys())))
    v = ",".join(list(pangenome_obj.keys()))
    cna = CollectionNamesAttr(digest=d, value=v)

    # Now create a Collection object
    collections_digest = sha512t24u_digest(
        canonical_str([x.digest for x in pangenome_obj.values()])
    )
    collections_digest

    pg_to_digest = {
        "names": cna.digest,
        "collections": collections_digest,
    }

    pangenome_digest = sha512t24u_digest(canonical_str(pg_to_digest))
    pangenome_digest

    p = Pangenome(
        digest=pangenome_digest,
        names=cna,
        collections=list(pangenome_obj.values()),
        collections_digest=collections_digest,
    )

    return p
