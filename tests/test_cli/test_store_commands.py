# tests/test_cli/test_store_commands.py

"""Tests for refget store CLI commands."""

import json
from types import SimpleNamespace

from refget.cli.store import _list_all_collection_metadata, _resolve_collection_selector
from tests._test_data import (
    BASE_FASTA,
    DIFFERENT_NAMES_FASTA,
    TEST_FASTA_DIGESTS,
    assert_json_output,
)


class TestStoreInit:
    """Tests for: refget store init"""

    def test_creates_store(self, cli, tmp_path):
        """Initializes new store directory."""
        store_path = tmp_path / "new_store"
        result = cli("store", "init", "--path", str(store_path))

        assert result.exit_code == 0
        assert store_path.exists()

    def test_idempotent(self, cli, tmp_path):
        """Re-init existing store succeeds."""
        store_path = tmp_path / "store"

        # First init
        result1 = cli("store", "init", "--path", str(store_path))
        assert result1.exit_code == 0

        # Second init should also succeed (idempotent)
        result2 = cli("store", "init", "--path", str(store_path))
        assert result2.exit_code == 0

    def test_creates_required_structure(self, cli, tmp_path):
        """Store init creates necessary subdirectories or files."""
        store_path = tmp_path / "store"
        result = cli("store", "init", "--path", str(store_path))

        assert result.exit_code == 0
        assert store_path.exists()
        assert store_path.is_dir()

    def test_init_default_path(self, cli, tmp_path, monkeypatch):
        """Store init uses default path if not specified."""
        monkeypatch.chdir(tmp_path)
        result = cli("store", "init")

        # Should succeed and create store in current directory or default location
        assert result.exit_code == 0


class TestStoreAdd:
    """Tests for: refget store add <fasta>"""

    def test_adds_fasta(self, cli, tmp_path):
        """Adds FASTA and returns digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        data = assert_json_output(result, ["digest"])
        assert len(data["digest"]) > 0

    def test_returns_correct_digest(self, cli, tmp_path):
        """Returns expected digest for known file."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        expected = TEST_FASTA_DIGESTS["base.fa"]["top_level_digest"]
        assert data["digest"] == expected

    def test_idempotent(self, cli, tmp_path):
        """Adding same file twice returns same digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result1 = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        result2 = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        digest1 = json.loads(result1.stdout)["digest"]
        digest2 = json.loads(result2.stdout)["digest"]
        assert digest1 == digest2

    def test_add_multiple_files(self, cli, tmp_path):
        """Can add multiple different FASTA files."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result1 = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        result2 = cli("store", "add", str(DIFFERENT_NAMES_FASTA), "--path", str(store_path))

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        digest1 = json.loads(result1.stdout)["digest"]
        digest2 = json.loads(result2.stdout)["digest"]
        assert digest1 != digest2

    def test_add_nonexistent_file(self, cli, tmp_path):
        """Returns error for nonexistent file."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", "/nonexistent/file.fa", "--path", str(store_path))

        assert result.exit_code != 0

    def test_add_with_mode_raw(self, cli, tmp_path):
        """Can add sequences in raw storage mode."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        # Add with raw mode
        result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path), "--mode", "raw")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "digest" in data

        # Verify sequences stored in raw mode
        stats_result = cli("store", "stats", "--path", str(store_path))
        stats_data = json.loads(stats_result.stdout)
        assert stats_data["storage_mode"] == "Raw"

    def test_add_with_mode_short_flag(self, cli, tmp_path):
        """Can use -m short flag for mode override."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path), "-m", "raw")

        assert result.exit_code == 0


class TestStoreList:
    """Tests for: refget store list"""

    def test_empty_store(self, cli, tmp_path):
        """Lists empty store."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "list", "--path", str(store_path))

        data = assert_json_output(result, ["collections"])
        assert data["collections"] == []

    def test_with_collections(self, cli, tmp_path):
        """Lists store with collections."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        result = cli("store", "list", "--path", str(store_path))

        data = assert_json_output(result, ["collections"])
        assert len(data["collections"]) >= 1

    def test_list_multiple_collections(self, cli, tmp_path):
        """Lists multiple collections."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        cli("store", "add", str(DIFFERENT_NAMES_FASTA), "--path", str(store_path))

        result = cli("store", "list", "--path", str(store_path))

        data = assert_json_output(result, ["collections"])
        assert len(data["collections"]) >= 2

    def test_list_returns_string_digests(self, cli, tmp_path):
        """Regression: list must return string digests, not metadata objects."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        result = cli("store", "list", "--path", str(store_path))

        data = assert_json_output(result, ["collections"])
        # Each collection must have a string digest, not a metadata object
        for item in data["collections"]:
            assert "digest" in item
            assert isinstance(item["digest"], str)
            assert len(item["digest"]) > 0

    def test_selector_and_inventory_use_bounded_metadata_lookups(self):
        """Digest selectors avoid scans; a complete inventory uses two calls."""
        first = SimpleNamespace(digest="first")
        second = SimpleNamespace(digest="second")

        class StoreDouble:
            def __init__(self):
                self.list_calls = []

            def get_collection_metadata(self, digest):
                return first if digest == "first" else None

            def list_collections(self, *, page, page_size):
                self.list_calls.append((page, page_size))
                results = [first] if page_size == 1 else [first, second]
                return {"results": results, "pagination": {"total": 2}}

        store = StoreDouble()
        assert _resolve_collection_selector(store, "first") == "first"
        assert store.list_calls == []
        assert _list_all_collection_metadata(store, page_size=1) == [first, second]
        assert store.list_calls == [(0, 1), (0, 2)]


class TestStoreGet:
    """Tests for: refget store get <digest>"""

    def test_get_collection(self, cli, tmp_path):
        """Gets collection by digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli("store", "get", digest, "--path", str(store_path))

        assert_json_output(result, ["names", "lengths", "sequences"])

    def test_get_nonexistent_digest(self, cli, tmp_path):
        """Returns error for nonexistent digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "get", "nonexistent_digest_123", "--path", str(store_path))

        assert result.exit_code != 0


def _run_cli(*args, shell_suffix=None):
    """Run the CLI in a subprocess.

    Export streams FASTA from Rust straight to file descriptor 1, which
    CliRunner cannot capture, so stdout tests need a real process.
    """
    import shlex
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "refget.cli.main", *args]
    if shell_suffix:
        line = " ".join(shlex.quote(c) for c in cmd) + " " + shell_suffix
        return subprocess.run(
            ["bash", "-o", "pipefail", "-c", line], capture_output=True, text=True
        )
    return subprocess.run(cmd, capture_output=True, text=True)


def _headers(fasta_text):
    return [line[1:] for line in fasta_text.splitlines() if line.startswith(">")]


class TestStoreExport:
    """Tests for: refget store export"""

    def _store(self, cli, tmp_path, *fastas):
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        digests = []
        for fasta in fastas or (BASE_FASTA,):
            add_result = cli("store", "add", str(fasta), "--path", str(store_path))
            digests.append(json.loads(add_result.stdout)["digest"])
        return store_path, digests

    def test_exports_fasta(self, cli, tmp_path):
        """Exports a collection to a file, labeled by digest, with summary counts."""
        store_path, (digest,) = self._store(cli, tmp_path)
        output = tmp_path / "exported.fa"

        result = cli("store", "export", digest, "-o", str(output), "--path", str(store_path))

        assert result.exit_code == 0, result.stdout
        report = json.loads(result.stdout)
        assert report["n_records"] == 3
        assert report["collections"] == [digest]
        assert all(h.startswith("SQ.") for h in _headers(output.read_text()))

    def test_stdout_matches_output_file(self, cli, tmp_path):
        """Streaming to stdout writes the same bytes as --output."""
        store_path, (digest,) = self._store(cli, tmp_path)
        output = tmp_path / "exported.fa"
        cli("store", "export", digest, "-l", "name", "-o", str(output), "--path", str(store_path))

        proc = _run_cli("store", "export", digest, "-l", "name", "--path", str(store_path))

        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == output.read_text()
        assert _headers(proc.stdout) == ["chrX", "chr1", "chr2"]

    def test_label_use_cases(self, cli, tmp_path):
        """The documented label examples produce the documented headers."""
        store_path, (base, renamed) = self._store(cli, tmp_path, BASE_FASTA, DIFFERENT_NAMES_FASTA)
        cli("store", "alias", "add", "ucsc", "hg38", base, "--path", str(store_path))
        cli("store", "alias", "add", "ensembl", "GRCh38", renamed, "--path", str(store_path))
        p = ["--path", str(store_path)]

        # -l name on a namespace:alias selector
        proc = _run_cli("store", "export", "ucsc:hg38", "-l", "name", *p)
        assert _headers(proc.stdout) == ["chrX", "chr1", "chr2"], proc.stderr

        # --all covers `store list --sequences`, each sequence once
        listed = json.loads(cli("store", "list", "--sequences", *p).stdout)["sequences"]
        proc = _run_cli("store", "export", "--all", *p)
        assert sorted(_headers(proc.stdout)) == sorted(f"SQ.{s['digest']}" for s in listed)

        # once per genome, qualified by the collection alias
        proc = _run_cli("store", "export", "--all", "-l", "{col:ucsc}/{name}", *p)
        headers = _headers(proc.stdout)
        assert "hg38/chr1" in headers
        assert f"{renamed}/1" in headers  # no ucsc alias: falls back to the digest
        assert len(headers) == 6
        assert "fell back" in proc.stderr

        # bare names across genomes that share sequences under different names
        proc = _run_cli("store", "export", "--all", "-l", "name", *p)
        assert proc.returncode == 0
        assert len(_headers(proc.stdout)) == 6

    def test_bad_flags_error_without_fasta(self, cli, tmp_path):
        """Conflicting selections, bad templates and unknown namespaces error cleanly."""
        store_path, (digest,) = self._store(cli, tmp_path)
        p = ["--path", str(store_path)]
        cases = [
            (["--all", digest], "exactly one selection"),
            (["--all", "--seq-digest", "x"], "exactly one selection"),
            ([], "exactly one selection"),
            (["--all", "--name", "chr1"], "--name"),
            ([digest, "-l", "{nope}"], "unknown field"),
            ([digest, "-l", "seq:nope"], "namespace"),
        ]
        for args, needle in cases:
            proc = _run_cli("store", "export", *args, *p)
            assert proc.returncode != 0, args
            assert proc.stdout == "", args
            assert needle in proc.stderr, (args, proc.stderr)
            assert "Traceback" not in proc.stderr

    def test_broken_pipe_exits_quietly(self, cli, tmp_path):
        """`export | head -1` exits 0 with no traceback."""
        big = tmp_path / "big.fa"
        big.write_text(">big\n" + "ACGT" * 2_000_000 + "\n")
        store_path, (digest,) = self._store(cli, tmp_path, big)

        proc = _run_cli("store", "export", digest, "--path", str(store_path), shell_suffix="| head -1")

        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.startswith(">SQ.")
        assert "Traceback" not in proc.stderr

    def test_export_nonexistent_digest(self, cli, tmp_path):
        """Returns error for nonexistent digest."""
        store_path, _ = self._store(cli, tmp_path)
        output = tmp_path / "exported.fa"

        result = cli(
            "store", "export", "nonexistent_digest_123", "-o", str(output), "--path", str(store_path)
        )

        assert result.exit_code != 0

    def test_export_by_seq_digest(self, cli, tmp_path):
        """Exports by sequence digest; the label is that digest as a refget ID."""
        store_path, _ = self._store(cli, tmp_path)
        list_result = cli("store", "list", "--sequences", "--path", str(store_path))
        seq_digest = json.loads(list_result.stdout)["sequences"][0]["digest"]

        proc = _run_cli("store", "export", "--seq-digest", seq_digest, "--path", str(store_path))

        assert proc.returncode == 0, proc.stderr
        assert _headers(proc.stdout) == [f"SQ.{seq_digest}"]

    def test_remote_all_does_not_cache_sequences(self, cli, tmp_path):
        """A remote --all export streams sequences without writing them to the cache."""
        import functools
        import http.server
        import threading

        served, (digest,) = self._store(cli, tmp_path)
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(served)
        )
        handler.log_message = lambda *a, **k: None
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/"
            local = tmp_path / "local"
            proc = _run_cli("store", "export", "--remote", url, "--all", "--path", str(local))
        finally:
            server.shutdown()

        assert proc.returncode == 0, proc.stderr
        assert len(_headers(proc.stdout)) == 3
        cache = local / ".remote_cache"
        assert cache.exists()
        assert list(cache.rglob("*.seq")) == []


class TestStoreRegions:
    """Tests for: refget store regions <digest> --bed"""

    def _setup(self, cli, tmp_path):
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]
        # Get a sequence name to build a valid BED region.
        list_result = cli("store", "list", "--sequences", "--path", str(store_path))
        seq = json.loads(list_result.stdout)["sequences"][0]
        bed = tmp_path / "regions.bed"
        bed.write_text(f"{seq['name']}\t0\t3\n")
        return store_path, digest, bed, seq["name"]

    def test_regions_fasta(self, cli, tmp_path):
        """Extracts regions as FASTA records."""
        store_path, digest, bed, name = self._setup(cli, tmp_path)
        result = cli("store", "regions", digest, "--bed", str(bed), "--path", str(store_path))
        assert result.exit_code == 0, result.stdout
        assert result.stdout.startswith(f">{name}:0-3")

    def test_regions_json(self, cli, tmp_path):
        """Extracts regions as JSON records."""
        store_path, digest, bed, name = self._setup(cli, tmp_path)
        result = cli(
            "store", "regions", digest, "--bed", str(bed), "--json", "--path", str(store_path)
        )
        assert result.exit_code == 0, result.stdout
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert data[0]["chrom_name"] == name
        assert data[0]["start"] == 0
        assert data[0]["end"] == 3
        assert len(data[0]["sequence"]) == 3

    def test_regions_missing_bed(self, cli, tmp_path):
        """Returns error when BED file does not exist."""
        store_path, digest, _bed, _name = self._setup(cli, tmp_path)
        result = cli(
            "store",
            "regions",
            digest,
            "--bed",
            str(tmp_path / "nope.bed"),
            "--path",
            str(store_path),
        )
        assert result.exit_code != 0


class TestStoreGetSequence:
    """Tests for: refget store get <digest> --sequence"""

    def test_gets_sequence_by_name(self, cli, tmp_path):
        """Gets sequence by name using get -s."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli("store", "get", digest, "-s", "--name", "chr1", "--path", str(store_path))

        assert result.exit_code == 0
        # Output should be sequence (GGAA for chr1 in base.fa)
        assert len(result.stdout.strip()) > 0

    def test_substring(self, cli, tmp_path):
        """Gets subsequence with range using get -s."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli(
            "store",
            "get",
            digest,
            "-s",
            "--name",
            "chrX",
            "--start",
            "0",
            "--end",
            "4",
            "--path",
            str(store_path),
        )

        assert result.exit_code == 0
        seq = result.stdout.strip()
        assert len(seq) <= 4

    def test_seq_nonexistent_name(self, cli, tmp_path):
        """Returns error for nonexistent sequence name."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli(
            "store",
            "get",
            digest,
            "-s",
            "--name",
            "nonexistent_chr",
            "--path",
            str(store_path),
        )

        assert result.exit_code != 0


class TestStoreListSequences:
    """Tests for: refget store list --sequences"""

    def test_list_sequences(self, cli, tmp_path):
        """Lists sequences with -s flag."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        result = cli("store", "list", "-s", "--path", str(store_path))

        data = assert_json_output(result, ["sequences"])
        assert len(data["sequences"]) >= 1
        # Each sequence should have digest, name, length
        for seq in data["sequences"]:
            assert "digest" in seq
            assert "name" in seq
            assert "length" in seq

    def test_list_sequences_empty_store(self, cli, tmp_path):
        """Lists sequences in empty store."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "list", "-s", "--path", str(store_path))

        data = assert_json_output(result, ["sequences"])
        assert data["sequences"] == []


class TestStoreStats:
    """Tests for: refget store stats"""

    def test_outputs_stats(self, cli, tmp_path):
        """Outputs store statistics."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        result = cli("store", "stats", "--path", str(store_path))

        data = assert_json_output(result, ["n_collections"])
        assert int(data["n_collections"]) >= 1

    def test_empty_store_stats(self, cli, tmp_path):
        """Stats for empty store."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "stats", "--path", str(store_path))

        data = assert_json_output(result, ["n_collections"])
        assert int(data["n_collections"]) == 0

    def test_stats_shows_storage_mode_encoded(self, cli, tmp_path):
        """Stats shows storage_mode for encoded store (default)."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        # Default mode is encoded
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path))

        result = cli("store", "stats", "--path", str(store_path))

        data = json.loads(result.stdout)
        assert "storage_mode" in data
        assert data["storage_mode"] == "Encoded"

    def test_stats_shows_storage_mode_raw(self, cli, tmp_path):
        """Stats shows storage_mode for raw store with data.

        Note: Storage mode must be specified at add time, not just init,
        because gtars doesn't persist mode settings between sessions.
        """
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        # Must use --mode raw during add to store data in raw mode
        cli("store", "add", str(BASE_FASTA), "--path", str(store_path), "--mode", "raw")

        result = cli("store", "stats", "--path", str(store_path))

        data = json.loads(result.stdout)
        assert "storage_mode" in data
        assert data["storage_mode"] == "Raw"


class TestStoreRemove:
    """Tests for: refget store remove <digest>"""

    def test_removes_collection(self, cli, tmp_path):
        """Removes collection from store."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        # Remove
        result = cli("store", "remove", digest, "--path", str(store_path))
        assert result.exit_code == 0

        # Verify removed
        list_result = cli("store", "list", "--path", str(store_path))
        data = json.loads(list_result.stdout)
        assert digest not in data.get("collections", [])

    def test_remove_nonexistent(self, cli, tmp_path):
        """Returns error for nonexistent digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "remove", "nonexistent_digest", "--path", str(store_path))

        assert result.exit_code != 0


class TestStoreErrorHandling:
    """Test error handling for store commands."""

    def test_operations_on_nonexistent_store(self, cli, tmp_path):
        """Operations on nonexistent store fail gracefully."""
        nonexistent = tmp_path / "nonexistent_store"

        result = cli("store", "list", "--path", str(nonexistent))

        assert result.exit_code != 0

    def test_add_to_nonexistent_store(self, cli, tmp_path):
        """Add to nonexistent store fails gracefully."""
        nonexistent = tmp_path / "nonexistent_store"

        result = cli("store", "add", str(BASE_FASTA), "--path", str(nonexistent))

        assert result.exit_code != 0
