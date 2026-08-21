# tests/test_cli/test_store_fhr.py

"""Tests for refget store fhr CLI commands."""

import json

from tests._test_data import (
    BASE_FASTA,
    SAMPLE_FHR_JSON,
    assert_json_output,
)


def _setup_store_with_fasta(cli, tmp_path):
    """Initialize a store, add BASE_FASTA, and return (store_path, digest)."""
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    add_result = cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
    digest = json.loads(add_result.stdout)["digest"]
    return store_path, digest


class TestStoreFhr:
    """Tests for: refget store fhr get / set / set-fields / rm / list"""

    def test_fhr_no_metadata_set(self, cli, tmp_path):
        """Error when no FHR metadata exists for a collection."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli("store", "fhr", "get", digest, "--path", str(store_path))

        assert result.exit_code != 0
        assert "No FHR metadata" in result.stderr

    def test_fhr_set_from_json_file(self, cli, tmp_path):
        """Happy path: set FHR metadata from a JSON file."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli(
            "store",
            "fhr",
            "set",
            digest,
            str(SAMPLE_FHR_JSON),
            "--path",
            str(store_path),
        )

        assert result.exit_code == 0
        assert "Set FHR metadata for collection" in result.stdout

    def test_fhr_read_after_set(self, cli, tmp_path):
        """Round-trip: set metadata then read it back."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        result = cli("store", "fhr", "get", digest, "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["genome"] == "Test organism"
        assert data["version"] == "v1.0"
        assert data["masking"] == "soft-masked"
        assert "test_v1" in data["genomeSynonym"]

    def test_fhr_output_is_valid_json(self, cli, tmp_path):
        """Output is valid JSON with camelCase keys per FHR spec."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        result = cli("store", "fhr", "get", digest, "--path", str(store_path))

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

    def test_fhr_set_nonexistent_file(self, cli, tmp_path):
        """Error when JSON file does not exist."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli(
            "store",
            "fhr",
            "set",
            digest,
            "/nonexistent/fhr.json",
            "--path",
            str(store_path),
        )

        assert result.exit_code != 0

    def test_fhr_get_nonexistent_digest(self, cli, tmp_path):
        """Error when reading metadata for a nonexistent digest."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli(
            "store",
            "fhr",
            "get",
            "nonexistent_digest_123",
            "--path",
            str(store_path),
        )

        assert result.exit_code != 0

    def test_fhr_set_then_overwrite(self, cli, tmp_path):
        """Overwriting metadata replaces the previous values."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        updated_fhr = tmp_path / "updated_fhr.json"
        updated_fhr.write_text(
            json.dumps(
                {
                    "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
                    "schemaVersion": 1.0,
                    "genome": "Updated organism",
                    "version": "v2.0",
                }
            )
        )

        cli("store", "fhr", "set", digest, str(updated_fhr), "--path", str(store_path))

        result = cli("store", "fhr", "get", digest, "--path", str(store_path))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["genome"] == "Updated organism"

    def test_fhr_removed_with_collection(self, cli, tmp_path):
        """Metadata sidecar is cleaned up when the collection is removed."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        cli("store", "remove", digest, "--path", str(store_path))

        result = cli("store", "fhr", "get", digest, "--path", str(store_path))

        assert result.exit_code != 0

    def test_fhr_set_fields_roundtrip(self, cli, tmp_path):
        """set-fields builds FhrMetadata from CLI options; get reads it back."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli(
            "store",
            "fhr",
            "set-fields",
            digest,
            "--genome",
            "Field organism",
            "--version",
            "v3.0",
            "--genome-synonym",
            "syn1",
            "--genome-synonym",
            "syn2",
            "--path",
            str(store_path),
        )
        assert result.exit_code == 0

        get_result = cli("store", "fhr", "get", digest, "--path", str(store_path))
        assert get_result.exit_code == 0
        data = json.loads(get_result.stdout)
        assert data["genome"] == "Field organism"
        assert data["version"] == "v3.0"

    def test_fhr_set_fields_requires_a_field(self, cli, tmp_path):
        """set-fields errors when no fields are provided."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        result = cli("store", "fhr", "set-fields", digest, "--path", str(store_path))
        assert result.exit_code != 0

    def test_fhr_rm(self, cli, tmp_path):
        """rm removes FHR metadata for a collection."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        rm_result = cli("store", "fhr", "rm", digest, "--path", str(store_path))
        assert rm_result.exit_code == 0
        assert json.loads(rm_result.stdout)["removed"] is True

        # Now reading should fail
        get_result = cli("store", "fhr", "get", digest, "--path", str(store_path))
        assert get_result.exit_code != 0

    def test_fhr_list(self, cli, tmp_path):
        """list reports collections that have FHR metadata."""
        store_path, digest = _setup_store_with_fasta(cli, tmp_path)

        # Empty initially
        result = cli("store", "fhr", "list", "--path", str(store_path))
        data = assert_json_output(result, ["collections"])
        assert digest not in data["collections"]

        cli("store", "fhr", "set", digest, str(SAMPLE_FHR_JSON), "--path", str(store_path))

        result = cli("store", "fhr", "list", "--path", str(store_path))
        data = assert_json_output(result, ["collections"])
        assert digest in data["collections"]
