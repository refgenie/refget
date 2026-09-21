"""
Pangenome digests: the seqcol algorithm applied to pangenomes.

A pangenome can be stored two ways. The linear form keeps each genome as an
ordinary sequence collection. The graph form moves the shared sequence into one
seqgraph and keeps each genome as walks (paths) through it::

    # linear form
    sequence_collection = {sequences, lengths, names}   # an ordinary seqcol
    pangenome           = {sequence_collections, sequence_collection_names}

    # graph form
    seqgraph        = {node_names, node_sequences, edges}
    path            = {steps}
    path_collection = {paths, names}                    # one genome
    pangenome_graph = {seqgraph, path_collections, path_collection_names}

Every object is digested with the unchanged seqcol algorithm
(``refget.utils.seqcol_digest``), and only each object's final digest is public.
An attribute that holds other objects (``seqgraph``, ``paths``,
``path_collections``, ``sequence_collections``) holds their digests. Collated
arrays keep their input order, as in seqcol.

Edges and path steps are signed, 1-based references into the seqgraph's node
order: ``+i`` is node ``i`` read forward, ``-i`` is its reverse complement. A path
spells a sequence, so a path collection resolves to a sequence collection and a
pangenome graph resolves to a pangenome. The optional ``derived_from`` attribute of
a path or pangenome graph (the digest it resolves to) is non-inherent: it never
changes a digest.

Phase-1 limits:
  - GFA import reads only S, L, and P lines. W lines and all other records are skipped.
  - L-line overlaps are ignored and never digested.
  - A pangenome graph has exactly one seqgraph, so an edge may join any two nodes,
    including nodes on different chromosomes.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .digests import sha512t24u_digest
from .utils import seqcol_digest

_SEQGRAPH_ATTRS = ("node_names", "node_sequences", "edges")
_COMPLEMENT = str.maketrans("ACGTUMRWSYKVHDBN", "TGCAAKYWSRMBDHVN")


@dataclass
class PangenomeGraph:
    """A pangenome in graph form: one seqgraph plus one path collection per genome.

    Attributes:
        seqgraph: The canonical seqgraph ``{node_names, node_sequences, edges}``.
        path_collections: Genome name -> {sequence name -> steps}, in input order.
            Steps are signed 1-based references into the seqgraph's node order.
    """

    seqgraph: dict
    path_collections: dict[str, dict[str, list[int]]]


def _digest(obj: dict) -> str:
    """Seqcol digest of an object whose attributes are all inherent."""
    return seqcol_digest(obj, inherent_attrs=list(obj))


def _normalize(sequence: str) -> str:
    """Refget sequence normalization: drop non-alphabetic characters, uppercase."""
    return re.sub(r"[^A-Za-z]", "", sequence).upper()


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def _node_order(names: Iterable[str]) -> list[str]:
    """Integer order if every name is an integer, else lexicographic order."""
    names = list(names)
    try:
        return sorted(names, key=lambda name: (int(name), name))
    except ValueError:
        return sorted(names)


def _oriented_ref(position: dict[str, int], name: str, orientation: str, where: str) -> int:
    if name not in position:
        raise ValueError(f"{where} references unknown segment {name!r}")
    if orientation not in ("+", "-"):
        raise ValueError(f"{where} has orientation {orientation!r}; expected '+' or '-'")
    return position[name] if orientation == "+" else -position[name]


def sequence_digest(sequence: str) -> str:
    """Refget sequence digest: "SQ." + sha512t24u of the uppercased sequence.

    This is the digest refget gives each record of a FASTA file, so it compares
    directly with ``refget.utils.fasta_to_seqcol_dict`` output.
    """
    return "SQ." + sha512t24u_digest(sequence.upper())


def sequence_collection(sequences: dict[str, str]) -> dict:
    """The seqcol object ``{sequences, lengths, names}`` for named raw sequences.

    Its ``seqcol_digest`` equals that of a FASTA file with the same records in the
    same order.

    Args:
        sequences: Sequence name -> raw sequence, in collection order.
    """
    return {
        "sequences": [sequence_digest(s) for s in sequences.values()],
        "lengths": [len(s) for s in sequences.values()],
        "names": list(sequences),
    }


def canonical_seqgraph(
    segments: dict[str, str], links: Iterable[tuple[str, str, str, str]]
) -> dict:
    """Build the canonical seqgraph ``{node_names, node_sequences, edges}``.

    Node sequences are normalized (non-alphabetic characters removed, uppercased).
    Nodes are ordered by name: numerically if every name is an integer, otherwise
    lexicographically. Each edge becomes a pair of signed node references and is
    written as ``min([a, b], [-b, -a])``, since both spell the same bidirected
    edge. Edges are then deduplicated and sorted.

    Args:
        segments: Node name -> literal sequence.
        links: ``(from_name, from_orientation, to_name, to_orientation)`` tuples,
            with orientations "+" or "-".
    """
    names = _node_order(segments)
    position = {name: i + 1 for i, name in enumerate(names)}
    edges = set()
    for a, a_orientation, b, b_orientation in links:
        ref_a = _oriented_ref(position, a, a_orientation, "link")
        ref_b = _oriented_ref(position, b, b_orientation, "link")
        edges.add(min((ref_a, ref_b), (-ref_b, -ref_a)))
    return {
        "node_names": names,
        "node_sequences": [_normalize(segments[name]) for name in names],
        "edges": [list(edge) for edge in sorted(edges)],
    }


def seqgraph_digest(seqgraph: dict) -> str:
    """Digest a canonical seqgraph (see ``canonical_seqgraph``)."""
    return _digest({attr: seqgraph[attr] for attr in _SEQGRAPH_ATTRS})


def path_digest(steps: list[int]) -> str:
    """Digest a path ``{steps}``."""
    return _digest({"steps": list(steps)})


def path_collection_digest(paths: dict[str, list[int]]) -> str:
    """Digest a path collection ``{paths, names}``.

    Args:
        paths: Sequence name (e.g. "chr1") -> steps, in collection order.
    """
    return _digest(
        {
            "paths": [path_digest(steps) for steps in paths.values()],
            "names": list(paths),
        }
    )


def pangenome_graph_digest(graph: PangenomeGraph) -> str:
    """Digest a pangenome graph ``{seqgraph, path_collections, path_collection_names}``."""
    return _digest(
        {
            "seqgraph": seqgraph_digest(graph.seqgraph),
            "path_collections": [
                path_collection_digest(paths) for paths in graph.path_collections.values()
            ],
            "path_collection_names": list(graph.path_collections),
        }
    )


def pangenome_digest(sequence_collections: dict[str, dict]) -> str:
    """Digest a linear pangenome ``{sequence_collections, sequence_collection_names}``.

    Args:
        sequence_collections: Genome name -> seqcol object, in pangenome order. Each
            seqcol (e.g. from ``refget.utils.fasta_to_seqcol_dict``) gets its
            standard seqcol digest.
    """
    return _digest(
        {
            "sequence_collections": [seqcol_digest(c) for c in sequence_collections.values()],
            "sequence_collection_names": list(sequence_collections),
        }
    )


def spell_path(seqgraph: dict, steps: list[int]) -> str:
    """Spell the sequence a path walks: its oriented node sequences, concatenated."""
    node_sequences = seqgraph["node_sequences"]
    parts = []
    for step in steps:
        if not 0 < abs(step) <= len(node_sequences):
            raise ValueError(f"step {step} is outside the seqgraph's {len(node_sequences)} nodes")
        sequence = node_sequences[abs(step) - 1]
        parts.append(sequence if step > 0 else _reverse_complement(sequence))
    return "".join(parts)


def resolve_path_collection(seqgraph: dict, paths: dict[str, list[int]]) -> dict:
    """Resolve a path collection to its sequence collection ``{sequences, lengths, names}``."""
    return sequence_collection({name: spell_path(seqgraph, steps) for name, steps in paths.items()})


def resolve_pangenome_graph(graph: PangenomeGraph) -> dict[str, dict]:
    """Resolve a pangenome graph to its linear form: genome name -> sequence collection.

    ``pangenome_digest`` of the result is the pangenome the graph resolves to (the
    graph's ``derived_from``).
    """
    return {
        name: resolve_path_collection(graph.seqgraph, paths)
        for name, paths in graph.path_collections.items()
    }


def _split_pansn(path_name: str) -> tuple[str, str]:
    """``sample#hap#seq`` -> (``sample#hap``, ``seq``); any other name -> (name, name)."""
    parts = path_name.split("#", 2)
    if len(parts) == 3 and all(parts):
        return f"{parts[0]}#{parts[1]}", parts[2]
    return path_name, path_name


def _parse_gfa_lines(lines: Iterable[str]) -> PangenomeGraph:
    segments: dict[str, str] = {}
    links: list[tuple[str, str, str, str]] = []
    paths: list[tuple[str, list[str]]] = []
    for line_number, line in enumerate(lines, start=1):
        fields = line.rstrip("\r\n").split("\t")
        record = fields[0]
        if record == "S":
            if len(fields) < 3:
                raise ValueError(f"line {line_number}: S-line needs a name and a sequence")
            name, sequence = fields[1], fields[2]
            if name in segments:
                raise ValueError(f"line {line_number}: duplicate segment name {name!r}")
            if sequence == "*":
                raise ValueError(f"line {line_number}: segment {name!r} has no inline sequence")
            segments[name] = sequence
        elif record == "L":
            if len(fields) < 5:
                raise ValueError(f"line {line_number}: L-line needs two segments and orientations")
            links.append((fields[1], fields[2], fields[3], fields[4]))
        elif record == "P":
            if len(fields) < 3:
                raise ValueError(f"line {line_number}: P-line needs a name and a segment list")
            paths.append((fields[1], fields[2].split(",")))

    seqgraph = canonical_seqgraph(segments, links)
    position = {name: i + 1 for i, name in enumerate(seqgraph["node_names"])}
    path_collections: dict[str, dict[str, list[int]]] = {}
    for path_name, steps in paths:
        genome, sequence_name = _split_pansn(path_name)
        collection = path_collections.setdefault(genome, {})
        if sequence_name in collection:
            raise ValueError(f"duplicate path {path_name!r}")
        where = f"path {path_name!r}"
        collection[sequence_name] = [
            _oriented_ref(position, step[:-1], step[-1:], where) for step in steps
        ]
    return PangenomeGraph(seqgraph, path_collections)


def parse_gfa(text: str) -> PangenomeGraph:
    """Build a pangenome graph from GFA 1 text.

    Reads S (segment), L (link), and P (path) lines and skips all other records,
    including W lines. L-line overlaps are ignored. Paths are grouped into genomes
    by PanSN name: ``sample#hap#seq`` becomes sequence ``seq`` of genome
    ``sample#hap``. A path whose name is not PanSN becomes its own genome, named
    after the path, holding one sequence with the same name. Genomes, and the
    sequences in each, keep the order their P lines appear in.

    Raises:
        ValueError: For a duplicate segment name, a segment with no inline sequence
            (``*``), a link or path that references an unknown segment, a duplicate
            path, or a malformed line.
    """
    return _parse_gfa_lines(text.splitlines())


def read_gfa(path: str | Path) -> PangenomeGraph:
    """Build a pangenome graph from a GFA 1 file. See ``parse_gfa``."""
    with open(path, encoding="utf-8") as f:
        return _parse_gfa_lines(f)
