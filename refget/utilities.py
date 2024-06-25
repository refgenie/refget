import base64
import binascii
import hashlib
import json
import logging
import os

from jsonschema import Draft7Validator
from typing import Optional, Callable, Union
from yacman import load_yaml

from .const import SeqCol
from .exceptions import *
from .models import *

_LOGGER = logging.getLogger(__name__)

try:
    from gc_count import checksum
    pyfaidx = None
    GC_COUNT_INSTALLED = True
except ImportError:
    GC_COUNT_INSTALLED = False
    _LOGGER.error("gc_count not installed")

try:
    import pyfaidx
    PYFAIDX_INSTALLED = True
    from .utilities_pyfaidx import *
except ImportError:
    _LOGGER.error("pyfaidx not installed")
    PYFAIDX_INSTALLED = False


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


def sha512t24u_digest_bytes(seq: bytes, offset: int = 24) -> str:
    """GA4GH digest function"""
    digest = hashlib.sha512(seq).digest()
    tdigest_b64us = base64.urlsafe_b64encode(digest[:offset])
    return tdigest_b64us.decode("ascii")


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
    digest_function: Callable[[bytes], str] = sha512t24u_digest_bytes,
) -> dict:
    """
    Convert a FASTA file into a Sequence Collection digest.
    """
    if GC_COUNT_INSTALLED: # Use gc_count if available
        fasta_seq_digests = checksum(fasta_file_path)
        CSC = {"lengths": [], "names": [], "sequences": [], "sorted_name_length_pairs": []}
        for s in fasta_seq_digests:
            seq_name = s.id
            seq_length = s.length
            seq_digest = "SQ." + s.sha512
            snlp = {"length": seq_length, "name": seq_name}  # sorted_name_length_pairs
            snlp_digest = digest_function(canonical_str(snlp))
            CSC["lengths"].append(seq_length)
            CSC["names"].append(seq_name)
            CSC["sorted_name_length_pairs"].append(snlp_digest)
            CSC["sequences"].append(seq_digest)
        CSC["sorted_name_length_pairs"].sort()
        # csc_digest = seqcol_digest(CSC)
        # dsc = DigestedSequenceCollection(**CSC)
        # dsc.digest = seqcol_digest(CSC)
        return CSC
    

    elif PYFAIDX_INSTALLED: # Use pyfaidx if available
        fa_obj = parse_fasta(fasta_file_path)
        return fasta_obj_to_seqcol(fa_obj, digest_function=digest_function)
    else:
        raise ImportError("Neither gc_count nor pyfaidx is installed")



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

    v = ",".join(seqcol_obj["sequences"])
    sequences_attr = SequencesAttr(
        digest = seqcol_obj3["sequences"],
        value = v
    )
    
    v = ",".join(seqcol_obj["names"])
    names_attr = NamesAttr(
        digest = seqcol_obj3["names"],
        value = v
    )

    v = ",".join([str(x) for x in seqcol_obj["lengths"]])
    lengths_attr = LengthsAttr(
        digest = seqcol_obj3["lengths"],
        value = v
    )
    print(seqcol_obj2)
    snlp = build_sorted_name_length_pairs(seqcol_obj)
    v =  ",".join(snlp)
    snlp_attr = SortedNameLengthPairsAttr(
        digest = sha512t24u_digest(canonical_str(snlp)),
        value = v
    )

    

    seqcol = SequenceCollection(digest=seqcol_digest,
                            sequences=sequences_attr, 
                            names=names_attr, 
                            lengths=lengths_attr,
                            sorted_name_length_pairs=snlp_attr)


    return seqcol
