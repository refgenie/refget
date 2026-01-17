"""Bridge functions between gtars types and refget Python types."""
from copy import copy

from gtars.refget import SequenceCollection as GtarsSequenceCollection

from .digest import sha512t24u_digest


def seqcol_from_gtars(gtars_seq_col: GtarsSequenceCollection):
    """
    Convert a gtars SequenceCollection to a refget Python SequenceCollection.

    Args:
        gtars_seq_col: PySequenceCollection object from gtars Rust bindings.

    Returns:
        SequenceCollection: The refget Python SequenceCollection object.
    """
    from ..utilities import canonical_str, build_name_length_pairs
    from ..models import (
        SequenceCollection,
        SequencesAttr,
        NamesAttr,
        LengthsAttr,
        SortedSequencesAttr,
        NameLengthPairsAttr,
    )

    sequences_value = []
    names_value = []
    lengths_value = []

    temp_seqcol_dict = {"names": [], "lengths": [], "sequences": []}

    for record in gtars_seq_col.sequences:
        sequences_value.append("SQ." + record.metadata.sha512t24u)
        names_value.append(record.metadata.name)
        lengths_value.append(record.metadata.length)

        temp_seqcol_dict["names"].append(record.metadata.name)
        temp_seqcol_dict["lengths"].append(record.metadata.length)
        temp_seqcol_dict["sequences"].append(record.metadata.sha512t24u)

    sequences_attr = SequencesAttr(
        digest=gtars_seq_col.lvl1.sequences_digest, value=sequences_value
    )

    names_attr = NamesAttr(digest=gtars_seq_col.lvl1.names_digest, value=names_value)

    lengths_attr = LengthsAttr(
        digest=gtars_seq_col.lvl1.lengths_digest,
        value=lengths_value,
    )

    nlp = build_name_length_pairs(temp_seqcol_dict)
    nlp_attr = NameLengthPairsAttr(digest=sha512t24u_digest(canonical_str(nlp)), value=nlp)

    sorted_sequences_value = copy(sequences_value)
    sorted_sequences_value.sort()
    sorted_sequences_digest = sha512t24u_digest(canonical_str(sorted_sequences_value))
    sorted_sequences_attr = SortedSequencesAttr(
        digest=sorted_sequences_digest, value=sorted_sequences_value
    )

    snlp_digests = []
    for pair in nlp:
        snlp_digests.append(sha512t24u_digest(canonical_str(pair)))
    snlp_digests.sort()
    sorted_name_length_pairs_digest = sha512t24u_digest(canonical_str(snlp_digests))

    seqcol = SequenceCollection(
        digest=gtars_seq_col.digest,
        human_readable_names=[],
        sequences=sequences_attr,
        sorted_sequences=sorted_sequences_attr,
        names=names_attr,
        lengths=lengths_attr,
        name_length_pairs=nlp_attr,
        sorted_name_length_pairs_digest=sorted_name_length_pairs_digest,
    )

    return seqcol


__all__ = ["seqcol_from_gtars"]
