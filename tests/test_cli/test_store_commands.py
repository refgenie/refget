# tests/test_cli/test_store_commands.py

"""Tests for refget store CLI commands."""

import pytest
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conftest import (
    BASE_FASTA,
    DIFFERENT_NAMES_FASTA,
    DIFFERENT_ORDER_FASTA,
    SAMPLE_FHR_JSON,
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


class TestStoreGet:
    """Tests for: refget store get <digest>"""

    def test_get_collection(self, cli, tmp_path):
        """Gets collection by digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli("store", "get", digest, "--path", str(store_path))

        data = assert_json_output(result, ["names", "lengths", "sequences"])

    def test_get_nonexistent_digest(self, cli, tmp_path):
        """Returns error for nonexistent digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "get", "nonexistent_digest_123", "--path", str(store_path))

        assert result.exit_code != 0


class TestStoreExport:
    """Tests for: refget store export <digest>"""

    def test_exports_fasta(self, cli, tmp_path):
        """Exports collection as FASTA."""
        store_path = tmp_path / "store"
        output = tmp_path / "exported.fa"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli("store", "export", digest, "-o", str(output), "--path", str(store_path))

        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert content.startswith(">")

    def test_export_to_stdout(self, cli, tmp_path):
        """Exports to stdout when no output file specified."""
        store_path = tmp_path / "store"

        cli("store", "init", "--path", str(store_path))
        add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
        digest = json.loads(add_result.stdout)["digest"]

        result = cli("store", "export", digest, "--path", str(store_path))

        assert result.exit_code == 0
        assert ">" in result.stdout  # FASTA format

    def test_export_nonexistent_digest(self, cli, tmp_path):
        """Returns error for nonexistent digest."""
        store_path = tmp_path / "store"
        output = tmp_path / "exported.fa"

        cli("store", "init", "--path", str(store_path))

        result = cli(
            "store",
            "export",
            "nonexistent_digest_123",
            "-o",
            str(output),
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

        result = cli(
            "store", "get", digest, "-s", "--name", "chr1", "--path", str(store_path)
        )

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

        data = assert_json_output(result, ["collections"])
        assert data["collections"] >= 1

    def test_empty_store_stats(self, cli, tmp_path):
        """Stats for empty store."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli("store", "stats", "--path", str(store_path))

        data = assert_json_output(result, ["collections"])
        assert data["collections"] == 0

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


def _setup_store_with_fasta(cli, tmp_path):
    """Initialize a store, add BASE_FASTA, and return (store_path, digest)."""
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
    digest = json.loads(add_result.stdout)["digest"]
    return store_path, digest


class TestStoreMetadata:
    """Tests for: refget store metadata / metadata-set"""

    def test_metadata_no_fhr_set(self, cli, tmp_path):
        """Error when no FHR metadata exists for a collection."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli("store", "metadata", digest, "--path", str(store_path))

        assert result.exit_code != 0
        assert "No FHR metadata" in result.stdout

    def test_metadata_set_from_json_file(self, cli, tmp_path):
        """Happy path: set FHR metadata from a JSON file."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli(
            "store", "metadata-set", digest, str(SAMPLE_FHR_JSON),
            "--path", str(store_path),
        )

        assert result.exit_code == 0
        assert "Set FHR metadata for collection" in result.stdout

    def test_metadata_read_after_set(self, cli, tmp_path):
        """Round-trip: set metadata then read it back."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli(
            "store", "metadata-set", digest, str(SAMPLE_FHR_JSON),
            "--path", str(store_path),
        )

        result = cli("store", "metadata", digest, "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["genome"] == "Test organism"
        assert data["version"] == "v1.0"
        assert data["masking"] == "soft-masked"
        assert "test_v1" in data["genomeSynonym"]

    def test_metadata_output_is_valid_json(self, cli, tmp_path):
        """Output is valid JSON with camelCase keys per FHR spec."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli(
            "store", "metadata-set", digest, str(SAMPLE_FHR_JSON),
            "--path", str(store_path),
        )

        result = cli("store", "metadata", digest, "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)

        # Verify camelCase keys from the FHR spec
        assert "schemaVersion" in data
        assert "genomeSynonym" in data
        assert "dateCreated" in data

        # Verify no snake_case keys leaked through
        raw = result.stdout
        assert "schema_version" not in raw
        assert "genome_synonym" not in raw
        assert "date_created" not in raw

    def test_metadata_set_nonexistent_file(self, cli, tmp_path):
        """Error when JSON file does not exist."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli(
            "store", "metadata-set", digest, "/nonexistent/fhr.json",
            "--path", str(store_path),
        )

        assert result.exit_code != 0

    def test_metadata_nonexistent_digest(self, cli, tmp_path):
        """Error when reading metadata for a nonexistent digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli(
            "store", "metadata", "nonexistent_digest_123",
            "--path", str(store_path),
        )

        assert result.exit_code != 0

    def test_metadata_set_then_overwrite(self, cli, tmp_path):
        """Overwriting metadata replaces the previous values."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        # Set original metadata
        cli(
            "store", "metadata-set", digest, str(SAMPLE_FHR_JSON),
            "--path", str(store_path),
        )

        # Create updated FHR JSON
        updated_fhr = tmp_path / "updated_fhr.json"
        updated_fhr.write_text(json.dumps({
            "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
            "schemaVersion": 1.0,
            "genome": "Updated organism",
            "version": "v2.0",
        }))

        # Overwrite
        cli(
            "store", "metadata-set", digest, str(updated_fhr),
            "--path", str(store_path),
        )

        result = cli("store", "metadata", digest, "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["genome"] == "Updated organism"

    def test_metadata_removed_with_collection(self, cli, tmp_path):
        """Metadata sidecar is cleaned up when the collection is removed."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        # Set metadata
        cli(
            "store", "metadata-set", digest, str(SAMPLE_FHR_JSON),
            "--path", str(store_path),
        )

        # Remove the collection
        cli("store", "remove", digest, "--path", str(store_path))

        # Metadata should be gone
        result = cli("store", "metadata", digest, "--path", str(store_path))

        assert result.exit_code != 0
