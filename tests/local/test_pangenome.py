"""Tests for refget.pangenome: seqgraph, path, and pangenome digests."""

import pytest

from refget import GTARS_INSTALLED
from refget.pangenome import (
    canonical_seqgraph,
    pangenome_digest,
    pangenome_graph_digest,
    parse_gfa,
    path_collection_digest,
    path_digest,
    read_gfa,
    resolve_pangenome_graph,
    seqgraph_digest,
    sequence_collection,
    spell_path,
)
from refget.utils import fasta_to_seqcol_dict


def _gfa(*lines: str) -> str:
    """GFA text from space-separated lines (spaces become tabs)."""
    return "\n".join(line.replace(" ", "\t") for line in lines) + "\n"


def _digest(text: str) -> str:
    return seqgraph_digest(parse_gfa(text).seqgraph)


# The example graphs from the graph-digest demo (tasks/2026-hprc-meeting/graph-digest-demo)
# and the seqgraph digests its refget_graph_digest.py prints for them.
BASE = _gfa(
    "H VN:Z:1.0",
    "S 11 ACGT",
    "S 12 A",
    "S 13 A",
    "S 14 GGG",
    "L 11 + 12 + 0M",
    "L 12 + 14 + 0M",
    "L 11 + 13 - 0M",
    "L 13 - 14 + 0M",
)
BASE_DIGEST = "hEvYimTgnylqxG5xJoIYU6zqwEytx8UL"
DEMO_CASES = {
    "base": (BASE, BASE_DIGEST),
    "case1_reordered_lines_only": (
        _gfa(
            "L 13 - 14 + 0M",
            "S 14 GGG",
            "L 11 + 13 - 0M",
            "S 12 A",
            "H VN:Z:1.1",
            "S 11 ACGT",
            "L 12 + 14 + 0M",
            "S 13 A",
            "L 11 + 12 + 0M",
        ),
        BASE_DIGEST,
    ),
    "case2_lowercase_only": (BASE.replace("ACGT", "acgt").replace("GGG", "ggg"), BASE_DIGEST),
    "case4_renamed_nodes": (
        _gfa(
            "H VN:Z:1.0",
            "S x ACGT",
            "S q A",
            "S z A",
            "S m GGG",
            "L x + q + 0M",
            "L q + m + 0M",
            "L x + z - 0M",
            "L z - m + 0M",
        ),
        "UwmnOr4y-xUWEMC1nlQTC5rrj8GnPSLX",
    ),
    "case5_reversed_edge_declarations": (
        _gfa(
            "H VN:Z:1.0",
            "S 11 ACGT",
            "S 12 A",
            "S 13 A",
            "S 14 GGG",
            "L 12 - 11 - 0M",
            "L 14 - 12 - 0M",
            "L 13 + 11 - 0M",
            "L 14 - 13 + 0M",
        ),
        BASE_DIGEST,
    ),
    "case6_changed_sequence": (
        BASE.replace("GGG", "GGA"),
        "fOqTt8hhaqucvng5-GZM7J2rPDDwkxi7",
    ),
    "case7_changed_sequence_changes_canonical_order": (
        BASE.replace("ACGT", "TTT"),
        "RfhBXWwEf5x3UrL4jnd2hOMQU35q_OHz",
    ),
    "case8_reverse_complemented_node": (
        _gfa(
            "H VN:Z:1.0",
            "S 11 ACGT",
            "S 12 A",
            "S 13 A",
            "S 14 CCC",
            "L 11 + 12 + 0M",
            "L 12 + 14 - 0M",
            "L 11 + 13 - 0M",
            "L 13 - 14 - 0M",
        ),
        "v0-8K5Mg_dogn1aj6l_3Yc_J7kOWOw73",
    ),
}

# A small pangenome: two genomes (PanSN hap1#1, hap2#2), two chromosomes each.
# hap2 has a SNP on chr1 and walks node 7 in reverse on chr2.
PANGENOME_SEQUENCES = {
    "hap1#1": {"chr1": "ACGTATTGA", "chr2": "CCATGG"},
    "hap2#2": {"chr1": "ACGTGTTGA", "chr2": "CCATGTT"},
}
PANGENOME_GFA = _gfa(
    "S 1 ACGT",
    "S 2 A",
    "S 3 G",
    "S 4 TTGA",
    "S 5 CCAT",
    "S 6 GG",
    "S 7 aac",
    "L 1 + 2 + 0M",
    "L 1 + 3 + 0M",
    "L 2 + 4 + 0M",
    "L 3 + 4 + 0M",
    "L 5 + 6 + 0M",
    "L 5 + 7 - 0M",
    "P hap1#1#chr1 1+,2+,4+ *",
    "P hap1#1#chr2 5+,6+ *",
    "P hap2#2#chr1 1+,3+,4+ *",
    "P hap2#2#chr2 5+,7- *",
)


@pytest.mark.parametrize("case", DEMO_CASES)
def test_seqgraph_digest_matches_demo(case):
    text, expected = DEMO_CASES[case]
    assert _digest(text) == expected


def test_seqgraph_ignores_line_order_case_and_edge_direction():
    for case in ["case1_reordered_lines_only", "case2_lowercase_only"]:
        assert _digest(DEMO_CASES[case][0]) == _digest(BASE)
    assert _digest(DEMO_CASES["case5_reversed_edge_declarations"][0]) == _digest(BASE)


def test_node_renaming_changes_digest():
    assert _digest(DEMO_CASES["case4_renamed_nodes"][0]) != _digest(BASE)


def test_canonical_seqgraph():
    seqgraph = parse_gfa(BASE).seqgraph
    assert seqgraph == {
        "node_names": ["11", "12", "13", "14"],
        "node_sequences": ["ACGT", "A", "A", "GGG"],
        "edges": [[-4, -2], [-4, 3], [-2, -1], [1, -3]],
    }


def test_node_order_integer_or_lexicographic():
    numeric = canonical_seqgraph({"10": "A", "2": "C", "1": "G"}, [])
    assert numeric["node_names"] == ["1", "2", "10"]
    named = canonical_seqgraph({"s10": "A", "s2": "C", "s1": "G"}, [])
    assert named["node_names"] == ["s1", "s10", "s2"]


def test_duplicate_edges_deduplicated():
    text = BASE + _gfa("L 11 + 12 + 0M", "L 12 - 11 - 0M")
    assert len(parse_gfa(text).seqgraph["edges"]) == 4
    assert _digest(text) == _digest(BASE)


def test_overlap_field_ignored():
    text = BASE.replace("L\t11\t+\t12\t+\t0M", "L\t11\t+\t12\t+\t*")
    text = text.replace("L\t12\t+\t14\t+\t0M", "L\t12\t+\t14\t+\t5M")
    text = text.replace("L\t11\t+\t13\t-\t0M", "L\t11\t+\t13\t-")
    assert text != BASE
    assert _digest(text) == _digest(BASE)


def test_w_and_other_lines_ignored():
    text = BASE + _gfa("W sample 1 chr1 0 8 >11>12>14", "C 11 + 12 + 0 *", "# comment")
    graph = parse_gfa(text)
    assert graph.path_collections == {}
    assert seqgraph_digest(graph.seqgraph) == _digest(BASE)


def test_cross_chromosome_edge_accepted():
    graph = parse_gfa(PANGENOME_GFA + _gfa("L 4 + 5 + 0M"))
    assert [-5, -4] in graph.seqgraph["edges"]  # [4, 5], canonicalized
    assert seqgraph_digest(graph.seqgraph) != seqgraph_digest(parse_gfa(PANGENOME_GFA).seqgraph)


def test_pansn_grouping():
    graph = parse_gfa(PANGENOME_GFA)
    assert graph.path_collections == {
        "hap1#1": {"chr1": [1, 2, 4], "chr2": [5, 6]},
        "hap2#2": {"chr1": [1, 3, 4], "chr2": [5, -7]},
    }


def test_non_pansn_path_is_its_own_genome():
    graph = parse_gfa(BASE + _gfa("P hapX 11+,12+,14+ *", "P a#b 11+,13-,14+ *"))
    assert graph.path_collections == {
        "hapX": {"hapX": [1, 2, 4]},
        "a#b": {"a#b": [1, -3, 4]},
    }


def test_spell_path_reverse_complements_negative_steps():
    seqgraph = parse_gfa(PANGENOME_GFA).seqgraph
    assert spell_path(seqgraph, [1, 2, 4]) == "ACGTATTGA"
    assert spell_path(seqgraph, [5, -7]) == "CCATGTT"
    assert spell_path(seqgraph, [-4, -2, -1]) == "TCAATACGT"
    with pytest.raises(ValueError, match="outside"):
        spell_path(seqgraph, [0])


def test_resolved_pangenome_equals_linear_pangenome():
    linear = {
        genome: sequence_collection(sequences) for genome, sequences in PANGENOME_SEQUENCES.items()
    }
    resolved = resolve_pangenome_graph(parse_gfa(PANGENOME_GFA))
    assert resolved == linear
    assert pangenome_digest(resolved) == pangenome_digest(linear)


@pytest.mark.skipif(not GTARS_INSTALLED, reason="gtars is not installed")
def test_resolved_pangenome_equals_fasta_pangenome(tmp_path):
    fasta_seqcols = {}
    for genome, sequences in PANGENOME_SEQUENCES.items():
        fasta = tmp_path / f"{genome.replace('#', '_')}.fa"
        fasta.write_text("".join(f">{name}\n{seq}\n" for name, seq in sequences.items()))
        fasta_seqcols[genome] = fasta_to_seqcol_dict(str(fasta))
    resolved = resolve_pangenome_graph(parse_gfa(PANGENOME_GFA))
    for genome, seqcol in resolved.items():
        for attr in ("sequences", "lengths", "names"):
            assert seqcol[attr] == fasta_seqcols[genome][attr]
    assert pangenome_digest(resolved) == pangenome_digest(fasta_seqcols)


def test_path_digests_stable_under_line_reordering():
    lines = PANGENOME_GFA.splitlines()
    graph_lines = [line for line in lines if not line.startswith("P")]
    path_lines = [line for line in lines if line.startswith("P")]
    reordered = "\n".join(graph_lines[::-1] + path_lines) + "\n"
    a, b = parse_gfa(PANGENOME_GFA), parse_gfa(reordered)
    assert a.path_collections == b.path_collections
    assert pangenome_graph_digest(a) == pangenome_graph_digest(b)


def test_path_and_collection_order_is_content():
    graph = parse_gfa(PANGENOME_GFA)
    hap1 = graph.path_collections["hap1#1"]
    assert path_digest([1, 2, 4]) != path_digest([4, 2, 1])
    assert path_collection_digest(hap1) != path_collection_digest(dict(reversed(hap1.items())))
    lines = PANGENOME_GFA.splitlines()
    swapped = "\n".join(lines[:-4] + lines[-2:] + lines[-4:-2]) + "\n"
    other = parse_gfa(swapped)
    assert list(other.path_collections) == ["hap2#2", "hap1#1"]
    assert pangenome_graph_digest(other) != pangenome_graph_digest(graph)


def test_pangenome_graph_digest_uses_every_part():
    graph = parse_gfa(PANGENOME_GFA)
    renamed = parse_gfa(PANGENOME_GFA.replace("hap2#2#", "hap9#9#"))
    assert pangenome_graph_digest(renamed) != pangenome_graph_digest(graph)
    extra_edge = parse_gfa(PANGENOME_GFA + _gfa("L 2 + 3 + 0M"))
    assert extra_edge.path_collections == graph.path_collections
    assert pangenome_graph_digest(extra_edge) != pangenome_graph_digest(graph)


def test_read_gfa_matches_parse_gfa(tmp_path):
    path = tmp_path / "pangenome.gfa"
    path.write_text(PANGENOME_GFA)
    assert read_gfa(path) == parse_gfa(PANGENOME_GFA)
    assert read_gfa(str(path)) == parse_gfa(PANGENOME_GFA)


@pytest.mark.parametrize(
    "extra, message",
    [
        ("S 11 TTTT", "duplicate segment name '11'"),
        ("S 15 *", "segment '15' has no inline sequence"),
        ("L 11 + 99 + 0M", "link references unknown segment '99'"),
        ("P p1 11+,99+ *", "path 'p1' references unknown segment '99'"),
        ("L 11 x 12 + 0M", "orientation 'x'"),
        ("P p1 11+ *\nP p1 12+ *", "duplicate path 'p1'"),
    ],
)
def test_gfa_errors(extra, message):
    with pytest.raises(ValueError, match=message):
        parse_gfa(BASE + _gfa(extra))
