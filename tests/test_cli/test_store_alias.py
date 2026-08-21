# tests/test_cli/test_store_alias.py

"""Tests for refget store alias CLI commands."""

import json

from tests._test_data import (
    BASE_FASTA,
    assert_json_output,
)


def _setup_store_with_fasta(cli, tmp_path):
    """Initialize a store, add BASE_FASTA, and return (store_path, digest)."""
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
    digest = json.loads(add_result.stdout)["digest"]
    return store_path, digest


class TestStoreAlias:
    """Tests for: refget store alias add / get / list / rm / load / for"""

    def test_alias_add_and_get(self, cli, tmp_path):
        """Add a collection alias and resolve it back to a digest."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        add = cli("store", "alias", "add", "ucsc", "hg38", digest, "--path", str(store_path))
        assert add.exit_code == 0
        assert json.loads(add.stdout)["kind"] == "collection"

        get = cli("store", "alias", "get", "ucsc", "hg38", "--path", str(store_path))
        data = assert_json_output(get, ["digest"])
        assert data["digest"] == digest

    def test_alias_get_not_found(self, cli, tmp_path):
        """Resolving a missing alias errors."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli("store", "alias", "get", "ucsc", "missing", "--path", str(store_path))
        assert result.exit_code != 0

    def test_alias_list_namespaces_and_aliases(self, cli, tmp_path):
        """List namespaces (no arg) and aliases (with namespace)."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)
        cli("store", "alias", "add", "ucsc", "hg38", digest, "--path", str(store_path))

        ns = cli("store", "alias", "list", "--path", str(store_path))
        data = assert_json_output(ns, ["namespaces"])
        assert "ucsc" in data["namespaces"]

        aliases = cli("store", "alias", "list", "ucsc", "--path", str(store_path))
        data = assert_json_output(aliases, ["aliases"])
        assert "hg38" in data["aliases"]

    def test_alias_rm(self, cli, tmp_path):
        """Remove an alias."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)
        cli("store", "alias", "add", "ucsc", "hg38", digest, "--path", str(store_path))

        rm = cli("store", "alias", "rm", "ucsc", "hg38", "--path", str(store_path))
        assert rm.exit_code == 0
        assert json.loads(rm.stdout)["removed"] is True

        # second remove fails
        rm2 = cli("store", "alias", "rm", "ucsc", "hg38", "--path", str(store_path))
        assert rm2.exit_code != 0

    def test_alias_for_reverse_lookup(self, cli, tmp_path):
        """Reverse lookup returns (namespace, alias) pairs for a digest."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)
        cli("store", "alias", "add", "ucsc", "hg38", digest, "--path", str(store_path))

        result = cli("store", "alias", "for", digest, "--path", str(store_path))
        data = assert_json_output(result, ["aliases"])
        assert ["ucsc", "hg38"] in data["aliases"]

    def test_alias_load(self, cli, tmp_path):
        """Load aliases from a TSV file."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)
        tsv = tmp_path / "aliases.tsv"
        tsv.write_text(f"hg38\t{digest}\n")

        result = cli("store", "alias", "load", "ucsc", str(tsv), "--path", str(store_path))
        data = assert_json_output(result, ["loaded"])
        assert data["loaded"] >= 1

    def test_alias_sequence_kind(self, cli, tmp_path):
        """--seq operates on sequence aliases."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        # Find a sequence digest
        seqs = cli("store", "list", "-s", "--path", str(store_path))
        seq_digest = json.loads(seqs.stdout)["sequences"][0]["digest"]

        add = cli(
            "store", "alias", "add", "ncbi", "seq1", seq_digest, "-s", "--path", str(store_path)
        )
        assert add.exit_code == 0
        assert json.loads(add.stdout)["kind"] == "sequence"

        get = cli("store", "alias", "get", "ncbi", "seq1", "-s", "--path", str(store_path))
        data = assert_json_output(get, ["digest"])
        assert data["digest"] == seq_digest
