# tests/test_cli/test_store_add_bulk.py

"""Tests for refget store add (bulk/glob/file-list/namespace)."""

from tests._test_data import (
    BASE_FASTA,
    DIFFERENT_NAMES_FASTA,
    assert_json_output,
)


class TestStoreAddBulk:
    """Tests for: refget store add (bulk/glob/file-list/namespace)."""

    def test_add_multiple_paths(self, cli, tmp_path):
        """Adding multiple explicit paths uses the bulk results shape."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli(
            "store",
            "add",
            str(BASE_FASTA),
            str(DIFFERENT_NAMES_FASTA),
            "--path",
            str(store_path),
        )
        data = assert_json_output(
            result,
            [
                "results",
                "count",
                "n_sequences_written",
                "n_sequences_deduped",
                "n_collections_new",
            ],
        )
        assert data["count"] == 2
        # Per-run ingest counters, not the RAM-residency numbers from `stats`.
        assert data["n_collections_new"] == 2
        assert data["n_sequences_written"] > 0
        assert data["n_sequences_written"] + data["n_sequences_deduped"] == sum(
            r["sequences"] for r in data["results"]
        )

    def test_add_bulk_reimport_writes_nothing(self, cli, tmp_path):
        """Re-importing the same FASTAs adds no collections and writes no bytes."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        args = (
            "store",
            "add",
            str(BASE_FASTA),
            str(DIFFERENT_NAMES_FASTA),
            "--path",
            str(store_path),
        )
        cli(*args)
        result = cli(*args)

        data = assert_json_output(result, ["count", "n_sequences_written", "n_collections_new"])
        assert data["count"] == 2
        assert data["n_collections_new"] == 0
        assert data["n_sequences_written"] == 0

    def test_add_glob(self, cli, tmp_path):
        """A glob pattern is expanded by gtars and imported."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        # Stage two FASTAs in a fresh directory to glob over.
        data_dir = tmp_path / "fastas"
        data_dir.mkdir()
        (data_dir / "a.fa").write_text(BASE_FASTA.read_text())
        (data_dir / "b.fa").write_text(DIFFERENT_NAMES_FASTA.read_text())

        result = cli("store", "add", str(data_dir / "*.fa"), "--path", str(store_path))
        data = assert_json_output(result, ["results", "count"])
        assert data["count"] == 2

    def test_add_file_list(self, cli, tmp_path):
        """--file-list imports all files listed."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        manifest = tmp_path / "manifest.txt"
        manifest.write_text(f"{BASE_FASTA}\n{DIFFERENT_NAMES_FASTA}\n")

        result = cli("store", "add", "--file-list", str(manifest), "--path", str(store_path))
        data = assert_json_output(result, ["results", "count"])
        assert data["count"] == 2

    def test_add_with_jobs_uses_bulk(self, cli, tmp_path):
        """--jobs>1 routes through the bulk import path."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", str(BASE_FASTA), "--jobs", "2", "--path", str(store_path))
        data = assert_json_output(result, ["results", "count"])
        assert data["count"] == 1

    def test_add_namespace_registers_aliases(self, cli, tmp_path):
        """--namespace extracts aliases from FASTA headers."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        fasta = tmp_path / "ns.fa"
        fasta.write_text(">ncbi:NC_000001.11 chr1\nACGTACGTAC\n>chr2\nTTTTGGGGCC\n")

        cli("store", "add", str(fasta), "-N", "ncbi", "--path", str(store_path))

        result = cli("store", "alias", "list", "ncbi", "-s", "--path", str(store_path))
        data = assert_json_output(result, ["aliases"])
        assert "NC_000001.11" in data["aliases"]

    def test_add_no_input_errors(self, cli, tmp_path):
        """Providing neither paths nor --file-list errors."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", "--path", str(store_path))
        assert result.exit_code != 0
