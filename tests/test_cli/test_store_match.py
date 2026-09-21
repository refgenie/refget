"""End-to-end contract test for refget store list and match."""

import json


def _add(cli, path, fasta):
    result = cli("store", "add", str(fasta), "--path", str(path))
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["digest"]


def test_list_and_match_contract(cli, tmp_path):
    store_path = tmp_path / "store"
    assert cli("store", "init", "--path", str(store_path)).exit_code == 0

    fasta_a = tmp_path / "a.fa"
    fasta_b = tmp_path / "b.fa"
    fasta_a.write_text(">chr1\nACGT\n>copy\nACGT\n>chr2\nGGCC\n>chr4\nCCCC\n")
    fasta_b.write_text(">four\nCCCC\n>one\nACGT\n>one_alt\nACGT\n>extra\nTTAA\n")
    digest_a = _add(cli, store_path, fasta_a)
    digest_b = _add(cli, store_path, fasta_b)
    alias_result = cli(
        "store", "alias", "add", "ucsc", "test", digest_a, "--path", str(store_path)
    )
    assert alias_result.exit_code == 0, alias_result.output

    inventory_result = cli("store", "list", "--path", str(store_path))
    assert inventory_result.exit_code == 0, inventory_result.output
    inventory = json.loads(inventory_result.stdout)["collections"]
    assert len(inventory) == 2
    by_digest = {row["digest"]: row for row in inventory}
    assert by_digest[digest_a] == {
        "digest": digest_a,
        "n_sequences": 4,
        "aliases": [["ucsc", "test"]],
    }
    assert by_digest[digest_b] == {
        "digest": digest_b,
        "n_sequences": 4,
        "aliases": [],
    }

    collection_result = cli(
        "store", "list", "ucsc:test", "--path", str(store_path)
    )
    assert collection_result.exit_code == 0, collection_result.output
    collection = json.loads(collection_result.stdout)
    assert collection["collection"] == by_digest[digest_a]
    assert [row["name"] for row in collection["sequences"]] == [
        "chr1",
        "copy",
        "chr2",
        "chr4",
    ]
    assert all(set(row) == {"name", "length", "digest"} for row in collection["sequences"])
    assert all(not row["digest"].startswith("SQ.") for row in collection["sequences"])
    assert collection["sequences"][0]["digest"] == collection["sequences"][1]["digest"]

    global_result = cli("store", "list", "--sequences", "--path", str(store_path))
    assert global_result.exit_code == 0, global_result.output
    global_sequences = json.loads(global_result.stdout)["sequences"]
    assert all(set(row) == {"digest", "name", "length"} for row in global_sequences)
    assert all(not row["digest"].startswith("SQ.") for row in global_sequences)
    assert {row["digest"] for row in global_sequences} == {
        row["digest"] for row in collection["sequences"]
    } | {
        row["digest"]
        for row in json.loads(
            cli("store", "list", digest_b, "--path", str(store_path)).stdout
        )["sequences"]
    }

    match_result = cli(
        "store",
        "match",
        "ucsc:test",
        digest_b,
        "--include-unmatched",
        "--path",
        str(store_path),
    )
    assert match_result.exit_code == 0, match_result.output
    body = json.loads(match_result.stdout)
    assert body["collection_a"] == digest_a
    assert body["collection_b"] == digest_b
    assert [row["names_a"] for row in body["matches"]] == [
        ["chr1", "copy"],
        ["chr4"],
    ]
    assert body["matches"][0]["names_b"] == ["one", "one_alt"]
    assert body["matches"][1]["names_b"] == ["four"]
    assert all(
        set(row) == {"digest", "length", "names_a", "names_b"}
        for group in ("matches", "a_only", "b_only")
        for row in body[group]
    )
    assert all(
        not row["digest"].startswith("SQ.")
        for group in ("matches", "a_only", "b_only")
        for row in body[group]
    )
    assert [row["names_a"] for row in body["a_only"]] == [["chr2"]]
    assert [row["names_b"] for row in body["b_only"]] == [["extra"]]
