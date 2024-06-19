from .utilities import sha512t24u_digest_bytes 


def fasta_obj_to_seqcol(
    fa_object: pyfaidx.Fasta,
    verbose: bool = True,
    digest_function: Callable[[str], str] = sha512t24u_digest_bytes,
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


def parse_fasta(fa_file_path: str):
    """
    Read in a gzipped or not gzipped FASTA file
    """
    if not PYFAIDX_INSTALLED:
        raise ImportError("pyfaidx is not installed")
    try:
        return pyfaidx.Fasta(fa_file_path)
    except pyfaidx.UnsupportedCompressionFormat:
        # pyfaidx can handle bgzip but not gzip; so we just hack it here and
        # gunzip the file into a temporary one and read it in not to interfere
        # with the original one.
        from gzip import open as gzopen
        from tempfile import NamedTemporaryFile

        with gzopen(fa_file_path, "rt") as f_in, NamedTemporaryFile(
            mode="w+t", suffix=".fa"
        ) as f_out:
            f_out.writelines(f_in.read())
            f_out.seek(0)
            return pyfaidx.Fasta(f_out.name)

