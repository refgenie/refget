# tests/test_cli/test_seqcol_commands.py

"""
Tests for refget seqcol CLI commands.

These are unit tests that do NOT require network access.
Network-dependent tests are in tests/integration/test_cli_seqcol_integration.py
"""

import importlib.util
import json
import os

_conftest_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"
)
_spec = importlib.util.spec_from_file_location("tests_conftest", _conftest_path)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)

BASE_FASTA = _conftest.BASE_FASTA
DIFFERENT_NAMES_FASTA = _conftest.DIFFERENT_NAMES_FASTA
DIFFERENT_ORDER_FASTA = _conftest.DIFFERENT_ORDER_FASTA
SUBSET_FASTA = _conftest.SUBSET_FASTA
TEST_FASTA_DIGESTS = _conftest.TEST_FASTA_DIGESTS
assert_json_output = _conftest.assert_json_output


class TestSeqcolCompare:
    """Tests for: refget seqcol compare <a> <b>"""

    def test_compare_identical_files(self, cli, sample_fasta, tmp_path):
        """Comparing identical files shows match."""
        fasta2 = tmp_path / "copy.fa"
        fasta2.write_text(sample_fasta.read_text())

        result = cli("seqcol", "compare", str(sample_fasta), str(fasta2))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Should indicate identical or full match
        assert "match" in data or "identical" in str(data).lower() or data.get("compatible", False)

    def test_compare_different_files(self, cli):
        """Comparing different files shows differences."""
        result = cli("seqcol", "compare", str(BASE_FASTA), str(DIFFERENT_NAMES_FASTA))

        # Exit code: 0=compatible, 1=incompatible (both are valid)
        assert result.exit_code in [0, 1]
        data = json.loads(result.stdout)
        # Should have comparison results
        assert isinstance(data, dict)
        assert "compatible" in data
        # Different names should be incompatible
        assert data["compatible"] is False

    def test_compare_different_order(self, cli):
        """Comparing files with different order."""
        result = cli("seqcol", "compare", str(BASE_FASTA), str(DIFFERENT_ORDER_FASTA))

        # Exit code: 0=compatible, 1=incompatible
        assert result.exit_code in [0, 1]
        data = json.loads(result.stdout)
        # Should have comparison results
        assert isinstance(data, dict)
        assert "compatible" in data

    def test_compare_subset(self, cli):
        """Comparing superset/subset."""
        result = cli("seqcol", "compare", str(BASE_FASTA), str(SUBSET_FASTA))

        # Exit code: 0=compatible, 1=incompatible
        assert result.exit_code in [0, 1]
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "compatible" in data

    def test_compare_seqcol_json_files(self, cli, sample_fasta, tmp_path):
        """Compare using seqcol JSON files."""
        # First create seqcol JSON
        seqcol1 = tmp_path / "a.seqcol.json"
        seqcol2 = tmp_path / "b.seqcol.json"

        cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol1))
        cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol2))

        result = cli("seqcol", "compare", str(seqcol1), str(seqcol2))

        assert result.exit_code == 0

    def test_compare_nonexistent_file(self, cli, sample_fasta):
        """Returns error for nonexistent file."""
        result = cli("seqcol", "compare", str(sample_fasta), "/nonexistent.fa")

        assert result.exit_code != 0


class TestSeqcolValidate:
    """Tests for: refget seqcol validate <file>"""

    def test_validate_valid_seqcol(self, cli, sample_fasta, tmp_path):
        """Validates valid seqcol JSON."""
        seqcol = tmp_path / "test.seqcol.json"
        cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol))

        result = cli("seqcol", "validate", str(seqcol))

        assert result.exit_code == 0

    def test_validate_invalid_seqcol(self, cli, tmp_path):
        """Fails validation for invalid seqcol JSON."""
        invalid = tmp_path / "invalid.seqcol.json"
        invalid.write_text('{"names": ["chr1"], "lengths": []}')  # Mismatched arrays

        result = cli("seqcol", "validate", str(invalid))

        assert result.exit_code != 0

    def test_validate_not_json(self, cli, tmp_path):
        """Fails validation for non-JSON file."""
        not_json = tmp_path / "notjson.seqcol.json"
        not_json.write_text("This is not JSON")

        result = cli("seqcol", "validate", str(not_json))

        assert result.exit_code != 0


class TestSeqcolDigest:
    """Tests for: refget seqcol digest <file>"""

    def test_digest_from_seqcol_json(self, cli, sample_fasta, tmp_path):
        """Computes digest from seqcol JSON."""
        seqcol = tmp_path / "test.seqcol.json"
        cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol))

        result = cli("seqcol", "digest", str(seqcol))

        data = assert_json_output(result, ["digest"])
        assert len(data["digest"]) >= 32

    def test_digest_from_fasta(self, cli, sample_fasta):
        """Computes digest from FASTA file."""
        result = cli("seqcol", "digest", str(sample_fasta))

        data = assert_json_output(result, ["digest"])
        assert len(data["digest"]) >= 32

    def test_digest_matches_fasta_digest(self, cli):
        """Seqcol digest matches fasta digest command."""
        # Both should produce the same digest
        result1 = cli("fasta", "digest", str(BASE_FASTA))
        result2 = cli("seqcol", "digest", str(BASE_FASTA))

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        digest1 = json.loads(result1.stdout)["digest"]
        digest2 = json.loads(result2.stdout)["digest"]
        assert digest1 == digest2


class TestSeqcolAttributes:
    """Tests for: refget seqcol attributes <file>"""

    def test_list_attributes(self, cli, sample_fasta, tmp_path):
        """Lists attributes of seqcol."""
        seqcol = tmp_path / "test.seqcol.json"
        cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol))

        result = cli("seqcol", "attributes", str(seqcol))

        assert result.exit_code == 0
        # Should list attribute names
        assert "names" in result.stdout.lower() or "lengths" in result.stdout.lower()


class TestSeqcolSchema:
    """Tests for: refget seqcol schema"""

    def test_show_schema(self, cli):
        """Shows seqcol schema."""
        result = cli("seqcol", "schema")

        assert result.exit_code == 0
        # Should output some schema information
        assert len(result.stdout) > 0


class TestSeqcolServers:
    """Tests for: refget seqcol servers"""

    def test_list_servers(self, cli):
        """List configured seqcol servers."""
        result = cli("seqcol", "servers")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "servers" in data


class TestSeqcolErrorHandling:
    """Test error handling for seqcol commands."""

    def test_compare_missing_argument(self, cli):
        """Compare with missing argument fails."""
        result = cli("seqcol", "compare", str(BASE_FASTA))

        assert result.exit_code != 0

    def test_invalid_file_format(self, cli, tmp_path):
        """Invalid file format produces clear error."""
        invalid = tmp_path / "invalid.txt"
        invalid.write_text("random text content")

        result = cli("seqcol", "digest", str(invalid))

        assert result.exit_code != 0


class TestSeqcolLocalStoreLookup:
    """Tests for local store lookup in seqcol show and compare commands."""

    def test_show_from_local_store(self, cli, populated_store):
        """Show command retrieves collection from local store."""
        digest = populated_store["digest"]
        store_path = populated_store["path"]

        # Use REFGET_STORE env var to point to our test store
        import os

        old_env = os.environ.get("REFGET_STORE")
        os.environ["REFGET_STORE"] = str(store_path)

        try:
            result = cli("seqcol", "show", digest)

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            # Level 2 (default) should have arrays
            assert "names" in data
            assert "lengths" in data
            assert "sequences" in data
            assert isinstance(data["names"], list)
        finally:
            if old_env:
                os.environ["REFGET_STORE"] = old_env
            elif "REFGET_STORE" in os.environ:
                del os.environ["REFGET_STORE"]

    def test_show_from_local_store_level1(self, cli, populated_store):
        """Show command with level=1 returns digests from local store."""
        digest = populated_store["digest"]
        store_path = populated_store["path"]

        import os

        old_env = os.environ.get("REFGET_STORE")
        os.environ["REFGET_STORE"] = str(store_path)

        try:
            result = cli("seqcol", "show", digest, "--level", "1")

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            # Level 1 should have string digests, not arrays
            assert "names" in data
            assert "lengths" in data
            assert "sequences" in data
            assert isinstance(data["names"], str)
            assert isinstance(data["lengths"], str)
            assert isinstance(data["sequences"], str)
        finally:
            if old_env:
                os.environ["REFGET_STORE"] = old_env
            elif "REFGET_STORE" in os.environ:
                del os.environ["REFGET_STORE"]

    def test_compare_uses_local_store_for_digest(self, cli, populated_store):
        """Compare command resolves digest inputs from local store first."""
        digest = populated_store["digest"]
        store_path = populated_store["path"]

        import os

        old_env = os.environ.get("REFGET_STORE")
        os.environ["REFGET_STORE"] = str(store_path)

        try:
            # Compare local store collection with itself
            result = cli("seqcol", "compare", digest, digest)

            # Should succeed (both resolved from local store)
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data.get("compatible", False) is True
        finally:
            if old_env:
                os.environ["REFGET_STORE"] = old_env
            elif "REFGET_STORE" in os.environ:
                del os.environ["REFGET_STORE"]

    def test_compare_local_digest_with_fasta(self, cli, populated_store):
        """Compare local store digest with FASTA file."""
        digest = populated_store["digest"]
        store_path = populated_store["path"]

        import os

        old_env = os.environ.get("REFGET_STORE")
        os.environ["REFGET_STORE"] = str(store_path)

        try:
            # Compare local store collection with original FASTA
            result = cli("seqcol", "compare", digest, str(BASE_FASTA))

            # Should succeed and show they are compatible (same content)
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data.get("compatible") is True
        finally:
            if old_env:
                os.environ["REFGET_STORE"] = old_env
            elif "REFGET_STORE" in os.environ:
                del os.environ["REFGET_STORE"]

    def test_show_nonexistent_digest_not_in_local_store(self, cli, temp_store, monkeypatch):
        """Show command falls back to remote for digest not in local store."""
        # Use a digest that doesn't exist anywhere
        fake_digest = "NONEXISTENT123456789012345678901234567890"

        monkeypatch.setenv("REFGET_STORE", str(temp_store))

        result = cli("seqcol", "show", fake_digest)

        # Should fail (not in local store, not on remote servers)
        assert result.exit_code != 0
